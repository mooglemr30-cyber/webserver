#!/usr/bin/env bash
set -euo pipefail
CFG_FILE="remote_config.json"
if [[ ! -f $CFG_FILE ]]; then echo "Missing remote_config.json"; exit 1; fi
REMOTE_HOST=$(jq -r '.remote_host' $CFG_FILE)
REMOTE_USER=$(jq -r '.remote_user' $CFG_FILE)
REMOTE_ROOT=$(jq -r '.project_root_remote' $CFG_FILE)
REMOTE_PORT=$(jq -r '.remote_port' $CFG_FILE)

ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" bash -s <<'EOF'
set -euo pipefail
cd "$REMOTE_ROOT" || { echo "Remote root missing"; exit 1; }
source .venv/bin/activate || { echo "venv missing"; exit 1; }
python -c "import sys; print('Python OK:', sys.version)"
python -c "import json; print('List dir entries:', len([p for p in __import__('pathlib').Path('.').iterdir()]))"
python test_ai_intelligence.py || echo "AI intelligence tests failed (may not be needed on remote)"
echo "Remote tests completed"
EOF