import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.database import get_db
from chatbot.config import settings
from chatbot.tools import INVENTORY_TOOLS, ACTION_TOOL_NAMES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["StockSense AI Assistant (LangGraph)"])

PROMPT_FILE = Path(__file__).parent / "prompt.txt"

def load_system_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8")
    return "You are StockSense AI, the intelligent virtual inventory co-pilot."


# ============================================================================
# PYDANTIC API CONTRACTS
# ============================================================================

class ChatMessageItem(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

class PendingAction(BaseModel):
    action_id: str
    tool: str
    arguments: Dict[str, Any]
    summary: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User prompt or inventory query")
    session_id: Optional[str] = Field(default="default", description="Conversation session ID for memory persistence")
    history: Optional[List[ChatMessageItem]] = Field(default=[], description="Previous conversation messages")
    confirmed_action: Optional[PendingAction] = Field(default=None, description="Action payload confirmed by user")
    provider: Optional[str] = Field(default=None, description="Override LLM provider ('groq' or 'ollama')")

class ChatResponse(BaseModel):
    reply: str
    actions_performed: List[Dict[str, Any]] = []
    pending_action: Optional[PendingAction] = None
    session_id: str
    provider: str
    model: str
    status: str


# ============================================================================
# LANGGRAPH STATE & WORKFLOW
# ============================================================================

class AgentState(MessagesState):
    pending_action: Optional[Dict[str, Any]]
    actions_performed: List[Dict[str, Any]]
    confirmed: bool


def format_action_summary(tool_name: str, args: Dict[str, Any]) -> str:
    """Format action and arguments into a clean summary without hardcoded branching."""
    action_label = tool_name.replace("_", " ").title()
    details = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in args.items() if v is not None)
    return f"{action_label} ({details})" if details else action_label


def get_llm(provider: str):
    """Instantiate production-grade LLM with exponential backoff retries."""
    if provider == "groq":
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("your_"):
            raise ValueError("GROQ_API_KEY is not configured.")
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=settings.TEMPERATURE,
            max_retries=settings.MAX_RETRIES,
            timeout=30.0
        )
    base = settings.OLLAMA_BASE_URL.replace("/v1", "").rstrip("/")
    return ChatOllama(
        base_url=base,
        model=settings.OLLAMA_MODEL,
        temperature=settings.TEMPERATURE
    )


