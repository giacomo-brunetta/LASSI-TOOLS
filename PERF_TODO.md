# Performance MCP Tools Specification

## Purpose

This document specifies a performance-analysis MCP server for evaluating code transformations and translations, especially:

1. C ↔ C optimization rewrites.

2. C ↔ Torch translations.

3. Future portability to GPUs, ROCm devices, TPUs, FPGAs, and other accelerators.

The goal is to make performance analysis evidence-driven, reproducible, differential, and compatible with the existing correctness-verification MCP architecture.

This specification covers:

```text

V1: Benchmarking + perf-based CPU performance analysis

V2: Roofline analysis + hardware-agnostic MetricProvider abstraction

```

The planner agent already exists. This document only specifies the MCP tools, schemas, artifacts, contracts, and execution semantics required by the performance-analysis layer.

References:

- Linux perf: https://perfwiki.github.io/main/

- perf stat manual: https://man7.org/linux/man-pages/man1/perf-stat.1.html

- perf record manual: https://man7.org/linux/man-pages/man1/perf-record.1.html

- hyperfine: https://github.com/sharkdp/hyperfine

- Roofline model: Williams, Waterman, Patterson, “Roofline: An Insightful Visual Performance Model for Multicore Architectures,” CACM 2009.

---

## Design Goals

The system must support:

1. Differential performance comparison between a reference implementation and candidate implementation.

2. Stable runtime benchmarking with repeated trials and warmups.

3. Low-level CPU performance counter collection via `perf stat`.

4. Hotspot localization via `perf record`.

5. Reproducible artifacts and raw logs.

6. Roofline analysis for compute-bound vs memory-bound classification.

7. A backend-neutral metric abstraction for future accelerator support.

8. Integration with correctness verification outputs and corpora.

The system must not assume that faster code is correct. Performance analysis should normally run after correctness gates pass, unless the planner explicitly requests performance-only diagnostics.

---

## System Architecture

```text

Planner Agent

    │

    └── Performance MCP Server

            │

            ├── Benchmark Tool

            │       └── hyperfine

            │

            ├── Perf Counter Tool

            │       └── perf stat

            │

            ├── Hotspot Profiling Tool

            │       └── perf record / perf report / perf script

            │

            ├── Differential Comparator

            │       └── statistical and counter-delta analysis

            │

            └── Roofline Tool

                    ├── MetricProvider abstraction

                    ├── Hardware model

                    └── arithmetic-intensity analysis

```

The Performance MCP server may expose all tools from a single server. This is preferred over separate servers because all tools share artifacts, benchmark cases, hardware metadata, and result schemas.

---

## Version Scope

### V1: Benchmarking + perf

V1 includes:

```text

run_benchmark

collect_perf_stats

profile_hotspots

compare_performance

```

Backends:

```text

hyperfine

perf stat

perf record

perf report

perf script

```

V1 outputs:

```text

runtime statistics

speedup/regression classification

hardware counter deltas

IPC

cache miss rates

branch miss rates

hotspot profiles

raw perf logs

```

### V2: Roofline + hardware abstraction

V2 includes:

```text

collect_hardware_model

estimate_workload_model

run_roofline_analysis

compare_roofline

```

V2 outputs:

```text

FLOP count

memory-byte estimate

arithmetic intensity

achieved FLOP/s

achieved bandwidth

memory-bound vs compute-bound classification

roofline utilization

hardware-neutral performance summaries

```

---

## Common Concepts

### Source Pair

Most performance tools should compare two implementations:

```json

{

  "source_a": "/path/to/reference",

  "source_b": "/path/to/candidate"

}

```

`source_a` is normally the reference implementation.

`source_b` is normally the optimized or translated candidate.

For C ↔ Torch:

```text

source_a: C/C++ implementation

source_b: Python/Torch implementation

```

Performance tools may also run single-target analysis when requested.

---

### Benchmark Case

A benchmark case defines one executable workload.

```json

{

  "case_id": "matmul_1024_float32",

  "command_a": "./orig --m 1024 --n 1024 --dtype float32",

  "command_b": "./opt --m 1024 --n 1024 --dtype float32",

  "working_dir": "/path/to/workdir",

  "environment": {

    "OMP_NUM_THREADS": "1"

  },

  "input_artifacts": [

    ".verify/corpus/equivalence/matmul_1024.pkl"

  ],

  "metadata": {

    "shape": [1024, 1024],

    "dtype": "float32",

    "problem_size": 1048576

  }

}

```

Benchmark cases should be derived from:

1. Real workloads.

2. Correctness/equivalence corpora.

3. Edge-case corpora.

4. Representative tensor shapes.

5. Planner-generated performance stress cases.

---

### Performance Verdicts

Performance tools use the following verdicts:

```text

PASS

REGRESSION

IMPROVEMENT

NEUTRAL

UNSURE

ERROR

```

Definitions:

| Verdict | Meaning |

|---|---|

| `IMPROVEMENT` | Candidate is statistically faster or better on target metrics. |

| `REGRESSION` | Candidate is statistically slower or worse on target metrics. |

| `NEUTRAL` | No meaningful performance difference detected. |

| `PASS` | Tool completed successfully but did not perform a direct comparison. |

| `UNSURE` | Evidence is insufficient due to noise, small sample size, or unstable measurements. |

| `ERROR` | Tool infrastructure failed. |

For top-level performance comparison, prefer:

```text

IMPROVEMENT

REGRESSION

NEUTRAL

UNSURE

ERROR

```

---

### Confidence

Confidence is evidence strength, not mathematical certainty.

