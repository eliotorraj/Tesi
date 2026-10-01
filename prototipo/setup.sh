#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v node >/dev/null || { echo "Installare Node.js 22 e npm; vedere docs/guida_passo_passo.md." >&2; exit 1; }
[[ "$(node --version)" == v22.* ]] || { echo "Richiesto Node.js 22." >&2; exit 1; }
command -v npm >/dev/null || { echo "Installare npm insieme a Node.js 22." >&2; exit 1; }
if [[ ! -d .venv ]]; then
  if command -v uv >/dev/null; then
    uv venv --python 3.12 .venv
  else
    command -v python3.12 >/dev/null || { echo "Installare uv oppure Python 3.12 con venv." >&2; exit 1; }
    python3.12 -m venv .venv
  fi
fi
[[ -x .venv/bin/python ]] || { echo "Ambiente non Linux o incompleto: conservare la cartella e prepararne una nuova." >&2; exit 1; }
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3,12), "Richiesto Python 3.12"'
if command -v uv >/dev/null; then
  uv pip install --python .venv/bin/python -r requirements.txt
else
  .venv/bin/python -m pip install -r requirements.txt
fi
npm ci --ignore-scripts --no-audit --no-fund --prefix prototype/prompting/toon_runtime
.venv/bin/python -B app.py prepare
.venv/bin/python -B app.py check
