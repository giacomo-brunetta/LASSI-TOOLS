#!/usr/bin/env bash
#
# Run graph/graph_flow.py inside an ephemeral Docker container.
#
# The selected project is the only host path mounted read-write. The LASSI
# implementation is baked into the image and the container root filesystem is
# read-only. Claude settings may be mounted read-only for authentication and
# are copied into ephemeral /tmp state before the graph starts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_NAME="${IMAGE_NAME:-lassi-graph:latest}"
SETTINGS_PATH="${HOME}/.claude/settings.json"
CONFIG_PATH="graph_code_test.json"
EXTERNAL_CONFIG=""
REBUILD=0
DRY_RUN=0
NO_PROFILE=0
USE_SETTINGS=1
PROJECT_READ_ONLY=0
WRITABLE_FILES=()
READ_ONLY_MOUNTS=()

usage() {
  cat <<'EOF'
Usage:
  graph/run_graph_docker.sh [options] PROJECT_DIR [CONFIG_PATH]

Arguments:
  PROJECT_DIR   Host project directory mounted read-write at /workspace.
  CONFIG_PATH   Config path relative to PROJECT_DIR. Defaults to
                graph_code_test.json. The graph generates it when missing.

Options:
  --image NAME       Docker image name (default: lassi-graph:latest).
  --rebuild          Rebuild the image from graph/Dockerfile.
  --settings PATH    Read-only Claude settings used for authentication.
  --no-settings      Do not mount Claude settings; use provider env vars only.
  --read-only-project
                     Mount PROJECT_DIR read-only. Generated reports and build
                     outputs are routed to container-only /tmp storage.
  --writable-file PATH
                     Overlay one file inside a read-only project as writable.
                     May be repeated.
  --external-config PATH
                     Mount a host config read-only instead of reading or
                     generating CONFIG_PATH inside the project.
  --read-only-mount HOST_PATH:CONTAINER_PATH
                     Add an auxiliary read-only file mount. May be repeated.
  --no-profile       Pass --no-profile to graph_flow.py.
  --dry-run          Print commands without running Docker.
  -h, --help         Show this help.

Provider environment variables such as ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL,
AWS_*, GOOGLE_*, and CLAUDE_CODE_SKIP_ANTHROPIC_AUTH are forwarded when set.
EOF
}

die() {
  printf '[run_graph_docker] ERROR: %s\n' "$*" >&2
  exit 1
}