Suggested interpretation:

| Confidence | Meaning |

|---:|---|

| 0.95–1.00 | Very stable result, low variance, multiple metrics agree. |

| 0.80–0.94 | Good evidence, statistically meaningful result. |

| 0.60–0.79 | Moderate evidence. |

| 0.40–0.59 | Weak evidence, noisy measurements. |

| 0.00–0.39 | Failure, infrastructure error, or unreliable result. |

---

### Common Response Schema

All tools must return:

```json

{

  "verdict": "IMPROVEMENT | REGRESSION | NEUTRAL | PASS | UNSURE | ERROR",

  "confidence": 0.0,

  "summary": "human-readable summary",

  "metrics": {},

  "artifacts": [],

  "warnings": [],

  "logs": {

    "stdout": "",

    "stderr": ""

  }

}

```

All raw tool output must be preserved.

---

## Measurement Hygiene Requirements

Performance measurement is fragile. The MCP server must record enough context to make results interpretable.

Every performance run should capture:

```json

{

  "host": {

    "hostname": "string",

    "kernel": "string",

    "cpu_model": "string",

    "num_cores": 0,

    "num_threads": 0

  },

  "runtime_context": {

    "timestamp": "ISO-8601",

    "governor": "performance | powersave | unknown",

    "cpu_affinity": "string",

    "numa_policy": "string",

    "thermal_warning": false

  },

  "software": {

    "compiler": "string",

    "compiler_version": "string",

    "python_version": "string",

    "torch_version": "string"

  }

}

```

The server should warn if:

1. CPU frequency governor is not stable.

2. System load is high.

3. benchmark variance is high.

4. CPU affinity is not pinned for sensitive benchmarks.

5. the task appears too short for reliable measurement.

6. the candidate was benchmarked with different environment variables than the reference.

---

## Recommended Environment Controls

For CPU benchmarks, the planner or server may set:

```bash

OMP_NUM_THREADS=1

MKL_NUM_THREADS=1

OPENBLAS_NUM_THREADS=1

NUMEXPR_NUM_THREADS=1

```

For multi-threaded benchmarks, thread count must be explicit.

Suggested command wrappers:

```bash

taskset -c 0 ./benchmark

numactl --cpunodebind=0 --membind=0 ./benchmark

```

Do not silently impose affinity if the workload is intended to measure parallel scaling. Record affinity decisions in the report.

---

# V1 Tool Specifications

---

## Tool: `run_benchmark`

### Purpose

Run stable timing benchmarks using `hyperfine`.

This tool answers:

```text

Is candidate B faster than reference A?

Is the speedup statistically meaningful?

How noisy is the benchmark?

```

### Backend

Primary backend:

```text

hyperfine

```

Optional future backends:

```text

custom Python timer

Google Benchmark JSON

pytest-benchmark

Torch benchmark utilities

```

### Input Schema

```json

{

  "benchmark_cases": [

    {

      "case_id": "case_001",

      "command_a": "./orig input.bin",

      "command_b": "./opt input.bin",

      "working_dir": "/path/to/workdir",

      "environment": {},

      "metadata": {}

    }

  ],

  "mode": "single | differential",

  "warmup": 3,

  "min_runs": 10,

  "max_runs": 100,

  "timeout_s": 600,

  "shell": "bash",

  "export_json": true,

  "prepare_command": null,

  "cleanup_command": null,

  "artifact_dir": ".perf/benchmarks/task_id"

}

```

For single-target benchmarking:

```json

{

  "benchmark_cases": [

    {

      "case_id": "case_001",

      "command": "./kernel input.bin"

    }

  ],

  "mode": "single"

}

```

### Backend Command Template

Differential mode:

```bash

hyperfine \

  --warmup 3 \

  --min-runs 10 \

  --max-runs 100 \

  --export-json .perf/benchmarks/<task_id>/hyperfine.json \

  './orig input.bin' \

  './opt input.bin'

```

With setup/cleanup:

```bash

hyperfine \

  --prepare '<prepare_command>' \

  --cleanup '<cleanup_command>' \

  --warmup 3 \

  --min-runs 10 \

  --max-runs 100 \

  --export-json <out.json> \

  '<command_a>' \

  '<command_b>'

```

### Output Schema

```json

{

  "verdict": "IMPROVEMENT",

  "confidence": 0.91,

  "summary": "Candidate is 1.32x faster than reference across 3 benchmark cases.",

  "metrics": {

    "cases": [

      {

        "case_id": "case_001",

        "mean_a_s": 1.204,

        "mean_b_s": 0.912,

        "median_a_s": 1.198,

        "median_b_s": 0.906,

        "stddev_a_s": 0.011,

        "stddev_b_s": 0.010,

        "speedup": 1.32,

        "relative_change_pct": -24.25,

        "verdict": "IMPROVEMENT"

      }

    ],

    "geomean_speedup": 1.32,

    "regression_count": 0,

    "improvement_count": 3,

    "neutral_count": 0

  },

  "artifacts": [

    {

      "kind": "hyperfine_json",

      "path": ".perf/benchmarks/task_id/hyperfine.json"

    },

    {

      "kind": "benchmark_report",

      "path": ".perf/benchmarks/task_id/report.md"

    }

  ],

  "warnings": [],

  "logs": {

    "stdout": "...",

    "stderr": "..."

  }

}

```

### Verdict Rules

For each case:

