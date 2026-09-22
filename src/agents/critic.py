"""Critic / Reflection node."""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.models.model_factory import get_chat_model
from src.prompts.researcher import CRITIC_PROMPT
from src.state.state import ResearchState, log


class CriticOutput(BaseModel):
    complete: bool
    quality: str = Field(description="'sufficient' or 'needs_more_research'")
    missing_information: list[str] = Field(default_factory=list)
    follow_up_queries: list[str] = Field(default_factory=list)
    reason: str = ""


def _mock_critique(state: ResearchState) -> CriticOutput:
    # In mock mode, complete after the first pass so the demo terminates quickly.
    already_replanned = state.get("replan_count", 0) > 0
    return CriticOutput(
        complete=True if already_replanned else len(state.get("findings", [])) >= 2,
        quality="sufficient",
        missing_information=[],
        follow_up_queries=[],
        reason="Mock mode: sufficient findings collected for a demo report.",
    )


def critic_node(state: ResearchState) -> ResearchState:
    settings = get_settings()
    try:
        if settings.effective_mock_mode:
            critique = _mock_critique(state)
        else:
            llm = get_chat_model().with_structured_output(CriticOutput)
            critique = llm.invoke(
                CRITIC_PROMPT.format_messages(
                    user_question=state["user_question"],
                    sub_questions="\n".join(state.get("sub_questions", [])),
                    findings=str(state.get("findings", []))[:3000],
                    missing_information="\n".join(state.get("missing_information", [])),
                )
            )

        state["critique"] = critique.model_dump()
        state["missing_information"] = critique.missing_information
        state["follow_up_queries"] = critique.follow_up_queries
        state["current_step"] = "reflecting"
        state["status"] = "reflecting"
        if critique.complete:
            log(state, "Critic confirmed the research is sufficient")
        else:
            log(state, f"Critic found missing information: {', '.join(critique.missing_information) or 'gaps identified'}")

    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"critic: {exc}")
        # fail safe towards "complete" so a critic failure cannot infinite-loop
        state["critique"] = {"complete": True, "quality": "unknown", "reason": str(exc)}
        log(state, "Critic step failed; proceeding to solver as a safety fallback")

    return state


def is_research_complete(state: ResearchState) -> str:
    """Conditional edge: route to 'solver' or 'replanner'."""
    critique = state.get("critique", {})
    replan_count = state.get("replan_count", 0)
    max_replans = state.get("max_replans", 2)

    if critique.get("complete") or replan_count >= max_replans:
        return "solver"
    return "replanner"
