#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-lassi-soda-mcp:latest}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CLIENT="${CLIENT:-claude}"

cd "${REPO_ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found on PATH." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed, but the Docker daemon is not reachable. Start Docker and retry." >&2
  exit 1
fi

echo "Building Docker image ${IMAGE_NAME} from mcp/Dockerfile.mcp"
docker build -f mcp/Dockerfile.mcp -t "${IMAGE_NAME}" .

echo "Writing ${CLIENT} MCP configuration"
"${PYTHON_BIN}" mcp/configure_MCP.py --client "${CLIENT}" --mode docker --image-name "${IMAGE_NAME}"

echo "Done."
echo "Image: ${IMAGE_NAME}"
echo "Config script: ${SCRIPT_DIR}/configure_MCP.py"
