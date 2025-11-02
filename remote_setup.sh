#!/usr/bin/env bash
set -euo pipefail
CFG_FILE="remote_config.json"
if [[ ! -f $CFG_FILE ]]; then echo "Missing remote_config.json"; exit 1; fi
REMOTE_HOST=$(jq -r '.remote_host' $CFG_FILE)
REMOTE_USER=$(jq -r '.remote_user' $CFG_FILE)
REMOTE_ROOT=$(jq -r '.project_root_remote' $CFG_FILE)
REMOTE_PORT=$(jq -r '.remote_port' $CFG_FILE)
SUDO_USER=$(jq -r '.sudo_user' $CFG_FILE)
SUDO_PW_VAR=$(jq -r '.sudo_password_env' $CFG_FILE)

# Expect environment variable holding sudo password (export before running)
SUDO_PASSWORD=${!SUDO_PW_VAR:-}
if [[ -z "$SUDO_PASSWORD" ]]; then
  echo "WARNING: Sudo password env ($SUDO_PW_VAR) not set; system package install may prompt interactively." >&2
fi

ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" bash -s <<EOF
set -euo pipefail
echo "== Remote setup on \\$(hostname) =="

if ! command -v python3 >/dev/null 2>&1; then
  if [[ -n "$SUDO_PASSWORD" ]]; then
    echo "Installing python3 via sudo..."
    echo "$SUDO_PASSWORD" | sudo -S apt update -y || true
    echo "$SUDO_PASSWORD" | sudo -S apt install -y python3 python3-venv python3-pip
  else
    echo "Python3 missing and no sudo password provided; please install manually."; exit 1
  fi
fi

if [[ -n "$SUDO_PASSWORD" ]]; then
  echo "$SUDO_PASSWORD" | sudo -S apt install -y jq rsync || true
fi

mkdir -p "$REMOTE_ROOT"
cd "$REMOTE_ROOT" || { echo "Remote root missing"; exit 1; }
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
if [[ -f requirements.txt ]]; then
  pip install -r requirements.txt
else
  echo "No requirements.txt found; skipping dependency install"
fi
echo "Remote setup complete"
EOF