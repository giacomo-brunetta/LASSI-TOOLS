#!/usr/bin/env bash
#
# Build the per-agent image consumed by graph/container_pool.py.
#
# The graph itself now runs on the host (python graph/graph_flow.py); each
# specialized agent is dispatched into its own container by DockerAgentPool.
# This script's only remaining job is to (re)build the shared image those
# containers boot from. The pool will also build it lazily if missing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_NAME="${IMAGE_NAME:-lassi-graph:latest}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-requirements/requirements_graph.txt}"

usage() {
  cat <<EOF
Usage:
  graph/run_graph_docker.sh [--image NAME] [--requirements PATH]

Options:
  --image NAME           Tag for the built image (default: ${IMAGE_NAME}).
  --requirements PATH    Requirements file baked into the image
                         (default: ${REQUIREMENTS_FILE}).
  -h, --help             Show this help.

After building, run the graph on the host:
  python graph/graph_flow.py PROJECT_DIR [CONFIG_PATH]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      [[ $# -ge 2 ]] || { echo "--image requires a value" >&2; exit 2; }
      IMAGE_NAME="$2"
      shift 2
      ;;
    --requirements)
      [[ $# -ge 2 ]] || { echo "--requirements requires a path" >&2; exit 2; }
      REQUIREMENTS_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

command -v docker >/dev/null 2>&1 || { echo "docker not found on PATH" >&2; exit 1; }

cd "${REPO_ROOT}"
exec docker build \
  --build-arg "REQUIREMENTS_FILE=${REQUIREMENTS_FILE}" \
  -f graph/Dockerfile \
  -t "${IMAGE_NAME}" \
  .
