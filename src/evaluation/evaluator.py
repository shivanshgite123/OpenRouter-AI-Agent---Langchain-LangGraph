"""Evaluator - checks the final research output.

Uses simple, transparent heuristics (not an ML benchmark) so the numbers
are never presented as validated scientific metrics.
"""
from __future__ import annotations

from src.state.state import ResearchState, log


def evaluate_research(state: ResearchState) -> ResearchState:
    try:
        findings = state.get("findings", [])
        sources = state.get("sources", [])
        sub_questions = state.get("sub_questions", []) or [""]
        final_answer = state.get("final_answer", "")

        # Completeness: rough coverage of sub-questions by keyword overlap.
        covered = 0
        for sq in sub_questions:
            terms = {t.lower() for t in sq.split() if len(t) > 3}
            if any(terms & {w.lower() for w in final_answer.split()} for _ in [0]):
                covered += 1
        completeness = round(covered / len(sub_questions), 2) if sub_questions else 0.0

        source_coverage = round(min(len(set(s.get("url") for s in sources)), 10) / 10, 2)

        cited_urls = sum(1 for s in sources if s.get("url") and s["url"] in final_answer)
        citation_coverage = round(cited_urls / len(sources), 2) if sources else 0.0

        issues = []
        if not findings:
            issues.append("No findings were collected")
        if not sources:
            issues.append("No sources were collected")
        if state.get("errors"):
            issues.append(f"{len(state['errors'])} non-fatal error(s) occurred during the run")

        overall = round((completeness + source_coverage + citation_coverage) / 3, 2)

        state["evaluation"] = {
            "completeness": completeness,
            "source_coverage": source_coverage,
            "citation_coverage": citation_coverage,
            "overall": overall,
            "issues": issues,
            "note": "Heuristic scores for demo purposes, not a validated benchmark.",
        }
        state["current_step"] = "evaluating"
        state["status"] = "completed"
        log(state, f"Evaluation complete - overall score {overall}")

    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"evaluator: {exc}")
        state["evaluation"] = {"overall": 0.0, "issues": [str(exc)]}
        state["status"] = "completed"
        log(state, "Evaluation step failed but the report is still available")

    return state
