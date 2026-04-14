#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-10000}"
export FEDSEG_MODEL_PATH="${FEDSEG_MODEL_PATH:-/app/model/model.pt}"
export FEDSEG_API_URL="${FEDSEG_API_URL:-${FEDSEG_INTERNAL_API_URL:-http://127.0.0.1:8000}}"
if [[ ! -f "${FEDSEG_MODEL_PATH}" ]]; then
  echo "CRITICAL WARNING: Model file missing at ${FEDSEG_MODEL_PATH}!" >&2
else
  echo "Found baked-in model at ${FEDSEG_MODEL_PATH}"
fi

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "${API_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

streamlit run frontend/app.py \
  --server.address 0.0.0.0 \
  --server.port "${PORT}"
