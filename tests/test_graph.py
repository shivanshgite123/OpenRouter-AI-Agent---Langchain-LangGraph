from src.graph.workflow import build_research_graph, run_research


def test_graph_builds_without_errors():
    graph = build_research_graph()
    assert graph is not None


def test_graph_end_to_end_mock_mode():
    final_state = run_research("test-run", "What is the CAGR of solar energy adoption?")
    assert final_state["status"] == "completed"
    assert final_state["final_answer"]
    assert "evaluation" in final_state
    # never an infinite loop
    assert final_state["replan_count"] <= final_state["max_replans"]