```text

IMPROVEMENT if candidate is faster by >= min_effect_size and measurement noise is acceptable.

REGRESSION if candidate is slower by >= min_effect_size and measurement noise is acceptable.

NEUTRAL if difference is smaller than min_effect_size.

UNSURE if variance is too high or measurements are unstable.

ERROR if the benchmark command fails.

```

Default thresholds:

```json

{

  "min_effect_size_pct": 3.0,

  "max_cv_pct": 10.0

}

```

Coefficient of variation:

```text

CV = stddev / mean

```

### Notes

`hyperfine` is preferred for wall-clock timing because it handles warmups, repeated runs, and statistical summaries better than ad hoc shell timing.

---

## Tool: `collect_perf_stats`

### Purpose

Collect CPU performance counters using `perf stat`.

This tool answers:

```text

Why did runtime change?

Did cycles, instructions, IPC, cache misses, or branch misses change?

```

### Backend

```text

perf stat

```

### Input Schema

```json

{

  "cases": [

    {

      "case_id": "case_001",

      "command_a": "./orig input.bin",

      "command_b": "./opt input.bin",

      "working_dir": "/path/to/workdir",

      "environment": {},

      "metadata": {}

    }

  ],

  "mode": "single | differential",

  "events": [

    "cycles",

    "instructions",

    "branches",

    "branch-misses",

    "cache-references",

    "cache-misses"

  ],

  "repeat": 5,

  "timeout_s": 600,

  "artifact_dir": ".perf/perf_stats/task_id",

  "use_json_output_if_available": true

}

```

### Recommended Default Events

```text

cycles

instructions

branches

branch-misses

cache-references

cache-misses

task-clock

context-switches

cpu-migrations

page-faults

```

Optional events, depending on platform support:

```text

L1-dcache-loads

L1-dcache-load-misses

LLC-loads

LLC-load-misses

dTLB-loads

dTLB-load-misses

fp_arith_inst_retired.scalar_single

fp_arith_inst_retired.128b_packed_single

fp_arith_inst_retired.256b_packed_single

fp_arith_inst_retired.512b_packed_single

```

The server must degrade gracefully when events are unavailable.

### Backend Command Template

```bash

perf stat \

  -r 5 \

  -e cycles,instructions,branches,branch-misses,cache-references,cache-misses \

  -x , \

  -o .perf/perf_stats/<task_id>/<case_id>_a.csv \

  ./orig input.bin

```

Candidate:

```bash

perf stat \

  -r 5 \

  -e cycles,instructions,branches,branch-misses,cache-references,cache-misses \

  -x , \

  -o .perf/perf_stats/<task_id>/<case_id>_b.csv \

  ./opt input.bin

```

### Derived Metrics

The server must compute:

```text

IPC = instructions / cycles

branch_miss_rate = branch-misses / branches

cache_miss_rate = cache-misses / cache-references

cycles_per_input_element = cycles / problem_size, if problem_size known

instructions_per_input_element = instructions / problem_size, if problem_size known

```

### Output Schema

```json

{

  "verdict": "PASS",

  "confidence": 0.88,

  "summary": "Candidate reduced cycles by 27.1% and improved IPC from 1.42 to 1.91.",

  "metrics": {

    "cases": [

      {

        "case_id": "case_001",

        "a": {

          "cycles": 1200000000,

          "instructions": 1704000000,

          "ipc": 1.42,

          "branches": 40000000,

          "branch_misses": 1200000,

          "branch_miss_rate": 0.03,

          "cache_references": 9000000,

          "cache_misses": 450000,

          "cache_miss_rate": 0.05

        },

        "b": {

          "cycles": 875000000,

          "instructions": 1671000000,

          "ipc": 1.91,

          "branches": 29000000,

          "branch_misses": 580000,

          "branch_miss_rate": 0.02,

          "cache_references": 8300000,

          "cache_misses": 390000,

          "cache_miss_rate": 0.047

        },

        "delta": {

          "cycles_pct": -27.1,

          "instructions_pct": -1.9,

          "ipc_pct": 34.5,

          "branch_miss_rate_pct": -33.3,

          "cache_miss_rate_pct": -6.0

        }

      }

    ]

  },

  "artifacts": [

    {

      "kind": "perf_stat_raw",

      "path": ".perf/perf_stats/task_id/case_001_a.csv"

    },

    {

      "kind": "perf_stat_raw",

      "path": ".perf/perf_stats/task_id/case_001_b.csv"

    }

  ],

  "warnings": [

    "Some requested events were unavailable and omitted: L1-dcache-load-misses"

  ]

}

```

### Failure Semantics

Return `ERROR` if:

1. `perf` is unavailable.

2. permissions prevent counter access.

3. command fails.

4. output cannot be parsed.

Return `UNSURE` if:

1. too many events are unsupported;

2. repeated runs disagree substantially;

3. system noise is high.

---

## Tool: `profile_hotspots`

### Purpose

Locate where time is spent using `perf record`.

This tool answers:

```text

Which functions dominate runtime?

Did the candidate move time into unexpected routines?

Did an optimization introduce memcpy, allocation, dispatch, or conversion overhead?

```

### Backend

```text

perf record

perf report

perf script

```

Optional flamegraph backend:

```text

FlameGraph stackcollapse-perf.pl

FlameGraph flamegraph.pl

```

### Input Schema

```json

{

  "cases": [

    {

      "case_id": "case_001",

      "command_a": "./orig input.bin",

      "command_b": "./opt input.bin",

      "working_dir": "/path/to/workdir",

      "environment": {},

      "metadata": {}

    }

  ],

  "mode": "single | differential",

  "callgraph": true,

  "frequency": 999,

  "timeout_s": 600,

  "generate_flamegraph": true,

  "artifact_dir": ".perf/profiles/task_id"

}

```

