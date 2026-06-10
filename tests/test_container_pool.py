from pathlib import Path

import graph.container_pool as container_pool
from graph.container_pool import AgentContainer


def test_container_mounts_editable_workspace_and_immutable_reference(monkeypatch, tmp_path):
    project = tmp_path / "project"
    reference = tmp_path / "reference"
    project.mkdir()
    reference.mkdir()
    (project / "original.c").write_text("editable view\n")
    (project / "config.json").write_text("{}")
    (reference / "original.c").write_text("reference snapshot\n")

    monkeypatch.setattr(container_pool.docker, "from_env", lambda: object())
    container = AgentContainer(
        project_dir=project,
        reference_dir=reference,
        read_only_overlays=[project / "config.json"],
        reference_overlays=[Path("original.c")],
    )

    mounts = {mount["Target"]: mount for mount in container._build_mounts()}

    assert mounts["/workspace"]["Source"] == str(project.resolve())
    assert mounts["/workspace"]["ReadOnly"] is False
    assert mounts["/reference"]["Source"] == str(reference.resolve())
    assert mounts["/reference"]["ReadOnly"] is True
    assert mounts["/workspace/original.c"]["Source"] == str(reference.resolve() / "original.c")
    assert mounts["/workspace/original.c"]["ReadOnly"] is True
    assert mounts["/workspace/config.json"]["ReadOnly"] is True
