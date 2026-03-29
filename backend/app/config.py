from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # LLM Provider API Keys
    groq_api_key: str = ""
    cerebras_api_key: str = ""
    openrouter_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/experiments.db"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Debate Defaults
    default_max_rounds: int = 5
    default_max_turns_per_round: int = 3
    deadlock_similarity_threshold: float = 0.90

    # Metrics
    sentence_transformer_model: str = "all-MiniLM-L6-v2"

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


settings = Settings()
