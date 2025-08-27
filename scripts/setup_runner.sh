#!/usr/bin/env bash
set -euo pipefail

# GitHub Actions self-hosted runner setup utility
# Usage:
#   scripts/setup_runner.sh install   # download, configure, and install service
#   scripts/setup_runner.sh uninstall # remove service and configuration
#   scripts/setup_runner.sh start     # start service
#   scripts/setup_runner.sh stop      # stop service
#   scripts/setup_runner.sh status    # service status
#   scripts/setup_runner.sh run-once  # run one job interactively (no service)
#
# Requires a .env file at repo root (see .env.example). Minimal required:
#   RUNNER_URL, RUNNER_TOKEN

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
echo "ROOT_DIR: ${ROOT_DIR}"
ENV_FILE="${ROOT_DIR}/.env"
echo "ENV_FILE: ${ENV_FILE}"

if [[ -f "${ENV_FILE}" ]]; then
  # Load .env safely, exporting variables
  set -o allexport
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +o allexport
else
  echo "ERROR: .env not found at ${ENV_FILE}. Copy .env.example to .env and fill values." >&2
  exit 1
fi

# Normalize: accept lowercase variants from .env and map to uppercase expected names
if [[ -z "${RUNNER_URL:-}" && -n "${runner_url:-}" ]]; then RUNNER_URL="${runner_url}"; fi
if [[ -z "${RUNNER_TOKEN:-}" && -n "${runner_token:-}" ]]; then RUNNER_TOKEN="${runner_token}"; fi
if [[ -z "${RUNNER_NAME:-}" && -n "${runner_name:-}" ]]; then RUNNER_NAME="${runner_name}"; fi
if [[ -z "${RUNNER_LABELS:-}" && -n "${runner_labels:-}" ]]; then RUNNER_LABELS="${runner_labels}"; fi
if [[ -z "${RUNNER_VERSION:-}" && -n "${runner_version:-}" ]]; then RUNNER_VERSION="${runner_version}"; fi
if [[ -z "${RUNNER_DIR:-}" && -n "${runner_dir:-}" ]]; then RUNNER_DIR="${runner_dir}"; fi
if [[ -z "${EPHEMERAL:-}" && -n "${ephemeral:-}" ]]; then EPHEMERAL="${ephemeral}"; fi
if [[ -z "${ENV_PATH:-}" && -n "${env_path:-}" ]]; then ENV_PATH="${env_path}"; fi
if [[ -z "${EXTRA_ENV:-}" && -n "${extra_env:-}" ]]; then EXTRA_ENV="${extra_env}"; fi

echo "RUNNER_URL: ${RUNNER_URL:-<unset>}"
if [[ -n "${RUNNER_TOKEN:-}" ]]; then
  echo "RUNNER_TOKEN: <set>"
else
  echo "RUNNER_TOKEN: <unset>"
fi

