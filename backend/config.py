import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "AI Financial Research Assistant"
    ENV: str = "development"
    DEBUG: bool = True

    # LLM & Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT: float = 60.0

    # Vector Database
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "financial_research"

    # Embedding Model
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # Database
    DATABASE_URL: str = f"sqlite:///{str(BASE_DIR / 'financial_assistant.db')}"
    SQLITE_DB_PATH: str = str(BASE_DIR / "financial_assistant.db")

    # API Keys
    ALPHA_VANTAGE_API_KEY: str = "demo"
    FMP_API_KEY: str = ""

    # RAG Settings
    TOP_K_RETRIEVAL: int = 4
    GROUNDING_THRESHOLD: float = 0.75

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
