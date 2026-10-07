#!/usr/bin/env bash
set -euo pipefail
KIT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v uv >/dev/null || { echo 'Install uv and Python 3.12; see documentazione/guida.md.' >&2; exit 1; }
command -v node >/dev/null || { echo 'Install Node.js 22 and npm.' >&2; exit 1; }
[[ "$(node --version)" == v22.* ]] || { echo 'Node.js 22 is required.' >&2; exit 1; }
if [[ -d "$KIT_DIR/.venv" ]]; then
  echo 'Environment already exists. Checking it; preserve installed MQT models before rebuilding.'
  "$KIT_DIR/.venv/bin/python" -B "$KIT_DIR/esperimento.py" verifica
  exit
fi
uv sync --frozen --python 3.12 --project "$KIT_DIR"
npm --prefix "$KIT_DIR/comune/framework/prototype/prompting/toon_runtime" ci --ignore-scripts
"$KIT_DIR/.venv/bin/python" -B "$KIT_DIR/esperimento.py" verifica
