"""Pydantic request/response schemas for the research API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The research question")


class ResearchStartResponse(BaseModel):
    research_id: str
    status: str


class ResearchStatusResponse(BaseModel):
    research_id: str
    status: str
    current_step: str | None = None
    agent_logs: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    replan_count: int = 0


class ResearchResultResponse(BaseModel):
    research_id: str
    status: str
    user_question: str | None = None
    final_answer: str | None = None
    evaluation: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    ranked_documents: list[dict[str, Any]] = Field(default_factory=list)
    calculations: list[dict[str, Any]] = Field(default_factory=list)
    critique: dict[str, Any] = Field(default_factory=dict)
    agent_logs: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    replan_count: int = 0
