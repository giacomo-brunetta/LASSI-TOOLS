# LASSI-Agentic Flow

LASSI is an agentic workflow for **code performance optimization**, **C/C++ → PyTorch translation**, **functional verification**, **profiling**, and **MLIR/TOSA model artifact generation**.

The tooling has migrated from a single FastMCP server to a set of **Claude Code Skills + Subagents**. Each former MCP tool is now an individual skill the agent can invoke through `Bash`, with no JSON-RPC server in the loop. The legacy MCP server is still shipped under [`mcp/`](mcp/README.md) for backward compatibility.

> **Heads up:** the entry point used to be `LASSI_mcp.py` at the repo root. It now lives at `mcp/LASSI_mcp.py`. All Dockerfiles, configure scripts, and bootstrap shells were moved into `mcp/` too.

---

## Repository Layout

```
LASSI-TOOLS/
├── .claude/
│   ├── agents/                 # Subagent prompts (analyst, coder, planner, ...)
│   └── skills/                 # One skill per former MCP tool (lassi-*)
├── agents/                     # Python agent implementations (used by graph/)
├── cli/                        # Standalone CLI scripts each skill shells out to
├── graph/                      # Pydantic-graph workflow that orchestrates agents
├── lassi/                      # Core libraries (profiling, verification, integrations)
├── mcp/                        # Legacy MCP server (LASSI_mcp.py, Dockerfiles, configure)
├── setup/                      # Non-Claude client setup (Roo Code modes)
├── soda-tools/                 # SODA MLIR/HLS toolchain wrappers
├── resources/                  # Compatibility wiki and prompt data
├── examples/                   # End-to-end examples
└── requirements/               # Pinned Python requirements
```

The `cli/` scripts are the runtime surface the skills call. The `lassi/` package holds the reusable Python primitives (`Compiler`, `Executer`, `Timer`, profiler probes, verification harnesses, torch-mlir bridge, etc.) those scripts depend on.

---

## Installation

### 1. Clone and create a Python environment

```bash
git clone <this-repo> ~/LASSI-TOOLS
cd ~/LASSI-TOOLS

conda create --name LASSI python=3.12 -y
conda activate LASSI
pip install -r requirements/requirements.txt
```

Make sure the CLI scripts are executable and on your `PATH` (the skills resolve them by name):

```bash
chmod +x cli/*.py
export PATH="$PWD/cli:$PATH"
```

Add the `export` line to your shell profile (`~/.zshrc`, `~/.bashrc`, …) if you want it to persist.

### 2. Install the Claude Code skills

Skills live under `~/.claude/skills/<skill-name>/SKILL.md`. Copy the bundled set into your user-level Claude config:

```bash
mkdir -p ~/.claude/skills
cp -R .claude/skills/lassi-* ~/.claude/skills/
```

To install them only for this project instead of globally, copy them into `<project>/.claude/skills/` (this repo already ships them there).

After copying, restart Claude Code (or run `/reload` in the REPL) so the new skills are discovered. They will then show up in the auto-loaded skill list:

```
- lassi-build-sanitized
- lassi-collect-perf-stats
- lassi-compare-csv-outputs
- ...
```

### 3. Install the Claude Code subagents

Subagents live under `~/.claude/agents/<agent>.md`. The LASSI workflow ships these:

| Agent | Role |
|-------|------|
| `lassi-orchestrator` | Coordinates the full optimization workflow |
| `translator-orchestrator` | Coordinates the C/C++ → PyTorch/TOSA workflow |
| `analyst` | Produces a minimal repo / build / target analysis artifact |
| `profiler` | Establishes the baseline performance measurements |
| `planner` | Picks one concrete optimization strategy |
| `coder` | Implements one planned optimization |
| `verifier` | Functional equivalence + sanitizer / fuzz checks |
| `post-profiler` | Re-measures the optimized variant against the baseline |
| `translator` | Writes export-friendly PyTorch translation candidates |
| `model-generator` | Produces `.pt`, TOSA, and SODA HLS artifacts |
| `debugger` | Last-resort investigator for translation/lowering failures |

Install them with:

```bash
mkdir -p ~/.claude/agents
cp .claude/agents/*.md ~/.claude/agents/
```

Restart Claude Code. The agents become callable through the `Agent` tool (e.g. `subagent_type: "lassi-orchestrator"`).

### 4. (Optional) Reduce permission prompts

The skills shell out to common tools (`clang`, `hyperfine`, `perf`, `python3`, `docker`, `git`, …). If you want fewer approval prompts, run `/fewer-permission-prompts` in Claude Code after exercising the workflow once, and Claude will write an allowlist into `.claude/settings.json`.

---

## Available Skills

Each former MCP tool is now a skill. Group → skill mapping:

### Profiling & benchmarking
| Skill | Purpose |
|-------|---------|
| `lassi-gprof-profiling` | Build with gprof, run, return flat + callgraph profile |
| `lassi-execute-with-latency` | One-shot binary run with wall-clock timing |
| `lassi-execute-with-profile` | Binary run with Timer + CPU/GPU power probes |
| `lassi-run-benchmark` | Stable timing via `hyperfine` (single or differential a/b) |
| `lassi-collect-perf-stats` | `perf stat` counters → IPC, cache/branch metrics (macOS falls back to `/usr/bin/time -l`) |
| `lassi-profile-hotspots` | `perf record/report/script` hotspot sampling (macOS falls back to `sample`) |
| `lassi-compare-performance` | Aggregate benchmark + perf-stat + hotspot into a verdict |
| `lassi-estimate-workload-model` | FLOPs / bytes / arithmetic-intensity estimation |
| `lassi-run-roofline-analysis` | Combine workload + hardware model into roofline placement |
| `lassi-compare-roofline` | Diff reference vs candidate roofline positions |

