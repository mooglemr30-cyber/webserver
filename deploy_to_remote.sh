#!/usr/bin/env bash
set -euo pipefail

# Load remote config
declare -A CFG
CFG_FILE="remote_config.json"
if [[ ! -f $CFG_FILE ]]; then
  echo "Missing remote_config.json" >&2
  exit 1
fi

REMOTE_HOST=$(jq -r '.remote_host' $CFG_FILE)
REMOTE_USER=$(jq -r '.remote_user' $CFG_FILE)
REMOTE_PORT=$(jq -r '.remote_port' $CFG_FILE)
REMOTE_ROOT=$(jq -r '.project_root_remote' $CFG_FILE)
AUTH_METHOD=$(jq -r '.auth_method' $CFG_FILE)

# Optional env file
if [[ -f .env.remote ]]; then
  source .env.remote || true
fi

echo "== Remote Deploy =="
echo "Host: $REMOTE_HOST"; echo "User: $REMOTE_USER"; echo "Port: $REMOTE_PORT"; echo "Root: $REMOTE_ROOT";

mkdir -p .deploy_tmp

# Rsync project (exclude venv, node_modules, logs, pycache)
RSYNC_EXCLUDES=(".venv" "node_modules" "__pycache__" "logs" "mobile-app/.expo" ".git")
EXCLUDE_ARGS=()
for ex in "${RSYNC_EXCLUDES[@]}"; do
  EXCLUDE_ARGS+=("--exclude" "$ex")
done

echo "Syncing files..."
rsync -az --delete "${EXCLUDE_ARGS[@]}" ./ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_ROOT" || {
  echo "rsync failed"; exit 1;
}

echo "Setting permissions..."
ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "chmod -R 755 $REMOTE_ROOT; find $REMOTE_ROOT -type f -name '*.sh' -exec chmod +x {} +"

echo "Install dependencies remotely..."
ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_ROOT && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"

echo "Deployment complete."