"""Research Analyst + Reranker nodes."""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.models.model_factory import get_chat_model
from src.prompts.researcher import RESEARCH_ANALYST_PROMPT
from src.state.state import ResearchState, log
from src.tools.reranker import rerank_documents


def reranker_node(state: ResearchState) -> ResearchState:
    docs = state.get("documents", [])
    query = state.get("research_plan", {}).get("research_goal", state["user_question"])
    try:
        ranked = rerank_documents(query, docs, top_n=min(10, len(docs)) or None)
        state["ranked_documents"] = ranked
        state["current_step"] = "reranking"
        state["status"] = "reranking"
        log(state, f"Documents reranked - top {len(ranked)} retained")
    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"reranker: {exc}")
        state["ranked_documents"] = docs
        log(state, "Reranking failed, using unranked documents")
    return state


class Finding(BaseModel):
    finding: str
    evidence: str
    source_url: str
    source_title: str
    confidence: str = Field(description="high | medium | low")


class AnalystOutput(BaseModel):
    findings: list[Finding]
    missing_information: list[str]
    agreements_and_conflicts: str = ""


def _mock_analysis(state: ResearchState) -> AnalystOutput:
    docs = state.get("ranked_documents", [])[:3]
    findings = [
        Finding(
            finding=f"Simulated finding derived from '{d.get('title', 'source')}'",
            evidence=(d.get("content", "") or "")[:200],
            source_url=d.get("url", ""),
            source_title=d.get("title", ""),
            confidence="medium",
        )
        for d in docs
    ]
    return AnalystOutput(findings=findings, missing_information=[], agreements_and_conflicts="")


def research_analyst_node(state: ResearchState) -> ResearchState:
    settings = get_settings()
    docs = state.get("ranked_documents") or state.get("documents", [])
    try:
        if settings.effective_mock_mode or not docs:
            analysis = _mock_analysis(state)
        else:
            llm = get_chat_model().with_structured_output(AnalystOutput)
            docs_text = "\n\n".join(
                f"Title: {d.get('title')}\nURL: {d.get('url')}\nContent: {(d.get('content') or '')[:800]}"
                for d in docs[:10]
            )
            analysis = llm.invoke(
                RESEARCH_ANALYST_PROMPT.format_messages(
                    user_question=state["user_question"],
                    sub_questions="\n".join(state.get("sub_questions", [])),
                    documents=docs_text,
                )
            )

        new_findings = [f.model_dump() for f in analysis.findings]
        state["findings"] = state.get("findings", []) + new_findings
        state["evidence"] = state.get("evidence", []) + [f["evidence"] for f in new_findings]
        state["sources"] = state.get("sources", []) + [
            {"title": f["source_title"], "url": f["source_url"]} for f in new_findings if f["source_url"]
        ]
        state["missing_information"] = analysis.missing_information
        state["current_step"] = "researching"
        state["status"] = "researching"
        log(state, f"Evidence extracted - {len(new_findings)} findings this pass")

    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"research_analyst: {exc}")
        log(state, "Research analysis step encountered an error but continued")

    return state
