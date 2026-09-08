#!/usr/bin/env bash
# Start both backends for local development (bash / macOS / Linux mirror of run.ps1).
#   - Node runner service on :8787
#   - FastAPI app on :8010
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

if [ ! -e "node_modules/elo-playground" ]; then
  echo "[playground] node_modules missing - running 'npm install' ..."
  npm install --no-audit --no-fund
fi

if [ ! -f ".env" ] && [ -f "env.sample" ]; then
  cp env.sample .env
  echo "[playground] created .env from env.sample"
fi

PY="python"
[ -x ".venv/bin/python" ] && PY=".venv/bin/python"
[ -x "../.venv/bin/python" ] && PY="../.venv/bin/python"

echo "[playground] starting Node runner on http://127.0.0.1:8787 ..."
node backend-node/src/server.mjs &
NODE_PID=$!
trap 'kill "$NODE_PID" 2>/dev/null || true' EXIT

sleep 1
echo "[playground] starting FastAPI app on http://127.0.0.1:8010 ..."
cd "$ROOT/backend-python"
exec "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8010
