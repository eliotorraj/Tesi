param([ValidateSet("cpu","desktop")][string]$RuntimeProfile="cpu",[switch]$DownloadRuntime)
$ErrorActionPreference="Stop"
Set-Location -LiteralPath $PSScriptRoot
if (-not(Get-Command py -ErrorAction SilentlyContinue)) { throw "Installare Python 3.12 per Windows, incluso il launcher py." }
& py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)"
if($LASTEXITCODE -ne 0){throw "Python 3.12 richiesto"}
if(-not(Get-Command node -ErrorAction SilentlyContinue)){throw "Installare Node.js 22 dal sito nodejs.org."}
$nodeVersion=(& node --version)
if($nodeVersion -notlike "v22.*"){throw "Richiesto Node.js 22; rilevato $nodeVersion"}
if(-not(Test-Path -LiteralPath ".venv\Scripts\python.exe")){& py -3.12 -m venv .venv;if($LASTEXITCODE -ne 0){throw "Creazione ambiente fallita"}}
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if($LASTEXITCODE -ne 0){throw "Installazione dipendenze fallita"}
$destination=Join-Path $PSScriptRoot "runtime\$RuntimeProfile"
if(-not(Test-Path -LiteralPath (Join-Path $destination "llama-server.exe"))){
 if(-not $DownloadRuntime){throw "Runtime assente. Ripetere con -DownloadRuntime, oppure copiare runtime dalla cartella gia preparata."}
 $suffix=if($RuntimeProfile -eq "cpu"){"cpu"}else{"vulkan"}
 $url="https://github.com/ggml-org/llama.cpp/releases/download/b10930/llama-b10930-bin-win-$suffix-x64.zip"
 $download=Join-Path $PSScriptRoot ("runtime\download-"+[guid]::NewGuid().ToString("N"))
 New-Item -ItemType Directory -Path $download | Out-Null
 $archive=Join-Path $download "llama.zip"
 Invoke-WebRequest -Uri $url -OutFile $archive
 Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $download "expanded")
 $binary=Get-ChildItem -LiteralPath (Join-Path $download "expanded") -Recurse -Filter llama-server.exe | Select-Object -First 1
 if(-not $binary){throw "llama-server.exe assente nel pacchetto"}
 New-Item -ItemType Directory -Path $destination -Force | Out-Null
 Copy-Item -Path (Join-Path $binary.Directory.FullName "*") -Destination $destination
 @{url=$url;sha256=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash;at=[DateTime]::UtcNow.ToString("o")} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destination "download.json")
}
$serverVersion=(& (Join-Path $destination "llama-server.exe") --version 2>&1 | Out-String)
if($serverVersion -notmatch "10930"){throw "Runtime diverso da llama.cpp b10930"}
if($RuntimeProfile -eq "desktop" -and -not(Test-Path -LiteralPath "runtime\pstools\pssuspend64.exe")){
 if(-not $DownloadRuntime){throw "Copiare runtime\pstools oppure usare -DownloadRuntime"}
 New-Item -ItemType Directory -Path "runtime\pstools" -Force | Out-Null
 Invoke-WebRequest -Uri "https://download.sysinternals.com/files/PSTools.zip" -OutFile "runtime\pstools\pstools.zip"
 Expand-Archive -LiteralPath "runtime\pstools\pstools.zip" -DestinationPath "runtime\pstools\extracted"
 Copy-Item -LiteralPath "runtime\pstools\extracted\pssuspend64.exe" -Destination "runtime\pstools\pssuspend64.exe"
 Copy-Item -LiteralPath "data\pstools_verified.json" -Destination "runtime\pstools\verified.json"
 $proof=Get-Content -LiteralPath "runtime\pstools\verified.json" -Raw | ConvertFrom-Json
 if((Get-FileHash -LiteralPath "runtime\pstools\pssuspend64.exe" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.sha256){throw "Versione PsSuspend cambiata; usare la copia gia verificata, non aggiornare il sigillo."}
}
& .\.venv\Scripts\python.exe app.py prepare
if($LASTEXITCODE -ne 0){throw "Preparazione train/RAG fallita"}
Write-Host "Preparazione completata. I pesi non sono scaricati: copiarli sul laptop e passare -ModelPath al server."
