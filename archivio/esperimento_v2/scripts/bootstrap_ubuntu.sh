#! /usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "Error: run this script inside Ubuntu/WSL, not PowerShell." >&2
    exit 1
fi

if [[ -n "${MQT_VENV_PATH:-}" ]]; then
    VENV_PATH="$MQT_VENV_PATH"
elif [[ "$PROJECT_ROOT" == /mnt/* ]]; then
    echo "Warning: the project is on a Windows drive mounted in WSL ($PROJECT_ROOT)."
    echo "Creating the virtual environment on the Linux filesystem to avoid slow I/O."
    VENV_PATH="$HOME/.venvs/$(basename "$PROJECT_ROOT")"
else
    VENV_PATH="$PROJECT_ROOT/.venv"
fi

if ! command -v uv >/dev/null 2>&1; then
    if ! command -v curl >/dev/null 2>&1; then
        echo "curl is missing. Install it with: sudo apt update && sudo apt install -y curl" >&2
        exit 1
    fi

    echo "Installing uv with Astral's official script..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "Preparing Python 3.12 and virtual environment $VENV_PATH..."
uv python install 3.12
export UV_PROJECT_ENVIRONMENT="$VENV_PATH"
uv sync --frozen --python 3.12

echo
"$VENV_PATH/bin/python" scripts/01_check_install.py

echo
echo "Setup complete. To activate the environment manually:"
echo "  source $VENV_PATH/bin/activate"
