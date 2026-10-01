#!/usr/bin/env bash
set -euo pipefail
KIT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v uv >/dev/null || { echo 'Installare uv e Python 3.12; vedere documentazione/guida.md.' >&2; exit 1; }
command -v node >/dev/null || { echo 'Installare Node.js 22 e npm.' >&2; exit 1; }
[[ "$(node --version)" == v22.* ]] || { echo 'Richiesto Node.js 22.' >&2; exit 1; }
if [[ -d "$KIT_DIR/.venv" ]]; then
  echo 'Ambiente già presente. Verifico; per ricrearlo conservare prima i modelli MQT runtime.'
  "$KIT_DIR/.venv/bin/python" -B "$KIT_DIR/esperimento.py" verifica
  exit
fi
uv sync --frozen --python 3.12 --project "$KIT_DIR"
npm --prefix "$KIT_DIR/comune/framework/prototype/prompting/toon_runtime" ci --ignore-scripts
"$KIT_DIR/.venv/bin/python" -B "$KIT_DIR/esperimento.py" verifica
