import argparse
import json
import os
import pathlib
import sys
from typing import List, Optional


setup_dir = pathlib.Path(__file__).resolve().parent
repo_root = setup_dir.parent
home = pathlib.Path.home()
default_image_name = "lassi-soda-mcp:latest"

mcp_server_path = repo_root / "LASSI_mcp.py"
default_roo_settings_path = (
    home
    / ".vscode-server"
    / "data"
    / "User"
    / "globalStorage"
    / "rooveterinaryinc.roo-cline"
    / "settings"
    / "mcp_settings.json"
)
default_claude_settings_path = home / ".claude.json"
default_codex_settings_path = home / ".codex" / "config.toml"

always_allow = [
    "execute",
    "compile_source",
    "execute_with_latency",
    "execute_with_profile",
    "gprof_profiling",
    "get_machine_info",
    "get_gpu_info",
    "get_toolchain_info",
    "summarize_csv",
    "compare_csv_outputs",
    "diff_csv_outputs",
    "compile_with_libtorch",
    "push_callgraph_to_memory",
    "export_model_to_pt",
    "compile_torch_to_mlir",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure MCP settings for the LASSI MCP server."
    )
    parser.add_argument(
        "--client",
        choices=("claude", "codex", "roo"),
        default=os.environ.get("LASSI_MCP_CLIENT", "claude"),
        help="Client to configure. Defaults to claude.",
    )
    parser.add_argument(
        "--mode",
        choices=("docker", "conda"),
        default=os.environ.get("LASSI_MCP_MODE", "docker"),
        help="How the client should launch the MCP server. Defaults to docker.",
    )
    parser.add_argument(
        "--image-name",
        default=os.environ.get("IMAGE_NAME", default_image_name),
        help="Docker image to use when --mode docker is selected.",
    )
    parser.add_argument(
        "--conda-prefix",
        default=os.environ.get("CONDA_PREFIX"),
        help="Absolute path to the Conda environment to use when --mode conda is selected.",
    )
    parser.add_argument(
        "--conda-env",
        default=os.environ.get("CONDA_DEFAULT_ENV"),
        help="Conda environment name to use when --mode conda is selected.",
    )
    parser.add_argument(
        "--settings-path",
        type=pathlib.Path,
        default=None,
        help="Override the target client settings path.",
    )
    parser.add_argument(
        "--server-name",
        default="lassi",
        help="Name of the MCP server entry.",
    )
    return parser.parse_args()


def default_settings_path(client: str) -> pathlib.Path:
    if client == "claude":
        return default_claude_settings_path
    if client == "codex":
        return default_codex_settings_path
    if client == "roo":
        return default_roo_settings_path
    raise SystemExit(f"Unsupported client: {client}")


def build_docker_launch_config(image_name: str) -> dict:
    return {
        "command": "docker",
        "args": [
            "run",
            "--rm",
            "-i",
            "-v",
            f"{home}:{home}",
            "--workdir",
            str(repo_root),
            "-e",
            "PYTHONUNBUFFERED=1",
            image_name,
            "python3",
            str(mcp_server_path),
        ],
        "env": {
            "PYTHONUNBUFFERED": "1",
        },
    }


def build_conda_launch_config(conda_prefix: Optional[str], conda_env: Optional[str]) -> dict:
    args = ["run", "--no-capture-output"]

    if conda_prefix:
        args.extend(["-p", conda_prefix])
        selected_env = f"prefix {conda_prefix}"
    elif conda_env:
        args.extend(["-n", conda_env])
        selected_env = f"env {conda_env}"
    else:
        raise SystemExit(
            "Conda mode requires either --conda-prefix, --conda-env, "
            "CONDA_PREFIX, or CONDA_DEFAULT_ENV."
        )

    args.extend(["python", str(mcp_server_path)])

    return {
        "command": "conda",
        "args": args,
        "env": {
            "PYTHONUNBUFFERED": "1",
        },
        "_selected_env": selected_env,
    }


def build_client_server_config(client: str, launch_config: dict) -> dict:
    server_config = {
        "command": launch_config["command"],
        "args": launch_config["args"],
        "env": launch_config["env"],
    }

    if client == "roo":
        server_config["disabled"] = False
        server_config["alwaysAllow"] = always_allow

    return server_config


def load_existing_json_config(settings_path: pathlib.Path) -> dict:
    if not settings_path.exists():
        return {"mcpServers": {}}

    with open(settings_path) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise SystemExit(f"Existing settings file is not a JSON object: {settings_path}")

    mcp_servers = data.get("mcpServers")
    if mcp_servers is None:
        data["mcpServers"] = {}
    elif not isinstance(mcp_servers, dict):
        raise SystemExit(f"Existing mcpServers entry is not a JSON object: {settings_path}")

    return data


def write_json_mcp_config(settings_path: pathlib.Path, server_name: str, server_config: dict) -> None:
    config = load_existing_json_config(settings_path)
    config["mcpServers"][server_name] = server_config

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def toml_quote(value: str) -> str:
    return json.dumps(value)


def toml_string_array(values: List[str]) -> str:
    return "[" + ", ".join(toml_quote(value) for value in values) + "]"


def remove_codex_mcp_server_section(toml_text: str, server_name: str) -> str:
    section_prefix = f"mcp_servers.{server_name}"
    kept_lines = []
    in_target_section = False

    for line in toml_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section_name = stripped.strip("[]").strip()
            in_target_section = (
                section_name == section_prefix
                or section_name.startswith(f"{section_prefix}.")
            )

        if not in_target_section:
            kept_lines.append(line)

    return "\n".join(kept_lines).rstrip()


def format_codex_mcp_server_section(server_name: str, server_config: dict) -> str:
    lines = [
        f"[mcp_servers.{server_name}]",
        f"command = {toml_quote(server_config['command'])}",
        f"args = {toml_string_array(server_config['args'])}",
        "",
        f"[mcp_servers.{server_name}.env]",
    ]

    for key, value in sorted(server_config.get("env", {}).items()):
        lines.append(f"{key} = {toml_quote(value)}")

    return "\n".join(lines)


def write_codex_mcp_config(settings_path: pathlib.Path, server_name: str, server_config: dict) -> None:
    existing = settings_path.read_text() if settings_path.exists() else ""
    config_without_server = remove_codex_mcp_server_section(existing, server_name)
    server_section = format_codex_mcp_server_section(server_name, server_config)
    new_config = "\n\n".join(part for part in (config_without_server, server_section) if part)

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(f"{new_config}\n")


def main() -> int:
    args = parse_args()
    settings_path = args.settings_path or default_settings_path(args.client)

    if args.mode == "docker":
        launch_config = build_docker_launch_config(args.image_name)
        summary = f"Docker image: {args.image_name}"
    else:
        launch_config = build_conda_launch_config(args.conda_prefix, args.conda_env)
        summary = f"Conda target: {launch_config.pop('_selected_env')}"

    server_config = build_client_server_config(args.client, launch_config)

    if args.client == "codex":
        write_codex_mcp_config(settings_path, args.server_name, server_config)
    else:
        write_json_mcp_config(settings_path, args.server_name, server_config)

    print(f"Configured MCP server '{args.server_name}' for {args.client} in {settings_path}")
    print(f"Launch mode: {args.mode}")
    print(summary)
    print(f"MCP server entrypoint: {mcp_server_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
