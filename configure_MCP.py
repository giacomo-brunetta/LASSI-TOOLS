import json
import pathlib

cwd = pathlib.Path(__file__).resolve().parent
home = pathlib.Path.home()
image_name = "lassi-soda-mcp:latest"

mcp_server_path = cwd / "LASSI_mcp.py"
roocode_global_settings_path = (
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

config = {
    "mcpServers": {
        "lassi": {
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
    }
}

roocode_global_settings_path.parent.mkdir(parents=True, exist_ok=True)
with open(roocode_global_settings_path, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")

print(f"Configured MCP server in {roocode_global_settings_path}")
print(f"Using Docker image: {image_name}")
print(f"Using MCP server entrypoint: {mcp_server_path}")
