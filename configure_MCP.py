import argparse
import json
import os
import pathlib
import sys


cwd = pathlib.Path(__file__).resolve().parent
home = pathlib.Path.home()
default_image_name = "lassi-soda-mcp:latest"

mcp_server_path = cwd / "LASSI_mcp.py"
default_roocode_global_settings_path = (
    home
    / ".vscode-server"
    / "data"
    / "User"
    / "globalStorage"
    / "rooveterinaryinc.roo-cline"
    / "settings"
    / "mcp_settings.json"
)

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
        description="Configure the Roo Code MCP settings for the LASSI MCP server."
    )
    parser.add_argument(
        "--mode",
        choices=("docker", "conda"),
        default=os.environ.get("LASSI_MCP_MODE", "docker"),
        help="How Roo should launch the MCP server. Defaults to docker.",
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
        default=default_roocode_global_settings_path,
        help="Path to Roo's mcp_settings.json file.",
    )
    parser.add_argument(
        "--server-name",
        default="lassi",
        help="Name of the MCP server entry inside mcp_settings.json.",
    )
    return parser.parse_args()


def build_docker_server_config(image_name: str) -> dict:
    return {
        "command": "docker",
        "args": [
            "run",
            "--rm",
            "-i",
            "-v",
            f"{home}:{home}",
            "--workdir",
            str(cwd),
            "-e",
            "PYTHONUNBUFFERED=1",
            image_name,
            "python3",
            str(mcp_server_path),
        ],
        "env": {
            "PYTHONUNBUFFERED": "1",
        },
        "disabled": False,
        "alwaysAllow": always_allow,
    }


def build_conda_server_config(conda_prefix: str | None, conda_env: str | None) -> dict:
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
        "disabled": False,
        "alwaysAllow": always_allow,
        "_selected_env": selected_env,
    }


def load_existing_config(settings_path: pathlib.Path) -> dict:
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


def main() -> int:
    args = parse_args()

    if args.mode == "docker":
        server_config = build_docker_server_config(args.image_name)
        summary = f"Docker image: {args.image_name}"
    else:
        server_config = build_conda_server_config(args.conda_prefix, args.conda_env)
        summary = f"Conda target: {server_config.pop('_selected_env')}"

    config = load_existing_config(args.settings_path)
    config["mcpServers"][args.server_name] = server_config

    args.settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(args.settings_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"Configured MCP server '{args.server_name}' in {args.settings_path}")
    print(f"Launch mode: {args.mode}")
    print(summary)
    print(f"MCP server entrypoint: {mcp_server_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
