param([Parameter(Mandatory=$true)][string]$RunDirectory,[Parameter(Mandatory=$true)][string]$Reason)
$ErrorActionPreference="Stop"
$record=Get-Content -LiteralPath (Join-Path $RunDirectory "launch.json") -Raw | ConvertFrom-Json
$owned=Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if ($null -eq $owned) { Write-Output "Owned process already exited"; exit 0 }
if ($owned.ProcessName -ne "llama-server" -or $owned.Path -ne $record.executable -or [Math]::Abs(($owned.StartTime.ToUniversalTime()-([DateTime]$record.process_start_time).ToUniversalTime()).TotalSeconds) -ge 1) { throw "Process identity mismatch; not stopped" }
@{at=[DateTime]::UtcNow.ToString("o");reason=$Reason;pid=$owned.Id;working_set_bytes=$owned.WorkingSet64;private_bytes=$owned.PrivateMemorySize64} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RunDirectory "stop_requested.json") -Encoding UTF8
Stop-Process -Id $owned.Id
Write-Output "Stopped owned llama-server"
