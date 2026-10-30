# Torch work estimates and roofline plots

`lassi_x.roofline` converts a candidate's `make_model()` / `build_inputs()` interface
into forward FLOPs, tensor read/write volumes, storage footprints, and an ATen
operator breakdown. It runs locally without CUDA, GroqWare, Poplar, or Cerebras SDKs.
`lassi_x.roofline_ncu` supplies an A100 counter capture and CSV importer when actual
HBM traffic is available. No command here submits remote jobs or calls an agent.

## Quick start

Use the project's Python environment. Only figure export needs the optional
`roofline` extra (`matplotlib>=3.9`); counting uses the existing Torch dependency.

```sh
.venv/bin/python -m lassi_x.roofline analyze \
  --module benchmarks/polybench-3mm/reference_mini.py \
  --precision fp16 --setup fake --output /tmp/3mm-cost.json

.venv/bin/python -m lassi_x.roofline batch \
  --manifest docs/experiments/roofline-tooling-20261024/example-manifest.json \
  --output /tmp/roofline-example

.venv/bin/python -m lassi_x.roofline plot \
  --points /tmp/roofline-example/points.json --output /tmp/a100-bicg-roofline
```

The last command produces PDF, SVG, PNG, and a JSON mapping of numeric point labels
to manifest IDs. The [checked-in example](experiments/roofline-tooling-20261024/figures/a100-bicg-example.pdf)
uses an existing LARGE A100 BICG timing, not a synthetic runtime.

For a model and inputs already constructed in Python:

```python
from lassi_x.roofline import analyze

report = analyze(model.eval(), inputs, execution="fake")  # inputs is a positional tuple
print(report["totals"], report["unsupported_operators"])
```

The [coverage manifest](experiments/roofline-tooling-20261024/coverage-manifest.json)
contains 31 source models from the Groq SOL porting plan, spanning 14 applications.
All 31 completed with covered operators; see [costs.csv](experiments/roofline-tooling-20261024/coverage/costs.csv)
and the individual cost reports. This checks the analyzer on real scientific
models; it does not certify those models' accuracy, precision, or destination ports.

## What the counts mean

For one inference forward, the report contains:

| Field | Meaning |
| --- | --- |
| `arithmetic_flops` | Scalar floating add/subtract/multiply/divide and supported reduction/matrix arithmetic. Dense matrix multiply uses `2*M*N*K`; FMA counts as two. |
| `special_function_ops` | `sqrt`, `exp`, `sin`, general `pow`, etc., each counted as one conventional operation. Kept separately because execution cost is not one FMA. |
| `flops` | Arithmetic FLOPs plus special-function operations. Comparisons, integer arithmetic, casts, and movement contribute zero. |
| `tensor_read_bytes` | Sum of input operand tensor volumes for each materializing ATen call. Each operand occurrence counts, including repeated operands. |
| `tensor_write_bytes` | Sum of output tensor volumes for each materializing call, including in-place writes. |
| `tensor_bytes` | Sum of tensor read and write volumes. |
| `input_state_storage_bytes` | Unique backing storages of supplied inputs, parameters, and buffers. |
| `output_storage_bytes` | Unique output backing storages. |
| `boundary_storage_bytes` | Input/state plus output storage, deduplicated separately on each side. A view includes its backing storage, even unused regions. This is a footprint, not an I/O count or lower bound. |

Views, transposes, slices, expansion, and uninitialized allocation have zero
materialization traffic. A transpose used by matmul is charged at the consuming
operation. Copies read their source and write their destination; fills write only.
Factory templates such as `zeros_like` supply metadata and are not read as data.
Broadcast arithmetic uses the output shape for FLOPs and each operand's logical
tensor size for bytes. Index/gather/scatter operations currently charge whole
operand/output tensor volumes, not selected addresses. Factory value generation
is treated as data initialization, not floating arithmetic; `linspace`/`logspace`
are deliberately unsupported pending explicit rules.

**Tensor bytes are a portable software traffic model, not HBM/SRAM transactions.**
Compiler fusion can remove intermediates; caches can retain inputs; matrix tiles
can reload operands; placement, spills, and exchange can add traffic. Consequently,
these counts are neither a universal upper nor lower bound on hardware traffic.
For example, BICG's two matvecs charge its matrix twice even if it remains in cache.