### Backend Command Template

Reference:

```bash

perf record \

  -F 999 \

  -g \

  -o .perf/profiles/<task_id>/<case_id>_a.perf.data \

  ./orig input.bin

```

Candidate:

```bash

perf record \

  -F 999 \

  -g \

  -o .perf/profiles/<task_id>/<case_id>_b.perf.data \

  ./opt input.bin

```

Reports:

```bash

perf report \

  --stdio \

  -i .perf/profiles/<task_id>/<case_id>_a.perf.data \

  > .perf/profiles/<task_id>/<case_id>_a.report.txt

```

Scripts:

```bash

perf script \

  -i .perf/profiles/<task_id>/<case_id>_a.perf.data \

  > .perf/profiles/<task_id>/<case_id>_a.perf.script

```

### Output Schema

```json

{

  "verdict": "PASS",

  "confidence": 0.82,

  "summary": "Candidate hotspot shifted from compute loop to tensor conversion overhead.",

  "metrics": {

    "cases": [

      {

        "case_id": "case_001",

        "top_functions_a": [

          {

            "symbol": "kernel_inner_loop",

            "percent": 64.2

          },

          {

            "symbol": "load_input",

            "percent": 8.1

          }

        ],

        "top_functions_b": [

          {

            "symbol": "torch::from_blob",

            "percent": 31.5

          },

          {

            "symbol": "candidate_kernel",

            "percent": 29.7

          }

        ],

        "hotspot_shift": [

          {

            "symbol": "torch::from_blob",

            "delta_percent": 31.5,

            "interpretation": "new overhead in candidate"

          }

        ]

      }

    ]

  },

  "artifacts": [

    {

      "kind": "perf_data",

      "path": ".perf/profiles/task_id/case_001_a.perf.data"

    },

    {

      "kind": "perf_report",

      "path": ".perf/profiles/task_id/case_001_a.report.txt"

    },

    {

      "kind": "flamegraph_svg",

      "path": ".perf/profiles/task_id/case_001_a.flame.svg"

    }

  ],

  "warnings": []

}

```

### Hotspot Comparison Requirements

For differential mode, compare:

```text

top functions by percentage

new functions in candidate

removed functions in candidate

large percentage shifts

library overhead

allocator overhead

memcpy/memmove overhead

Python/Torch dispatch overhead

```

Special symbols to flag:

```text

malloc

free

memcpy

memmove

operator new

torch::from_blob

at::native

PyObject_Call

pthread_mutex_lock

```

The exact symbol names are platform-dependent. The server should use substring and demangling heuristics.

---

## Tool: `compare_performance`

### Purpose

Aggregate benchmark, perf-stat, and hotspot-profile results into a differential performance verdict.

This is the main V1 summary tool.

### Input Schema

```json

{

  "benchmark_result_path": ".perf/benchmarks/task_id/result.json",

  "perf_stats_result_path": ".perf/perf_stats/task_id/result.json",

  "profile_result_path": ".perf/profiles/task_id/result.json",

  "policy": {

    "min_speedup_for_improvement": 1.03,

    "max_slowdown_for_neutral": 1.03,

    "max_cv_pct": 10.0,

    "regression_is_failure": true

  },

  "artifact_dir": ".perf/reports/task_id"

}

```

### Output Schema

```json

{

  "verdict": "IMPROVEMENT",

  "confidence": 0.9,

  "summary": "Candidate is faster with consistent counter evidence: 1.32x geomean speedup, 27% fewer cycles, improved IPC.",

  "metrics": {

    "geomean_speedup": 1.32,

    "cases": [

      {

        "case_id": "case_001",

        "runtime_speedup": 1.32,

        "cycles_delta_pct": -27.1,

        "instructions_delta_pct": -1.9,

        "ipc_delta_pct": 34.5,

        "cache_miss_rate_delta_pct": -6.0,

        "branch_miss_rate_delta_pct": -33.3,

        "verdict": "IMPROVEMENT"

      }

    ],

    "regression_count": 0,

    "improvement_count": 3,

    "neutral_count": 0,

    "unsure_count": 0

  },

  "artifacts": [

    {

      "kind": "performance_report_json",

      "path": ".perf/reports/task_id/performance_report.json"

    },

    {

      "kind": "performance_report_md",

      "path": ".perf/reports/task_id/performance_report.md"

    }

  ],

  "warnings": []

}

```

### Aggregation Logic

The tool should prefer wall-clock benchmark results for the primary performance verdict.

Perf counters provide explanatory evidence.

Rules:

1. If runtime improves and counters agree, return `IMPROVEMENT`.

2. If runtime regresses and counters agree, return `REGRESSION`.

3. If runtime changes but counters are contradictory, return `UNSURE` or low-confidence `IMPROVEMENT`/`REGRESSION`.

4. If runtime difference is smaller than threshold, return `NEUTRAL`.

5. If variance is high, return `UNSURE`.

---

# V2 Tool Specifications

---

## MetricProvider Abstraction

### Purpose

Define a hardware-neutral interface for collecting performance metrics.

V1 uses CPU backends:

```text

PerfProvider

HyperfineProvider

```

V2 adds:

```text

RooflineProvider

```

Future providers:

```text

NsightProvider

ROCmProvider

VTuneProvider

LIKWIDProvider

TPUProvider

FPGAProvider

CustomAcceleratorProvider

```

### Conceptual Interface

