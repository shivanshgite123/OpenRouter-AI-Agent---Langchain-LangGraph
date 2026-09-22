"""FastAPI backend entrypoint.

Run with:  uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import health, research
from src.config.settings import get_settings

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="Multi-Agent AI Research System",
    description="LangChain + LangGraph powered deep research API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(research.router)


@app.get("/")
def root():
    return {
        "service": "Multi-Agent AI Research System",
        "mock_mode": settings.effective_mock_mode,
        "docs": "/docs",
    }
