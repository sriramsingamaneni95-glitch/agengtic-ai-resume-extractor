"""Tests for the dynamic routing logic itself (offline, no API calls)."""
from agent_graph import AgentGraph, AgentState
from orchestrator import (
    router_plan, router_extract, router_validate,
)


def test_router_plan_routes_to_clean_text_when_messy():
    state = AgentState(resume_text="x")
    state.plan = {"is_scanned_or_messy": True}
    assert router_plan(state) == "clean_text"


def test_router_plan_routes_to_extract_when_clean():
    state = AgentState(resume_text="x")
    state.plan = {"is_scanned_or_messy": False}
    assert router_plan(state) == "extract"


def test_router_extract_retries_on_error():
    state = AgentState(resume_text="x")
    state.raw_extraction_error = "bad json"
    state.extraction_attempts = 1
    assert router_extract(state) == "extract"


def test_router_extract_gives_up_after_3_attempts():
    state = AgentState(resume_text="x")
    state.raw_extraction_error = "bad json"
    state.extraction_attempts = 3
    assert router_extract(state) == "END"


def test_router_validate_routes_to_verification_when_low_confidence():
    state = AgentState(resume_text="x")
    state.low_confidence_fields = ["email"]
    assert router_validate(state) == "targeted_verification"


def test_router_validate_routes_to_score_when_confident():
    state = AgentState(resume_text="x")
    state.low_confidence_fields = []
    assert router_validate(state) == "score"


def test_graph_executes_simple_path():
    graph = AgentGraph()
    graph.add_node("a", lambda s: s)
    graph.add_node("b", lambda s: s)
    graph.add_router("a", lambda s: "b")
    graph.add_router("b", lambda s: "END")
    graph.set_entry("a")

    state = AgentState(resume_text="x")
    state = graph.run(state)
    assert state.log == ["a", "b"]