# Defaults
RUNNER_NAME=${RUNNER_NAME:-"plateshapez-runner-1"}
RUNNER_LABELS=${RUNNER_LABELS:-"self-hosted,plateshapez"}
RUNNER_VERSION=${RUNNER_VERSION:-"2.319.1"}
RUNNER_DIR=${RUNNER_DIR:-"$HOME/actions-runner"}
EPHEMERAL=${EPHEMERAL:-"false"}
ENV_PATH=${ENV_PATH:-"$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}
EXTRA_ENV=${EXTRA_ENV:-""}

if [[ -z "${RUNNER_URL:-}" || -z "${RUNNER_TOKEN:-}" ]]; then
  echo "ERROR: RUNNER_URL and RUNNER_TOKEN must be set in .env" >&2
  exit 1
fi

ARCH="x64"
PKG="actions-runner-linux-${ARCH}-${RUNNER_VERSION}.tar.gz"
DL_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${PKG}"

ensure_deps() {
  command -v curl >/dev/null 2>&1 || { echo "ERROR: curl is required" >&2; exit 1; }
  command -v tar >/dev/null 2>&1 || { echo "ERROR: tar is required" >&2; exit 1; }
}

download_runner() {
  mkdir -p "${RUNNER_DIR}"
  cd "${RUNNER_DIR}"
  if [[ ! -f "${PKG}" ]]; then
    echo "Downloading ${PKG} ..."
    curl -fsSL -o "${PKG}" "${DL_URL}"
  fi
  if [[ ! -x ./run.sh ]]; then
    echo "Extracting runner ..."
    tar xzf "${PKG}"
  fi
}

configure_runner() {
  cd "${RUNNER_DIR}"
  if [[ -f .runner ]]; then
    echo "Runner appears configured at ${RUNNER_DIR} (found .runner). Skipping config."
    return
  fi

  echo "Configuring runner for ${RUNNER_URL} as ${RUNNER_NAME} with labels ${RUNNER_LABELS} ..."
  ARGS=("--url" "${RUNNER_URL}" "--token" "${RUNNER_TOKEN}" "--name" "${RUNNER_NAME}" "--labels" "${RUNNER_LABELS}")
  if [[ "${EPHEMERAL}" == "true" ]]; then
    ARGS+=("--ephemeral")
  fi
  # unattended + replace to avoid prompts on reconfig
  ./config.sh --unattended --replace "${ARGS[@]}"
}

install_service() {
  cd "${RUNNER_DIR}"
  sudo ./svc.sh install

  # Ensure PATH contains user local bin for uv and others
  # Create a systemd drop-in override to set Environment PATH and custom EXTRA_ENV
  UNIT_NAME=$(systemctl list-units --type=service --all | awk '/actions\.runner\./ {print $1; exit}')
  if [[ -z "${UNIT_NAME}" ]]; then
    # Fallback common pattern
    UNIT_NAME="actions.runner.$(hostname | tr '[:upper:]' '[:lower:]').service"
  fi

  sudo mkdir -p "/etc/systemd/system/${UNIT_NAME}.d"
  TMP_OVERRIDE=$(mktemp)
  {
    echo "[Service]"
    echo "Environment=PATH=${ENV_PATH}"
    if [[ -n "${EXTRA_ENV}" ]]; then
      IFS=',' read -ra pairs <<< "${EXTRA_ENV}"
      for kv in "${pairs[@]}"; do
        [[ -n "${kv}" ]] && echo "Environment=${kv}"
      done
    fi
  } > "${TMP_OVERRIDE}"
  sudo mv "${TMP_OVERRIDE}" "/etc/systemd/system/${UNIT_NAME}.d/override.conf"
  sudo systemctl daemon-reload
}

start_service() {
  cd "${RUNNER_DIR}"
  sudo ./svc.sh start
}

stop_service() {
  cd "${RUNNER_DIR}"
  sudo ./svc.sh stop || true
}

uninstall_service() {
  stop_service || true
  cd "${RUNNER_DIR}"
  sudo ./svc.sh uninstall || true
  # Optionally remove config
  if [[ -f .runner ]]; then
    ./config.sh remove --unattended --token "${RUNNER_TOKEN}" || true
  fi
}

run_once() {
  cd "${RUNNER_DIR}"
  ./run.sh
}

cmd=${1:-install}
case "${cmd}" in
  install)
    ensure_deps
    download_runner
    configure_runner
    install_service
    start_service
    echo "Runner installed and started."
    ;;
  uninstall)
    uninstall_service
    echo "Runner service uninstalled."
    ;;
  start)
    start_service
    ;;
  stop)
    stop_service
    ;;
  status)
    systemctl status "$(systemctl list-units --type=service --all | awk '/actions\.runner\./ {print $1; exit}')" || true
    ;;
  run-once)
    ensure_deps
    download_runner
    configure_runner
    run_once
    ;;
  *)
    echo "Usage: $0 {install|uninstall|start|stop|status|run-once}" >&2
    exit 1
    ;;
 esac
