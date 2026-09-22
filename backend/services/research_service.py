"""
In-memory research store + background execution service.

For a simple Replit-style deployment we deliberately avoid Redis or any
external infrastructure: a process-local dict is enough to track research
status and results, matching the "lightweight" requirement.
"""
from __future__ import annotations

import logging
import uuid
from threading import Lock
from typing import Any

from src.graph.workflow import run_research

logger = logging.getLogger(__name__)

# research_id -> ResearchState-like dict
_STORE: dict[str, dict[str, Any]] = {}
_LOCK = Lock()


def create_research(question: str) -> str:
    research_id = str(uuid.uuid4())[:8]
    with _LOCK:
        _STORE[research_id] = {
            "research_id": research_id,
            "user_question": question,
            "status": "queued",
            "current_step": "queued",
            "agent_logs": [],
            "errors": [],
            "replan_count": 0,
        }
    return research_id


def get_research(research_id: str) -> dict[str, Any] | None:
    with _LOCK:
        return _STORE.get(research_id)


def _update(research_id: str, state: dict[str, Any]) -> None:
    with _LOCK:
        _STORE[research_id] = state


def execute_research(research_id: str, question: str) -> None:
    """Runs synchronously inside a FastAPI BackgroundTask (i.e. off the
    request/response cycle, so POST /api/research returns immediately)."""
    with _LOCK:
        if research_id in _STORE:
            _STORE[research_id]["status"] = "planning"

    try:
        final_state = run_research(research_id, question)
        _update(research_id, dict(final_state))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Research run %s failed", research_id)
        with _LOCK:
            existing = _STORE.get(research_id, {"research_id": research_id, "user_question": question})
            existing["status"] = "failed"
            existing.setdefault("errors", []).append(str(exc))
            _STORE[research_id] = existing
