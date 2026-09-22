from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.schemas.research import (
    ResearchRequest,
    ResearchResultResponse,
    ResearchStartResponse,
    ResearchStatusResponse,
)
from backend.services.research_service import create_research, execute_research, get_research

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("", response_model=ResearchStartResponse)
def start_research(payload: ResearchRequest, background_tasks: BackgroundTasks):
    research_id = create_research(payload.question)
    background_tasks.add_task(execute_research, research_id, payload.question)
    return ResearchStartResponse(research_id=research_id, status="started")


@router.get("/{research_id}/status", response_model=ResearchStatusResponse)
def get_status(research_id: str):
    state = get_research(research_id)
    if state is None:
        raise HTTPException(status_code=404, detail="research_id not found")
    return ResearchStatusResponse(
        research_id=research_id,
        status=state.get("status", "unknown"),
        current_step=state.get("current_step"),
        agent_logs=state.get("agent_logs", []),
        errors=state.get("errors", []),
        replan_count=state.get("replan_count", 0),
    )


@router.get("/{research_id}", response_model=ResearchResultResponse)
def get_result(research_id: str):
    state = get_research(research_id)
    if state is None:
        raise HTTPException(status_code=404, detail="research_id not found")
    return ResearchResultResponse(
        research_id=research_id,
        status=state.get("status", "unknown"),
        user_question=state.get("user_question"),
        final_answer=state.get("final_answer"),
        evaluation=state.get("evaluation", {}),
        sources=state.get("sources", []),
        findings=state.get("findings", []),
        ranked_documents=state.get("ranked_documents", []),
        calculations=state.get("calculations", []),
        critique=state.get("critique", {}),
        agent_logs=state.get("agent_logs", []),
        errors=state.get("errors", []),
        replan_count=state.get("replan_count", 0),
    )
