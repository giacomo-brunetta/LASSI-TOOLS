# LASSI-Agentic Flow

This repository implements an agentic workflow focused on code performance optimization, C/C++ to PyTorch translation, verification, profiling, and model artifact generation.

## Key Components

### LASSI MCP Server
- FastMCP server entrypoint: `LASSI_mcp.py`
- FastMCP display name: `LASSI`
- Recommended MCP config entry name: `lassi`
- Provides tools for:
  - gprof-based profiling
  - executable latency and power/energy profiling
  - hyperfine benchmarking, perf-stat counter collection, perf hotspot profiling, and roofline analysis
  - CPU, RAM, GPU, and toolchain inspection
  - C/C++ sanitizer builds, shared assertion harnesses, randomized equivalence testing, libFuzzer execution, and verification report aggregation
  - numeric CSV summarization, comparison, and mismatch reports
  - PyTorch model export to `.pt`
  - PyTorch `.pt` lowering to MLIR through `torch-mlir`
- Provides resources for:
  - compiler flag cheat sheets at `compiler://{name}/flags`
  - Torch-MLIR/TOSA compatibility wiki resources at `wiki://compatibility/*`, backed by `resources/compatibility/`

<details>
  <summary>Available MCP Tools</summary>

  | Tool | Description | Parameters |
  |------|-------------|------------|
  | `gprof_profiling` | Compiles source file(s) with gprof instrumentation and returns callgraph information. | `path`, `compiler` (optional), `kwds` (optional), `includes` (optional), `libraries` (optional), `args` (optional) |
  | `execute_with_latency` | Runs an executable and returns stdout/stderr plus execution timing. | `path`, `args` (optional), `dump_output` (optional), `expected_output` (optional) |
  | `execute_with_profile` | Runs an executable and returns stdout/stderr plus multi-profiler timing, CPU power, and GPU power reporting when probes are available. | `path`, `args` (optional), `dump_output` (optional), `expected_output` (optional) |
  | `get_machine_info` | Returns CPU and RAM information from the MCP runtime environment. | None |
  | `get_gpu_info` | Returns GPU information using available `nvidia-smi`, `rocm-smi`, or `xpu-smi` tooling. | None |
  | `get_toolchain_info` | Returns Python, torch, torch-mlir, and LLVM-related toolchain information from the MCP runtime environment. | None |
  | `run_benchmark` | Runs stable timing benchmarks with `hyperfine`, writes `.perf/benchmarks/*` artifacts, and classifies runtime improvement/regression. | `benchmark_cases`, `mode` (optional), `warmup` (optional), `min_runs` (optional), `max_runs` (optional), `timeout_s` (optional), `artifact_dir` (optional), `thresholds` (optional) |
  | `collect_perf_stats` | Collects CPU counters with `perf stat` and derives IPC, cache miss, branch miss, and per-input metrics. | `cases`, `mode` (optional), `events` (optional), `repeat` (optional), `timeout_s` (optional), `artifact_dir` (optional) |
  | `profile_hotspots` | Uses `perf record/report/script` to identify top functions and differential hotspot shifts. | `cases`, `mode` (optional), `callgraph` (optional), `frequency` (optional), `timeout_s` (optional), `generate_flamegraph` (optional), `artifact_dir` (optional) |
  | `compare_performance` | Aggregates benchmark, perf-stat, and hotspot evidence into a top-level performance verdict. | `benchmark_result_path`, `perf_stats_result_path` (optional), `profile_result_path` (optional), `policy` (optional), `artifact_dir` (optional) |
  | `collect_hardware_model` | Creates a hardware model for roofline analysis, accepting manual peak FLOP/s and bandwidth overrides. | `device_selector` (optional), `precision_modes` (optional), `bandwidth_levels` (optional), `manual_overrides` (optional), `artifact_dir` (optional) |
  | `estimate_workload_model` | Estimates FLOPs, bytes moved, and arithmetic intensity for common workloads or manual annotations. | `benchmark_cases`, `source_a` (optional), `source_b` (optional), `estimation_mode` (optional), `artifact_dir` (optional) |
  | `run_roofline_analysis` | Combines benchmark timing, workload model, and hardware model artifacts into roofline utilization and bound classification. | `benchmark_result_path`, `workload_model_path`, `hardware_model_path`, `precision` (optional), `memory_level` (optional), `mode` (optional), `artifact_dir` (optional) |
  | `compare_roofline` | Compares reference and candidate roofline positions and utilization. | `roofline_result_path`, `policy` (optional), `artifact_dir` (optional) |
  | `summarize_csv` | Summarizes a numeric CSV file, including shape, size, range, mean/std, and NaN/Inf checks. | `path` |
  | `compare_csv_outputs` | Compares golden and candidate numeric CSV outputs with exact and tolerant match status plus error metrics. | `golden_csv`, `candidate_csv`, `rtol` (optional), `atol` (optional), `expected_shape` (optional) |
  | `diff_csv_outputs` | Reports element-wise CSV mismatches and can write the mismatch report as JSON. | `golden_csv`, `candidate_csv`, `output_path` (optional), `max_rows` (optional) |
  | `export_model_to_pt` | Loads a PyTorch model class from a Python file and exports a `.pt` artifact. | `model_file`, `class_name`, `output_path`, `init_args` (optional), `weights_path` (optional), `export_type` (optional), `input_shape` (optional) |
  | `compile_torch_to_mlir` | Compiles a PyTorch `.pt` model into MLIR using `torch-mlir`. | `model_path`, `inputs`, `target` (optional), `frontend` (optional), `validate` (optional), `output_path` (optional) |
  | `build_sanitized` | Compiles C/C++ code with strict warnings and sanitizer instrumentation across optimization levels. | `source_path`, `language` (optional), `entrypoint_hint` (optional), `build_mode` (optional), `optimization_levels` (optional), `sanitizers` (optional), `warnings_as_errors` (optional), `timeout_s` (optional), `extra_compile_flags` (optional), `extra_link_flags` (optional) |
  | `synthesize_common_harness` | Generates an inspectable common Python harness for Python callables and scalar shared-library entrypoints. | `source_a`, `source_b`, `task_type`, `entrypoints` (optional), `input_schema` (optional), `output_schema` (optional) |
  | `generate_assertion_suite` | Generates shared semantic assertion checks and harness metadata for two implementations. | `source_a`, `source_b`, `task_type`, `entrypoints` (optional), `existing_tests` (optional), `semantic_hints` (optional), `numeric_tolerance` (optional), `timeout_s` (optional) |
  | `run_assertion_suite` | Executes a generated shared assertion suite against two artifacts. | `assertion_suite_path`, `implementation_a_artifact`, `implementation_b_artifact`, `task_type`, `timeout_s` (optional) |
  | `run_random_equivalence_tests` | Runs randomized differential tests for Python callables or scalar shared-library entrypoints and persists counterexamples. | `source_a`, `source_b`, `artifact_a` (optional), `artifact_b` (optional), `task_type` (optional), `entrypoints` (optional), `input_schema` (optional), `comparison` (optional), `budget` (optional), `corpus_dir` (optional) |
  | `run_robustness_fuzzer` | Runs or builds a libFuzzer target, persists corpus/crashes, and reports sanitizer findings. | `source_path`, `artifact` (optional), `entrypoint` (optional), `input_schema` (optional), `sanitizers` (optional), `corpus_dir` (optional), `seed_corpus_dir` (optional), `budget` (optional), `max_len` (optional) |
  | `run_differential_fuzzer` | Runs an existing differential libFuzzer target and preserves mismatch/crash evidence. | `source_a`, `source_b`, `artifact` (optional), `task_type` (optional), `comparison` (optional), `corpus_dir` (optional), `seed_corpus_dir` (optional), `budget` (optional), `max_len` (optional) |
  | `synthesize_verification_report` | Aggregates verification MCP result objects into `.verify/reports/*.json` and `.md`. | `task_id` (optional), `task_type` (optional), `tool_results` (optional), `output_dir` (optional) |
