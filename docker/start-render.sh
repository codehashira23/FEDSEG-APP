#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-10000}"
export FEDSEG_MODEL_PATH="${FEDSEG_MODEL_PATH:-/app/model/model.pt}"
export FEDSEG_API_URL="${FEDSEG_API_URL:-${FEDSEG_INTERNAL_API_URL:-http://127.0.0.1:8000}}"
export FEDSEG_MODEL_DOWNLOAD_URL="${FEDSEG_MODEL_DOWNLOAD_URL:-}"
export FEDSEG_MODEL_GDRIVE_ID="${FEDSEG_MODEL_GDRIVE_ID:-}"

mkdir -p "$(dirname "${FEDSEG_MODEL_PATH}")"

if [[ ! -f "${FEDSEG_MODEL_PATH}" ]]; then
  if [[ -n "${FEDSEG_MODEL_GDRIVE_ID}" ]]; then
    echo "Downloading model to ${FEDSEG_MODEL_PATH} from Google Drive"
    gdown --id "${FEDSEG_MODEL_GDRIVE_ID}" -O "${FEDSEG_MODEL_PATH}"
  elif [[ -n "${FEDSEG_MODEL_DOWNLOAD_URL}" ]]; then
    echo "Downloading model to ${FEDSEG_MODEL_PATH}"
    curl -L --fail --output "${FEDSEG_MODEL_PATH}" "${FEDSEG_MODEL_DOWNLOAD_URL}"
  else
    echo "Model file missing at ${FEDSEG_MODEL_PATH} and neither FEDSEG_MODEL_DOWNLOAD_URL nor FEDSEG_MODEL_GDRIVE_ID is set." >&2
    exit 1
  fi
else
  echo "Using existing model at ${FEDSEG_MODEL_PATH}"
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
