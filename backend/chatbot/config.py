import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class ChatbotSettings(BaseSettings):
    # LLM Provider: 'groq' or 'ollama'
    # Defaults to 'groq' if GROQ_API_KEY is set, otherwise 'ollama'
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq" if os.getenv("GROQ_API_KEY") else "ollama")
    
    # Groq Cloud Configuration
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Ollama Local Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    
    # Generation parameters
    TEMPERATURE: float = float(os.getenv("CHATBOT_TEMPERATURE", "0.2"))
    MAX_TOKENS: int = int(os.getenv("CHATBOT_MAX_TOKENS", "2048"))
    MAX_TOOL_ITERATIONS: int = int(os.getenv("CHATBOT_MAX_TOOL_ITERATIONS", "5"))
    MAX_RETRIES: int = int(os.getenv("CHATBOT_MAX_RETRIES", "3"))
    REQUIRE_CONFIRMATION: bool = os.getenv("REQUIRE_ACTION_CONFIRMATION", "true").lower() in ["1", "true", "yes"]

settings = ChatbotSettings()
