#!/usr/bin/env bash
# Launch the paper benchmark suite after the Academy/Globus resources are ready.
#
# Required before running this script:
#   1. On the Groq login node, start the configured Globus Compute endpoint:
#        conda activate lassi-globus-compute
#        globus-compute-endpoint start lassi-x
#   2. On this harness, activate the LASSI environment and install the Globus extra:
#        conda activate LASSI
#        pip install -e '.[globus]'
#
# The endpoint identifier and workspace paths are generated from benchmarks.yaml
# by generate_configs.py.  This script deliberately does not start or configure
# remote endpoint daemons: they must remain owned by their respective machines.

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
readonly FIRST_CONFIG="${REPO_ROOT}/experiments/paper/configs/gpt-5.6-sol-xhigh/gemm.yaml"

usage() {
    cat <<'EOF'
Usage: bash experiments/paper/launch_suite.sh [--doctor-only] [run-suite options...]

Regenerates the paper configs, verifies Academy/Globus connectivity, then runs
all kernels with GPT-5.6 Sol xhigh followed by Claude Opus 5 xhigh.

Options:
  --doctor-only  Regenerate configs and run the endpoint preflight only.
  -h, --help     Show this help text.

All other options are passed through to run_suite.py, for example:
  --repetitions 3
  --kernel 3mm
  --model gpt-5.6-sol-xhigh
  --resume runs/paper-suite/session-YYYYMMDDTHHMMSSZ.jsonl

The script does not start Globus Compute endpoints. Start the Groq login-node
endpoint first, then run this command from the local CUDA harness.
EOF
}

doctor_only=false
runner_args=()
while (($#)); do
    case "$1" in
        --doctor-only)
            doctor_only=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            runner_args+=("$1")
            ;;
    esac
    shift
done

cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

python experiments/paper/generate_configs.py
python -m lassi_x.cli execution doctor --config "${FIRST_CONFIG}"

if [[ "${doctor_only}" == true ]]; then
    printf '%s\n' 'Endpoint preflight passed; no benchmark was launched.'
    exit 0
fi

# The doctor above has already checked the one shared resource topology. Avoid
# launching a duplicate doctor inside run_suite.py before the first model turn.
python experiments/paper/run_suite.py --skip-doctor "${runner_args[@]}"
