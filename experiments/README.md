# Experiments

Start with the [experiment driver guide](../docs/experiment-driver-guide.md) and
[plan and handoff template](../docs/experiment-plan-template.md). They explain which
workflow to use and what evidence to preserve before launching or resuming work.

New campaigns should use the [frozen campaign workflow](../docs/campaigns.md)
and `lassi-x campaign`. The scripts listed below are retained historical workflows;
their campaign-specific selection and resume rules have not been migrated to the
shared runner. Do not use their directory discovery as a template for new campaigns.

Campaign orchestration and run configurations live here; reference sources live
in [benchmarks](../benchmarks/README.md). These files were moved from `examples/`;
the move does not establish a new experimental protocol or validate old results.

| Location | Purpose |
| --- | --- |
| `cpu-generation/` | Prepare and run CPU translation campaigns |
| `gpu-evaluation/` | Evaluate saved GPU candidates and measure transfers |
| `repair-campaigns/` | Run and resume numerical and compatibility repair campaigns |
| `precision-audits/` | Inspect precision use and quarantine invalid promotion cells |
| `holdout-validation/` | Prepare, execute, inspect and report independent holdout checks |
| `reporting/` | Plot campaign summaries |
| `cpu-generation/models/` | Luna, Sol and Terra profiles still used by campaign tools |
| `run.yaml` | General run configuration template |
| `run-remote-node.yaml.example` | Remote node configuration template |

Prepare a campaign from the repository root without making model calls:

```sh
python experiments/cpu-generation/suite.py prepare \
  --models-config experiments/cpu-generation/models/luna.yaml \
  --output runs/cpu-suite-mini-luna
python experiments/cpu-generation/suite.py run runs/cpu-suite-mini-luna/suite.json
```

The suite uses `benchmarks/polybench` by default. `--polybench` selects an
alternative checkout. Preparation records source hashes and refuses an existing
output directory. Execution requires `--execute`; see the
[suite instructions](cpu-generation/README.md) for budgets and methodology.

Campaign-specific tools retain model and device names when those choices are
hard-coded. `run_gpu_repair_comparison.py` and `prepare_large_restart_inventory.py`
replace the former `run_clean_gpu_repairs.py` and `prepare_clean_large_restart.py`.
Run scripts from the repository root. Shared model configurations remain in
`cpu-generation/models/`.
Historical evidence in `docs/experiments/` and external archives retains its
original recorded paths; those paths describe the old repository layout.
Globus endpoint templates now live in [docker/globus-endpoint](../docker/globus-endpoint/).
