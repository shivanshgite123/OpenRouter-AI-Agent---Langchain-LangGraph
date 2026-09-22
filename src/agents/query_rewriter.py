"""Query Rewriter agent - turns the research plan into concrete search queries."""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.models.model_factory import get_chat_model
from src.prompts.solver import QUERY_REWRITER_PROMPT
from src.state.state import ResearchState, log


class QueryList(BaseModel):
    queries: list[str] = Field(description="3-6 distinct, high-value search queries")


def _dedupe(queries: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for q in queries:
        key = q.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(q.strip())
    return out


def rewrite_queries(state: ResearchState) -> ResearchState:
    plan = state.get("research_plan", {})
    goal = plan.get("research_goal", state["user_question"])
    sub_qs = state.get("sub_questions", [])
    settings = get_settings()

    try:
        if settings.effective_mock_mode:
            queries = [state["user_question"]] + [f"{q}" for q in sub_qs]
        else:
            llm = get_chat_model().with_structured_output(QueryList)
            result = llm.invoke(
                QUERY_REWRITER_PROMPT.format_messages(
                    research_goal=goal, sub_questions="\n".join(sub_qs)
                )
            )
            queries = result.queries

        queries = _dedupe(queries) or [state["user_question"]]
        state["rewritten_queries"] = queries
        state["search_queries"] = list(set(state.get("search_queries", []) + queries))
        state["current_step"] = "query_rewriting"
        log(state, f"{len(queries)} search queries generated")

    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"query_rewriter: {exc}")
        state["rewritten_queries"] = [state["user_question"]]
        log(state, "Query rewriter failed, falling back to the raw question")

    return state
