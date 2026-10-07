#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v node >/dev/null || { echo "Install Node.js 22 and npm; see docs/guida_passo_passo.md." >&2; exit 1; }
[[ "$(node --version)" == v22.* ]] || { echo "Node.js 22 is required." >&2; exit 1; }
command -v npm >/dev/null || { echo "Install npm with Node.js 22." >&2; exit 1; }
if [[ ! -d .venv ]]; then
  if command -v uv >/dev/null; then
    uv venv --python 3.12 .venv
  else
    command -v python3.12 >/dev/null || { echo "Install uv or Python 3.12 with venv." >&2; exit 1; }
    python3.12 -m venv .venv
  fi
fi
[[ -x .venv/bin/python ]] || { echo "Non-Linux or incomplete environment: preserve this directory and prepare a new one." >&2; exit 1; }
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3,12), "Python 3.12 is required"'
if command -v uv >/dev/null; then
  uv pip install --python .venv/bin/python -r requirements.txt
else
  .venv/bin/python -m pip install -r requirements.txt
fi
npm ci --ignore-scripts --no-audit --no-fund --prefix prototype/prompting/toon_runtime
.venv/bin/python -B app.py prepare
.venv/bin/python -B app.py check
