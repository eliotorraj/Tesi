#! /usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "Errore: esegui questo script dentro Ubuntu/WSL, non da PowerShell." >&2
    exit 1
fi

if [[ -n "${MQT_VENV_PATH:-}" ]]; then
    VENV_PATH="$MQT_VENV_PATH"
elif [[ "$PROJECT_ROOT" == /mnt/* ]]; then
    echo "Avviso: il progetto si trova su un disco Windows montato in WSL ($PROJECT_ROOT)."
    echo "Creo l'ambiente virtuale nel filesystem Linux per evitare forti rallentamenti I/O."
    VENV_PATH="$HOME/.venvs/$(basename "$PROJECT_ROOT")"
else
    VENV_PATH="$PROJECT_ROOT/.venv"
fi

if ! command -v uv >/dev/null 2>&1; then
    if ! command -v curl >/dev/null 2>&1; then
        echo "Manca curl. Installalo con: sudo apt update && sudo apt install -y curl" >&2
        exit 1
    fi

    echo "Installo uv usando lo script ufficiale di Astral..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "Preparo Python 3.12 e l'ambiente virtuale $VENV_PATH..."
uv python install 3.12
export UV_PROJECT_ENVIRONMENT="$VENV_PATH"
uv sync --python 3.12

echo
"$VENV_PATH/bin/python" scripts/01_check_install.py

echo
echo "Setup completato. Per attivare manualmente l'ambiente:"
echo "  source $VENV_PATH/bin/activate"
