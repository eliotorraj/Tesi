param([Parameter(Mandatory=$true)][string]$ModelPath)
$ErrorActionPreference="Stop"
$config=Get-Content -LiteralPath (Join-Path $PSScriptRoot "config.json") -Raw | ConvertFrom-Json
$item=Get-Item -LiteralPath $ModelPath
if ($item.Length -ne $config.profile.artifact.size_bytes) { throw "Dimensione GGUF diversa da Qwen3.5-4B Q8_0 selezionato" }
Write-Host "Verifica SHA256 dei 4,48 GB del modello in corso..."
$hash=(Get-FileHash -LiteralPath $ModelPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne $config.profile.artifact.gguf_sha256) { throw "SHA256 dei pesi diverso da quello selezionato" }
Write-Host "Pesi Qwen Q8_0 verificati."
