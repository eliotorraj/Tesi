param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference="Stop"
$launch=Get-Content -LiteralPath (Join-Path $RunDirectory "launch.json") -Raw | ConvertFrom-Json
$destination=Join-Path $RunDirectory "gpu_resources.jsonl"
$stream=[IO.StreamWriter]::new($destination,$true,[Text.UTF8Encoding]::new($false))
$stream.AutoFlush=$true
try {
 while ($process=Get-Process -Id $launch.pid -ErrorAction SilentlyContinue) {
  if ($process.Path -ne $launch.executable -or [Math]::Abs(($process.StartTime.ToUniversalTime()-([DateTime]$launch.process_start_time).ToUniversalTime()).TotalSeconds) -ge 1) { throw "Process identity changed" }
  $gpu=Get-CimInstance -ClassName Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like ("pid_"+$launch.pid+"_*") }
  $samples=@($gpu | ForEach-Object { @{name=$_.Name;dedicated_bytes=[long]$_.DedicatedUsage;shared_bytes=[long]$_.SharedUsage;committed_bytes=[long]$_.TotalCommitted} })
  $row=@{utc=[DateTime]::UtcNow.ToString("o");pid=$launch.pid;method="Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory";samples=$samples;missing=($samples.Count -eq 0)}
  $stream.WriteLine(($row | ConvertTo-Json -Depth 5 -Compress))
  Start-Sleep -Seconds 2
 }
} finally { $stream.Dispose() }