### Verification
| Skill | Purpose |
|-------|---------|
| `lassi-build-sanitized` | Compile C/C++ with strict warnings + sanitizers across `-O` levels |
| `lassi-synthesize-common-harness` | Drop the shared `common_harness.py` fixture |
| `lassi-generate-assertion-suite` | Generate the shared `assertion_suite.py` |
| `lassi-run-assertion-suite` | Execute the generated suite against two implementations |
| `lassi-run-random-equivalence-tests` | Broad-coverage randomized differential testing |
| `lassi-run-robustness-fuzzer` | Run a libFuzzer target with sanitizers |
| `lassi-run-differential-fuzzer` | Run a differential libFuzzer target, preserve divergences |
| `lassi-synthesize-verification-report` | Aggregate verification JSON into one report |
| `lassi-summarize-csv` | Sanity-check a numeric CSV |
| `lassi-compare-csv-outputs` | Golden-vs-candidate CSV comparison with rtol/atol |
| `lassi-diff-csv-outputs` | Element-wise CSV mismatch report |

### Toolchain & hardware
| Skill | Purpose |
|-------|---------|
| `lassi-get-machine-info` | OS / CPU / ISA / RAM fingerprint |
| `lassi-get-gpu-info` | GPU info via vendor tool (nvidia/rocm/xpu/macOS) |
| `lassi-get-toolchain-info` | Python / torch / torch-mlir / LLVM versions |

### Translation & synthesis
| Skill | Purpose |
|-------|---------|
| `lassi-export-model-to-pt` | Export a PyTorch model class to `.pt` |
| `lassi-compile-torch-to-mlir` | Lower a `.pt` to MLIR (torch / linalg / tosa / stablehlo) |
| `lassi-synthesize-tosa-with-soda` | Drive the SODA Makefile from `01_tosa.mlir` (linalg → bambu) |

---

## Workflows

### General optimization workflow

Driven by `~/.claude/agents/lassi-orchestrator.md`:

1. **Workspace setup** — confirm the project directory, constraints, and `LASSI/` artifact folder.
2. **Analysis** — `analyst` writes `LASSI/phase1_analysis.md`.
3. **Baseline profiling** — `profiler` writes `LASSI/baseline_profile.json` and `LASSI/profile_summary.md`.
4. **Planning** — `planner` writes `LASSI/refactor-plan.md`.
5. **Implementation** — `coder` applies the change and writes `LASSI/changes.md`.
6. **Verification** — `verifier` runs sanitizer / assertion / equivalence / fuzz / CSV skills and writes `LASSI/verification_report.md`.
7. **Final profiling** — `post-profiler` compares against the baseline in `LASSI/comparison.md`.
8. **Finalization** — the orchestrator writes `LASSI/final_summary.md`.

### C/C++ → PyTorch translation workflow

Driven by `~/.claude/agents/translator-orchestrator.md`:

1. **Environment setup** — confirm entrypoint, build/run command, IO shapes; check toolchain with `lassi-get-toolchain-info`.
2. **Analysis** — `analyst` writes `LASSI/phase1_analysis.md`.
3. **Translation** — `translator` writes export-friendly PyTorch candidates and `LASSI/translation_notes.md`.
4. **Verification** — `verifier` compares each candidate to the C/C++ oracle.
5. **Variant selection** — `profiler` benchmarks the verified variants.
6. **Model generation** — `model-generator` runs `lassi-export-model-to-pt`, `lassi-compile-torch-to-mlir`, and optionally `lassi-synthesize-tosa-with-soda` to produce `.pt` / MLIR / HLS artifacts; writes `LASSI/model_generation.md`.
7. **Finalization** — the orchestrator writes `LASSI/translation_final_summary.md`.

Workflow artifacts always land in `<project>/LASSI/`. Prefer file handoffs over chat summaries.

---

## Programmatic Orchestration (Pydantic-graph)

`graph/graph_flow.py` runs the same agents headlessly via the Claude Agent SDK + `pydantic_graph`, with a built-in benchmarking and verification loop. See `graph/example.py` and `graph/graph_code_test.json` for the input shape. This is the path to take when you want repeatable batch runs rather than interactive Claude Code sessions.

---

## Legacy MCP Server

If you need the original FastMCP server (e.g. for Roo Code, Codex, or non-Claude clients), see [`mcp/README.md`](mcp/README.md). The Docker and conda launch paths are the same as before; only the file locations changed.

---

## Other Clients (Roo Code)

`setup/roo/` ships the Roo Code custom modes and per-mode rule folders that mirror the Claude subagents above. Install them with:

```bash
ROO_SETTINGS="$HOME/.vscode-server/data/User/globalStorage/rooveterinaryinc.roo-cline/settings"
mkdir -p "$ROO_SETTINGS" "$HOME/.roo"
cp setup/roo/custom_modes.yaml "$ROO_SETTINGS/custom_modes.yaml"
cp -R setup/roo/rules-* "$HOME/.roo/"
```

If you already keep custom modes, merge `custom_modes.yaml` instead of overwriting it. Roo Code still talks to the legacy MCP server — configure it from `mcp/` (see that folder's README).
