# C-to-Torch model comparison: Luna and Terra at medium effort

Status: clean phase-1 results under `bounded-tool-output-v1`.

Both campaigns used the same 33-kernel MINI suite, three candidate slots,
two correction rounds, and FP64 CPU equivalence (`rtol=1e-10`, `atol=1e-12`).
Planner and candidate roles used the same model within each campaign. Luna used
`gpt-5.6-luna`; Terra used `gpt-5.6-terra`. Both used medium reasoning effort.
The C-oracle preflight passed for all 33 kernels in each campaign.

| Model | CPU-verified kernels | Kernel coverage | Passing candidates / candidates with terminal outcomes |
| --- | ---: | ---: | ---: |
| GPT-5.6 Luna | 32/33 | 97.0% | 92/94 (97.9%) |
| GPT-5.6 Terra | 33/33 | 100% | 96/98 (98.0%) |

Kernel coverage counts a kernel as successful when at least one candidate passes
the CPU equivalence gate. Candidate pass fraction is reported separately and uses
the latest candidate-evaluated attempt for each kernel; quota and connection
interruptions without candidate outcomes are excluded from its denominator. Some
kernels completed with fewer than three candidate outcomes, so these denominators
are the outcomes recorded, not the planned 99 candidate slots.

Luna's only unverified kernel was `polybench-deriche`: both evaluated candidates
were rejected by FP64 equivalence. Terra's `polybench-nussinov` and
`mutual-information` attempts were interrupted by quota or connection failures;
both later passed on clean reruns. Terra therefore finished 33/33. No accelerator
measurements or GPU numerical-correction results are included here.

## Provenance

- Dataset: MINI; 33 kernels per model.
- Source tree: the campaign ran from the worktree based on Git revision `58eba2b`;
  its implementation changes are included in the publication commit containing
  this report.
- Tool-output policy: `bounded-tool-output-v1`.
- Luna suite manifest SHA-256: `f31edf4ccd636b24c35d7810f2119d62398ba7800e9f3c27267f679c0d0dd0fa`.
- Terra suite manifest SHA-256: `a7b4e2409e3b50676d1bd80e0616de8d2636d9e8eb203e38781383ecfecbcff1`.
- Run manifests and logs are retained in the originating workspace under `runs/`;
  that raw corpus is ignored by Git.
