# Phase 6 Multi-Size Baseline vs Optimized Comparison

## Scope
- Project: `/home/gbrun/LJ-v3`
- Branches compared:
  - Baseline: `agent/lassi-optimization-init`
  - Optimized: `agent/opt/stabilize-ljcut-deterministic`
- Dataset set (all available artifacts):
  - `lammps_ljcut_32.txt`
  - `lammps_ljcut_500.txt`
  - `lammps_ljcut_4000.txt`
  - `lammps_ljcut_32K.bin`

## Reproducible Methodology (apples-to-apples)
1. Same profiling tool class as prior reports: MCP `execute_with_profile`.
2. Fixed run count per branch per dataset: 3 runs.
3. Same executable class: `harness.exe` built from each branch with `make clean && make`.
4. Invocation semantics held constant across baseline/optimized for each dataset: no CLI args, dataset selected by replacing `/home/gbrun/lj-refactor/lammps_ljcut_32K.bin` with the target dataset payload before each paired run set.
5. Parity gate per dataset: accept metrics only if baseline and optimized show identical input provenance pattern (same resolved path + same parsed header tuple family + same terminal failure class).

## Dataset Results (means over 3 runs)

| Dataset | Baseline Lat (s) | Opt Lat (s) | Δ Lat % | Baseline CPU E (J) | Opt CPU E (J) | Δ CPU E % | Baseline GPU E (J) | Opt GPU E (J) | Δ GPU E % | Baseline CPU P (W) | Opt CPU P (W) | Δ CPU P % | Baseline GPU P (W) | Opt GPU P (W) | Δ GPU P % | Validity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| lammps_ljcut_32.txt | 0.047588293 | 0.020636978 | -56.63% | 2.716135184 | 2.714371898 | -0.06% | 2.516237836 | 2.657440725 | +5.61% | 34.232333 | 33.946667 | -0.83% | 29.316141 | 29.296152 | -0.07% | PASS (same resolved input path, same parsed header tuple, same terminal error: E_NEIGHBOR_COUNT_MISMATCH) |
| lammps_ljcut_500.txt | 0.083565315 | 0.116395109 | +39.29% | 3.527877051 | 6.497753432 | +84.18% | 3.182188844 | 5.776830603 | +81.54% | 33.561333 | 34.379833 | +2.44% | 29.242503 | 29.260917 | +0.06% | PASS (same resolved input path, same parsed header tuple incl. nlocal=32000, same terminal error: output snapshot open failure) |
| lammps_ljcut_4000.txt | 0.125439391 | 0.114144284 | -9.00% | 5.975343356 | 5.457285647 | -8.67% | 5.687999545 | 4.611350529 | -18.93% | 34.071333 | 34.542333 | +1.38% | 29.238217 | 29.273191 | +0.12% | PASS (same resolved input path, same parsed header tuple, same terminal error: E_NEIGHBOR_COUNT_MISMATCH) |
| lammps_ljcut_32K.bin | 0.658512866 | 0.661044983 | +0.38% | 23.532222371 | 23.722964374 | +0.81% | 19.971235105 | 20.484798624 | +2.57% | 34.519667 | 34.036115 | -1.40% | 29.282734 | 29.274001 | -0.03% | PASS (same resolved input path, same parsed header tuple, same terminal error: E_NEIGHBOR_COUNT_MISMATCH) |

## Per-dataset decision validity notes
- `lammps_ljcut_32.txt`: PASS (same resolved input path, same parsed header tuple, same terminal error: E_NEIGHBOR_COUNT_MISMATCH)
- `lammps_ljcut_500.txt`: PASS (same resolved input path, same parsed header tuple incl. nlocal=32000, same terminal error: output snapshot open failure)
- `lammps_ljcut_4000.txt`: PASS (same resolved input path, same parsed header tuple, same terminal error: E_NEIGHBOR_COUNT_MISMATCH)
- `lammps_ljcut_32K.bin`: PASS (same resolved input path, same parsed header tuple, same terminal error: E_NEIGHBOR_COUNT_MISMATCH)

## Overall trend summary
- Latency improved on 2/4 datasets: lammps_ljcut_32.txt, lammps_ljcut_4000.txt.
- CPU energy improved on 2/4 datasets: lammps_ljcut_32.txt, lammps_ljcut_4000.txt.
- GPU energy improved on 1/4 datasets: lammps_ljcut_4000.txt.
- No dataset was skipped for runtime incompatibility; all 4 executed under the same harness semantics.
