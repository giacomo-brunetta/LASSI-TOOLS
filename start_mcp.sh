#!/usr/bin/env bash
#
# start_mcp.sh — ensure the LASSI MCP server is ready to launch.
#
# Claude Code (and other clients) spawn the MCP server on demand via
#   docker run -i ... lassi-soda-mcp:latest python3 .../LASSI_mcp.py
# This script makes that command succeed by:
#   1. Starting Docker Desktop if the daemon is not reachable.
#   2. Building the lassi-soda-mcp image if it is missing (or when --rebuild).
#   3. Running a short stdio smoke test so a failure shows up here, not
#      later as a cryptic "Failed to reconnect to lassi" in the client.
#
# Usage:
#   ./start_mcp.sh                # ensure daemon + image, smoke-test
#   ./start_mcp.sh --rebuild      # force rebuild the image
#   ./start_mcp.sh --no-smoke     # skip the stdio smoke test
#   IMAGE_NAME=foo:tag ./start_mcp.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-lassi-soda-mcp:latest}"
DOCKER_WAIT_SECONDS="${DOCKER_WAIT_SECONDS:-60}"

REBUILD=0
RUN_SMOKE=1
for arg in "$@"; do
  case "$arg" in
    --rebuild)   REBUILD=1 ;;
    --no-smoke)  RUN_SMOKE=0 ;;
    -h|--help)
      sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

log() { printf '[start_mcp] %s\n' "$*"; }
die() { printf '[start_mcp] ERROR: %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "docker not found on PATH"

start_docker_desktop() {
  case "$(uname -s)" in
    Darwin)
      if [ -d "/Applications/Docker.app" ]; then
        log "Starting Docker Desktop..."
        open -ga Docker
      else
        die "Docker daemon is not running and /Applications/Docker.app was not found"
      fi
      ;;
    Linux)
      if command -v systemctl >/dev/null 2>&1; then
        log "Attempting: sudo systemctl start docker"
        sudo systemctl start docker || die "Could not start docker service"
      else
        die "Docker daemon not running; start it manually"
      fi
      ;;
    *)
      die "Unsupported OS for auto-start: $(uname -s)"
      ;;
  esac
}

wait_for_docker() {
  local waited=0
  while ! docker info >/dev/null 2>&1; do
    if [ "$waited" -ge "$DOCKER_WAIT_SECONDS" ]; then
      die "Docker daemon did not become ready within ${DOCKER_WAIT_SECONDS}s"
    fi
    sleep 2
    waited=$((waited + 2))
    if [ $((waited % 10)) -eq 0 ]; then
      log "still waiting for Docker daemon (${waited}s)..."
    fi
  done
}

if ! docker info >/dev/null 2>&1; then
  log "Docker daemon not reachable."
  start_docker_desktop
  wait_for_docker
fi
log "Docker daemon is up."

image_exists() { docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; }

if [ "$REBUILD" -eq 1 ] || ! image_exists; then
  if [ "$REBUILD" -eq 1 ]; then
    log "Rebuilding image ${IMAGE_NAME} (--rebuild)"
  else
    log "Image ${IMAGE_NAME} not found; building."
  fi
  (cd "$SCRIPT_DIR" && docker build -f setup/Dockerfile.mcp -t "$IMAGE_NAME" .)
else
  log "Image ${IMAGE_NAME} already present."
fi

if [ "$RUN_SMOKE" -eq 1 ]; then
  log "Running MCP stdio smoke test (initialize handshake)..."
  # Send a minimal JSON-RPC initialize request over stdin; the server should
  # respond on stdout and exit cleanly when stdin closes.
  smoke_payload='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"start_mcp.sh","version":"0"}}}'
  smoke_out=$(printf '%s\n' "$smoke_payload" | \
    docker run --rm -i \
      -v "${HOME}:${HOME}" \
      --workdir "${SCRIPT_DIR}" \
      -e PYTHONUNBUFFERED=1 \
      "$IMAGE_NAME" \
      python3 "${SCRIPT_DIR}/LASSI_mcp.py" 2>&1 | head -c 4096 || true)
  if printf '%s' "$smoke_out" | grep -q '"result"'; then
    log "Smoke test OK — server responded to initialize."
  else
    log "Smoke test did NOT see a JSON-RPC result. Output (truncated):"
    printf '%s\n' "$smoke_out" >&2
    die "MCP server failed smoke test"
  fi
fi

log "Ready. Clients can now launch ${IMAGE_NAME} via stdio."