print_command() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      [[ $# -ge 2 ]] || die "--image requires a value"
      IMAGE_NAME="$2"
      shift 2
      ;;
    --rebuild)
      REBUILD=1
      shift
      ;;
    --settings)
      [[ $# -ge 2 ]] || die "--settings requires a path"
      SETTINGS_PATH="$2"
      USE_SETTINGS=1
      shift 2
      ;;
    --no-settings)
      USE_SETTINGS=0
      shift
      ;;
    --read-only-project)
      PROJECT_READ_ONLY=1
      shift
      ;;
    --writable-file)
      [[ $# -ge 2 ]] || die "--writable-file requires a path"
      WRITABLE_FILES+=("$2")
      shift 2
      ;;
    --external-config)
      [[ $# -ge 2 ]] || die "--external-config requires a path"
      EXTERNAL_CONFIG="$2"
      shift 2
      ;;
    --read-only-mount)
      [[ $# -ge 2 ]] || die "--read-only-mount requires HOST_PATH:CONTAINER_PATH"
      READ_ONLY_MOUNTS+=("$2")
      shift 2
      ;;
    --no-profile)
      NO_PROFILE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      POSITIONAL+=("$@")
      break
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

[[ ${#POSITIONAL[@]} -ge 1 ]] || {
  usage >&2
  exit 2
}
[[ ${#POSITIONAL[@]} -le 2 ]] || die "expected PROJECT_DIR and optional CONFIG_PATH"

PROJECT_DIR="${POSITIONAL[0]}"
if [[ ${#POSITIONAL[@]} -eq 2 ]]; then
  CONFIG_PATH="${POSITIONAL[1]}"
fi

[[ -d "${PROJECT_DIR}" ]] || die "project directory does not exist: ${PROJECT_DIR}"
PROJECT_DIR="$(cd "${PROJECT_DIR}" && pwd -P)"
[[ "${PROJECT_DIR}" != "/" ]] || die "refusing to mount the host root as the writable project"

if [[ "${CONFIG_PATH}" = /* ]]; then
  case "${CONFIG_PATH}" in
    "${PROJECT_DIR}"/*) CONFIG_PATH="${CONFIG_PATH#"${PROJECT_DIR}"/}" ;;
    *) die "absolute config path must be inside the project directory" ;;
  esac
fi
case "/${CONFIG_PATH}/" in
  */../*|*/./../*) die "config path must not escape the project directory" ;;
esac

if [[ -n "${EXTERNAL_CONFIG}" ]]; then
  [[ -f "${EXTERNAL_CONFIG}" ]] || die "external config does not exist: ${EXTERNAL_CONFIG}"
  EXTERNAL_CONFIG="$(cd "$(dirname "${EXTERNAL_CONFIG}")" && pwd -P)/$(basename "${EXTERNAL_CONFIG}")"
fi

NORMALIZED_WRITABLE_FILES=()
if [[ ${#WRITABLE_FILES[@]} -gt 0 ]]; then
  for path in "${WRITABLE_FILES[@]}"; do
    if [[ "${path}" != /* ]]; then
      path="${PROJECT_DIR}/${path}"
    fi
    [[ -f "${path}" ]] || die "writable file does not exist: ${path}"
    path="$(cd "$(dirname "${path}")" && pwd -P)/$(basename "${path}")"
    case "${path}" in
      "${PROJECT_DIR}"/*) ;;
      *) die "writable file must be inside the project directory: ${path}" ;;
    esac
    NORMALIZED_WRITABLE_FILES+=("${path}")
  done
fi

if [[ "${PROJECT_READ_ONLY}" -eq 0 && ${#NORMALIZED_WRITABLE_FILES[@]} -gt 0 ]]; then
  die "--writable-file requires --read-only-project"
fi

NORMALIZED_READ_ONLY_MOUNTS=()
if [[ ${#READ_ONLY_MOUNTS[@]} -gt 0 ]]; then
  for spec in "${READ_ONLY_MOUNTS[@]}"; do
    host_path="${spec%%:*}"
    container_path="${spec#*:}"
    [[ "${host_path}" != "${spec}" && -n "${container_path}" ]] || die "read-only mount must use HOST_PATH:CONTAINER_PATH"
    [[ -f "${host_path}" ]] || die "read-only mount source does not exist: ${host_path}"
    [[ "${container_path}" = /* ]] || die "read-only mount destination must be absolute: ${container_path}"
    case "${container_path}" in
      /workspace|/workspace/*) die "auxiliary read-only mounts must be outside /workspace" ;;
    esac
    host_path="$(cd "$(dirname "${host_path}")" && pwd -P)/$(basename "${host_path}")"
    NORMALIZED_READ_ONLY_MOUNTS+=("${host_path}:${container_path}")
  done
fi

if [[ "${USE_SETTINGS}" -eq 1 ]]; then
  [[ -f "${SETTINGS_PATH}" ]] || die "Claude settings not found: ${SETTINGS_PATH}; use --no-settings to rely on environment credentials"
  SETTINGS_PATH="$(cd "$(dirname "${SETTINGS_PATH}")" && pwd -P)/$(basename "${SETTINGS_PATH}")"
fi

BUILD_CMD=(
  docker build
  --build-arg REQUIREMENTS_FILE=requirements/requirements_graph.txt
  -f graph/Dockerfile
  -t "${IMAGE_NAME}"
  .
)

RUN_CMD=(
  docker run --rm --init
  --read-only
  --cap-drop ALL
  --security-opt no-new-privileges
  --pids-limit 512
  --tmpfs /tmp:rw,nosuid,nodev,size=2g,mode=1777
  --tmpfs /lassi-build:rw,exec,nosuid,nodev,size=2g,mode=1777
  --workdir /workspace
  --user "$(id -u):$(id -g)"
  --env HOME=/tmp/lassi-home
  --env CLAUDE_CONFIG_DIR=/tmp/lassi-home/.claude
  --env PYTHONUNBUFFERED=1
)

if [[ "${PROJECT_READ_ONLY}" -eq 1 ]]; then
  RUN_CMD+=(
    --mount "type=bind,src=${PROJECT_DIR},dst=/workspace,readonly"
    --env LASSI_ARTIFACT_DIR=/tmp/lassi-artifacts/LASSI
    --env LASSI_BUILD_ROOT=/lassi-build/refactoring
  )
  if [[ ${#NORMALIZED_WRITABLE_FILES[@]} -gt 0 ]]; then
    for path in "${NORMALIZED_WRITABLE_FILES[@]}"; do
      relative="${path#"${PROJECT_DIR}"/}"
      RUN_CMD+=(--mount "type=bind,src=${path},dst=/workspace/${relative}")
    done
  fi
else
  RUN_CMD+=(--mount "type=bind,src=${PROJECT_DIR},dst=/workspace")
fi

if [[ "${USE_SETTINGS}" -eq 1 ]]; then
  RUN_CMD+=(--mount "type=bind,src=${SETTINGS_PATH},dst=/run/claude-settings.json,readonly")
fi

FORWARDED_ENV=(
  ANTHROPIC_API_KEY
  ANTHROPIC_AUTH_TOKEN
  ANTHROPIC_BASE_URL
  CLAUDE_CODE_SKIP_ANTHROPIC_AUTH
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_SESSION_TOKEN
  AWS_REGION
  AWS_DEFAULT_REGION
  CLAUDE_CODE_USE_BEDROCK
  CLAUDE_CODE_USE_VERTEX
  GOOGLE_APPLICATION_CREDENTIALS
  CLOUD_ML_REGION
  ANTHROPIC_VERTEX_PROJECT_ID
)
for name in "${FORWARDED_ENV[@]}"; do
  if [[ -n "${!name:-}" ]]; then
    RUN_CMD+=(--env "${name}")
  fi
done

if [[ -n "${EXTERNAL_CONFIG}" ]]; then
  RUN_CMD+=(--mount "type=bind,src=${EXTERNAL_CONFIG},dst=/run/lassi-graph-config.json,readonly")
fi
if [[ ${#NORMALIZED_READ_ONLY_MOUNTS[@]} -gt 0 ]]; then
  for spec in "${NORMALIZED_READ_ONLY_MOUNTS[@]}"; do
    host_path="${spec%%:*}"
    container_path="${spec#*:}"
    RUN_CMD+=(--mount "type=bind,src=${host_path},dst=${container_path},readonly")
  done
fi

RUN_CMD+=(
  "${IMAGE_NAME}"
  /opt/lassi/graph/docker_entrypoint.sh
  /opt/lassi/.venv/bin/python
  /opt/lassi/graph/graph_flow.py
)
if [[ -n "${EXTERNAL_CONFIG}" ]]; then
  RUN_CMD+=(/run/lassi-graph-config.json)
else
  RUN_CMD+=("/workspace/${CONFIG_PATH}")
fi
RUN_CMD+=(
  --repo /workspace
)
if [[ "${NO_PROFILE}" -eq 1 ]]; then
  RUN_CMD+=(--no-profile)
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  if [[ "${REBUILD}" -eq 1 ]]; then
    printf 'Build command:\n'
    print_command "${BUILD_CMD[@]}"
  fi
  printf 'Run command:\n'
  print_command "${RUN_CMD[@]}"
  exit 0
fi

command -v docker >/dev/null 2>&1 || die "docker not found on PATH"
docker info >/dev/null 2>&1 || die "Docker daemon is not reachable"

if [[ "${REBUILD}" -eq 1 ]] || ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  printf '[run_graph_docker] Building %s from graph/Dockerfile\n' "${IMAGE_NAME}"
  (cd "${REPO_ROOT}" && "${BUILD_CMD[@]}")
fi

if [[ "${PROJECT_READ_ONLY}" -eq 1 ]]; then
  printf '[run_graph_docker] Project mounted read-only: %s -> /workspace\n' "${PROJECT_DIR}"
  if [[ ${#NORMALIZED_WRITABLE_FILES[@]} -gt 0 ]]; then
    for path in "${NORMALIZED_WRITABLE_FILES[@]}"; do
      printf '[run_graph_docker] Writable file overlay: %s\n' "${path}"
    done
  fi
else
  printf '[run_graph_docker] Project mounted read-write: %s -> /workspace\n' "${PROJECT_DIR}"
fi
printf '[run_graph_docker] Container root and baked LASSI source are read-only\n'
exec "${RUN_CMD[@]}"
