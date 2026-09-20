param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference = "Stop"
$launch = Get-Content -LiteralPath (Join-Path $RunDirectory "launch.json") -Raw | ConvertFrom-Json
$process = Get-Process -Id $launch.pid -ErrorAction SilentlyContinue
$owned = $false
if ($process) {
 $owned = ($process.Path -eq $launch.executable -and $process.StartTime.ToUniversalTime() -eq [DateTime]::Parse($launch.process_start_time).ToUniversalTime())
}
@{checked_at=[DateTime]::UtcNow.ToString("o");pid=$launch.pid;owned_process_running=$owned;inspection="PID, executable path and process creation time; no process stopped"} | ConvertTo-Json -Compress