</details>

### Repository Structure

All MCP tools are registered in `LASSI_mcp.py` at the repository root. Their
implementations live under `lassi/`, grouped by responsibility:

```
LASSI-TOOLS/
├── LASSI_mcp.py              # FastMCP server — registers every tool
├── lassi/
│   ├── core/                 # Compiler, executer, source-file, data models
│   │   ├── compiler.py
│   │   ├── executer.py
│   │   ├── source_file.py
│   │   ├── data_models.py
│   │   ├── command.py        # Shared subprocess runner helpers
│   │   ├── responses.py      # Shared MCP JSON response formatting
│   │   ├── utils.py
│   │   └── mcp_helpers.py    # Shared helpers (now_task_id, short, write_json)
│   ├── profiling/            # Profiler primitives + performance MCP impls
│   │   ├── profiler.py       # Timer, MultiProfiler, CPU/GPU/ARM/NVIDIA probes
│   │   ├── gprof.py
│   │   └── performance_tools.py
│   ├── verification/         # Sanitizer / equivalence / fuzz / CSV MCP impls
│   │   ├── verification_tools.py
│   │   ├── checks.py         # File/MLIR/numeric artifact checks
│   │   └── csv_tools.py
│   ├── analysis/             # Source-level translation analysis helpers
│   │   └── translation_utils.py
│   ├── integrations/         # External toolchain wrappers
│   │   ├── export_pt.py      # PyTorch model → .pt
│   │   ├── torch_to_mlir.py  # .pt → MLIR via torch-mlir
│   │   ├── torch_utils.py    # Shared Torch input/module helpers
│   │   ├── toolchain_info.py
│   │   ├── hardware_info.py
│   │   ├── soda.py
│   │   └── compatibility_resources.py
│   ├── prompt_dicts/         # JSON prompt templates for LASSI agents
│   └── helper_usage.md       # In-repo helper reuse guide for agents
├── setup/                    # Client (Claude / Codex / Roo) MCP setup
├── soda-tools/               # SODA MLIR/HLS toolchain wrappers
├── resources/                # Compatibility wiki and prompts data
├── examples/                 # End-to-end examples
└── requirements/             # Python requirements pinned per platform
```

