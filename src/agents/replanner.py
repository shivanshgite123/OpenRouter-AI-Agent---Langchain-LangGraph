"""Replanner node - only reached when the critic says research is incomplete."""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.models.model_factory import get_chat_model
from src.prompts.researcher import REPLANNER_PROMPT
from src.state.state import ResearchState, log


class ReplanOutput(BaseModel):
    rewritten_queries: list[str] = Field(description="2-4 new, non-duplicate search queries")


def replanner_node(state: ResearchState) -> ResearchState:
    settings = get_settings()
    previous_queries = state.get("search_queries", [])
    try:
        if settings.effective_mock_mode:
            new_queries = [f"additional details {state['user_question']}"]
        else:
            llm = get_chat_model().with_structured_output(ReplanOutput)
            result = llm.invoke(
                REPLANNER_PROMPT.format_messages(
                    user_question=state["user_question"],
                    previous_queries=", ".join(previous_queries),
                    missing_information=", ".join(state.get("missing_information", [])),
                    follow_up_queries=", ".join(state.get("follow_up_queries", [])),
                )
            )
            new_queries = result.rewritten_queries

        state["rewritten_queries"] = new_queries
        state["replan_count"] = state.get("replan_count", 0) + 1
        state["current_step"] = "replanning"
        state["status"] = "replanning"
        log(state, f"Research plan updated - replan #{state['replan_count']} with {len(new_queries)} new queries")

    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"replanner: {exc}")
        state["rewritten_queries"] = state.get("follow_up_queries") or [state["user_question"]]
        state["replan_count"] = state.get("replan_count", 0) + 1
        log(state, "Replanner failed; retrying with follow-up queries from the critic")

    return state
