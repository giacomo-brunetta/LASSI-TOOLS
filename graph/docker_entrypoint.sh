#!/usr/bin/env bash

set -euo pipefail

export HOME="${HOME:-/tmp/lassi-home}"
export CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-${HOME}/.claude}"

mkdir -p "${CLAUDE_CONFIG_DIR}"

if [[ -f /run/claude-settings.json ]]; then
  cp /run/claude-settings.json "${CLAUDE_CONFIG_DIR}/settings.json"
fi

exec "$@"