For a timing `t`, the plotting coordinates are `x = FLOPs / bytes` and
`y = FLOPs / t`. The hardware reference is `min(peak_FLOP/s, bandwidth*x)`.
Estimated traffic panels explicitly identify their software byte model; being
above that reference does not imply a hardware violation. Use memory-tier counters
for an empirical HBM/SRAM roofline. Even with measured bytes, the FLOP numerator
here describes the Torch algorithm, not issued device instructions: a compiler
may fold constants, fuse, pad, or change the algorithm's executed work.

Parameters and buffers retain their actual dtypes, matching the benchmark worker;
the requested precision is passed to `build_inputs`, not forced over model state.
`flops_by_dtype_signature` and per-operator dtypes expose mixed tensor arithmetic.
They cannot establish hidden accumulator precision or whether Tensor Cores ran.
For mixed precision or SFU-heavy work, a single FP16 FMA peak is only a reference.

## Large models and coverage failures

The default `--execution fake` uses PyTorch FakeTensor metadata instead of numerical
kernels. Fixed Python loops still execute and are counted iteration by iteration,
so recurrences and stencils need no manually unrolled FX graph. Python execution
cost remains proportional to the number of ATen calls. Use `--max-ops` to cap it.

Input/model construction is excluded from counts. By default setup is real, so
fixture readers and builders inspecting values work. `--setup fake` also avoids
numerical work during setup, useful for large deterministic builders; reading a
NumPy fixture still performs host file I/O. Fake execution does not supply values
for `.item()`, tensor-valued branches, boolean indexing with dynamic output size,
or value-dependent loop termination. Those fail with a diagnostic. `--execution real`
follows the observed path when practical; unsupported scalar extraction or Python
arithmetic is still reported, not silently assumed to have zero cost. Real mode
may mutate supplied inputs/state and run an expensive workload.

`complete=true` means all dispatched operators have a rule under the documented
conventions. Unsupported operators, including complex arithmetic and unmodeled
factorizations, remain explicit and prevent timing-point generation. To extend
coverage, add a shape-based formula to `_work` and test it against a closed-form
count. Do not classify an unknown floating operator as movement just to clear a
failure. Higher-level `einsum`/`matmul` operations often dispatch into covered ATen
matrix operations. Torch's convolution formulas are reused, with bias additions
included; the report records the Torch version because decomposition can change.

## Timing manifests and provenance

Manifest paths resolve relative to the manifest file. Entries need `id`, `module`,
`source_sha256`, `precision`, and `dataset`; optional fields include `fixture`,
`setup`, `execution`, `seed`, and `max_ops`. Without a timing block, batch produces
costs only. Each model runs in a subprocess with a `--timeout` (default 180 s).
Errors are recorded per entry; partial batches exit nonzero and preserve good
reports. `costs.csv` includes completed analyses and `points.csv` includes only
complete analyses with successfully bound timings.

For plotted entries, add `hardware`, `eligibility_note`, and `timing` as in the
[example manifest](experiments/roofline-tooling-20261024/example-manifest.json).
The timing block requires an evidence path and SHA256, a JSON pointer to latency
in seconds, and `scope: "device_forward"`. Optional `identity_pointers` check
source hash, dataset, and precision inside the evidence as well. A source/dataset/
precision mismatch, changed evidence, incomplete cost, nonpositive duration, or
incompatible hardware precision is rejected. The output hashes adjacent NPZ/NPY/
JSON assets and any explicit fixture; transitive Python dependencies are not hashed.

Manifest selection is the researcher's eligibility decision. A raw `status=ok`
does not supersede current source/input/semantic holds. Use the decisions linked
from [RESULTS-HANDOFF.md](experiments/RESULTS-HANDOFF.md), and count destination
models separately when a port changes the implementation. A source hash from
an A100 model cannot be attached to a different Groq/Graphcore source's timing.
Do not reuse MINI counts for LARGE latencies. Use a consistent unprofiled timing
protocol; exclude compilation, input construction, and host/device transfers.

## A100: measure HBM bytes

On the A100 host, with the same source, fixture, precision, dataset, and seed as
the latency run, collect exactly one warmed CUDA graph replay:

