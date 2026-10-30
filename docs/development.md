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
