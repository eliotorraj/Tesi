param([ValidateSet("cpu","desktop")][string]$RuntimeProfile="cpu",[switch]$DownloadRuntime)
$ErrorActionPreference="Stop"
Set-Location -LiteralPath $PSScriptRoot
if (-not(Get-Command py -ErrorAction SilentlyContinue)) { throw "Install Python 3.12 for Windows, including the py launcher." }
& py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)"
if($LASTEXITCODE -ne 0){throw "Python 3.12 is required"}
if(-not(Get-Command node -ErrorAction SilentlyContinue)){throw "Install Node.js 22 from nodejs.org."}
$nodeVersion=(& node --version)
if($nodeVersion -notlike "v22.*"){throw "Node.js 22 is required; detected $nodeVersion"}
if(-not(Test-Path -LiteralPath ".venv\Scripts\python.exe")){& py -3.12 -m venv .venv;if($LASTEXITCODE -ne 0){throw "Environment creation failed"}}
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if($LASTEXITCODE -ne 0){throw "Dependency installation failed"}
# The clone contains the codec lockfile, not node_modules.
if(-not(Get-Command npm.cmd -ErrorAction SilentlyContinue)){throw "Install npm with Node.js 22."}
& npm.cmd ci --ignore-scripts --no-audit --no-fund --prefix (Join-Path $PSScriptRoot "prototype\prompting\toon_runtime")
if($LASTEXITCODE -ne 0){throw "TOON codec installation failed"}
$destination=Join-Path $PSScriptRoot "runtime\$RuntimeProfile"
if(-not(Test-Path -LiteralPath (Join-Path $destination "llama-server.exe"))){
 if(-not $DownloadRuntime){throw "Runtime missing. Repeat with -DownloadRuntime or copy it from an existing prepared directory."}
 $suffix=if($RuntimeProfile -eq "cpu"){"cpu"}else{"vulkan"}
 $url="https://github.com/ggml-org/llama.cpp/releases/download/b10930/llama-b10930-bin-win-$suffix-x64.zip"
 $download=Join-Path $PSScriptRoot ("runtime\download-"+[guid]::NewGuid().ToString("N"))
 New-Item -ItemType Directory -Path $download | Out-Null
 $archive=Join-Path $download "llama.zip"
 Invoke-WebRequest -Uri $url -OutFile $archive
 Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $download "expanded")
 $binary=Get-ChildItem -LiteralPath (Join-Path $download "expanded") -Recurse -Filter llama-server.exe | Select-Object -First 1
 if(-not $binary){throw "llama-server.exe is missing from the package"}
 New-Item -ItemType Directory -Path $destination -Force | Out-Null
 Copy-Item -Path (Join-Path $binary.Directory.FullName "*") -Destination $destination
 @{url=$url;sha256=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash;at=[DateTime]::UtcNow.ToString("o")} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destination "download.json")
}
$serverVersion=(& (Join-Path $destination "llama-server.exe") --version 2>&1 | Out-String)
if($serverVersion -notmatch "10930"){throw "Runtime differs from llama.cpp b10930"}
if($RuntimeProfile -eq "desktop" -and -not(Test-Path -LiteralPath "runtime\pstools\pssuspend64.exe")){
 if(-not $DownloadRuntime){throw "Copy runtime\pstools or use -DownloadRuntime"}
 New-Item -ItemType Directory -Path "runtime\pstools" -Force | Out-Null
 Invoke-WebRequest -Uri "https://download.sysinternals.com/files/PSTools.zip" -OutFile "runtime\pstools\pstools.zip"
 Expand-Archive -LiteralPath "runtime\pstools\pstools.zip" -DestinationPath "runtime\pstools\extracted"
 Copy-Item -LiteralPath "runtime\pstools\extracted\pssuspend64.exe" -Destination "runtime\pstools\pssuspend64.exe"
 Copy-Item -LiteralPath "data\pstools_verified.json" -Destination "runtime\pstools\verified.json"
 $proof=Get-Content -LiteralPath "runtime\pstools\verified.json" -Raw | ConvertFrom-Json
 if((Get-FileHash -LiteralPath "runtime\pstools\pssuspend64.exe" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.sha256){throw "PsSuspend version changed; use the previously verified copy without updating the seal."}
}
& .\.venv\Scripts\python.exe app.py prepare
if($LASTEXITCODE -ne 0){throw "Train/RAG preparation failed"}
Write-Host "Preparation complete. Weights are not downloaded: copy them to the laptop and pass -ModelPath to the server."
