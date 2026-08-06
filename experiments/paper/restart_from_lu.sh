#!/usr/bin/env bash
# Kill the in-flight paper suite and resume it from the LU kernel.
#
# Why this exists: the LU run wedged on an arena candidate that transliterated
# the reference's scalar loop nest, so a single forward could not finish. The
# per-measurement ceilings and the arena prompts have both changed since that
# run started, and a live run holds its configs from launch time -- it will not
# pick up either change. Restarting is the only way to apply them.
#
# What is preserved: the existing session journal. run_suite.py --resume skips
# every (model, kernel, repetition) that already finished with exit 0, so gemm,
# 3mm, covariance, and jacobi-2d are not re-run and their artifacts are
# untouched. The suite picks up at LU and continues through the matrix.
#
# What is NOT done here: nothing on the Groq side. Remote endpoints are owned by
# their own machines, and SSH to ALCF needs interactive MFA. If the Groq
# endpoint has died, start it there yourself before running this.
#
# Usage:
#   bash experiments/paper/restart_from_lu.sh            # kill, then resume
#   bash experiments/paper/restart_from_lu.sh --dry-run  # show what it would do
#
# Any other options are passed through to run_suite.py.

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
readonly RUNS_DIR="${REPO_ROOT}/runs/paper-suite"

dry_run=false
passthrough=()
for arg in "$@"; do
    case "${arg}" in
        --dry-run) dry_run=true ;;
        *) passthrough+=("${arg}") ;;
    esac
done

cd "${REPO_ROOT}"

# --- Locate the journal to resume ------------------------------------------
JOURNAL="$(ls -t "${RUNS_DIR}"/session-*.jsonl 2>/dev/null | head -1 || true)"
if [[ -z "${JOURNAL}" ]]; then
    printf 'No session journal under %s; use launch_suite.sh for a fresh run.\n' "${RUNS_DIR}" >&2
    exit 1
fi
printf 'Resuming journal: %s\n' "${JOURNAL}"
printf 'Already complete (will be skipped):\n'
python - "${JOURNAL}" <<'PY'
import json
import sys

for line in open(sys.argv[1]):
    event = json.loads(line)
    if event.get("event") == "finish" and event.get("exit_code") == 0:
        print(f"  {event['model']} / {event['kernel']} / rep {event['repetition']}")
PY

# --- Stop the live suite ----------------------------------------------------
# The runner puts each kernel child in its own process group, so signalling the
# runner alone would orphan the child. Kill the child's group first, then the
# runner, so nothing is left holding a log file or an Academy session open.
stop_suite() {
    local child runner
    mapfile -t child < <(pgrep -f 'lassi_x.cli run .*/configs/.*\.yaml' || true)
    mapfile -t runner < <(pgrep -f 'experiments/paper/run_suite.py' || true)

    if ((${#child[@]} == 0 && ${#runner[@]} == 0)); then
        printf 'No suite process is running; nothing to kill.\n'
        return 0
    fi

    for pid in "${child[@]}" "${runner[@]}"; do
        printf 'Stopping pid %s: %s\n' "${pid}" "$(ps -o cmd= -p "${pid}" 2>/dev/null || echo gone)"
        if [[ "${dry_run}" == false ]]; then
            # Negative pid signals the whole group, which reaps MCP servers and
            # Academy workers along with the process itself.
            kill -TERM -- "-${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null || true
        fi
    done

    [[ "${dry_run}" == true ]] && return 0

    for _ in $(seq 1 30); do
        pgrep -f 'experiments/paper/run_suite.py' >/dev/null || break
        sleep 1
    done
    for pid in "${child[@]}" "${runner[@]}"; do
        kill -KILL -- "-${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null || true
    done
    printf 'Suite stopped.\n'
}
stop_suite

# The killed LU run left a partial artifact tree. It is kept rather than deleted
# so the wedged candidate stays available as evidence, and it is journaled as a
# failure, so --resume will redo the kernel regardless.
printf '\nPartial LU artifacts retained under %s/gpt-5.6-sol-xhigh/lu/\n' "${RUNS_DIR}"

if [[ "${dry_run}" == true ]]; then
    printf '\nDry run: would now execute\n  bash experiments/paper/launch_suite.sh --resume %s %s\n' \
        "${JOURNAL}" "${passthrough[*]-}"
    exit 0
fi

# launch_suite.sh regenerates the configs from generate_configs.py (picking up
# the new per-measurement ceilings) and runs the endpoint preflight before
# handing off to the runner.
printf '\nRelaunching from LU...\n'
exec bash experiments/paper/launch_suite.sh --resume "${JOURNAL}" "${passthrough[@]-}"
