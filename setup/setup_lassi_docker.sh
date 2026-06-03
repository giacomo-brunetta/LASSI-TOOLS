#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-lassi-mcp:latest}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CLIENT="${CLIENT:-claude}"
SERVER_NAME="${SERVER_NAME:-lassi}"

CONTAINER_WORKDIR="/opt/lassi"
CONTAINER_SERVER_PATH="/opt/lassi/LASSI_mcp.py"
CONTAINER_PYTHON="/opt/lassi/.venv/bin/python"

cd "${REPO_ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found on PATH." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed, but the Docker daemon is not reachable. Start Docker and retry." >&2
  exit 1
fi

echo "Building Docker image ${IMAGE_NAME} from setup/Dockerfile.lassi"
docker build -f setup/Dockerfile.lassi -t "${IMAGE_NAME}" .

echo "Writing ${CLIENT} MCP configuration (server name: ${SERVER_NAME})"
"${PYTHON_BIN}" setup/configure_MCP.py \
  --client "${CLIENT}" \
  --mode docker \
  --image-name "${IMAGE_NAME}" \
  --server-name "${SERVER_NAME}" \
  --container-workdir "${CONTAINER_WORKDIR}" \
  --container-server-path "${CONTAINER_SERVER_PATH}" \
  --container-python "${CONTAINER_PYTHON}"

echo "Done."
echo "Image: ${IMAGE_NAME}"
echo "Server entry: ${SERVER_NAME}"
echo "Reload your MCP client (Claude Code / Codex / Roo) to pick up the new configuration."
