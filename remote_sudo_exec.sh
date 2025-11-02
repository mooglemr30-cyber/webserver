#!/usr/bin/env bash
# Remote sudo execution helper
# Usage: REMOTE_SUDO_PASSWORD=pearce ./remote_sudo_exec.sh "apt update"
set -euo pipefail
CFG_FILE="remote_config.json"
if [[ ! -f $CFG_FILE ]]; then echo "Missing remote_config.json"; exit 1; fi
REMOTE_HOST=$(jq -r '.remote_host' $CFG_FILE)
REMOTE_USER=$(jq -r '.remote_user' $CFG_FILE)
REMOTE_PORT=$(jq -r '.remote_port' $CFG_FILE)
SUDO_PW_VAR=$(jq -r '.sudo_password_env' $CFG_FILE)
SUDO_PASSWORD=${!SUDO_PW_VAR:-}
if [[ -z "$SUDO_PASSWORD" ]]; then
  echo "Sudo password env ($SUDO_PW_VAR) not set" >&2
  exit 1
fi
if [[ $# -lt 1 ]]; then
  echo "Provide command to run, e.g. 'apt update'" >&2
  exit 1
fi
CMD="$*"
ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" bash -s <<EOF
set -euo pipefail
echo "Running: sudo $CMD" 
echo "$SUDO_PASSWORD" | sudo -S $CMD
EOF
