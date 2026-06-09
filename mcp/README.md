# LASSI MCP Server (legacy)

Originally this repository was a single **FastMCP** server. Every tool was registered in `LASSI_mcp.py` and consumed over JSON-RPC by Claude Code, Codex, or Roo Code.

The project has since moved to **Claude Code Skills + CLI tools** (see the top-level [`README.md`](../README.md) and the `cli/` + `.claude/skills/` directories). The MCP server is kept here for:

- **Roo Code** users — Roo still drives LASSI through MCP.
- **Codex** users.
- Anyone who needs JSON-RPC tool calls from a non-Claude client.
- Reproducibility against older runs that referenced MCP tool names directly.

> **Path note.** The server entrypoint used to live at the repo root. It now lives at `mcp/LASSI_mcp.py`. The MCP Dockerfile, `configure_MCP.py`, and its bootstrap shells live in this folder.

---

## Contents

```
mcp/
├── LASSI_mcp.py            # FastMCP server — registers every tool
├── configure_MCP.py        # Writes the MCP entry into a client config
├── Dockerfile.mcp          # Slim image: derives from agostini01/soda:latest
├── setup_mcp_docker.sh     # Build Dockerfile.mcp + configure a client
├── start_mcp.sh            # Boot Docker, ensure image, run stdio smoke test
└── README.md
```

`configure_MCP.py` writes / merges an `mcpServers` entry for Claude (`~/.claude.json`), an `mcp_servers` section for Codex (`~/.codex/config.toml`), or a Roo Code `mcp_settings.json` block. Use `--client` to choose.

---

## Quickstart

Run everything from the repo root unless noted.

### Option A — Docker (recommended)

The Dockerfile derives from the SODA image and keeps the MCP runtime out of the
host environment:

```bash
# Builds mcp/Dockerfile.mcp and writes the MCP entry for Claude Code.
CLIENT=claude ./mcp/setup_mcp_docker.sh
```

Switch clients with `CLIENT=roo` or `CLIENT=codex`. Override the image tag with `IMAGE_NAME=foo:tag` and the MCP entry name with `SERVER_NAME=lassi`.

The script ends by writing an MCP entry that runs:

```
docker run --rm -i -v $HOME:$HOME --workdir /opt/lassi \
  --cap-add=SYS_ADMIN --cap-add=PERFMON --security-opt seccomp=unconfined \
  lassi-mcp:latest \
  /opt/lassi/.venv/bin/python /opt/lassi/mcp/LASSI_mcp.py
```

The `SYS_ADMIN` / `PERFMON` / `seccomp=unconfined` flags unlock `perf_event_open` on Linux hosts. On Docker-for-Mac the LinuxKit kernel still gates with `perf_event_paranoid` and the perf tools fall back to software-only events.

### Option B — Conda on the host

```bash
conda create --name LASSI python=3.12 -y
conda activate LASSI
pip install -r requirements/requirements.txt

python mcp/configure_MCP.py \
  --client claude \
  --mode conda \
  --conda-env LASSI \
  --server-name lassi
```

`--client codex` and `--client roo` work the same way. Use `--conda-prefix /path/to/env` instead of `--conda-env` if you'd rather select by absolute path.

### Boot helper

`start_mcp.sh` is a convenience wrapper that:

1. Starts Docker Desktop (macOS) or `systemctl start docker` (Linux) if the daemon isn't reachable.
2. Builds the `lassi-soda-mcp:latest` image if it's missing (or with `--rebuild`).
3. Runs a JSON-RPC `initialize` handshake against the freshly built container so failures surface here, not later as a cryptic *"Failed to reconnect to lassi"* in your client.

```bash
./mcp/start_mcp.sh                # ensure daemon + image, run smoke test
./mcp/start_mcp.sh --rebuild      # force rebuild
./mcp/start_mcp.sh --no-smoke     # skip the handshake
IMAGE_NAME=foo:tag ./mcp/start_mcp.sh
```

---

## After Configuring

Restart your client so it picks up the new `mcpServers` / `mcp_servers` entry.

In Claude Code, run `/mcp` to verify the server is connected and list its tools. In Roo Code, the LASSI mode dropdown should populate.

---

## Tools Exposed

The server registers ~30 tools grouped by responsibility. Each maps 1-to-1 with a skill under `.claude/skills/lassi-*` and a CLI in `cli/lassi-*.py` — that's the new path for Claude Code users.

| Group | MCP tools |
|-------|-----------|
| Profiling | `gprof_profiling`, `execute_with_latency`, `execute_with_profile`, `run_benchmark`, `collect_perf_stats`, `profile_hotspots`, `compare_performance`, `collect_hardware_model`, `estimate_workload_model`, `run_roofline_analysis`, `compare_roofline` |
| Verification | `build_sanitized`, `synthesize_common_harness`, `generate_assertion_suite`, `run_assertion_suite`, `run_random_equivalence_tests`, `run_robustness_fuzzer`, `run_differential_fuzzer`, `synthesize_verification_report` |
| CSV | `summarize_csv`, `compare_csv_outputs`, `diff_csv_outputs` |
| Toolchain & hardware | `get_machine_info`, `get_gpu_info`, `get_toolchain_info` |
| Translation | `export_model_to_pt`, `compile_torch_to_mlir` |

The server also exposes resources for compiler flag cheat sheets (`compiler://{name}/flags`) and the Torch-MLIR/TOSA compatibility wiki (`wiki://compatibility/*`, backed by `resources/compatibility/`).

For per-tool parameters and behavior, read the registrations in `LASSI_mcp.py` directly — they're the source of truth.

---

## Troubleshooting

- **`perf_event_open` fails inside Docker.** Expected on Docker-for-Mac. The MCP tools degrade to software-only events and return `UNSURE` instead of `ERROR`. On Linux, make sure the container has `--cap-add=PERFMON` (or `SYS_ADMIN`) and the host's `kernel.perf_event_paranoid` allows non-root access.
- **`"Failed to reconnect to lassi"` in Claude Code.** Run `./mcp/start_mcp.sh` once — the smoke test will surface the underlying error (missing image, broken image, missing host bind mount, etc.).
- **`COPY . /opt/lassi` rebuild loops.** The Dockerfiles bake the source last so dependency layers stay cached across edits. Forcing a rebuild only invalidates the final `COPY` layer.
