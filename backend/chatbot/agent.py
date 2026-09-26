import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any, Sequence, TypedDict, Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from app.database import get_db
from app.models import Product, Receipt, Delivery, Adjustment, MoveHistory
from app.fetchers import (
    dashboard_fetcher, product_fetcher, receipt_fetcher,
    delivery_fetcher, transfer_fetcher, move_fetcher, warehouse_fetcher
)
from chatbot.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["AI Inventory Chatbot (LangGraph)"])

PROMPT_FILE = Path(__file__).parent / "prompt.txt"

def load_system_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8")
    return "You are StockSense AI, the intelligent virtual inventory co-pilot."

def _gen_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

# ============================================================================
# PYDANTIC SCHEMAS
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
    message: str = Field(..., min_length=1, max_length=2000, description="User prompt or question")
    session_id: Optional[str] = Field(default="default", description="Conversation session ID for memory persistence")
    history: Optional[List[ChatMessageItem]] = Field(default=[], description="Previous conversation messages")
    confirmed_action: Optional[PendingAction] = Field(default=None, description="Action payload confirmed by the user")
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
# TOOL BUILDER (Directly reuses existing backend models & fetchers)
# ============================================================================

ACTION_TOOLS = {
    "create_product",
    "create_receipt",
    "validate_receipt",
    "create_delivery",
    "validate_delivery",
    "create_stock_adjustment"
}

def format_action_summary(tool_name: str, args: Dict[str, Any]) -> str:
    if tool_name == "create_product":
        name = args.get("product_name", "Unknown Item")
        price = args.get("unit_price", 0.0)
        stock = args.get("stock_quantity", 0)
        return f"Create product '{name}' (Initial Stock: {stock}, Price: ${price:.2f})"
    elif tool_name == "create_receipt":
        return f"Create inbound receipt for {args.get('quantity_received', 0)} units of SKU '{args.get('product_id')}'"
    elif tool_name == "validate_receipt":
        return f"Validate inbound receipt '{args.get('receipt_id')}' and add stock to inventory"
    elif tool_name == "create_delivery":
        return f"Create outbound delivery of {args.get('quantity_delivered', 0)} units of SKU '{args.get('product_id')}' to '{args.get('customer_name', 'Customer')}'"
    elif tool_name == "validate_delivery":
        return f"Validate outbound delivery '{args.get('delivery_id')}' and decrement stock"
    elif tool_name == "create_stock_adjustment":
        return f"Adjust physical stock for SKU '{args.get('product_id')}' to {args.get('counted_quantity', 0)} units"
    return f"Execute operation: {tool_name}"


