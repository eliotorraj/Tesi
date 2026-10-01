#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v node >/dev/null || { echo "Installare Node.js 22 e npm." >&2; exit 1; }
[[ "$(node --version)" == v22.* ]] || { echo "Richiesto Node.js 22." >&2; exit 1; }
command -v npm >/dev/null || { echo "Installare npm insieme a Node.js 22." >&2; exit 1; }
npm ci --ignore-scripts --no-audit --no-fund --prefix prototype/prompting/toon_runtime
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py prepare
