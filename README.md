# LASSI-Agentic Flow

This repository implements an agentic workflow focused on code performance and efficiency optimization.

## Key Components

### LASSI MCP Server
- Portable toolset for performance engineering capable of:
  - Reading machine information (CPU, GPU, memory)
  - Compiling and executing code
  - Measuring execution latency plus power/energy consumption
  - Running gprof profiling (flat and callgraph)
- Tool specifications:
  <details>
    <summary>Available Tools</summary>

    | Tool | Description | Parameters |
    |------|-------------|------------|
    | `compile_source` | Compiles a source file using a specific compiler. | `path`, `compiler`, `kwds` (optional), `output` (optional) |
    | `compile_to_mlir` | Compiles a C/C++ source file to MLIR using cgeist. | `path`, `kwds` (optional), `output` (optional) |
    | `gprof_profiling` | Compiles with gprof and returns the callgraph info. | `path`, `compiler`, `kwds` (optional), `args` (optional) |
    | `execute_with_latency` | Runs executables and returns output plus execution time. | `path`, `args` (optional) |
    | `execute_with_profile` | Runs executables and returns output plus power profiling report. | `path`, `args` (optional) |
    | `push_callgraph_to_memory` | Pushes gprof callgraph to the Memory MCP server. | `path`, `compiler` (optional), `kwds` (optional), `args` (optional) |
    | `get_machine_info` | Reads CPU and RAM information. | None |
    | `get_gpu_info` | Retrieves GPU information using SMI tools. | None |
  </details>

### Workflow (RooCode Optimized)
1. **Analyst Agent** – maps the codebase and produces a technical specification.
2. **Initial Profiler** – establishes a performance baseline (latency, energy, callgraph).
3. **Planning Agent** – creates an optimization plan, strategies, and expected outcomes.
4. **Coding Agent** – applies optimizations via a non-destructive Git workflow (branches + PRs).
5. **QA Verifier** – guarantees functional equivalence versus the "Golden Master" output.
6. **Post-Optimization Profiler** – re-runs profiling to confirm improvements versus baseline.

<details>
  <summary>Workflow Diagram</summary>

  ![Mermaid plot](assets/mermaid.png)
</details>

## Installation

Run these commands from the repository root:

```bash
cd ~/LASSI-TOOLS
```

1. **Install Roo Code**

   Follow the Roo Code install guide: https://docs.roocode.com/getting-started/installing

2. **Install the LASSI Roo modes and rules**

   Roo loads global custom modes from `settings/custom_modes.yaml`. For a VS Code Remote server, that settings directory is:

   ```bash
   ROO_SETTINGS="$HOME/.vscode-server/data/User/globalStorage/rooveterinaryinc.roo-cline/settings"
   ```

   Install the LASSI mode definitions and their matching global rule folders:

   ```bash
   mkdir -p "$ROO_SETTINGS" "$HOME/.roo"
   cp custom_modes.yaml "$ROO_SETTINGS/custom_modes.yaml"
   cp -R .roo/rules-* "$HOME/.roo/"
   ```

   This overwrites Roo's global `custom_modes.yaml`. If you already have other custom modes, merge this file into the existing one instead of copying it over. The rule directory names must match the mode slugs. For example, the `model-generator` mode uses `.roo/rules-model-generator/`.

3. **Configure the LASSI MCP server**

   Use Docker when you want the MCP server and its Python dependencies to run in a container:

   ```bash
   ./setup_mcp_docker.sh
   ```

   Use Conda when you want the MCP server to run directly on the host:

   ```bash
   conda create --name LASSI python=3.12
   conda activate LASSI
   pip install -r requirements.txt
   python configure_MCP.py --mode conda --conda-env LASSI
   ```

   Docker mode writes a Roo MCP entry that launches `LASSI_mcp.py` through `docker run`. Conda mode writes a Roo MCP entry that launches `LASSI_mcp.py` through `conda run`.

4. **Reload Roo Code**

   Reload the VS Code window or restart the Roo Code extension. The mode dropdown should include:

   - `LASSI Optimizer`
   - `LASSI Torch Translator`
   - `LASSI Analyst`
   - `LASSI Profiler`
   - `LASSI Planner`
   - `LASSI Coder`
   - `LASSI Translator`
   - `LASSI Verifier`
   - `LASSI Model Generator`
   - `LASSI Post Profiler`

5. **Verify MCP availability**

   In Roo Code, open the MCP servers view and confirm the `lassi` server is enabled. If it is not, inspect:

   ```bash
   sed -n '1,220p' "$ROO_SETTINGS/mcp_settings.json"
   ```

## Example Usage

> "Optimize the performance of my `@~/TEST/matmul.c` script. Make it as fast as possible."

## Tips

- Use Roo context mentions to pass files, such as `@TEST/file.c`.
- If custom modes do not appear, confirm `custom_modes.yaml` is in Roo's `settings` directory and the rule folders are directly under `~/.roo/` as `rules-{slug}` directories.
- If MCP tools do not appear, rerun `python configure_MCP.py --mode docker --image-name lassi-soda-mcp:latest` or `python configure_MCP.py --mode conda --conda-env LASSI`.
