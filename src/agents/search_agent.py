"""Search Agent node - executes parallel web search across all rewritten
queries using the LangChain web_search tool."""
from __future__ import annotations

from src.state.state import ResearchState, log
from src.tools.web_search import run_web_search_batch


def search_node(state: ResearchState) -> ResearchState:
    queries = state.get("rewritten_queries") or [state["user_question"]]
    try:
        results = run_web_search_batch(queries)
        existing = state.get("search_results", [])
        existing_urls = {r.get("url") for r in existing}
        merged = existing + [r for r in results if r.get("url") not in existing_urls]
        state["search_results"] = merged
        state["current_step"] = "searching"
        state["status"] = "searching"
        log(state, f"Web search completed - {len(results)} new results across {len(queries)} queries")
    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"search_agent: {exc}")
        log(state, "Web search step encountered an error but continued")
    return state
