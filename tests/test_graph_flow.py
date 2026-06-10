import asyncio
from pathlib import Path
from types import SimpleNamespace

import graph.graph_flow as graph_flow
from agents import set_dispatch_backend
from graph.graph_flow import (
    CODER_AGENT,
    CONFIG_BUILDER_AGENT,
    PLANNER_AGENT,
    PipelineStage,
    PipelineConfig,
    _compile_reference,
    _ensure_candidate_seeded,
    _launch_graph_container,
    _record_report,
    _resolve_config_path,
    _run_graph,
    _validate_report,
    _write_generated_config,
)


def test_candidate_is_seeded_only_once(tmp_path):
    original = tmp_path / "original.c"
    candidate = tmp_path / "build" / "candidate.c"
    original.write_text("original")

    seeded = _ensure_candidate_seeded(original, candidate, already_seeded=False)
    candidate.write_text("first attempt")
    seeded = _ensure_candidate_seeded(original, candidate, already_seeded=seeded)

    assert candidate.read_text() == "first attempt"


def test_reference_compile_resolves_relative_paths_from_reference(monkeypatch, tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    original_cwd = Path.cwd()
    seen = {}

    class FakeSource:
        def compile(self, **kwargs):
            seen["cwd"] = Path.cwd()
            seen["kwargs"] = kwargs

    monkeypatch.setattr(graph_flow, "REFERENCE_ROOT", reference)
    _compile_reference(FakeSource(), flags="-I utilities", output_file=tmp_path / "out")

    assert seen["cwd"] == reference
    assert seen["kwargs"]["kwds"] == "-I utilities"
    assert Path.cwd() == original_cwd


def test_headless_agents_do_not_expose_skills():
    assert PLANNER_AGENT.allowed_skills == []
    assert CODER_AGENT.allowed_skills == []
    assert CONFIG_BUILDER_AGENT.allowed_skills == []


def test_planner_is_read_only_and_returns_plan_for_orchestrator():
    assert PLANNER_AGENT.access_mode == "read"
    assert PLANNER_AGENT.tools == ["Read", "Grep", "Glob"]

    prompt = PLANNER_AGENT.build_task_prompt(
        context_message="# Pipeline Context\n\nOptimize optimized.c",
    )
    assert "Pipeline context message" in prompt
    assert "Optimize optimized.c" in prompt


def test_coder_receives_plan_message_and_returns_report():
    prompt = CODER_AGENT.build_task_prompt(
        plan_message="# Plan\n\n## Strategy 1\n- change: tile loops",
        target_file=Path("optimized.c"),
        reference_file=Path("/reference/original.c"),
    )

    assert "Planner message" in prompt
    assert "tile loops" in prompt
    assert "Return the complete Markdown changes report" in prompt


def test_python_validates_and_logs_agent_reports(caplog):
    caplog.set_level("INFO", logger="graph.graph_flow")
    state = PipelineStage()
    report = _validate_report(
        "  # Plan\n\n## Strategy 1\n- change: tile loops  ",
        stage="planner",
        heading="# Plan",
    )

    _record_report(state, "planner", report)

    assert report == "# Plan\n\n## Strategy 1\n- change: tile loops"
    assert state.reports == [("planner", report)]
    assert "planner report:" in caplog.text


def test_python_writes_generated_config_from_agent_message(tmp_path):
    config_path = tmp_path / "config.json"
    result = """
    ```json
    {
      "sources": {"original": "original.c", "optimized": "optimized.c"},
      "compiler": "clang",
      "flags": {"correctness": "-O0", "performance": "-O3"},
      "arguments": {"benchmark": "", "golden": []}
    }
    ```
    """

    config = _write_generated_config(config_path, result)

    assert config.original_path == Path("original.c")
    assert config_path.is_file()
    assert config_path.read_text().startswith("{")


def test_graph_agents_use_message_reports_not_handoff_files():
    assert "Write" not in PLANNER_AGENT.tools
    assert "Write" not in CONFIG_BUILDER_AGENT.tools
    assert "Write" in CODER_AGENT.tools


def test_graph_passes_messages_without_handoff_files(monkeypatch, tmp_path, caplog):
    original = tmp_path / "original.c"
    optimized = tmp_path / "optimized.c"
    config = tmp_path / "config.json"
    original.write_text("int main(void) { return 0; }\n")
    config.write_text(
        """
        {
          "sources": {"original": "original.c", "optimized": "optimized.c"},
          "compiler": "clang",
          "flags": {"correctness": "-O0", "performance": "-O3"},
          "arguments": {"benchmark": "", "golden": []}
        }
        """
    )
    seen = {}

    async def backend(agent, **kwargs):
        if agent.name == "planner":
            seen["context"] = kwargs["context_message"]
            return "# Plan\n\n## Strategy 1\n- change: add an explanatory comment"
        if agent.name == "coder":
            seen["plan"] = kwargs["plan_message"]
            optimized.write_text(original.read_text() + "/* optimized */\n")
            return "# Changes\n\n## Files changed\n- optimized.c: added comment"
        raise AssertionError(f"unexpected agent: {agent.name}")

    caplog.set_level("INFO", logger="graph.graph_flow")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(graph_flow, "REFERENCE_ROOT", tmp_path)
    set_dispatch_backend(backend)
    try:
        asyncio.run(
            _run_graph(
                SimpleNamespace(no_profile=True),
                config.resolve(),
                tmp_path.resolve(),
            )
        )
    finally:
        set_dispatch_backend(None)

    assert seen["context"].startswith("# Pipeline Context")
    assert seen["plan"].startswith("# Plan")
    assert optimized.is_file()
    assert not (tmp_path / "LASSI").exists()
    assert "planner report:" in caplog.text
    assert "coder report:" in caplog.text


def test_default_retry_budget_caps_coder_calls_at_six():
    state = PipelineStage()

    calls_per_plan = 1 + state.max_coder_iterations
    plan_attempts = 1 + state.max_planner_iterations

    assert calls_per_plan * plan_attempts == 6


def test_relative_config_path_resolves_from_project(tmp_path):
    assert _resolve_config_path(tmp_path, Path("config.json")) == (
        tmp_path / "config.json"
    ).resolve()


def test_pipeline_config_rejects_source_path_escape(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(
        """
        {
          "sources": {"original": "../original.c", "optimized": "optimized.c"},
          "compiler": "clang",
          "flags": {"correctness": "-O0", "performance": "-O3"},
          "arguments": {"benchmark": "", "golden": []}
        }
        """
    )

    try:
        PipelineConfig.load(config)
    except ValueError as exc:
        assert "project-relative" in str(exc)
    else:
        raise AssertionError("expected project path escape to be rejected")


def test_pipeline_config_requires_distinct_reference_and_target(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(
        """
        {
          "sources": {"original": "kernel.c", "optimized": "kernel.c"},
          "compiler": "clang",
          "flags": {"correctness": "-O0", "performance": "-O3"},
          "arguments": {"benchmark": "", "golden": []}
        }
        """
    )

    try:
        PipelineConfig.load(config)
    except ValueError as exc:
        assert "must be different" in str(exc)
    else:
        raise AssertionError("expected identical reference and target to be rejected")


def test_missing_config_restarts_with_immutable_config_and_reference(monkeypatch, tmp_path):
    original = tmp_path / "original.c"
    config = tmp_path / "config.json"
    original.write_text("int main(void) { return 0; }\n")
    containers = []

    class FakeContainer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            containers.append(self)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        async def exec_graph(self, args):
            if "--generate-config-only" in args:
                config.write_text(
                    """
                    {
                      "sources": {"original": "original.c", "optimized": "optimized.c"},
                      "compiler": "clang",
                      "flags": {"correctness": "-O0", "performance": "-O3"},
                      "arguments": {"benchmark": "", "golden": []}
                    }
                    """
                )
            return ""

    monkeypatch.setattr(graph_flow, "AgentContainer", FakeContainer)
    args = SimpleNamespace(
        no_settings=True,
        settings=tmp_path / "settings.json",
        readonly=[],
        image="test-image",
        no_auto_build=True,
        no_profile=True,
    )

    asyncio.run(_launch_graph_container(args, tmp_path.resolve(), config.resolve()))

    assert len(containers) == 2
    final = containers[1].kwargs
    assert config.resolve() in final["read_only_overlays"]
    assert final["reference_overlays"] == [Path("original.c")]
