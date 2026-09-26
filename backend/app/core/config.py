"""
Central configuration for the Agentic CSE Research Assistant backend.

All values are read from the environment (or a local .env file) so no
credentials are ever hardcoded. See ../../.env.example for the full list.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM provider ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Storage ---
    # Phase 1 uses a JSON-file-backed store under this directory. This is
    # swapped for a real database (Postgres/Mongo) in a later phase without
    # changing the SessionStore interface (see services/session_store.py).
    data_dir: str = "data/sessions"

    # --- Research workflow limits ---
    max_literature_results: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