def build_agent_graph(llm):
    """
    Construct canonical LangGraph workflow:
    - Uses official prebuilt ToolNode
    - Human-in-the-Loop Confirmation Gate for state-changing operations
    - Conversation checkpointing via MemorySaver
    """
    llm_with_tools = llm.bind_tools(INVENTORY_TOOLS)
    tool_node = ToolNode(INVENTORY_TOOLS)

    def agent_node(state: AgentState) -> Dict[str, Any]:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def confirmation_gate_node(state: AgentState) -> Dict[str, Any]:
        """Intercepts mutating actions, stages pending_action, and prompts assistant to request confirmation."""
        last_msg = state["messages"][-1]
        tool_results = []
        pending_act = None

        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                t_name = tc.get("name")
                t_args = tc.get("args") or {}
                t_id = tc.get("id")

                if t_name in ACTION_TOOL_NAMES:
                    summary = format_action_summary(t_name, t_args)
                    pending_act = {
                        "action_id": f"act_{uuid.uuid4().hex[:8]}",
                        "tool": t_name,
                        "arguments": t_args,
                        "summary": summary
                    }
                    instruction = (
                        f"The action '{summary}' is ready. Summarize the details to the user "
                        f"and ask for their explicit confirmation before proceeding."
                    )
                    tool_results.append(ToolMessage(
                        content=json.dumps({"status": "confirmation_required", "summary": summary, "instruction": instruction}),
                        tool_call_id=t_id,
                        name=t_name
                    ))

        return {
            "messages": tool_results,
            "pending_action": pending_act
        }

    def route_agent_output(state: AgentState) -> str:
        last_msg = state["messages"][-1]
        if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
            return END

        # If any requested tool is a state-changing action and not yet confirmed, route to confirmation gate
        has_mutating_action = any(tc.get("name") in ACTION_TOOL_NAMES for tc in last_msg.tool_calls)
        if has_mutating_action and not state.get("confirmed", False):
            return "confirmation_gate"

        return "tools"

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("confirmation_gate", confirmation_gate_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        route_agent_output,
        {
            "tools": "tools",
            "confirmation_gate": "confirmation_gate",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("confirmation_gate", "agent")

    return workflow.compile(checkpointer=MemorySaver())


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Production-grade conversational agent endpoint powered by LangGraph:
    - Full tool execution using prebuilt ToolNode
    - Human-in-the-loop action confirmation gate
    - Built-in tenacity exponential backoff on 429/5xx
    """
    provider = (payload.provider or settings.LLM_PROVIDER).lower()
    model = settings.GROQ_MODEL if provider == "groq" else settings.OLLAMA_MODEL
    session_id = payload.session_id or "default"
    actions_performed = []

    # 1. Handle Explicit Action Confirmation (from frontend button click / confirmed payload)
    if payload.confirmed_action:
        t_name = payload.confirmed_action.tool
        t_args = payload.confirmed_action.arguments
        tools_map = {t.name: t for t in INVENTORY_TOOLS}
        tool_func = tools_map.get(t_name)
        if tool_func:
            raw_res = tool_func.invoke(t_args, config={"configurable": {"db": db}})
            res_obj = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
            actions_performed.append({"action": t_name, "args": t_args, "result": res_obj})
            return {
                "reply": f"✅ Confirmed and executed: {payload.confirmed_action.summary}\n\nResult: {res_obj.get('message', 'Completed successfully')}",
                "actions_performed": actions_performed,
                "pending_action": None,
                "session_id": session_id,
                "provider": provider,
                "model": model,
                "status": "action_confirmed"
            }

    # 2. Check if user typed an affirmative confirmation ("yes", "confirm", "proceed")
    user_text = payload.message.strip().lower()
    is_affirming = user_text in ["yes", "confirm", "proceed", "sure", "do it", "ok", "go ahead"]

    try:
        llm = get_llm(provider)
        agent = build_agent_graph(llm)

        # Build conversation messages
        messages: List[BaseMessage] = [SystemMessage(content=load_system_prompt())]
        if payload.history:
            for item in payload.history:
                if item.role == "user":
                    messages.append(HumanMessage(content=item.content))
                elif item.role == "assistant":
                    messages.append(AIMessage(content=item.content))
        messages.append(HumanMessage(content=payload.message))

        # Invoke LangGraph workflow with dependency injection
        config = {"configurable": {"thread_id": session_id, "db": db}}
        final_state = await agent.ainvoke(
            {
                "messages": messages,
                "pending_action": None,
                "actions_performed": [],
                "confirmed": is_affirming
            },
            config=config
        )

        last_msg = final_state["messages"][-1]
        reply_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        pending = final_state.get("pending_action")
        pending_obj = PendingAction(**pending) if pending else None

        # Track actions executed by ToolNode in this turn
        for m in final_state["messages"]:
            if isinstance(m, ToolMessage) and m.name in ACTION_TOOL_NAMES:
                try:
                    res_json = json.loads(m.content)
                    if res_json.get("status") != "confirmation_required":
                        actions_performed.append({"action": m.name, "result": res_json})
                except Exception:
                    pass

        return {
            "reply": reply_text or "Processed request.",
            "actions_performed": actions_performed,
            "pending_action": pending_obj,
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "status": "success"
        }

    except Exception as ex:
        logger.warning(f"LangGraph execution exception ({ex}). Running fallback handler.")
        return handle_fallback(payload.message, db, provider, model, str(ex), session_id)


def handle_fallback(message: str, db: Session, provider: str, model: str, reason: str, session_id: str) -> Dict[str, Any]:
    """Production fallback when external LLM service is offline."""
    msg = message.lower()
    tools_map = {t.name: t for t in INVENTORY_TOOLS}

    if "status" in msg and ("predict" in msg or "might" in msg or "future" in msg):
        raw = tools_map["predict_inventory_trends"].invoke({}, config={"configurable": {"db": db}})
        data = json.loads(raw)
        reply = (
            f"### 📊 Inventory Predictive Analysis (Fallback)\n\n"
            f"**Outlook:** {data.get('outlook')}\n\n"
            f"- **Imminent Stockout Hazards:** {data.get('stockout_hazards_count')} items\n"
            f"- **Recommended Procurement Reorders:** {len(data.get('recommended_reorders', []))} items ready for purchase order\n"
        )
        return {"reply": reply, "actions_performed": [], "pending_action": None, "session_id": session_id, "provider": provider, "model": model, "status": "fallback"}

    if "status" in msg or "overview" in msg or "health" in msg:
        raw = tools_map["get_inventory_status"].invoke({}, config={"configurable": {"db": db}})
        data = json.loads(raw)
        k = data.get("kpis", {})
        reply = (
            f"### 📦 StockSense Current Inventory Status (Fallback)\n\n"
            f"- **Total Products:** {k.get('total_products', 0)}\n"
            f"- **Total Inventory Valuation:** ${data.get('total_valuation_usd', 0.0):,.2f}\n"
            f"- **Low Stock Items:** {k.get('low_stock_items', 0)}\n"
            f"- **Pending Shipments:** {k.get('pending_receipts', 0)} Inbound Receipts, {k.get('pending_deliveries', 0)} Outbound Deliveries\n"
            f"- **Total Stock Movements Audited:** {k.get('total_stock_movements', 0):,}\n"
        )
        return {"reply": reply, "actions_performed": [], "pending_action": None, "session_id": session_id, "provider": provider, "model": model, "status": "fallback"}

    if "create" in msg and "product" in msg:
        name = "New Item"
        for part in message.split('"'):
            if len(part.strip()) > 2 and "create" not in part.lower():
                name = part.strip()
                break
        pending = PendingAction(
            action_id=f"act_{uuid.uuid4().hex[:8]}",
            tool="create_product",
            arguments={"product_name": name, "stock_quantity": 20, "unit_price": 49.99},
            summary=f"Create new product '{name}' (Stock: 20, Price: $49.99)"
        )
        return {
            "reply": f"⚠️ **Confirmation Required:**\n\nI have prepared to create product **{name}** with initial stock of **20 units** at **$49.99**.\n\nWould you like me to proceed and add this to the inventory?",
            "actions_performed": [],
            "pending_action": pending,
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "status": "pending_confirmation"
        }

    return {
        "reply": f"👋 StockSense AI is online.\n\n*Note: LLM provider ({provider}) offline ({reason}). Add `GROQ_API_KEY` in `.env` or start Ollama (`ollama serve`).*",
        "actions_performed": [],
        "pending_action": None,
        "session_id": session_id,
        "provider": provider,
        "model": model,
        "status": "fallback"
    }


@router.get("/status")
def status_endpoint():
    """Health check verifying LangGraph engine and provider setup."""
    provider = settings.LLM_PROVIDER.lower()
    model = settings.GROQ_MODEL if provider == "groq" else settings.OLLAMA_MODEL
    has_groq = bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your_"))
    return {
        "framework": "LangGraph",
        "provider": provider,
        "model": model,
        "max_retries": settings.MAX_RETRIES,
        "configured": has_groq if provider == "groq" else False,
        "prompt_loaded": PROMPT_FILE.exists()
    }


@router.get("/tools")
def tools_endpoint():
    """List all registered LangGraph tools."""
    return {
        "framework": "LangGraph",
        "count": len(INVENTORY_TOOLS),
        "tools": [
            {"name": t.name, "description": t.description}
            for t in INVENTORY_TOOLS
        ]
    }
