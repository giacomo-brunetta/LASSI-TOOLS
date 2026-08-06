#!/usr/bin/env bash
# Poll the execution preflight and launch the paper suite once it passes.
#
# For the case where the endpoints are restarted from somewhere other than this
# machine: leave this running, restart the endpoints on their own nodes, and the
# suite starts by itself. It never restarts an endpoint -- those stay owned by
# the machines they run on.
#
#   bash experiments/paper/wait_and_launch.sh            # poll forever
#   bash experiments/paper/wait_and_launch.sh --max-wait-s 7200
#
# Any further options are passed through to launch_suite.sh, and from there to
# run_suite.py (--kernel, --model, --repetitions, --resume).
#
# The preflight is the gate on purpose: it fails in about 6.5 minutes against a
# wedged endpoint, so a failed probe costs little and a passing one means all
# three resources answered a real handshake, not just a heartbeat.

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

poll_interval_s=120
max_wait_s=0 # 0 means wait indefinitely
launch_args=()
while (($#)); do
    case "$1" in
        --poll-interval-s)
            poll_interval_s="$2"
            shift
            ;;
        --max-wait-s)
            max_wait_s="$2"
            shift
            ;;
        *)
            launch_args+=("$1")
            ;;
    esac
    shift
done

cd "${REPO_ROOT}"
started_at="$(date +%s)"
attempt=0

while true; do
    attempt=$((attempt + 1))
    printf '[%s] preflight attempt %d\n' "$(date -Is)" "${attempt}"
    if bash experiments/paper/launch_suite.sh --doctor-only; then
        printf '[%s] preflight passed; launching the suite\n' "$(date -Is)"
        exec bash experiments/paper/launch_suite.sh "${launch_args[@]}"
    fi

    elapsed=$(($(date +%s) - started_at))
    if ((max_wait_s > 0 && elapsed >= max_wait_s)); then
        printf '[%s] giving up after %ds without a healthy preflight\n' "$(date -Is)" "${elapsed}"
        exit 1
    fi
    printf '[%s] resources still unreachable; retrying in %ds\n' "$(date -Is)" "${poll_interval_s}"
    sleep "${poll_interval_s}"
done
