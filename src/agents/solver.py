"""Solver node - produces the final research report."""
from __future__ import annotations

import re

from src.config.settings import get_settings
from src.models.model_factory import get_chat_model
from src.prompts.solver import SOLVER_PROMPT
from src.state.state import ResearchState, log
from src.tools.calculator import UnsafeExpressionError, safe_calculate


def _maybe_run_calculations(state: ResearchState) -> None:
    """Very small heuristic: if the question mentions typical quantitative
    terms, try to extract a simple arithmetic expression from findings and
    run it through the controlled calculator tool. Best-effort only."""
    question = state["user_question"].lower()
    quantitative_terms = ("percent", "%", "average", "growth", "cagr", "ratio", "compare")
    if not any(t in question for t in quantitative_terms):
        return

    calculations = []
    for finding in state.get("findings", []):
        text = finding.get("evidence", "") or finding.get("finding", "")
        for match in re.findall(r"[\d.]+\s*[\+\-\*/]\s*[\d.]+", text):
            try:
                result = safe_calculate(match)
                calculations.append({"expression": match, "result": result})
            except UnsafeExpressionError:
                continue
    if calculations:
        state["calculations"] = state.get("calculations", []) + calculations


def _mock_report(state: ResearchState) -> str:
    findings = state.get("findings", [])
    sources = state.get("sources", [])
    findings_md = "\n".join(f"- {f.get('finding', '')}" for f in findings) or "- No findings collected."
    sources_md = "\n".join(f"- [{s.get('title')}]({s.get('url')})" for s in sources if s.get("url")) or "- No sources collected."
    return (
        f"## Executive Summary\nThis is a MOCK_MODE demo report for: "
        f"\"{state['user_question']}\". No real LLM or API calls were made.\n\n"
        f"## Detailed Analysis\nThe workflow executed planning, query rewriting, "
        f"search, reading, reranking, analysis, critique, and solving using "
        f"simulated data end-to-end.\n\n"
        f"## Key Findings\n{findings_md}\n\n"
        f"## Evidence\nSee findings above; each is tied to a simulated source.\n\n"
        f"## Comparison\nNot applicable in this mock run.\n\n"
        f"## Limitations\nAll data in this report is simulated (MOCK_MODE=true). "
        f"Provide real API keys and set MOCK_MODE=false for live research.\n\n"
        f"## Sources\n{sources_md}\n"
    )


def solver_node(state: ResearchState) -> ResearchState:
    settings = get_settings()
    try:
        _maybe_run_calculations(state)

        if settings.effective_mock_mode:
            report = _mock_report(state)
        else:
            llm = get_chat_model()
            sources_text = "\n".join(
                f"- {s.get('title')}: {s.get('url')}" for s in state.get("sources", []) if s.get("url")
            )
            report = llm.invoke(
                SOLVER_PROMPT.format_messages(
                    user_question=state["user_question"],
                    research_plan=str(state.get("research_plan", {})),
                    findings=str(state.get("findings", []))[:4000],
                    calculations=str(state.get("calculations", [])),
                    critique=str(state.get("critique", {})),
                    sources=sources_text,
                )
            ).content

        state["final_answer"] = report
        state["current_step"] = "solving"
        state["status"] = "solving"
        log(state, "Final answer generated")

    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"solver: {exc}")
        state["final_answer"] = state.get("final_answer") or "Report generation failed. See errors for details."
        log(state, "Solver step failed")

    return state