```python

class MetricProvider:

    def collect_runtime(self, benchmark_case) -> RuntimeMetrics:

        ...

    def collect_counters(self, benchmark_case) -> CounterMetrics:

        ...

    def collect_memory_traffic(self, benchmark_case) -> MemoryTrafficMetrics:

        ...

    def collect_flops(self, benchmark_case) -> FlopMetrics:

        ...

    def collect_hardware_model(self) -> HardwareModel:

        ...

```

### Provider Output Types

#### RuntimeMetrics

```json

{

  "mean_s": 0.912,

  "median_s": 0.906,

  "stddev_s": 0.010,

  "min_s": 0.890,

  "max_s": 0.940,

  "runs": 30

}

```

#### CounterMetrics

```json

{

  "cycles": 875000000,

  "instructions": 1671000000,

  "ipc": 1.91,

  "branches": 29000000,

  "branch_misses": 580000,

  "cache_references": 8300000,

  "cache_misses": 390000

}

```

#### MemoryTrafficMetrics

```json

{

  "bytes_read": 1200000000,

  "bytes_written": 400000000,

  "total_bytes": 1600000000,

  "source": "estimated | measured"

}

```

#### FlopMetrics

```json

{

  "flops": 2000000000,

  "source": "estimated | measured | annotated"

}

```

#### HardwareModel

```json

{

  "device_id": "cpu_0",

  "device_type": "CPU | GPU | TPU | FPGA | CUSTOM",

  "name": "Intel Xeon ...",

  "peak_flops": {

    "fp32": 1000000000000,

    "fp64": 500000000000

  },

  "peak_bandwidth_Bps": {

    "dram": 100000000000

  },

  "memory_hierarchy": [

    {

      "level": "L1",

      "bandwidth_Bps": null,

      "capacity_bytes": 32768

    },

    {

      "level": "DRAM",

      "bandwidth_Bps": 100000000000,

      "capacity_bytes": null

    }

  ],

  "metadata": {}

}

```

---

## Tool: `collect_hardware_model`

### Purpose

Collect or accept a hardware model for roofline analysis.

This tool answers:

```text

What is the peak compute throughput?

What is the peak memory bandwidth?

What hardware target is being analyzed?

```

### Input Schema

```json

{

  "device_selector": {

    "type": "CPU | GPU | TPU | FPGA | CUSTOM | auto",

    "id": "optional"

  },

  "precision_modes": ["fp32", "fp64"],

  "bandwidth_levels": ["dram"],

  "manual_overrides": {

    "peak_flops": {},

    "peak_bandwidth_Bps": {}

  },

  "artifact_dir": ".perf/hardware/task_id"

}

```

### Output Schema

```json

{

  "verdict": "PASS",

  "confidence": 0.8,

  "summary": "Collected CPU hardware model with manually provided DRAM bandwidth.",

  "metrics": {

    "hardware_model": {

      "device_id": "cpu_0",

      "device_type": "CPU",

      "name": "unknown",

      "peak_flops": {

        "fp32": 1000000000000

      },

      "peak_bandwidth_Bps": {

        "dram": 100000000000

      }

    }

  },

  "artifacts": [

    {

      "kind": "hardware_model_json",

      "path": ".perf/hardware/task_id/hardware_model.json"

    }

  ],

  "warnings": [

    "peak_bandwidth_Bps was manually provided, not measured"

  ]

}

```

### Notes

For V2, it is acceptable to rely on manually supplied peak FLOP/s and peak bandwidth values.

Automated peak measurement may be added later.

---

## Tool: `estimate_workload_model`

### Purpose

Estimate workload FLOPs and memory traffic.

This tool is needed for roofline analysis.

It answers:

```text

How many floating-point operations does this workload perform?

How many bytes does it move?

What is its arithmetic intensity?

```

### Input Schema

```json

{

  "benchmark_cases": [

    {

      "case_id": "matmul_1024_float32",

      "operation": "matmul | conv2d | elementwise | reduction | custom | unknown",

      "metadata": {

        "shape": [1024, 1024],

        "dtype": "float32",

        "m": 1024,

        "n": 1024,

        "k": 1024

      },

      "manual_flops": null,

      "manual_bytes": null

    }

  ],

  "source_a": "/path/to/reference",

  "source_b": "/path/to/candidate",

  "estimation_mode": "manual | formula | static_analysis | agent_assisted",

  "artifact_dir": ".perf/roofline/task_id/workload_model"

}

```

### Common FLOP Formulas

#### Matrix multiplication

For:

```text

C[M, N] = A[M, K] × B[K, N]

```

FLOPs:

```text

2 * M * N * K

```

Approximate memory bytes:

```text

sizeof(dtype) * (M*K + K*N + M*N)

```

This is a lower-bound model. Actual traffic may be higher due to cache misses, layout, and implementation.

#### Elementwise unary operation

FLOPs:

```text

N * flops_per_element

```

Memory bytes:

```text

sizeof(dtype) * (N input + N output)

```

#### Elementwise binary operation

FLOPs:

```text

N * flops_per_element

```

Memory bytes:

```text

sizeof(dtype) * (2*N input + N output)

```

#### Reduction

For sum over N elements:

```text

FLOPs ≈ N - 1

Memory bytes ≈ sizeof(dtype) * (N input + 1 output)

```

### Output Schema