```sh
ncu --profile-from-start off --replay-mode application \
  --app-replay-mode strict --cache-control none --clock-control none \
  --graph-profiling node \
  --metrics dram__bytes_read.sum,dram__bytes_write.sum \
  --csv --page raw --print-units base --print-metric-name name \
  --log-file /tmp/bicg-ncu.csv \
  python -m lassi_x.roofline_ncu capture \
    --module /path/to/candidate.py --dataset large --precision fp16 \
    --output /tmp/bicg-capture.json

python -m lassi_x.roofline_ncu import \
  --csv /tmp/bicg-ncu.csv --capture /tmp/bicg-capture.json \
  --output /tmp/bicg-traffic.json
```

Add `--fixture /path/to/c-inputs.npz` to capture when the builder requires it.
The capture excludes setup, warmup, and graph creation using CUDA profiler start/
stop calls. The importer sums both counters over the captured graph's kernel
nodes. It rejects duplicate metrics, missing read/write counters, multiple devices,
nonfinite values, and unknown units. CSV values use decimal SI units. The CUDA
capture itself requires A100 and was not executed on the local macOS host; CSV
parsing is tested locally with format fixtures.

Set `byte_basis: "measured"` on the manifest entry and add:

```json
"traffic": {
  "path": "bicg-traffic.json",
  "sha256": "<SHA256 of that file>",
  "bytes_pointer": "/bytes",
  "memory_tier": "HBM2"
}
```

Traffic evidence must contain matching `source_sha256`, `dataset`, `precision`,
and `scope: "device_forward"`. The memory tier must match the profile bandwidth.
Other accelerator tools can produce the same JSON contract with an appropriate
SRAM byte count. This importer does not extract Groq/Graphcore/Cerebras counters.
Nsight replay and cache policies can change observed traffic; record those settings
and use an independently measured unprofiled latency. Very small warm workloads
can have near-zero HBM traffic and need an L2 roofline instead. Do not replace
zero counters with an invented positive byte count.

The collection recipe follows NVIDIA's [CLI documentation](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html)
and [profiling guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html).
Consult the installed version and available metrics on the device.

## Hardware references

[roofline-hardware.json](../lassi_x/resources/roofline-hardware.json) stores decimal
units, device scope, memory tier, peak convention, and source URLs. It follows the
paper's hardware inventory in `AgenticAI4HPC-2026---Giacomo/sections/experimental-setup.tex`.

| Profile | Compute reference | Memory bandwidth |
| --- | --- | --- |
| A100 PCIe 40 GB | 312 TFLOP/s dense FP16 Tensor Core; 78 TFLOP/s non-Tensor Core reference | 1.555 TB/s HBM2 |
| GroqChip at 900 MHz | 188 TFLOP/s FP16 | 80 TB/s on-chip SRAM |
| One Graphcore Bow IPU | 350 TFLOP/s FP16.16 | 65.25 TB/s on-chip SRAM |
| One Cerebras WSE-3 | Dense FP16 ceiling pending; bandwidth line only | 21 PB/s on-chip SRAM |

A100 values come from the [PCIe brief](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/A100-PCIE-Prduct-Brief.pdf)
and [Ampere architecture description](https://developer.nvidia.com/blog/nvidia-ampere-architecture-in-depth/).
Groq compute comes from [ALCF](https://docs.alcf.anl.gov/ai-testbed/groq/) and bandwidth
from its [chip brief](https://groq.com/wp-content/uploads/2024/08/GroqChip%E2%84%A2-Processor-Product-Brief-v1.7.pdf).
Graphcore's [glossary](https://docs.graphcore.ai/projects/graphcore-glossary/en/latest/)
specifies the compute mode; its [Bow-2000 datasheet](https://docs.graphcore.ai/projects/bow-2000-datasheet/en/latest/product-description.html)
specifies 261 TB/s across four IPUs, divided here by four. Cerebras bandwidth is
also given in its [company filing](https://investors.cerebras.ai/static-files/ee277690-ec46-4a23-8439-53f0816bf7d5).
The paper's vendor CS-3 datasheet labels the 125 PFLOP/s number sparse. The tooling
keeps that field separate and does not guess a dense ceiling by dividing it by two.

Each profile is one device. Verify active chip count, clock, accumulator mode,
replication, and wafer allocation before selecting it. SRAM bandwidth is not an
exchange/fabric or host transfer bandwidth. Provide a manifest-level `hardware`
JSON path to use measured sustained ceilings or additional memory tiers. Keep
the same `devices` mapping structure; each entry needs `precision`, `label`,
`memory_tier`, `bandwidth_bytes_s`, and `peak_flops_s` (nullable).