MCP tool group → backing module:

| MCP tool group | Implementation module |
|----------------|-----------------------|
| `gprof_profiling`, `execute_with_latency`, `execute_with_profile`, `get_machine_info`, `get_gpu_info` | `lassi.profiling.gprof`, `lassi.profiling.profiler` |
| `run_benchmark`, `collect_perf_stats`, `profile_hotspots`, `compare_performance`, `collect_hardware_model`, `estimate_workload_model`, `run_roofline_analysis`, `compare_roofline` | `lassi.profiling.performance_tools` |
| `build_sanitized`, `synthesize_common_harness`, `generate_assertion_suite`, `run_assertion_suite`, `run_random_equivalence_tests`, `run_robustness_fuzzer`, `run_differential_fuzzer`, `synthesize_verification_report` | `lassi.verification.verification_tools` |
| `summarize_csv`, `compare_csv_outputs`, `diff_csv_outputs` | `lassi.verification.csv_tools` |
| `export_model_to_pt` | `lassi.integrations.export_pt` |
| `compile_torch_to_mlir` | `lassi.integrations.torch_to_mlir` |
| `get_toolchain_info` | `lassi.integrations.toolchain_info` |

**Note on the two large modules.** `lassi/profiling/performance_tools.py`
and `lassi/verification/verification_tools.py` are each ~1.8k LOC because
they bundle many related MCP entrypoints with their internal helpers.
Splitting them further (e.g. one file per `*_impl`) is deferred — it would
trade a single grep-friendly file for many imports without changing
behavior. Truly shared helpers across the two modules are factored into
`lassi.core.mcp_helpers`.

### Workflow Sessions

The `setup/` directory contains client-specific workflow setup:

- Roo Code modes and rules: `setup/roo/custom_modes.yaml` and `setup/roo/rules-*`
- Claude Code subagents: `setup/claude/agents/*.md`
- MCP client configuration helper: `setup/configure_MCP.py`

#### General Optimization Workflow
Defined by `setup/roo/rules-lassi-orchestrator/rules.md` and `setup/claude/agents/lassi-orchestrator.md`:

1. **Workspace Setup** - confirm the project directory, constraints, and `LASSI/` artifact folder.
2. **Analysis** - `LASSI Analyst` maps the project and writes `LASSI/phase1_analysis.md`.
3. **Baseline Profiling** - `LASSI Profiler` establishes latency, perf-counter, hotspot, and optional roofline baselines in `LASSI/baseline_profile.json` and `LASSI/profile_summary.md`.
4. **Planning** - `LASSI Planner` writes `LASSI/refactor-plan.md` with measurable targets.
5. **Implementation** - `LASSI Coder` applies scoped changes and writes `LASSI/changes.md`.
6. **Verification** - `LASSI Verifier` checks functional equivalence with sanitizer, assertion, equivalence, fuzzing, and CSV MCP tools where applicable, then writes `LASSI/verification_report.md`.
7. **Final Profiling** - `LASSI Post Profiler` compares optimized metrics against baseline in `LASSI/comparison.md`.
8. **Finalization** - the orchestrator writes `LASSI/final_summary.md` with metrics, correctness status, and unresolved risks.