def create_inventory_tools(db: Session, confirmation_granted: bool = False):
    """Factory creating LangChain tools bound to the active request DB session."""

    @tool
    def get_inventory_status() -> str:
        """Fetch real-time overall KPIs, total inventory valuation in USD, and health breakdown (low stock, out of stock, pending operations)."""
        kpis = dashboard_fetcher.fetch_kpis(db)
        products = db.query(Product).all()
        total_valuation = round(sum(p.stock_quantity * (p.unit_price or 0.0) for p in products), 2)
        out_of_stock = [p.product_name for p in products if p.stock_quantity == 0]
        return json.dumps({
            "kpis": kpis,
            "total_valuation_usd": total_valuation,
            "out_of_stock_items": out_of_stock[:10],
            "categories": product_fetcher.fetch_categories(db)
        })

    @tool
    def predict_inventory_trends() -> str:
        """Analyze sales volume, turnover rates, and pending orders to forecast stockout risks, overstocked items, and recommended replenishment quantities."""
        products = db.query(Product).all()
        stockout_hazards = []
        reorder_plans = []
        for p in products:
            if p.stock_quantity <= p.reorder_level:
                stockout_hazards.append({
                    "sku": p.product_id,
                    "name": p.product_name,
                    "stock": p.stock_quantity,
                    "reorder_level": p.reorder_level,
                    "urgency": "CRITICAL" if p.stock_quantity == 0 else "HIGH"
                })
                reorder_plans.append({
                    "sku": p.product_id,
                    "name": p.product_name,
                    "suggested_order_qty": p.reorder_quantity or 50,
                    "supplier": p.supplier_name or p.supplier_id or "Primary Supplier"
                })
        return json.dumps({
            "stockout_hazards_count": len(stockout_hazards),
            "stockout_hazards": stockout_hazards[:8],
            "recommended_reorders": reorder_plans[:8],
            "outlook": "Replenishment required for low-stock SKUs." if stockout_hazards else "Inventory levels are healthy."
        })

    @tool
    def search_products(search: Optional[str] = None, category: Optional[str] = None, warehouse: Optional[str] = None, low_stock_only: bool = False, limit: int = 20) -> str:
        """Search products with filters (search query, category, warehouse, low_stock_only)."""
        res = product_fetcher.fetch(db, search=search, category=category, warehouse=warehouse, low_stock_only=low_stock_only, limit=limit)
        items = [
            {"sku": p.product_id, "name": p.product_name, "category": p.category, "stock": p.stock_quantity, "price": p.unit_price}
            for p in res.get("items", [])
        ]
        return json.dumps({"total": res.get("total", 0), "products": items})

    @tool
    def get_product(sku: str) -> str:
        """Get full details of a specific product by SKU or product_id."""
        p = product_fetcher.fetch_by_sku(db, sku)
        if not p:
            return json.dumps({"error": f"Product with SKU '{sku}' not found"})
        return json.dumps({
            "sku": p.product_id, "name": p.product_name, "category": p.category,
            "stock": p.stock_quantity, "unit_price": p.unit_price, "rack": p.rack_location,
            "warehouse": p.warehouse_name, "supplier": p.supplier_name, "status": p.status
        })

    @tool
    def create_product(product_name: str, product_id: Optional[str] = None, category: str = "General", stock_quantity: int = 0, unit_price: float = 0.0, reorder_level: int = 10, reorder_quantity: int = 50, warehouse_name: str = "Main Warehouse", rack_location: str = "A-01-01") -> str:
        """Action: Add and register a new product in the inventory. Requires confirmation before execution."""
        args = {
            "product_name": product_name, "product_id": product_id, "category": category,
            "stock_quantity": stock_quantity, "unit_price": unit_price, "reorder_level": reorder_level,
            "reorder_quantity": reorder_quantity, "warehouse_name": warehouse_name, "rack_location": rack_location
        }
        if not confirmation_granted:
            summary = format_action_summary("create_product", args)
            return json.dumps({"status": "confirmation_required", "tool": "create_product", "arguments": args, "summary": summary})

        pid = product_id or _gen_id("SKU")
        if product_fetcher.fetch_by_sku(db, pid):
            return json.dumps({"error": f"Product with SKU '{pid}' already exists"})

        product = Product(
            product_id=pid, product_name=product_name, category=category,
            stock_quantity=int(stock_quantity), unit_price=float(unit_price),
            reorder_level=int(reorder_level), reorder_quantity=int(reorder_quantity),
            unit_of_measure="units", warehouse_name=warehouse_name,
            rack_location=rack_location, status="Active", date_received=datetime.now().strftime("%m/%d/%Y")
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        if product.stock_quantity > 0:
            move = MoveHistory(
                move_id=_gen_id("MOV-INIT"), product_id=product.product_id, movement_type="Receipt",
                from_location="Initial Setup", to_location=product.rack_location,
                quantity=product.stock_quantity, timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                reference_id="INITIAL_STOCK"
            )
            db.add(move)
            db.commit()

        return json.dumps({"success": True, "message": f"Successfully created product '{product.product_name}'", "sku": product.product_id, "stock": product.stock_quantity})

    @tool
    def create_receipt(product_id: str, quantity_received: int, supplier_id: str = "SUP-001") -> str:
        """Action: Register an inbound purchase receipt in Draft status. Requires confirmation before execution."""
        args = {"product_id": product_id, "quantity_received": quantity_received, "supplier_id": supplier_id}
        if not confirmation_granted:
            summary = format_action_summary("create_receipt", args)
            return json.dumps({"status": "confirmation_required", "tool": "create_receipt", "arguments": args, "summary": summary})

        receipt = Receipt(
            receipt_id=_gen_id("REC"), supplier_id=supplier_id, product_id=product_id,
            quantity_received=int(quantity_received), receipt_date=datetime.now().strftime("%m/%d/%Y"), status="Draft"
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        return json.dumps({"success": True, "receipt_id": receipt.receipt_id, "status": receipt.status})

    @tool
    def validate_receipt(receipt_id: str) -> str:
        """Action: Validate and complete incoming receipt, incrementing physical stock. Requires confirmation."""
        args = {"receipt_id": receipt_id}
        if not confirmation_granted:
            summary = format_action_summary("validate_receipt", args)
            return json.dumps({"status": "confirmation_required", "tool": "validate_receipt", "arguments": args, "summary": summary})

        receipt = db.query(Receipt).filter(Receipt.receipt_id == receipt_id).first()
        if not receipt:
            return json.dumps({"error": f"Receipt '{receipt_id}' not found"})
        if receipt.status == "Done":
            return json.dumps({"error": "Receipt is already completed"})

        p = product_fetcher.fetch_by_sku(db, receipt.product_id)
        if p:
            p.stock_quantity += receipt.quantity_received
        receipt.status = "Done"

        move = MoveHistory(
            move_id=_gen_id("MOV-REC"), product_id=receipt.product_id, movement_type="Receipt",
            from_location="Vendors / Supplier", to_location=p.rack_location if p else "Main Warehouse",
            quantity=receipt.quantity_received, timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
            reference_id=receipt.receipt_id
        )
        db.add(move)
        db.commit()
        return json.dumps({"success": True, "message": f"Receipt {receipt.receipt_id} validated. New stock: {p.stock_quantity if p else 'N/A'}"})

    @tool
    def create_delivery(product_id: str, quantity_delivered: int, customer_name: str = "General Customer") -> str:
        """Action: Create an outbound delivery order in Draft status. Requires confirmation."""
        args = {"product_id": product_id, "quantity_delivered": quantity_delivered, "customer_name": customer_name}
        if not confirmation_granted:
            summary = format_action_summary("create_delivery", args)
            return json.dumps({"status": "confirmation_required", "tool": "create_delivery", "arguments": args, "summary": summary})

        delivery = Delivery(
            delivery_id=_gen_id("DEL"), product_id=product_id, quantity_delivered=int(quantity_delivered),
            customer_name=customer_name, delivery_date=datetime.now().strftime("%m/%d/%Y"), status="Draft"
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return json.dumps({"success": True, "delivery_id": delivery.delivery_id, "status": delivery.status})

    @tool
    def validate_delivery(delivery_id: str) -> str:
        """Action: Validate outbound delivery, decrementing physical stock and creating movement record. Requires confirmation."""
        args = {"delivery_id": delivery_id}
        if not confirmation_granted:
            summary = format_action_summary("validate_delivery", args)
            return json.dumps({"status": "confirmation_required", "tool": "validate_delivery", "arguments": args, "summary": summary})

        delivery = db.query(Delivery).filter(Delivery.delivery_id == delivery_id).first()
        if not delivery:
            return json.dumps({"error": f"Delivery '{delivery_id}' not found"})
        if delivery.status == "Done":
            return json.dumps({"error": "Delivery is already completed"})

        p = product_fetcher.fetch_by_sku(db, delivery.product_id)
        if p:
            if p.stock_quantity < delivery.quantity_delivered:
                return json.dumps({"error": f"Insufficient stock: {p.stock_quantity} available, {delivery.quantity_delivered} requested"})
            p.stock_quantity -= delivery.quantity_delivered
            p.sales_volume = (p.sales_volume or 0) + delivery.quantity_delivered
        delivery.status = "Done"

        move = MoveHistory(
            move_id=_gen_id("MOV-DEL"), product_id=delivery.product_id, movement_type="Delivery",
            from_location=p.rack_location if p else "Main Warehouse", to_location=f"Customer: {delivery.customer_name}",
            quantity=delivery.quantity_delivered, timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
            reference_id=delivery.delivery_id
        )
        db.add(move)
        db.commit()
        return json.dumps({"success": True, "message": f"Delivery {delivery.delivery_id} validated. Remaining stock: {p.stock_quantity if p else 'N/A'}"})

    @tool
    def create_stock_adjustment(product_id: str, counted_quantity: int, reason: str = "Physical inventory count") -> str:
        """Action: Adjust physical inventory count and record variance in ledger. Requires confirmation."""
        args = {"product_id": product_id, "counted_quantity": counted_quantity, "reason": reason}
        if not confirmation_granted:
            summary = format_action_summary("create_stock_adjustment", args)
            return json.dumps({"status": "confirmation_required", "tool": "create_stock_adjustment", "arguments": args, "summary": summary})

        p = product_fetcher.fetch_by_sku(db, product_id)
        if not p:
            return json.dumps({"error": f"Product with SKU '{product_id}' not found"})

        recorded = p.stock_quantity
        diff = int(counted_quantity) - recorded
        p.stock_quantity = int(counted_quantity)

        adj = Adjustment(
            adjustment_id=_gen_id("ADJ"), product_id=product_id, recorded_quantity=recorded,
            counted_quantity=int(counted_quantity), adjustment_reason=reason,
            adjustment_date=datetime.now().strftime("%m/%d/%Y")
        )
        db.add(adj)
        db.commit()
        return json.dumps({"success": True, "message": f"Stock adjusted for '{p.product_name}' to {counted_quantity} (variance: {diff:+d})"})

    @tool
    def list_movements(movement_type: Optional[str] = None, limit: int = 15) -> str:
        """Query immutable stock movement ledger records."""
        res = move_fetcher.fetch(db, movement_type=movement_type, limit=limit)
        items = [
            {"move_id": m.move_id, "sku": m.product_id, "type": m.movement_type, "from": m.from_location, "to": m.to_location, "qty": m.quantity, "time": m.timestamp}
            for m in res.get("items", [])
        ]
        return json.dumps({"total": res.get("total", 0), "movements": items})

    @tool
    def list_warehouses() -> str:
        """List all registered warehouses and capacities."""
        res = warehouse_fetcher.fetch(db, limit=20)
        items = [{"id": w.warehouse_id, "name": w.warehouse_name, "city": w.city, "capacity": w.capacity} for w in res.get("items", [])]
        return json.dumps({"warehouses": items})

    return [
        get_inventory_status,
        predict_inventory_trends,
        search_products,
        get_product,
        create_product,
        create_receipt,
        validate_receipt,
        create_delivery,
        validate_delivery,
        create_stock_adjustment,
        list_movements,
        list_warehouses
    ]


# ============================================================================
# LLM FACTORY (Production-Grade with Built-in Retries)
# ============================================================================

def get_llm(provider: str):
    """Instantiate production-grade LLM client with native exponential backoff retries."""
    if provider == "groq":
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("your_"):
            raise ValueError("GROQ_API_KEY is not configured in .env.")
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=settings.TEMPERATURE,
            max_retries=settings.MAX_RETRIES,
            timeout=30.0
        )
    else:
        # Ollama local client
        base = settings.OLLAMA_BASE_URL.replace("/v1", "").rstrip("/")
        return ChatOllama(
            base_url=base,
            model=settings.OLLAMA_MODEL,
            temperature=settings.TEMPERATURE
        )


# ============================================================================
# LANGGRAPH STATE & AGENT ENGINE
# ============================================================================

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    pending_action: Optional[Dict[str, Any]]
    actions_performed: List[Dict[str, Any]]


def build_inventory_graph(tools_list: list, llm):
    """Build production-grade LangGraph workflow with tool calling and action gating."""
    tools_by_name = {t.name: t for t in tools_list}
    llm_with_tools = llm.bind_tools(tools_list)

    def agent_node(state: AgentState) -> Dict[str, Any]:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def tool_node(state: AgentState) -> Dict[str, Any]:
        last_msg = state["messages"][-1]
        tool_results = []
        pending_act = state.get("pending_action")
        performed = list(state.get("actions_performed") or [])

        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                t_name = tc.get("name")
                t_args = tc.get("args") or {}
                t_id = tc.get("id")

                t_func = tools_by_name.get(t_name)
                if t_func:
                    try:
                        raw_result = t_func.invoke(t_args)
                        parsed = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
                    except Exception as err:
                        parsed = {"error": str(err)}
                        raw_result = json.dumps(parsed)

                    # Check if action requires confirmation
                    if isinstance(parsed, dict) and parsed.get("status") == "confirmation_required":
                        pending_act = {
                            "action_id": f"act_{uuid.uuid4().hex[:8]}",
                            "tool": t_name,
                            "arguments": t_args,
                            "summary": parsed.get("summary", format_action_summary(t_name, t_args))
                        }
                        instruction_msg = json.dumps({
                            "status": "staged_pending_confirmation",
                            "summary": pending_act["summary"],
                            "instruction": f"The action '{pending_act['summary']}' is ready. Summarize the details to the user and politely ask for their confirmation before executing."
                        })
                        tool_results.append(ToolMessage(content=instruction_msg, tool_call_id=t_id, name=t_name))
                    else:
                        if t_name in ACTION_TOOLS:
                            performed.append({"action": t_name, "args": t_args, "result": parsed})
                        tool_results.append(ToolMessage(content=raw_result if isinstance(raw_result, str) else json.dumps(raw_result), tool_call_id=t_id, name=t_name))
                else:
                    tool_results.append(ToolMessage(content=json.dumps({"error": f"Tool '{t_name}' not found"}), tool_call_id=t_id, name=t_name))

        return {
            "messages": tool_results,
            "pending_action": pending_act,
            "actions_performed": performed
        }

    def should_continue(state: AgentState) -> str:
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=MemorySaver())


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Production-grade conversational endpoint powered by LangGraph:
    - Retries and exponential backoff on 429/5xx via LangChain/tenacity
    - Gated state-changing actions requiring user confirmation
    - Multi-turn conversation state persistence by session_id
    """
    provider = (payload.provider or settings.LLM_PROVIDER).lower()
    model = settings.GROQ_MODEL if provider == "groq" else settings.OLLAMA_MODEL
    session_id = payload.session_id or "default"
    actions_performed = []

    # 1. Handle Explicit Action Confirmation (from interactive button or confirmed_action payload)
    if payload.confirmed_action:
        t_name = payload.confirmed_action.tool
        t_args = payload.confirmed_action.arguments
        # Instantiate tools with confirmation_granted=True
        exec_tools = {t.name: t for t in create_inventory_tools(db, confirmation_granted=True)}
        tool_func = exec_tools.get(t_name)
        if tool_func:
            raw_res = tool_func.invoke(t_args)
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

    # 2. Check affirmative natural language confirmation ("yes", "confirm", "proceed")
    user_text_clean = payload.message.strip().lower()
    is_affirming = user_text_clean in ["yes", "confirm", "proceed", "sure", "do it", "ok", "go ahead"]

    # 3. Build LangGraph tools and app
    tools = create_inventory_tools(db, confirmation_granted=is_affirming)

    try:
        llm = get_llm(provider)
        app = build_inventory_graph(tools, llm)

        # Build message history
        messages: List[BaseMessage] = [SystemMessage(content=load_system_prompt())]
        if payload.history:
            for item in payload.history:
                if item.role == "user":
                    messages.append(HumanMessage(content=item.content))
                elif item.role == "assistant":
                    messages.append(AIMessage(content=item.content))
        messages.append(HumanMessage(content=payload.message))

        # Run LangGraph with session memory thread
        config = {"configurable": {"thread_id": session_id}}
        final_state = await app.ainvoke(
            {"messages": messages, "pending_action": None, "actions_performed": []},
            config=config
        )

        last_message = final_state["messages"][-1]
        reply_text = last_message.content if hasattr(last_message, "content") else str(last_message)
        pending = final_state.get("pending_action")
        pending_obj = PendingAction(**pending) if pending else None

        return {
            "reply": reply_text or "Processed your request.",
            "actions_performed": final_state.get("actions_performed") or [],
            "pending_action": pending_obj,
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "status": "success"
        }

    except Exception as ex:
        logger.warning(f"LangGraph execution exception ({ex}). Running rule-based fallback.")
        return handle_rule_fallback(payload.message, db, provider, model, str(ex), session_id)


def handle_rule_fallback(message: str, db: Session, provider: str, model: str, reason: str, session_id: str) -> Dict[str, Any]:
    """Graceful direct response when Groq/Ollama is offline or unconfigured."""
    msg = message.lower()
    tools_dict = {t.name: t for t in create_inventory_tools(db, confirmation_granted=True)}

    if "status" in msg and ("predict" in msg or "might" in msg or "future" in msg):
        raw = tools_dict["predict_inventory_trends"].invoke({})
        trends = json.loads(raw)
        reply = (
            f"### 📊 Inventory Predictive Analysis (LangGraph Fallback)\n\n"
            f"**Strategic Outlook:** {trends.get('outlook')}\n\n"
            f"- **Imminent Stockout Hazards:** {trends.get('stockout_hazards_count')} items\n"
            f"- **Recommended Reorders:** {len(trends.get('recommended_reorders', []))} items ready for purchase order\n"
        )
        return {"reply": reply, "actions_performed": [], "pending_action": None, "session_id": session_id, "provider": provider, "model": model, "status": "fallback"}

    if "status" in msg or "overview" in msg or "health" in msg:
        raw = tools_dict["get_inventory_status"].invoke({})
        status = json.loads(raw)
        k = status.get("kpis", {})
        total_val = status.get("total_valuation_usd", 0.0)
        reply = (
            f"### 📦 StockSense Current Inventory Status (LangGraph Fallback)\n\n"
            f"- **Total Products:** {k.get('total_products', 0)}\n"
            f"- **Total Inventory Valuation:** ${total_val:,.2f}\n"
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
        "reply": f"👋 StockSense AI (LangGraph) is active.\n\n*Note: LLM provider ({provider}) offline ({reason}). Add `GROQ_API_KEY` in `.env` or start Ollama (`ollama serve`).*",
        "actions_performed": [],
        "pending_action": None,
        "session_id": session_id,
        "provider": provider,
        "model": model,
        "status": "fallback"
    }


@router.get("/status")
def status_endpoint():
    """Verify LangGraph engine and LLM provider connectivity."""
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
def tools_endpoint(db: Session = Depends(get_db)):
    """Inspect all LangGraph tools available to the chatbot."""
    tools = create_inventory_tools(db)
    return {
        "framework": "LangGraph",
        "count": len(tools),
        "tools": [
            {"name": t.name, "description": t.description}
            for t in tools
        ]
    }
