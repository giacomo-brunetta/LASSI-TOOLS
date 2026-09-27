# CPU-verification ablation suite

The default campaign covers **24 of the 30 PolyBench/C 4.2.1 kernels plus five
scientific kernels**. It stops at local FP64 CPU verification and publishes an
immutable CPU baseline for each successful run. No accelerator endpoint is needed.

| Coverage | Core kernels |
| --- | --- |
| Statistics | correlation, covariance |
| BLAS | gemm, gemver, gesummv, syr2k, trmm |
| Contractions / matrix-vector | 3mm, atax, bicg, doitgen, mvt |
| Factorizations / recurrences | cholesky, durbin, gramschmidt, lu |
| Filters / dynamic programming | deriche, floyd-warshall, nussinov |
| Stencils / PDEs | adi, fdtd-2d, heat-3d, jacobi-2d, seidel-2d |
| Scientific additions | direct-dft, softened-nbody, lorenz-rk4, poisson-cg, mutual-information |

`--full-polybench` adds 2mm, symm, syrk, ludcmp, trisolv and jacobi-1d for a
35-kernel campaign. The core prioritizes distinct computational patterns over
near-duplicate BLAS operations. It retains dependency-heavy kernels that may
be difficult to accelerate: correctness or compilation failures are useful results.

The scientific additions exercise transcendental reductions, all-pairs forces,
batched nonlinear ODE integration, fixed-iteration sparse conjugate gradient and
information-theoretic reductions. The four standalone C fixtures are deliberately
small, deterministic validation problems, not established benchmark-suite results.
Mutual information uses the existing scientific reference in this repository.

## Prepare and check

Run from the repository root with its environment active. By default, the script
expects `../PolyBenchC-4.2.1`; use `--polybench /path/to/PolyBenchC-4.2.1` otherwise.
It uses the source tree you supply, including local modifications; hashes establish
identity, not certification that the tree is pristine upstream PolyBench.

To isolate candidate execution, build the [CPU Docker image](../../docker/cpu/README.md)
and add `--execution docker` when preparing a new campaign. The default remains
local unsandboxed execution; C-only oracle checks always execute on the host.

```sh
python examples/cpu-ablation-suite/suite.py prepare \
  --models-config examples/polybench-jacobi-2d/run-luna-a100.yaml \
  --output runs/cpu-suite-mini-luna

python examples/cpu-ablation-suite/suite.py run \
  runs/cpu-suite-mini-luna/suite.json --check-oracles
```

The models argument accepts an existing run YAML (only `models` is copied), or a
YAML with `planner`, `candidates` and `compensation` at its root. Remote settings,
memory, compensation and accelerator repair are not copied. The default is three
candidates and two CPU correction rounds; the model list must have exactly three
entries. Set `--candidates N` and provide N model entries to change that budget.
Credential/provider configuration is inherited; preparation does not validate
credentials or contact model services. The example reuses existing Luna settings;
it is not a model recommendation.

Preparation refuses existing output directories. It records source, context and
config hashes in `suite.json`; execution rejects changed campaign inputs. The C
oracles use `-O0`, disabled FP contraction, the selected dataset, two determinism
runs and the production output parser. Floating dumps use 17 significant digits;
integer dumps retain `%d`. Computation and initialization are not rewritten.

## Launch CPU verification

```sh
# Preview commands only (default).
python examples/cpu-ablation-suite/suite.py run runs/cpu-suite-mini-luna/suite.json

# Explicit model execution; sequential benchmarks, normal pipeline concurrency within each.
python examples/cpu-ablation-suite/suite.py run \
  runs/cpu-suite-mini-luna/suite.json --execute

# Pilot subset before the complete campaign.
python examples/cpu-ablation-suite/suite.py run \
  runs/cpu-suite-mini-luna/suite.json --execute \
  --only polybench-3mm polybench-correlation polybench-jacobi-2d \
         polybench-cholesky direct-dft poisson-cg

# CSV to stdout, including failures and all attempts (not just the best run).
python examples/cpu-ablation-suite/suite.py summary runs/cpu-suite-mini-luna/suite.json
```

A core run requests 87 candidates, plus 29 planner calls and up to two correction
rounds per candidate. This can consume substantial time and model quota. Execution
continues after an individual benchmark fails and returns nonzero if any failed.
Repeating `--execute` creates fresh attempts; it does not silently resume or skip
previous runs. Resume a specific interrupted run explicitly:

```sh
lassi-x run runs/cpu-suite-mini-luna/configs/polybench-3mm.yaml \
  --resume runs/cpu-suite-mini-luna/runs/polybench-3mm/<run-id> --until cpu-verified
```

## Comparison protocol

Start with MINI, a common FP64 gate (`rtol=1e-10`, `atol=1e-12`), three candidate
slots and two correction rounds. Integer kernels should be checked for exact
integer semantics. Keep every failure; do not relax thresholds for one model.
Report candidate pass fraction and benchmark coverage separately: a run is
successful if **any** candidate passes, not necessarily all three.

For a candidate-model ablation, hold the planner model/settings constant and put
the model under test in all three candidate slots. Make one campaign directory
per model and replicate, with identical sources, dataset and budgets. The planner
may still vary its strategies between runs; this workflow does not yet freeze
planner strategies or guarantee deterministic model sampling. If the planner also
changes, describe the comparison as an end-to-end model-stack ablation. Memory is
disabled to avoid deliberate cross-run memory carryover.

After the pilot, repeat with `--dataset small` in a new directory to expose more
reduction and recurrence stress; optionally use MEDIUM. These are **different
CPU baselines**, not larger accelerator inputs interchangeable with MINI. A
small correctness fixture alone says little about accelerator throughput.
The four standalone fixtures use sizes 32/64/128 and ODE step counts 20/50/100;
CG always performs ten iterations. PolyBench and mutual-information sizes come
from their original headers.

## Frozen accelerator follow-up

Each run with passing candidates exports `<run>/cpu-baseline`. Copy that benchmark's
generated config, change only accelerator/execution/measurement settings, and use:

```sh
lassi-x run accelerator-a.yaml --from-cpu-baseline <cpu-run>
lassi-x run accelerator-b.yaml --from-cpu-baseline <cpu-run>
```

Keep `kernel`, `oracle`, CPU equivalence, referenced files and the dataset unchanged;
the importer checks their contract. In particular, retain the generated precision
header and campaign directory. Imported runs skip generation and default to frozen
candidates (no compensation or model repair). Each receives independent copies of
the same passing modules and oracle. For cross-model accelerator comparisons, use
the **same chosen CPU run** for every accelerator, not each model's own candidates.
Selection of that baseline should be recorded explicitly to avoid selection bias.
