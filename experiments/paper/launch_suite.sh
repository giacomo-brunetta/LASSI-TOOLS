#!/usr/bin/env bash
# Launch the paper benchmark suite after the Academy/Globus resources are ready.
#
# Required before running this script:
#   1. On the Groq compute node that owns the LPUs, refresh the checkout the
#      measurement workers import and start the endpoint. PYTHONPATH must be
#      cleared: GroqRack exports /opt/groq/runtime/site-packages site-wide and
#      it shadows the conda environment.
#        ssh groq-r01-gn-01.ai.alcf.anl.gov
#        git -C /home/gbrun/LASSI-TOOLS pull
#        conda activate lassi-globus-compute
#        env -u PYTHONPATH globus-compute-endpoint start lassi-x-compute
#   2. On this harness, activate the LASSI environment, install the checkout so
#      compat_tool and its console commands are available, and sync the bundled
#      Hermes skills:
#        conda activate LASSI
#        pip install -e '.[globus]'
#        lassi-x skills sync
#   3. Start the Argo-compatible LLM shim every agent turn goes through. Its
#      port is assigned at startup and the generated default is
#      http://127.0.0.1:52226, so export LASSI_PAPER_LLM_BASE_URL when it lands
#      somewhere else. A stale value here is the single most expensive failure
#      mode: it kills every run about 110 s in with "Connection error."
#   4. Nothing else to select. Direct mode and the compute endpoint above are the
#      defaults, as is the A100 endpoint for CUDA. Override only when an
#      endpoint is re-registered (LASSI_PAPER_GROQ_ENDPOINT,
#      LASSI_PAPER_GPU_ENDPOINT) or to opt back into the login-node batch
#      path (LASSI_PAPER_GROQ_MODE=pbs).
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

Regenerates the paper configs, probes every model's LLM endpoint, verifies
Academy/Globus connectivity, then runs all kernels with GPT-5.6 Sol xhigh
followed by Claude Opus 5 xhigh.

Options:
  --doctor-only  Regenerate configs and run both preflights only.
  -h, --help     Show this help text.

All other options are passed through to run_suite.py, for example:
  --repetitions 3
  --kernel 3mm
  --model gpt-5.6-sol-xhigh
  --resume runs/paper-suite/session-YYYYMMDDTHHMMSSZ.jsonl
  --max-consecutive-failures 3   (0 disables the circuit breaker)

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
export PYTHONPATH="${REPO_ROOT}/src:${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

python experiments/paper/generate_configs.py
python -m lassi_x.cli skills sync
python -m compat_tool.query_wiki targets
# Until the first exact Groq snapshot is published, keep the restored corpus
# available only through an explicit, visibly legacy smoke check.
python -m compat_tool.query_wiki op aten.mm --target legacy-torch-mlir-tosa

# Probe the LLM endpoints first: it takes about a second, needs no remote
# resource, and catches the failures that historically cost whole sessions -- a
# dead proxy, a wrong model identifier, an endpoint that rejects tool-call
# replay. One --config per model, because each carries its own identifier.
model_configs=()
for config in "${REPO_ROOT}"/experiments/paper/configs/*/gemm.yaml; do
    model_configs+=(--config "${config}")
done
# Reported here but not fatal under set -e: run_suite.py re-probes and skips only
# the models that failed, so one dead model does not cost the healthy one's runs.
# Under --doctor-only there is no later run to make that call, so it is fatal.
models_code=0
python -m lassi_x.cli models doctor "${model_configs[@]}" || models_code=$?

python -m lassi_x.cli execution doctor --config "${FIRST_CONFIG}"

if [[ "${models_code}" -ne 0 && "${doctor_only}" == true ]]; then
    printf '%s\n' 'Model preflight failed; see the probe hints above.' >&2
    exit "${models_code}"
fi

if [[ "${doctor_only}" == true ]]; then
    printf '%s\n' 'Endpoint preflight passed; no benchmark was launched.'
    exit 0
fi

# The doctor above has already checked the one shared resource topology. Avoid
# launching a duplicate doctor inside run_suite.py before the first model turn.
python experiments/paper/run_suite.py --skip-doctor "${runner_args[@]}"