```json

{

  "verdict": "PASS",

  "confidence": 0.75,

  "summary": "Estimated workload model for 3 benchmark cases.",

  "metrics": {

    "cases": [

      {

        "case_id": "matmul_1024_float32",

        "flops": 2147483648,

        "bytes_moved": 12582912,

        "arithmetic_intensity": 170.67,

        "flops_source": "formula",

        "bytes_source": "formula_lower_bound"

      }

    ]

  },

  "artifacts": [

    {

      "kind": "workload_model_json",

      "path": ".perf/roofline/task_id/workload_model/model.json"

    }

  ],

  "warnings": [

    "Memory traffic is a lower-bound estimate."

  ]

}

```

### Failure Semantics

Return `UNSURE` if:

1. operation type cannot be inferred;

2. shapes are unknown;

3. FLOPs cannot be estimated;

4. bytes moved cannot be estimated.

Return `PASS` with low confidence if manual annotations are incomplete but sufficient for approximate roofline classification.

---

## Tool: `run_roofline_analysis`

### Purpose

Perform roofline analysis for one or more benchmark cases.

This tool answers:

```text

Is the workload memory-bound or compute-bound?

How far is it from the hardware roofline?

Did the candidate move closer to the roofline?

```

### Input Schema

```json

{

  "benchmark_result_path": ".perf/benchmarks/task_id/result.json",

  "workload_model_path": ".perf/roofline/task_id/workload_model/model.json",

  "hardware_model_path": ".perf/hardware/task_id/hardware_model.json",

  "precision": "fp32",

  "memory_level": "dram",

  "mode": "single | differential",

  "artifact_dir": ".perf/roofline/task_id"

}

```

### Roofline Definitions

Arithmetic intensity:

```text

AI = FLOPs / bytes_moved

```

Achieved FLOP/s:

```text

achieved_flops = FLOPs / runtime_seconds

```

Achieved bandwidth:

```text

achieved_bandwidth = bytes_moved / runtime_seconds

```

Compute roof:

```text

compute_roof = peak_flops

```

Memory roof:

```text

memory_roof = AI * peak_bandwidth

```

Attainable roof:

```text

attainable = min(compute_roof, memory_roof)

```

Utilization:

```text

utilization = achieved_flops / attainable

```

Bound classification:

```text

memory_bound if memory_roof < compute_roof

compute_bound if compute_roof <= memory_roof

```

### Output Schema

```json

{

  "verdict": "PASS",

  "confidence": 0.82,

  "summary": "Candidate improved achieved FLOP/s from 2.1e11 to 3.3e11 and remains memory-bound.",

  "metrics": {

    "cases": [

      {

        "case_id": "matmul_1024_float32",

        "a": {

          "runtime_s": 0.0102,

          "flops": 2147483648,

          "bytes_moved": 12582912,

          "arithmetic_intensity": 170.67,

          "achieved_flops": 210537612549.0,

          "achieved_bandwidth_Bps": 1233618823.5,

          "attainable_flops": 1000000000000.0,

          "utilization": 0.2105,

          "bound": "compute"

        },

        "b": {

          "runtime_s": 0.0065,

          "flops": 2147483648,

          "bytes_moved": 12582912,

          "arithmetic_intensity": 170.67,

          "achieved_flops": 330382099692.0,

          "achieved_bandwidth_Bps": 1935832615.4,

          "attainable_flops": 1000000000000.0,

          "utilization": 0.3304,

          "bound": "compute"

        },

        "delta": {

          "achieved_flops_speedup": 1.57,

          "utilization_delta": 0.1199,

          "bound_changed": false

        }

      }

    ]

  },

  "artifacts": [

    {

      "kind": "roofline_report_json",

      "path": ".perf/roofline/task_id/roofline_report.json"

    },

    {

      "kind": "roofline_report_md",

      "path": ".perf/roofline/task_id/roofline_report.md"

    },

    {

      "kind": "roofline_plot",

      "path": ".perf/roofline/task_id/roofline.png"

    }

  ],

  "warnings": [

    "Bytes moved are formula-based lower-bound estimates."

  ]

}

```

### Verdict Semantics

`run_roofline_analysis` usually returns `PASS` for successful analysis.

It should not alone declare `IMPROVEMENT` or `REGRESSION` unless explicitly used in differential mode with a comparison policy.

For differential mode:

```text

IMPROVEMENT if achieved_flops or utilization improves beyond threshold and runtime does not regress.

REGRESSION if achieved_flops or utilization worsens beyond threshold and runtime regresses.

NEUTRAL if changes are below threshold.

UNSURE if workload or hardware model confidence is too low.

```

---

## Tool: `compare_roofline`

### Purpose

Compare reference and candidate roofline positions.

This tool is useful for accelerator portability analysis because it separates:

```text

algorithmic intensity

achieved throughput

hardware-bound classification

```

### Input Schema

```json

{

  "roofline_result_path": ".perf/roofline/task_id/roofline_report.json",

  "policy": {

    "min_utilization_delta": 0.03,

    "min_achieved_flops_speedup": 1.03,

    "runtime_must_not_regress": true

  },

  "artifact_dir": ".perf/roofline/task_id/comparison"

}

```

### Output Schema

```json

{

  "verdict": "IMPROVEMENT",

  "confidence": 0.81,

  "summary": "Candidate improves roofline utilization from 21.0% to 33.0% with unchanged bound classification.",

  "metrics": {

    "cases": [

      {

        "case_id": "matmul_1024_float32",

        "a_utilization": 0.2105,

        "b_utilization": 0.3304,

        "utilization_delta": 0.1199,

        "a_bound": "compute",

        "b_bound": "compute",

        "bound_changed": false,

        "achieved_flops_speedup": 1.57,

        "verdict": "IMPROVEMENT"

      }

    ],

    "improvement_count": 1,

    "regression_count": 0,

    "neutral_count": 0

  },

  "artifacts": [

    {

      "kind": "roofline_comparison_md",

      "path": ".perf/roofline/task_id/comparison/report.md"

    }

  ],

  "warnings": []

}

```

