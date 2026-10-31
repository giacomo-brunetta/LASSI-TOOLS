# Working in LASSI-TOOLS

For experiment planning, execution, recovery, and reporting, start with
[the experiment driver guide](docs/experiment-driver-guide.md). Use
[the experiment plan template](docs/experiment-plan-template.md) to record the
cohort, budgets, gates, and artifact destinations before running a sweep.

## Repository conventions

- `lassi_x/` contains the framework; `benchmarks/` contains reference programs.
  `experiments/` contains configurations and historical launchers.
- Use `lassi-x campaign` for new explicitly planned campaigns. Its scientific stage
  adapters are not all implemented, and its task runner is sequential. Use
  `lassi-x run` for the integrated single-kernel pipeline. Read the guide's capability
  table before choosing or extending either workflow.
- Preserve historical evidence under `docs/experiments/` and external archives.
  Untracked historical artifacts are not new source files to stage or commit.
- Identify inputs by explicit paths and hashes. Do not select experimental cohorts
  by scanning for the latest directory or selecting whichever cases passed.
- A source change, workload change, precision change, or target change needs its own
  validation evidence. Keep development feedback separate from final holdouts.
- Keep model credentials in their configured external sources. Record credential
  variable names and endpoint identity, never credential values in artifacts.
- Work within the user's experiment scope and finite budgets. Separate preparation
  from commands that actually contact models or consume accelerator resources.

For code changes, follow [development checks](docs/development.md) and run
`python tools/check_quality.py` in the locked environment. If pushing changes,
verify GitHub Actions for the exact pushed commit. Local checks do not establish
remote hardware correctness or a green CI result.
