"""
Model factory - returns a configured LangChain chat model based on the
MODEL_PROVIDER / MODEL_NAME environment variables. Never hard-codes keys.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel

from src.config.settings import get_settings


@lru_cache
def get_chat_model(temperature: float = 0.0) -> BaseChatModel:
    """Build (and cache) the chat model configured for this deployment."""
    settings = get_settings()

    if settings.model_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.model_name or "gemini-2.5-flash",
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )

    # default: openai
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.model_name or "gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=temperature,
    )
