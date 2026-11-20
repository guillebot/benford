#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if command -v uv >/dev/null 2>&1; then
  uv venv .venv 2>/dev/null || true
  uv pip install -r requirements.txt
  . .venv/bin/activate
else
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -q -r requirements.txt
fi
exec streamlit run app.py --server.port 43123 --server.address 127.0.0.1