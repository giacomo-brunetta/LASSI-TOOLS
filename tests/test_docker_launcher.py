import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "graph" / "run_graph_docker.sh"


def test_dry_run_mounts_only_project_read_write(tmp_path):
    result = subprocess.run(
        [
            "bash",
            str(LAUNCHER),
            "--dry-run",
            "--no-settings",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    command = result.stdout.replace("\\,", ",")
    assert "--read-only" in command
    assert "--cap-drop ALL" in command
    assert f"src={tmp_path},dst=/workspace" in command
    assert "/opt/lassi/graph/graph_flow.py" in command
    assert str(Path.home()) not in command


def test_rebuild_uses_graph_dockerfile(tmp_path):
    result = subprocess.run(
        [
            "bash",
            str(LAUNCHER),
            "--dry-run",
            "--rebuild",
            "--no-settings",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "-f graph/Dockerfile" in result.stdout
    assert "mcp/Dockerfile.lassi" not in result.stdout


def test_dry_run_rejects_config_outside_project(tmp_path):
    result = subprocess.run(
        [
            "bash",
            str(LAUNCHER),
            "--dry-run",
            "--no-settings",
            str(tmp_path),
            "/tmp/outside.json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "must be inside the project directory" in result.stderr


def test_read_only_project_overlays_only_selected_file(tmp_path):
    source = tmp_path / "kernel.c"
    config = tmp_path.parent / "config.json"
    reference = tmp_path.parent / "reference.c"
    source.write_text("int main(void) { return 0; }\n")
    config.write_text("{}")
    reference.write_text(source.read_text())

    result = subprocess.run(
        [
            "bash",
            str(LAUNCHER),
            "--dry-run",
            "--no-settings",
            "--read-only-project",
            "--writable-file",
            str(source),
            "--external-config",
            str(config),
            "--read-only-mount",
            f"{reference}:/run/lassi-input/reference.c",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    command = result.stdout.replace("\\,", ",")
    assert f"src={tmp_path},dst=/workspace,readonly" in command
    assert f"src={source},dst=/workspace/kernel.c" in command
    assert "LASSI_ARTIFACT_DIR=/tmp/lassi-artifacts/LASSI" in command
    assert "LASSI_BUILD_ROOT=/lassi-build/refactoring" in command
    assert "/lassi-build:rw,exec,nosuid,nodev,size=2g,mode=1777" in command
    assert "dst=/workspace/LASSI" not in command
    assert "dst=/workspace/.verify" not in command
    assert "dst=/run/lassi-graph-config.json,readonly" in command
    assert "dst=/run/lassi-input/reference.c,readonly" in command
