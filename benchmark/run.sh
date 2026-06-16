#!/usr/bin/env bash
#
# PolyBench LASSI benchmark runner.
#
# Runs each kernel config N times back-to-back. Each pipeline run starts
# from a freshly-seeded optimized.c (the pipeline overwrites it from the
# reference before the first coder dispatch), so runs are independent and
# safe to aggregate.
#
# Per-run output:
#   $POLYBENCH_REPO/lassi_runs/logs/run_<ts>.json   (full RunRecord)
#   $POLYBENCH_REPO/lassi_runs/logs/runs.jsonl      (one summary/line)
#
# Logs are deliberately OUTSIDE .verify/ so the next run's planner — which
# has read access to .verify/ via `scope` — cannot see prior runs' attempts.
#
# Env overrides:
#   POLYBENCH_REPO  PolyBench project root           (default: $HOME/PolyBenchC-4.2.1)
#   RUNS            runs per kernel                   (default: 5)
#   CONFIGS         space-separated subset of kernels (default: all 5)
#   COOLDOWN        seconds to sleep between runs     (default: 5)
#
# Extra arguments to this script are forwarded to graph.graph_flow, e.g.
#   ./benchmark/run.sh --no-docker
#   ./benchmark/run.sh --no-profile

set -uo pipefail

POLYBENCH_REPO="${POLYBENCH_REPO:-$HOME/PolyBenchC-4.2.1}"
RUNS="${RUNS:-5}"
COOLDOWN="${COOLDOWN:-5}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LASSI_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$SCRIPT_DIR/configs"
LOG_DIR="$POLYBENCH_REPO/lassi_runs/logs"

DEFAULT_CONFIGS=(gemm 3mm lu covariance jacobi-2d)
read -r -a CONFIGS_ARR <<< "${CONFIGS:-${DEFAULT_CONFIGS[*]}}"

if [[ ! -d "$POLYBENCH_REPO" ]]; then
    echo "POLYBENCH_REPO does not exist: $POLYBENCH_REPO" >&2
    exit 2
fi
for cfg in "${CONFIGS_ARR[@]}"; do
    if [[ ! -f "$CONFIG_DIR/${cfg}.json" ]]; then
        echo "missing config: $CONFIG_DIR/${cfg}.json" >&2
        exit 2
    fi
done

cd "$LASSI_ROOT"

total=$((${#CONFIGS_ARR[@]} * RUNS))
done_count=0
pass_count=0
fail_count=0
suite_start=$(date +%s)

echo "=================================================================="
echo " LASSI PolyBench benchmark"
echo "   project root : $POLYBENCH_REPO"
echo "   configs      : ${CONFIGS_ARR[*]}"
echo "   runs/config  : $RUNS"
echo "   total runs   : $total"
echo "   cooldown     : ${COOLDOWN}s between runs"
echo "   logs land in : $LOG_DIR"
if [[ $# -gt 0 ]]; then
    echo "   passthrough  : $*"
fi
echo "=================================================================="

for cfg in "${CONFIGS_ARR[@]}"; do
    cfg_path="$CONFIG_DIR/${cfg}.json"
    for i in $(seq 1 "$RUNS"); do
        done_count=$((done_count + 1))
        # Cooldown before the next run (skip before the very first one).
        if [[ $done_count -gt 1 && $COOLDOWN -gt 0 ]]; then
            echo ""
            echo "... cooldown ${COOLDOWN}s"
            sleep "$COOLDOWN"
        fi
        run_start=$(date +%s)
        echo ""
        echo "------------------------------------------------------------------"
        echo " [$done_count/$total] $cfg  run $i/$RUNS"
        echo "------------------------------------------------------------------"
        if python -m graph.graph_flow "$POLYBENCH_REPO" "$cfg_path" "$@"; then
            pass_count=$((pass_count + 1))
            status="ok"
        else
            rc=$?
            fail_count=$((fail_count + 1))
            status="exit=$rc"
        fi
        run_elapsed=$(( $(date +%s) - run_start ))
        echo "[$done_count/$total] $cfg run $i: $status (${run_elapsed}s)"
    done
done

suite_elapsed=$(( $(date +%s) - suite_start ))
echo ""
echo "=================================================================="
echo " suite finished in ${suite_elapsed}s   pass=$pass_count  fail=$fail_count"
echo "   full records  : $LOG_DIR/run_*.json"
echo "   rolling log   : $LOG_DIR/runs.jsonl"
echo "=================================================================="

if [[ -f "$LOG_DIR/runs.jsonl" ]]; then
    echo ""
    echo "Last $total summaries (one per run):"
    tail -n "$total" "$LOG_DIR/runs.jsonl"
fi
