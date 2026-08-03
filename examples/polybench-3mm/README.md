# PolyBench 3mm reproduction

This reproduces the earlier LASSI-TOOLS three-candidate arena experiment using
the LASSI-X pipeline. It uses the unchanged PolyBench/C 4.2.1 source in the
sibling `PolyBenchC-4.2.1` checkout and executes that C program in FP64 as the
authoritative oracle.

The reproduction is deliberately the original MINI case:

- dimensions: `NI=16`, `NJ=18`, `NK=20`, `NL=22`, `NM=24`;
- exactly three independently modeled candidates;
- at most two correction turns for each candidate;
- FP64, FP32, FP16, and BF16 CPU and CUDA measurements;
- low-precision compensation followed by Pareto selection.

PolyBench/C normally serializes doubles with only two decimal places. The
`oracle_precision.h` forced include mirrors the original MINI/FP64 header and
changes only that output format to 17 significant digits. The executed
algorithm and initialization remain the original `3mm.c`; this prevents text
rounding from dominating the measured FP16/BF16 error.

Install and verify the Hermes skills, then run:

```bash
cd /home/gbrun/LASSI-X
pip install -e '.[dev]'
lassi-x skills install
lassi-x skills doctor
lassi-x run examples/polybench-3mm/run.yaml
```

The example reuses `~/.claude/settings.json`: Hermes executes its
`apiKeyHelper` and sends the resulting credential only to Argo's
OpenAI-compatible endpoint. No credential is stored in this repository.

The checked-in `golden_candidate.py` is not supplied to the arena agents. It is
an independent regression fixture for validating the C oracle and measurement
path without spending model tokens:

```bash
lassi-x validate candidate \
  --config examples/polybench-3mm/run.yaml \
  --module examples/polybench-3mm/golden_candidate.py \
  --artifact-dir .reproduction/3mm-validation

lassi-x benchmark run \
  --config examples/polybench-3mm/run.yaml \
  --module examples/polybench-3mm/golden_candidate.py \
  --backend cpu --precision fp64
```