---

# Differential Performance Contract

Every differential performance run must compare the same workload across both implementations.

The server must enforce:

1. same input files;

2. same environment variables unless explicitly overridden;

3. same CPU affinity unless explicitly overridden;

4. same thread settings unless explicitly overridden;

5. same correctness-validated input corpus, when available;

6. same timeout policy;

7. same measurement backend.

The server must report any deviations.

---

## Required Differential Metrics

At minimum:

```json

{

  "runtime_speedup": 1.0,

  "runtime_delta_pct": 0.0,

  "cycles_delta_pct": 0.0,

  "instructions_delta_pct": 0.0,

  "ipc_delta_pct": 0.0,

  "cache_miss_rate_delta_pct": 0.0,

  "branch_miss_rate_delta_pct": 0.0

}

```

For roofline:

```json

{

  "arithmetic_intensity_a": 0.0,

  "arithmetic_intensity_b": 0.0,

  "achieved_flops_speedup": 1.0,

  "utilization_delta": 0.0,

  "bound_a": "memory | compute | unknown",

  "bound_b": "memory | compute | unknown"

}

```

---

# Recommended Planner Flow

Performance analysis should normally happen after correctness verification.

```text

1. Correctness verification passes

2. Build release binaries

3. run_benchmark

4. collect_perf_stats

5. compare_performance

6. profile_hotspots if:

      - regression detected

      - surprising counter deltas

      - user requested explanation

7. V2:

      - collect_hardware_model

      - estimate_workload_model

      - run_roofline_analysis

      - compare_roofline

8. Final report synthesis

```

### Early Stop Rules

Stop with `ERROR` if:

```text

benchmark command fails

perf unavailable and no fallback allowed

required artifact missing

```

Stop with `UNSURE` if:

```text

variance too high

runtime too short

environment unstable

hardware counters unavailable

```

Continue to hotspot profiling if:

```text

runtime regressed

candidate unexpectedly allocates/copies

perf counters contradict runtime

roofline utilization worsens

```

---

# Artifact Layout

Recommended directory:

```text

.perf/

  benchmarks/

    <task_id>/

      hyperfine.json

      result.json

      report.md

  perf_stats/

    <task_id>/

      case_001_a.csv

      case_001_b.csv

      result.json

      report.md

  profiles/

    <task_id>/

      case_001_a.perf.data

      case_001_b.perf.data

      case_001_a.report.txt

      case_001_b.report.txt

      case_001_a.perf.script

      case_001_b.perf.script

      case_001_a.flame.svg

      case_001_b.flame.svg

      result.json

      report.md

  hardware/

    <task_id>/

      hardware_model.json

  roofline/

    <task_id>/

      workload_model/

        model.json

      roofline_report.json

      roofline_report.md

      roofline.png

      comparison/

        report.json

        report.md

  reports/

    <task_id>/

      performance_summary.json

      performance_summary.md

```

Raw logs must be preserved.

---

# Final Report Schema

The Performance MCP server or planner synthesizer should produce:

```json

{

  "task_id": "perf_2026_06_02_001",

  "status": "IMPROVEMENT | REGRESSION | NEUTRAL | UNSURE | ERROR",

  "confidence": 0.9,

  "summary": "Candidate is 1.32x faster with fewer cycles and improved IPC. Roofline utilization improved from 21% to 33%.",

  "benchmark": {

    "status": "IMPROVEMENT",

    "geomean_speedup": 1.32,

    "cases": 3

  },

  "perf_stats": {

    "status": "PASS",

    "cycles_delta_geomean_pct": -27.1,

    "instructions_delta_geomean_pct": -1.9,

    "ipc_delta_geomean_pct": 34.5,

    "cache_miss_rate_delta_geomean_pct": -6.0

  },

  "hotspots": {

    "status": "PASS",

    "summary": "No new dominant overheads detected."

  },

  "roofline": {

    "status": "IMPROVEMENT",

    "average_utilization_delta": 0.12,

    "bound_changes": []

  },

  "warnings": [],

  "artifacts": [

    ".perf/reports/perf_2026_06_02_001/performance_summary.json",

    ".perf/reports/perf_2026_06_02_001/performance_summary.md"

  ]

}

```

---

# Failure and Regression Reports

A regression report must include:

1. case ID;

2. command used;

3. runtime statistics;

4. counter deltas;

5. profile artifacts if available;

6. likely explanation if inferable;

7. reproducible commands.

Example:

```json

{

  "status": "REGRESSION",

  "summary": "Candidate is 18.4% slower on matmul_1024_float32.",

  "case_id": "matmul_1024_float32",

  "reproduce": {

    "benchmark": "hyperfine './orig --case matmul_1024' './opt --case matmul_1024'",

    "perf_stat": "perf stat -e cycles,instructions,cache-misses ./opt --case matmul_1024",

    "profile": "perf record -g ./opt --case matmul_1024"

  },

  "evidence": {

    "runtime_delta_pct": 18.4,

    "cycles_delta_pct": 21.0,

    "instructions_delta_pct": 2.1,

    "ipc_delta_pct": -15.6,

    "cache_miss_rate_delta_pct": 47.2

  },

  "hypothesis": "Regression likely caused by worse memory locality."

}

```

The `hypothesis` field is optional and should be marked as an inference.

---

# Integration with Correctness MCP

