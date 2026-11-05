# Deterministic Stage 2 repair replay, schema 1

`lassi_x.stage2_deterministic.run` is an opt-in Stage 2 step for a trusted Torch FX
graph. It replaces model planning/coding with an explicit frozen proposal list.
It does not change the existing `lassi-x run` compensation worker or the model-led
`ReplanningRun` API. Campaign adapters can call this step directly and report its
validation results. Target performance and Stage 3 remain downstream.

## Frozen preparation

1. Freeze source, workload/reference contract, validation thresholds and environment.
   Include model state and opaque helper implementations, input-generation rules,
   exact precision policy, validator implementation and executor deadlines. Graph
   text alone cannot identify these. The caller owns source-to-graph provenance.
2. Capture a trusted model with FX. For stateless scan helpers use
   `herbie_fx.capture_with_leaf_methods(model, ("_scan",))`. Capture executes Python;
   the replay API takes the already captured graph. Do not silently specialize
   dtype or shape. Record any specialization as a new source/workload contract.
3. Discover regions at the declared precision. Supply justified boundary domains
   explicitly. No automatic sampling, domain estimation or inference is performed.
4. Run bounded, seeded Herbie search using the existing `prepare`/`optimize` tools
   as a separate preparation action. Freeze successful FPCore results verbatim.
   Tool versions, platform and search provenance belong in the environment record.
   A fixed seed plus a time budget does not guarantee identical search outcomes.
5. Construct an immutable `Plan` with SHA256 identities and ordered `Proposal`
   records. `kind="herbie"` carries root, FPCore and boundary domain tuples;
   `kind="matmul_fp32"` carries an explicit matmul root. Each proposal is applied
   independently to the baseline. Combinations require an explicitly prepared
   subsequent plan; this version does not automatically compose proposals.

## Execution and gates

Call `run(graph, plan, source=source_text, contract=contract_bytes,
environment=environment_bytes, output=new_directory, validate=validator)`.

The step verifies the frozen identities and implementation hash before creating
artifacts. It refuses existing output directories. It records the baseline, then
applies every proposal in fixed order, up to the plan maximum. No LLM calls,
Herbie searches, random choices, retry loops or adaptive proposal selection occur.
FPCore domains must exactly match the declared bounds. Crash-marked Herbie outputs
are rejected. Unsupported proposals and validator exceptions are retained as
incomplete records and never accepted.

The required validator receives a copy of the graph, declared precision, and
proposal ID. It returns `Validation`: FP64, FP32, target-precision numerical and
precision-audit gates, finite nonnegative error, and an evidence SHA256. The caller
must implement these checks against the frozen original reference/input contract;
the step cannot manufacture C oracle or hardware precision evidence. The validator
executor must enforce its declared finite time/resource budgets. `target_pass`
means requested numerical precision, not Stage 3 hardware/performance qualification.

Baseline FP64 must pass; low-precision recovery also requires baseline FP32.
Every accepted revision must pass all four validator gates and strictly improve
the baseline's error metric. The selected candidate has the lowest accepted error;
exact ties retain the earliest plan entry. Return value is the selected GraphModule
or None. No passing proposal means no repaired model is returned. FP32 repair
precedes low-precision recovery through separate explicit plans.

## Artifacts and determinism boundary

The output contains source, baseline graph code, exact contract/environment bytes,
plan, proposal graph code and atomically updated result.json. Every proposal status
is retained. A completed step can have no accepted repair. Graph text is diagnostic,
not a standalone serialized model: reconstruct using the frozen source, capture
contract and replay plan, or retain the returned graph for downstream execution.
Caller-owned evidence files must be retained at their recorded hashes.

The step's ordering, transformations, gates and selection are deterministic given
the same graph, plan and validation results. Bitwise reproducibility of Torch
kernels or validator results requires deterministic execution settings and a fixed
runtime/hardware environment. This API does not claim to enforce those settings or
sandbox callbacks. A schema-1 plan freezes the behavior; do not reinterpret a
historical plan under changed adapter code.

Development tests cover byte-identical replay reports, a supplied cancellation
repair, changed-source rejection, missing-domain rejection, nonfinite metrics and
baseline blocking. These are implementation tests, not scientific repair results.

## Repository command

The standardized step is exposed through the installed repository CLI:

```sh
uv run --locked lassi-x stage2 replay replay.json runs/my-stage2-replay
```

`replay.json` has exactly these fields (paths resolve relative to this file):

```json
{
  "schema": 1,
  "source": "candidate.py",
  "plan": "plan.json",
  "contract": "contract.json",
  "environment": "environment.json",
  "driver": "driver.py",
  "driver_sha256": "<SHA256 of the exact driver bytes>"
}
```

Serialize the immutable Plan with `json.dumps(dataclasses.asdict(plan))`; this
includes the required `implementation_sha256`. The CLI strictly parses the plan,
rejects unknown fields, checks source/contract/environment/driver hashes and the
adapter identity before executing driver code. The CLI never searches for a driver.
The explicitly selected driver is trusted Python, with two required functions:

- `build_graph(source: str, contract: bytes) -> torch.fx.GraphModule` captures the
  declared source using the frozen contract, including leaf helpers where needed.
- `validate(graph, precision, proposal_id) -> Validation` implements the bounded
  reference suite and precision audit specified above. Dependencies and validator
  settings must be included in the frozen environment/contract.

Exit 0 means a repair was selected; exit 1 means none was selected. Inspect
result.json to distinguish rejected proposals, incomplete checks and blocked
baselines. Input/configuration errors raise before replay. Output directories
cannot be reused. The output also retains driver.py and invocation.json.

Use this command inside an explicitly planned campaign for runner-enforced task
budgets. A campaign stage adapter must translate result.json into its declared
verdict; a successful command is not a hardware qualification. The existing
model-led `lassi-x run` remains separately selectable; this integration does not
silently change existing run configurations.
