#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-lassi-soda-mcp:latest}"

cd "${SCRIPT_DIR}"

echo "Building Docker image ${IMAGE_NAME} from Dockerfile.mcp"
docker build -f Dockerfile.mcp -t "${IMAGE_NAME}" .

echo "Writing Roo MCP configuration"
python3 configure_MCP.py --mode docker --image-name "${IMAGE_NAME}"

echo "Done."
echo "Image: ${IMAGE_NAME}"
echo "Config script: ${SCRIPT_DIR}/configure_MCP.py"
