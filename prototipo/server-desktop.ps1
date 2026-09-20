param([Parameter(Mandatory=$true)][string]$ModelPath,[string]$RunRoot=(Join-Path $env:LOCALAPPDATA "QwenPrototype\runs"),[int]$Port=8089)
$ErrorActionPreference="Stop"
& (Join-Path $PSScriptRoot "verify-model.ps1") -ModelPath $ModelPath
$run=Join-Path $RunRoot ([DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss")+"-"+[guid]::NewGuid().ToString("N").Substring(0,8))
& (Join-Path $PSScriptRoot "server-desktop-internal.ps1") -ModelPath $ModelPath -RunDirectory $run -Context 60000 -CacheType q8_0 -GpuLayers all -Port $Port -Batch 512 -MicroBatch 128 -MinimumAvailableBytes 1073741824
