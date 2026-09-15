param(
 [Parameter(Mandatory=$true)][string]$ModelPath,
 [Parameter(Mandatory=$true)][string]$RunDirectory,
 [int]$Context = 131072,
 [string]$CacheType = "f16",
 [string]$GpuLayers = "all",
 [int]$Port = 8089
)
$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot
$experiment = Join-Path $workspace "artifacts\experiments\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\llm_selection"
$executable = Join-Path $experiment "runtime\b10930\llama-server.exe"
if (Get-Process -Name llama-server -ErrorAction SilentlyContinue) { throw "An existing llama-server must be inspected before starting another." }
if (Test-Path -LiteralPath $RunDirectory) { throw "Use a new run directory; logs are never overwritten." }
New-Item -ItemType Directory -Path $RunDirectory | Out-Null
$arguments = @("-m", ('"' + $ModelPath + '"'), "--host", "127.0.0.1", "--port", $Port, "-c", $Context,
 "--parallel", "1", "-ngl", $GpuLayers, "-fa", "on", "-ctk", $CacheType, "-ctv", $CacheType,
 "--threads", "6", "--threads-batch", "6", "--jinja", "--no-context-shift",
 "--cache-ram", "0", "--metrics", "--fit", "off", "-b", "512", "-ub", "256")
$start = [DateTime]::UtcNow
$server = Start-Process -FilePath $executable -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $RunDirectory "stdout.log") -RedirectStandardError (Join-Path $RunDirectory "stderr.log")
$metadata = @{ started_at=$start.ToString("o"); pid=$server.Id; process_start_time=$server.StartTime.ToUniversalTime().ToString("o"); executable=$executable; model_path=$ModelPath; arguments=$arguments; context=$Context; cache_type=$CacheType; gpu_layers=$GpuLayers; port=$Port; memory_method="Windows Process WorkingSet64 and PeakWorkingSet64; private bytes; sampled each second"; gpu_memory_peak_bytes=$null; gpu_memory_missing_reason="No per-process hardware counter collected; allocation estimates remain in server log" }
$metadata | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $RunDirectory "launch.json") -Encoding UTF8
$metadata | ConvertTo-Json -Depth 10 -Compress
$stream = [System.IO.StreamWriter]::new((Join-Path $RunDirectory "resources.jsonl"), $true, [System.Text.UTF8Encoding]::new($false))
$stream.AutoFlush=$true
try {
 while (-not $server.HasExited) {
  $server.Refresh()
  $os = Get-CimInstance Win32_OperatingSystem
  @{utc=[DateTime]::UtcNow.ToString("o"); pid=$server.Id; working_set_bytes=$server.WorkingSet64; peak_working_set_bytes=$server.PeakWorkingSet64; private_bytes=$server.PrivateMemorySize64; cpu_seconds=$server.TotalProcessorTime.TotalSeconds; system_available_bytes=[long]$os.FreePhysicalMemory*1024} | ConvertTo-Json -Compress | ForEach-Object { $stream.WriteLine($_) }
  Start-Sleep -Seconds 1
 }
} finally {
 $stream.Dispose()
 @{ended_at=[DateTime]::UtcNow.ToString("o");exit_code=$server.ExitCode} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RunDirectory "exit.json") -Encoding UTF8
}
