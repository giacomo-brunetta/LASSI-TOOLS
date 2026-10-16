from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pytest

import lassi_x.pipeline as pipeline
from lassi_x.config import RunConfig
from lassi_x.types import Candidate, Status
from lassi_x.validation import OracleResult

from .test_config import minimal_config
from .test_pipeline import measured

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("interrupted_again", [False, True])
def test_retry_preserves_completed_work_and_checkpoints_each_leaf(
    tmp_path: Path, monkeypatch: Any, interrupted_again: bool
) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    source = tmp_path / "parent.py"
    source.write_text("parent")
    saved = tmp_path / "repair.py"
    saved.write_text("saved edits")
    parent = Candidate("c1", "one", None, "direct", source, status=Status.OK)
    previous = Candidate(
        "repair",
        "one",
        None,
        "repair",
        saved,
        parent_candidate_id="c1",
        target_backend="cpu",
        target_precision="fp16",
    )
    completed = Candidate("finished", "one", None, "repair", source, status=Status.OK)
    base = measured(source, variant_id="c1-base", compensation="none", error=0.1)
    old_point = measured(saved, variant_id="repair-base", compensation="compatibility", error=0.1)
    old_point.candidate_id = "repair"
    replacement = Candidate.from_dict(previous.to_dict())
    replacement.status = Status.CRASHED if interrupted_again else Status.OK
    new_point = measured(saved, variant_id="repair-base", compensation="compatibility", error=0.01)
    new_point.candidate_id = "repair"
    state = pipeline.PipelineState(
        oracle=OracleResult(tmp_path / "oracle.npy", np.empty(0)),
        candidates=[parent],
        compatibility_candidates=[previous, completed],
        valid_candidates=[parent, completed],
        measurements=[base, old_point],
    )
    checkpoints = []

    async def repair(*args: Any, **kwargs: Any) -> Any:
        assert kwargs["previous"] is previous
        assert saved.read_text() == "saved edits"
        assert args[4] is parent
        return replacement, new_point

    async def run_model(call: Any) -> Any:
        return await call()

    monkeypatch.setattr(pipeline, "repair_accelerator_candidate", repair)
    monkeypatch.setattr(
        pipeline, "build_backends", lambda *_: [SimpleNamespace(spec=SimpleNamespace(name="cpu"))]
    )
    monkeypatch.setattr(pipeline, "select_compatibility_failures", lambda *_: [base])
    monkeypatch.setattr(pipeline, "_load_candidate_journal", lambda *_: None)
    monkeypatch.setattr(pipeline, "_save_checkpoint", lambda *a, **k: checkpoints.append(a))
    deps = SimpleNamespace(
        config=config,
        execution=object(),
        scheduler=SimpleNamespace(run_model=run_model),
        run_dir=tmp_path,
    )
    if interrupted_again:
        with pytest.raises(RuntimeError, match="interrupted again"):
            asyncio.run(
                pipeline._retry_interrupted_repairs(state, cast("pipeline.PipelineDeps", deps))
            )
    else:
        asyncio.run(pipeline._retry_interrupted_repairs(state, cast("pipeline.PipelineDeps", deps)))
    assert state.measurements == [base, new_point]
    assert state.compatibility_candidates == [replacement, completed]
    assert completed in state.valid_candidates
    assert len(checkpoints) == 1
    assert (
        next((tmp_path / "repair-history").glob("*/repair/candidate.py")).read_text()
        == "saved edits"
    )