Performance MCP should consume artifacts from correctness verification when available:

```text

.verify/corpus/equivalence/

.verify/counterexamples/

.verify/harnesses/

.verify/builds/

```

Preferred flow:

```text

correctness corpus

   ↓

benchmark cases

   ↓

performance analysis

```

This ensures that the performance workload is semantically relevant.

For C ↔ Torch, benchmark harnesses from correctness tests may already expose:

```python

run_a(input_case)

run_b(input_case)

```

The Performance MCP should reuse these when possible.

---

# V1 Implementation Plan

Implement in this order.

## Step 1: `run_benchmark`

Required:

```text

hyperfine invocation

JSON parsing

speedup calculation

variance detection

report generation

```

## Step 2: `collect_perf_stats`

Required:

```text

perf stat invocation

event support detection

CSV parsing

derived metrics

differential deltas

```

## Step 3: `compare_performance`

Required:

```text

merge benchmark and perf-stat results

classify improvement/regression/neutral

generate JSON + MD report

```

## Step 4: `profile_hotspots`

Required:

```text

perf record

perf report --stdio

top-symbol extraction

optional flamegraph artifact

```

V1 is complete when the system can answer:

```text

Is candidate faster?

How much faster/slower?

Are measurements stable?

What low-level metrics changed?

Where is time spent?

```

---

# V2 Implementation Plan

Implement after V1.

## Step 1: `collect_hardware_model`

Initially allow manual configuration.

Example:

```json

{

  "peak_flops": {

    "fp32": 1000000000000

  },

  "peak_bandwidth_Bps": {

    "dram": 100000000000

  }

}

```

## Step 2: `estimate_workload_model`

Start with formula-based estimators for:

```text

matmul

elementwise

reduction

stencil-like kernels

custom manual annotations

```

## Step 3: `run_roofline_analysis`

Compute:

```text

AI

achieved FLOP/s

achieved bandwidth

attainable roof

utilization

bound classification

```

## Step 4: `compare_roofline`

Compare source A and source B.

V2 is complete when the system can answer:

```text

Is the workload memory-bound or compute-bound?

Did optimization improve hardware utilization?

Is the candidate more portable to bandwidth-rich or compute-rich accelerators?

```

---

# Accelerator Portability Hooks

The architecture must support future providers without changing the planner contract.

Future providers may implement:

```text

NsightProvider:

  NVIDIA GPU counters

  kernel occupancy

  achieved memory bandwidth

  achieved FLOP/s

ROCmProvider:

  AMD GPU counters

  rocprof integration

VTuneProvider:

  CPU roofline and memory analysis

TPUProvider:

  XLA/HLO profiling metrics

FPGAProvider:

  pipeline initiation interval

  bandwidth utilization

  resource utilization

```

All providers must map their outputs into:

```text

RuntimeMetrics

CounterMetrics

MemoryTrafficMetrics

FlopMetrics

HardwareModel

RooflineMetrics

```

---

# Non-Goals for V1/V2

Do not prioritize:

```text

automatic compiler optimization diagnostics

clang -Rpass

llvm-mca

BOLT

full cache simulation

full energy modeling

automatic peak FLOP benchmarking

automatic DRAM bandwidth benchmarking

```

These can be added later.

The immediate goal is:

```text

stable differential runtime

perf counter explanation

hotspot localization

roofline classification

accelerator-ready metric abstraction

```

---

# Hard Requirements

1. Every benchmark must be reproducible from a command in the report.

2. Raw hyperfine and perf outputs must be preserved.

3. Candidate and reference must be benchmarked under equivalent environments.

4. Performance verdicts must account for variance.

5. `perf stat` must report unavailable events instead of failing silently.

6. Roofline analysis must distinguish measured values from estimates.

7. Manual FLOP and byte annotations must be preserved in reports.

8. Hardware model assumptions must be explicit.

9. Differential performance comparison must be first-class.

10. Performance MCP must not override correctness verdicts.

---

# Notes for Coding Agent

When implementing this specification:

1. Start with a single `PerformanceMCP` server exposing all tools.

2. Keep backend wrappers small and testable.

3. Store all raw command outputs.

4. Use JSON as the stable internal exchange format.

5. Keep Markdown reports human-readable but secondary.

6. Treat missing `perf` permissions as `ERROR` with actionable diagnostics.

7. Do not require root unless absolutely necessary.

8. Prefer user-provided hardware model values for V2 initial implementation.

9. Make benchmark cases reusable across correctness and performance pipelines.

10. Keep planner policy separate from tool execution.

---

# Minimal CLI Debug Commands

The implementation should make each generated artifact runnable manually.

Benchmark:

```bash

hyperfine './orig input.bin' './opt input.bin'

```

Counters:

```bash

perf stat -r 5 \

  -e cycles,instructions,branches,branch-misses,cache-references,cache-misses \

  ./opt input.bin

```

Profile:

```bash

perf record -g ./opt input.bin

perf report

```

Roofline calculation should emit a standalone JSON file and, optionally, a script:

```bash

python .perf/roofline/<task_id>/compute_roofline.py

```

---

# Summary

V1 makes performance claims reproducible and evidence-backed:

```text

hyperfine

perf stat

perf record

differential comparison

```

V2 makes the analysis portable and scientifically meaningful:

```text

hardware model

FLOPs

bytes moved

arithmetic intensity

roofline classification

MetricProvider abstraction

```

Together, V1 and V2 provide a performance-verification layer suitable for LLM-generated C/C++ optimizations, C ↔ Torch translations, and future accelerator-oriented optimization workflows.
