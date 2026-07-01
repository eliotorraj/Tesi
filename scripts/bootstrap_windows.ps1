[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error @"
uv non è installato. Installalo dal terminale PowerShell con il comando ufficiale:
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
Poi chiudi e riapri PowerShell e rilancia questo script.
"@
}

Write-Host "Preparo Python 3.12 e l'ambiente virtuale .venv..."
uv python install 3.12
uv sync --python 3.12

Write-Host ""
uv run python scripts/01_check_install.py

Write-Host ""
Write-Host "Setup completato. Per attivare manualmente l'ambiente:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
