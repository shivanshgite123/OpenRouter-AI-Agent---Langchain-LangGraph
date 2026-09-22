"""Planner agent - LangChain structured-output LLM call, invoked from the
LangGraph `planner_node`."""
from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.models.model_factory import get_chat_model
from src.prompts.planner import PLANNER_PROMPT
from src.state.state import ResearchState, log

logger = logging.getLogger(__name__)


class ResearchPlan(BaseModel):
    research_goal: str = Field(description="What a complete answer looks like")
    sub_questions: list[str] = Field(description="2-5 concrete sub-questions")
    required_sources: list[str] = Field(description="Kinds of sources needed")
    requires_research: bool = Field(description="Whether web research is needed")


def _mock_plan(question: str) -> ResearchPlan:
    return ResearchPlan(
        research_goal=f"Produce a well-sourced answer to: {question}",
        sub_questions=[
            f"What are the key facts about {question}?",
            f"What do recent sources say about {question}?",
        ],
        required_sources=["news articles", "official sources"],
        requires_research=True,
    )


def plan_research(state: ResearchState) -> ResearchState:
    question = state["user_question"]
    settings = get_settings()

    try:
        if settings.effective_mock_mode:
            plan = _mock_plan(question)
        else:
            llm = get_chat_model().with_structured_output(ResearchPlan)
            plan = llm.invoke(PLANNER_PROMPT.format_messages(user_question=question))

        state["research_plan"] = plan.model_dump()
        state["sub_questions"] = plan.sub_questions
        state["required_sources"] = plan.required_sources
        state["current_step"] = "planning"
        state["status"] = "planning"
        log(state, f"Research plan created ({len(plan.sub_questions)} sub-questions)")

    except Exception as exc:  # noqa: BLE001
        state.setdefault("errors", []).append(f"planner: {exc}")
        log(state, "Planner failed, using minimal fallback plan")
        fallback = _mock_plan(question)
        state["research_plan"] = fallback.model_dump()
        state["sub_questions"] = fallback.sub_questions
        state["required_sources"] = fallback.required_sources

    return state
