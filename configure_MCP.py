import json
import os
import sys
import pathlib
import subprocess

# get python path for the current environment
python_path = sys.executable

#get cwd
cwd = pathlib.Path().absolute()

mcp_server_path = cwd / "LASSI_mcp.py"

mcp_server_config = json.dumps({
    "mcpServers": {
        "lassi": {
            "command": python_path,
            "args": [str(mcp_server_path)],
            "env": {"PYTHONUNBUFFERED": "1"},
            "disabled": False,
            "alwaysAllow": []
        }
    }
})

roocode_global_settings_path = pathlib.Path.home() / ".vscode-server" / "data" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json"

with open(roocode_global_settings_path, "w") as f:
    f.write(mcp_server_config)

print(f"Configured MCP server in {roocode_global_settings_path}")   
