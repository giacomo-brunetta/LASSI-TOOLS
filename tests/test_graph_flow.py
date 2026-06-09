from graph.graph_flow import (
    CODER_AGENT,
    CONFIG_BUILDER_AGENT,
    PLANNER_AGENT,
    PipelineStage,
    _ensure_candidate_seeded,
)


def test_candidate_is_seeded_only_once(tmp_path):
    original = tmp_path / "original.c"
    candidate = tmp_path / "build" / "candidate.c"
    original.write_text("original")

    seeded = _ensure_candidate_seeded(original, candidate, already_seeded=False)
    candidate.write_text("first attempt")
    seeded = _ensure_candidate_seeded(original, candidate, already_seeded=seeded)

    assert candidate.read_text() == "first attempt"


def test_headless_agents_do_not_expose_skills():
    assert PLANNER_AGENT.allowed_skills == []
    assert CODER_AGENT.allowed_skills == []
    assert CONFIG_BUILDER_AGENT.allowed_skills == []


def test_default_retry_budget_caps_coder_calls_at_six():
    state = PipelineStage()

    calls_per_plan = 1 + state.max_coder_iterations
    plan_attempts = 1 + state.max_planner_iterations

    assert calls_per_plan * plan_attempts == 6
