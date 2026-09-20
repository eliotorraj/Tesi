param(
 [Parameter(Mandatory=$true)][string]$Label,
 [Parameter(Mandatory=$true)][ValidateSet("qwen","phi","gemma")][string]$Model,
 [ValidateSet("BF16","Q8_0")][string]$Precision="Q8_0",
 [int]$Context=131072,
 [string]$CacheType="q8_0",
 [string]$GpuLayers="all",
 [string]$Circuit="dj_indep_tket_2",
 [int]$Timeout=7200
)
$ErrorActionPreference="Stop"
if ($Label -notmatch '^[a-z0-9_-]+$' -or $Circuit -notmatch '^[a-zA-Z0-9_-]+$') { throw "Invalid label or circuit identifier" }
$workspace=Split-Path -Parent $PSScriptRoot
$output=Join-Path $workspace "artifacts\experiments\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\llm_selection\background"
$directory=Join-Path $output $Label
if(Test-Path -LiteralPath $directory) { throw "Use a new execution label; existing logs must be preserved" }
New-Item -ItemType Directory -Path $directory | Out-Null
$arguments=@("-d","Ubuntu","--cd","/home/elio/Tesi-mqt-2.4-v2","--",".venv/bin/python","-m","llm_selection.controller",
 "--technical","--model",$Model,"--label",$Label,"--precision",$Precision,"--context",$Context,
 "--cache-type",$CacheType,"--gpu-layers",$GpuLayers,"--circuit",$Circuit,"--technical-timeout",$Timeout)
$process=Start-Process -FilePath "wsl.exe" -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $directory "stdout.log") -RedirectStandardError (Join-Path $directory "stderr.log")
@{at=[DateTime]::UtcNow.ToString("o");pid=$process.Id;arguments=$arguments;phase="technical_train_only";directory=$directory} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $directory "launch.json") -Encoding UTF8
Write-Output ("Started technical controller PID "+$process.Id+"; logs: "+$directory)