#### C/C++ to PyTorch Translation Workflow
Defined by `setup/roo/rules-translator-orchestrator/rules.md` and `setup/claude/agents/translator-orchestrator.md`:

1. **Environment Setup** - confirm the source entrypoint, build/run command, input shapes/dtypes, constraints, and toolchain details from `get_toolchain_info`.
2. **Analysis** - `LASSI Analyst` reads the source and project docs, then writes or updates `LASSI/phase1_analysis.md`.
3. **Translation Implementation** - `LASSI Translator` writes export-friendly PyTorch candidate variants and `LASSI/translation_notes.md`.
4. **Verification** - `LASSI Verifier` compares every candidate against the original C/C++ oracle, using sanitizer, assertion, equivalence, fuzzing, and CSV MCP tools where applicable.
5. **Variant Selection** - `LASSI Profiler` benchmarks multiple verified variants with the performance MCP tools when needed and records the selected export candidate.
6. **Model Generation** - `LASSI Model Generator` uses `get_toolchain_info`, `export_model_to_pt`, and `compile_torch_to_mlir` to produce `.pt` and MLIR artifacts, then writes `LASSI/model_generation.md`.
7. **Finalization** - the orchestrator writes `LASSI/translation_final_summary.md` with equivalence, variants, selected artifacts, fallback paths, and risks.

The rules require LASSI MCP tools for compile/export/lowering/performance tasks whenever a matching MCP tool exists. File authoring and edits still happen in the workspace files.

<details>
  <summary>Workflow Diagram</summary>

  ![Mermaid plot](assets/mermaid.png)
</details>

## Installation

Run these commands from the repository root:

```bash
cd ~/LASSI-TOOLS
```

1. **Install the client you want to use**

   LASSI can configure MCP for Claude Code, Codex, or Roo Code. Install the client first:

   - Claude Code
   - Codex
   - Roo Code: https://docs.roocode.com/getting-started/installing

2. **Install optional workflow agents or modes**

   Roo Code loads global custom modes from `settings/custom_modes.yaml`. For a VS Code Remote server, that settings directory is:


   ```bash
   ROO_SETTINGS="$HOME/.vscode-server/data/User/globalStorage/rooveterinaryinc.roo-cline/settings"
   ```

   Install the LASSI mode definitions and their matching global rule folders:

   ```bash
   mkdir -p "$ROO_SETTINGS" "$HOME/.roo"
   cp setup/roo/custom_modes.yaml "$ROO_SETTINGS/custom_modes.yaml"
   cp -R setup/roo/rules-* "$HOME/.roo/"
   ```

   This overwrites Roo's global `custom_modes.yaml`. If you already have other custom modes, merge this file into the existing one instead of copying it over. Copy the bundled `setup/roo/rules-*` folders as-is so each workflow session can load its matching rules.

   Claude Code can use the bundled specialist agents:

   ```bash
   mkdir -p "$HOME/.claude/agents"
   cp setup/claude/agents/*.md "$HOME/.claude/agents/"
   ```

   Codex does not need extra workflow files for MCP tool access; configure the MCP server in the next step.

3. **Configure the LASSI MCP server**

   Use Docker when you want the MCP server and its Python dependencies to run in a container:

   ```bash
   CLIENT=claude ./setup/setup_mcp_docker.sh
   ```

   Set `CLIENT=roo` or `CLIENT=codex` to write the MCP configuration for a different client.

   Use Conda when you want the MCP server to run directly on the host:

   ```bash
   conda create --name LASSI python=3.12
   conda activate LASSI
   pip install -r requirements/requirements.txt
   python setup/configure_MCP.py --client claude --mode conda --conda-env LASSI --server-name lassi
   ```

   The setup defaults to Claude and Docker. Use `--client roo` for Roo Code or `--client codex` for Codex. Use `--server-name` to choose the MCP server entry name; the bundled rules and agents refer to `lassi`. Docker mode writes an MCP entry that launches `LASSI_mcp.py` through `docker run`. Conda mode writes an MCP entry that launches `LASSI_mcp.py` through `conda run`.

4. **Reload your client**

   Reload Claude Code, Codex, or the VS Code window running Roo Code so the MCP configuration is picked up. Roo Code's mode dropdown should include:

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
