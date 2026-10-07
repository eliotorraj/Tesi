param([Parameter(Mandatory=$true)][string]$ModelPath)
$ErrorActionPreference="Stop"
$config=Get-Content -LiteralPath (Join-Path $PSScriptRoot "config.json") -Raw | ConvertFrom-Json
$item=Get-Item -LiteralPath $ModelPath
if ($item.Length -ne $config.profile.artifact.size_bytes) { throw "GGUF size differs from the selected Qwen3.5-4B Q8_0" }
Write-Host "Checking SHA256 of the 4.48 GB model..."
$hash=(Get-FileHash -LiteralPath $ModelPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne $config.profile.artifact.gguf_sha256) { throw "Weight SHA256 differs from the selected artifact" }
Write-Host "Qwen Q8_0 weights verified."
