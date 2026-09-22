"""Reader / content-extraction node."""
from __future__ import annotations

from src.state.state import ResearchState, log
from src.tools.web_scraper import extract_documents


def reader_node(state: ResearchState) -> ResearchState:
    results = state.get("search_results", [])
    try:
        docs = extract_documents(results, limit=20)
        existing = state.get("documents", [])
        existing_urls = {d.get("url") for d in existing}
        merged = existing + [d for d in docs if d.get("url") not in existing_urls]
        state["documents"] = merged
        failed = [d for d in docs if d.get("error")]
        state["current_step"] = "reading"
        state["status"] = "reading"
        log(state, f"{len(docs)} documents collected ({len(failed)} had extraction issues)")
    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"reader: {exc}")
        log(state, "Reader step encountered an error but continued")
    return state
