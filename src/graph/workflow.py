"""
LangGraph StateGraph orchestration.

This is the actual multi-agent controller: every node below wraps a
LangChain-powered agent (structured-output LLM calls, or LangChain tools),
and LangGraph is responsible for shared state, routing, the
critic -> replanner -> search reflection loop, and error recovery.

    planner -> query_rewriter -> search -> reader -> reranker -> researcher
      -> critic --(incomplete, budget left)--> replanner -> search (loop)
      -> critic --(complete or budget exhausted)--> solver -> evaluator -> END
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.critic import critic_node, is_research_complete
from src.agents.planner import plan_research
from src.agents.query_rewriter import rewrite_queries
from src.agents.reader import reader_node
from src.agents.replanner import replanner_node
from src.agents.researcher import reranker_node, research_analyst_node
from src.agents.search_agent import search_node
from src.agents.solver import solver_node
from src.config.settings import get_settings
from src.evaluation.evaluator import evaluate_research
from src.state.state import ResearchState, new_research_state


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", plan_research)
    graph.add_node("query_rewriter", rewrite_queries)
    graph.add_node("search", search_node)
    graph.add_node("reader", reader_node)
    graph.add_node("reranker", reranker_node)
    graph.add_node("researcher", research_analyst_node)
    graph.add_node("critic", critic_node)
    graph.add_node("replanner", replanner_node)
    graph.add_node("solver", solver_node)
    graph.add_node("evaluator", evaluate_research)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "query_rewriter")
    graph.add_edge("query_rewriter", "search")
    graph.add_edge("search", "reader")
    graph.add_edge("reader", "reranker")
    graph.add_edge("reranker", "researcher")
    graph.add_edge("researcher", "critic")

    graph.add_conditional_edges(
        "critic",
        is_research_complete,
        {"solver": "solver", "replanner": "replanner"},
    )
    # Replanning loop: new queries -> back into search.
    graph.add_edge("replanner", "search")

    graph.add_edge("solver", "evaluator")
    graph.add_edge("evaluator", END)

    return graph.compile()


_COMPILED_GRAPH = None


def get_compiled_graph():
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_research_graph()
    return _COMPILED_GRAPH


def run_research(research_id: str, user_question: str, status_callback=None) -> ResearchState:
    """Run the full graph synchronously and return the final state.

    `status_callback(state)` is invoked after the graph finishes if provided
    (the FastAPI background task also streams intermediate status via the
    in-memory store, see backend/services/research_service.py).
    """
    settings = get_settings()
    initial_state = new_research_state(research_id, user_question, settings.max_replans)
    graph = get_compiled_graph()
    final_state = graph.invoke(initial_state, config={"recursion_limit": 50})
    if status_callback:
        status_callback(final_state)
    return final_state
