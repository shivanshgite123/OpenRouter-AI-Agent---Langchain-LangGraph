"""
Typed shared state for the LangGraph research workflow.

This is the single object threaded through every node in the graph. Keeping
it flat and well-typed makes the workflow easy to debug and to inspect from
the FastAPI / Streamlit layers.
"""
from __future__ import annotations

from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    # --- identity --------------------------------------------------------
    research_id: str
    user_question: str

    # --- planning ----------------------------------------------------------
    research_plan: dict
    sub_questions: list[str]
    required_sources: list[str]
    current_step: str

    # --- querying ----------------------------------------------------------
    search_queries: list[str]
    rewritten_queries: list[str]

    # --- retrieval -----------------------------------------------------
    search_results: list[dict]
    documents: list[dict]
    ranked_documents: list[dict]

    # --- analysis ------------------------------------------------------
    findings: list[dict]
    evidence: list[dict]
    sources: list[dict]
    calculations: list[dict]

    # --- reflection ------------------------------------------------------
    critique: dict
    missing_information: list[str]
    follow_up_queries: list[str]

    # --- replanning ----------------------------------------------------
    replan_count: int
    max_replans: int

    # --- output ----------------------------------------------------------
    final_answer: str
    evaluation: dict

    # --- bookkeeping ---------------------------------------------------
    status: str
    errors: list[str]
    agent_logs: list[str]


def new_research_state(research_id: str, user_question: str, max_replans: int) -> ResearchState:
    """Create a fresh, fully-initialised ResearchState."""
    return ResearchState(
        research_id=research_id,
        user_question=user_question,
        research_plan={},
        sub_questions=[],
        required_sources=[],
        current_step="queued",
        search_queries=[],
        rewritten_queries=[],
        search_results=[],
        documents=[],
        ranked_documents=[],
        findings=[],
        evidence=[],
        sources=[],
        calculations=[],
        critique={},
        missing_information=[],
        follow_up_queries=[],
        replan_count=0,
        max_replans=max_replans,
        final_answer="",
        evaluation={},
        status="queued",
        errors=[],
        agent_logs=[],
    )


def log(state: ResearchState, message: str) -> None:
    """Append a concise, user-safe status line. No chain-of-thought, ever."""
    state.setdefault("agent_logs", []).append(message)
