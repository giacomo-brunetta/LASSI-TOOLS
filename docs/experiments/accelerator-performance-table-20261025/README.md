# Consolidated paper performance table

The generated full-width table covers 21 LARGE FP16 source-version cases across
11 applications, with 178 available metric cells. It is included from
`sections/results.tex` in the sibling `AgenticAI4HPC-2026---Giacomo` paper as
Table IX (page 10 of the current 13-page preview).

## Outputs

- `accelerator-performance.tex`: table source, displaying milliseconds.
- `accelerator-performance.csv`: unrounded seconds, case IDs, backend source
  hashes, and qualification flags.
- `provenance.json`: input SHA-256 hashes, generator hash, cohort and column counts.
- `validation.json`: source-join, units, copy, build and layout checks.
- `table-preview.pdf` / `table-page.png`: rendered page containing the table.
- `paper-preview.pdf`: full compiled paper, preserving the paper checkout's
  existing `revision-preview.pdf`.
- `paper-build.log`: Tectonic output.

## Regeneration

From the LASSI-TOOLS root:

```sh
.venv/bin/python docs/experiments/accelerator-performance-table-20261025/build_table.py \
  --paper /Users/giacomobrunetta/Projects/AgenticAI4HPC-2026---Giacomo
```

The generator reads the frozen transfer-timing, GPU-active, CS3-streaming and
CS3-native-budget CSV exports. It joins exact case IDs and checks source hashes
where records share a backend. Backend ports have different source hashes;
their common case ID preserves original workload lineage. The retired IIR
profile-only alias `14882e83f7d350a7` is excluded.

Lorenz c3 has no entry in the newer GPU-active campaign. Its GPU call and
resident medians come from the original transfer campaign, matched to the
original pre-port source hash recorded in its CS3 result. Input, source,
transfer verification and numerical qualification are checked against the
archived result. Its active-profile cell remains unavailable.

## Timing scopes

The table explicitly distinguishes measured call/resident timings (M),
profile-derived active estimates (P), compiler schedule estimates (C), and
derived CS3 wafer-native component budgets (D). These are different timing
boundaries and must not be pooled into a common measured speedup.

CS3 streaming/first-iteration columns are compiler predictions including modeled
streaming stalls, not measured host-to-host transfer timings. CS3 native columns
assume preloaded layouts and resident code; they do not establish placement
feasibility or give a newly compiled resident executable's latency. Five CS3
cases have uncosted host helpers. The IIR GPU profiling anomaly is marked.
Independent run medians and instrumentation differences can reverse expected
column ordering; subtraction does not isolate PCIe costs. Missing cells are
unavailable qualified evidence, not zero latency.

## Validation

All 178 numeric cells were checked against the source join, seven input-file
hashes were verified, seconds-to-milliseconds formatting was checked, and paper
copies match the generated artifacts. The paper compiled successfully using the
cached Tectonic binary, and the rendered table was visually checked for clipping.
No table overfull warning occurred. The build retains existing unrelated
bibliography, encoding and layout warnings, recorded in `paper-build.log`.
No new hardware jobs were submitted.
