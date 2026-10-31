# Candidate correctness suites

A candidate passes only when the primary reference workload and every configured
`arena.correctness_tests` workload pass on the current revision. Every repair
reruns all tests; passes from an earlier revision are never reused.

Existing configurations keep their primary-only behavior. To add workloads:

```yaml
arena:
  suite_timeout_s: 3600
  correctness_tests:
    - id: medium-seed-17
      dataset: medium
      timeout_s: 60
      input_contract: fixtures/medium-seed-17-inputs.npz
      oracle:
        build: [cc, reference.c, '-o', '{oracle_dir}/reference']
        run: ['{oracle_dir}/reference', '{input}', '{output}']
        input_fixture: fixtures/medium-seed-17.dat
        output: oracle.csv
        format: numeric
```

Commands are argument lists, never shell commands. Paths resolve from the project
root. The reference program must support the supplied input fixture. This example
assumes a reference executable that accepts input/output paths; adapt commands to
the kernel. A seed in a case ID is descriptive: the harness does not automatically
randomize a kernel's initialization. Prepare deterministic fixtures and matching
trusted reference commands for each seed.

Additional workloads using the historical builder interface require a harness-owned
input contract in the format described in [input-validation.md](input-validation.md),
with matching dataset metadata. Cases using `oracle.fixture_spec` obtain their
contract from executed C initialization and can omit a separate `input_contract`;
see [c-fixtures.md](c-fixtures.md). Input parity is enforced for every additional
workload. For the historical builder interface, the primary workload retains the
configured `arena.input_check` policy; enable it for new campaigns. Fixture-spec
validation supplies harness-owned inputs regardless of that legacy opt-in.
Candidate-authored inputs on the historical path are checked against the trusted
contract; passing outputs alone cannot bypass input parity. Reference output generation
also checks determinism and rejects nonfinite outputs.

Use different values as well as sizes, valid edge cases, and awkward dimensions
where the reference and candidate interface support them. More tests do not by
themselves guarantee correctness. GPU readiness and reduced-precision accuracy
remain separate evaluation gates.

Each validation attempt writes `suite.json`, listing every required test's ID,
dataset, status, reason, diagnostics, and numerical metrics when available.
Individual test directories contain reference and execution artifacts.

- `passed`: the workload completed and satisfied all checks.
- `failed`: a candidate check failed, including an execution timeout.
- `not_run`: no result exists; the reason records why execution stopped.
- `inconclusive`: reference preparation or infrastructure raised an error.

Repair feedback enumerates every test, with failure diagnostics and totals.
Numerical failures do not stop the remaining tests. Missing source, compilation
failure, two runtime failures, or exhaustion of the suite budget stop further
execution; remaining tests explicitly remain `not_run`. Each command uses the
smaller of its configured timeout and the remaining suite budget. The budget is
checked between preparation/execution steps; reference commands retain their own
oracle timeout. It is not a hard wall-clock deadline for file transfers or
reference preparation.

Reference/infrastructure exceptions save the partial report and propagate to the
caller, rather than requesting a candidate repair. No incomplete or inconclusive
suite can pass. Keep final held-out fixtures outside this feedback suite: once
exposed in repair feedback, a test is a development test. This configuration
implements the development gate, not a separate held-out promotion stage.
