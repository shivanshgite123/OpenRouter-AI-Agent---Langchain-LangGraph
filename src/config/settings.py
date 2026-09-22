"""
Centralized configuration for the Multi-Agent AI Research System.

All configuration is sourced from environment variables (typically via a
.env file). Nothing here should ever hard-code an API key.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Model provider -----------------------------------------------
    model_provider: str = Field(default="openai", alias="MODEL_PROVIDER")
    model_name: str = Field(default="gpt-4o-mini", alias="MODEL_NAME")

    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    jina_api_key: str | None = Field(default=None, alias="JINA_API_KEY")

    # --- Research behaviour ---------------------------------------------
    max_search_results: int = Field(default=10, alias="MAX_SEARCH_RESULTS")
    max_replans: int = Field(default=2, alias="MAX_REPLANS")
    max_scrape_chars: int = Field(default=4000, alias="MAX_SCRAPE_CHARS")

    # --- Services ---------------------------------------------------------
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    streamlit_port: int = Field(default=8501, alias="STREAMLIT_PORT")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")

    # --- Mock mode ----------------------------------------------------
    mock_mode: bool = Field(default=False, alias="MOCK_MODE")

    @property
    def effective_mock_mode(self) -> bool:
        """Force mock mode on automatically if required API keys are missing."""
        if self.mock_mode:
            return True
        if self.model_provider == "openai" and not self.openai_api_key:
            return True
        if self.model_provider == "google" and not self.google_api_key:
            return True
        if not self.tavily_api_key:
            return True
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()
