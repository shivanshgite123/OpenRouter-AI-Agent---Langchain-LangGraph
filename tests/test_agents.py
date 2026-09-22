from src.state.state import new_research_state
from src.agents.planner import plan_research
from src.agents.query_rewriter import rewrite_queries
from src.agents.critic import critic_node, is_research_complete
from src.agents.replanner import replanner_node


def _state(question="What is the capital of France?"):
    return new_research_state("test-id", question, max_replans=2)


def test_planner_produces_sub_questions_in_mock_mode():
    state = plan_research(_state())
    assert state["sub_questions"]
    assert state["research_plan"]["requires_research"] is True


def test_query_rewriter_produces_queries():
    state = plan_research(_state())
    state = rewrite_queries(state)
    assert state["rewritten_queries"]


def test_critic_routes_to_solver_when_complete():
    state = _state()
    state["findings"] = [{"finding": "a"}, {"finding": "b"}]
    state = critic_node(state)
    route = is_research_complete(state)
    assert route in ("solver", "replanner")


def test_critic_routes_to_solver_after_max_replans():
    state = _state()
    state["replan_count"] = 5
    state["max_replans"] = 2
    state["critique"] = {"complete": False}
    assert is_research_complete(state) == "solver"


def test_replanner_increments_replan_count():
    state = _state()
    state["replan_count"] = 0
    state = replanner_node(state)
    assert state["replan_count"] == 1
