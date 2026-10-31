# Development checks

Run the same command used by GitHub Actions before pushing:

```sh
uv sync --locked --extra dev --extra globus --extra roofline
uv run --locked --extra dev --extra globus --extra roofline python tools/check_quality.py
```

Use Python 3.12 and uv 0.11.7 to match CI. The committed lockfile fixes the
dependency and development-tool versions. The roofline extra is required for
repository-wide type checking of its plotting module; an existing local
matplotlib installation previously concealed this missing CI dependency.

The command runs all four checks and exits unsuccessfully if any fails:

- Ruff lint across every versioned Python file and new Python source.
- Ruff formatting across the same files.
- Strict mypy using the complete repository configuration, including tests.
- Plain pytest, including its normal hardware/service availability skips.

Passing pytest or checking only modified files is not sufficient.
Individual checks can be selected with `lint`, `format`, `types`, or `tests`.

Untracked historical artifacts under `docs/experiments/` are not source inputs
to lint/format. Versioned Python scripts there remain checked. New files elsewhere
are included before staging; deleted files are omitted.

CI runs on Ubuntu 24.04. Local macOS results do not establish Linux compatibility.
For changes to dependencies, packaging, paths, or platform behavior, also run the
checks in a clean checkout and verify the GitHub Actions result after pushing.

## Reliability boundaries

Hermes sessions drain stderr continuously into a bounded diagnostic buffer. Each
turn attempt bounds initialization, request writing, and response reading together;
standalone initialization is bounded too. Shutdown drains stdout and escalates from
a graceful close to process-group termination. Execution cancellation kills and
reaps its command group before propagating cancellation.

Execution contexts use temporary Hermes homes by default, and each Hermes worker
receives its own temporary profile with an explicit `HERMES_HOME`. Workspace MCP
registrations are copied from that run's configuration. Credentials are resolved
from the environment or the selected/default Hermes home; credential files are
copied only into temporary worker profiles, never into run artifacts. Bundled
skills are installed into each profile and their source hashes are recorded in
run provenance. An explicit Hermes-home override should be unique to its run.

Academy transport retries exclude action requests: a lost acknowledgement cannot
prove that the remote command did not execute. Callers must reconcile ambiguous
submissions before issuing work again. File actions use Academy's synchronous
worker executor so shared-storage operations do not block heartbeat handling.
Startup owns resources as they are acquired, and independent cleanup steps continue
when another cleanup step fails.

Configuration rejects nonfinite values and validates assignments. Use
`validated_update(...)` to change related fields together; `model_copy(update=...)`
does not validate updates. Wire-model collections reject mutation and retain their
JSON and pickle representation. Inline text limits count UTF-8 bytes, binary limits
count decoded bytes, and worker JSONL frames are bounded.

Measurement evidence uses strict field types, including boolean flags, timing
counts, and finite latency values. Malformed worker evidence becomes an explicit
`worker_protocol` failure. Compiler targets, checkpoints, and restored candidate
and measurement records are validated at their boundaries. Checkpoints retain the
fixture contract path and verify the recorded oracle checksum before resuming.

## Skill and instruction provenance

Pipeline startup validates the packaged skill bundle. It does not require an
installation in the user's global Hermes home: each worker installs the package
into its own temporary profile. `skills doctor` and `skills sync` continue to
manage explicit user installations. Sync preserves conflicting local edits across
repeated attempts; those edits are never adopted as an installation baseline or
removed by uninstall.

Skills advertise the `skills` toolset so Hermes can discover them with custom
workspace MCP tools. Their instructions do not grant extra tool access: the
session's assigned tools and file scope still apply. The planner receives the
configured input interface and the explicit C input specification when present.

Each session initialization saves a content-addressed JSON file under
`agent-instructions/` in its working directory, including resumed initializations.
It contains the exact harness-supplied system instructions, their hash, enabled
toolsets, role, Hermes/package versions, and hashes of all bundled skill resources
and prompt source modules. Worker assembly and snapshot assembly share one helper.
`run.json` also fingerprints every bundled skill file, including references and
scripts. Snapshot records contain no provider configuration or credential files.

These snapshots cover harness-supplied instructions. Hermes adds its own SDK
identity, tool guidance, and any configured external memory; the snapshot does
not claim to capture that complete dynamic context. Preserve the locked environment
alongside run artifacts when reproducing an experiment. A passing prompt test
establishes assembly behavior, not whether a model follows those instructions.

Skill installation, run records, and instruction snapshots share one sorted resource
inventory that excludes hidden files and Python bytecode caches. Skill sync removes
retired package resources only when their installed hashes are unchanged; modified
retired resources remain conflicts across repeated syncs.

Each worker initialization also writes an attempt record under
`agent-instructions/attempts/`, linking its snapshot hash to a session identifier,
initialization index, timestamps, and initialization outcome. An interrupted process
can leave an `initializing` record. Failure records store exception types rather than
provider error text.

Fixture-spec runs must use `--until cpu-verified` until the downstream compiler,
precision-audit, and measurement adapters support direct inputs. Full runs and resumes
reject this configuration before allocating resources or contacting models.

Worker prompts inline essential role skills and the shared diagnostic output policy once.
Coder prompts route rejected candidates, numerical comparisons, elementary approximations,
and accelerator targets to their relevant skills on demand. Compensation workers receive
core diagnosis and compensation instructions; technique examples and platform tables remain
linked resources. Bundle validation checks these resources before startup, and provenance
continues to hash every resource whether or not it is inlined. Standalone skills link the
same diagnostic policy installed alongside them.
