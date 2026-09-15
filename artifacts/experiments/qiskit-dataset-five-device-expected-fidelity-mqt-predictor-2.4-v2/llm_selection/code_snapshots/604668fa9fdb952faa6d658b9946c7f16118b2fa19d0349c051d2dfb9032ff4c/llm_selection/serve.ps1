param(
 [Parameter(Mandatory=$true)][string]$ModelPath,
 [Parameter(Mandatory=$true)][string]$RunDirectory,
 [int]$Context = 131072,
 [string]$CacheType = "q8_0",
 [string]$GpuLayers = "all",
 [int]$Port = 8089,
 [int]$Batch = 512,
 [int]$MicroBatch = 128,
 [long]$MinimumAvailableBytes = 1610612736,
 [int]$MaximumEdgeC = 95,
 [int]$MaximumHotspotC = 108,
 [int]$PauseHotspotC = 105,
 [int]$ResumeHotspotC = 100
)
$ErrorActionPreference = "Stop"
if ($MicroBatch -le 0 -or $Batch -lt $MicroBatch) { throw "Require 0 < MicroBatch <= Batch" }
if ($ResumeHotspotC -le 0 -or $ResumeHotspotC -ge $PauseHotspotC -or $PauseHotspotC -ge $MaximumHotspotC -or $MaximumHotspotC -gt 108) { throw "Require 0 < resume < pause < maximum hotspot <= 108 C" }
if ($MaximumEdgeC -le 0 -or $MaximumEdgeC -gt 95 -or $MinimumAvailableBytes -le 0) { throw "Invalid edge or RAM limit" }
if ($RunDirectory -notmatch '^[A-Za-z]:[\\\\/]') { throw "Server logs require a native Windows drive path. Start through llm_selection.controller." }
$workspace = Split-Path -Parent $PSScriptRoot
$experiment = Join-Path $workspace "artifacts\experiments\qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2\llm_selection"
$executable = Join-Path $experiment "runtime\b10930\llama-server.exe"
if (Get-Process -Name llama-server -ErrorAction SilentlyContinue) { throw "An existing llama-server must be inspected before starting another." }
if (Test-Path -LiteralPath $RunDirectory) { throw "Use a new run directory; logs are never overwritten." }
if (-not (Test-Path -LiteralPath $ModelPath)) { throw "Missing model file" }
Add-Type -Path (Join-Path $PSScriptRoot "AmdSensors.cs")
$sensors = [AmdSensors]::new()
$pauseExecutable = Join-Path $experiment "runtime\pstools\pssuspend64.exe"
$pauseProof = Get-Content -LiteralPath (Join-Path $experiment "runtime\pstools\verified.json") -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $pauseExecutable -Algorithm SHA256).Hash -ne $pauseProof.sha256) { throw "Pause utility hash mismatch" }
if (-not ($sensors.Read() | Where-Object { $null -ne $_.edge_c -and $null -ne $_.hotspot_c })) { $sensors.Dispose(); throw "No usable GPU temperature sensor" }
if ([long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024 -lt $MinimumAvailableBytes) { $sensors.Dispose(); throw "Insufficient free RAM before launch" }
New-Item -ItemType Directory -Path $RunDirectory | Out-Null
function Save-DurableJson($Path, $Value) {
 $bytes=[System.Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 20))
 $file=[System.IO.File]::Open($Path,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::Read)
 try { $file.Write($bytes,0,$bytes.Length); $file.Flush($true) } finally { $file.Dispose() }
}
$arguments = @("-m", ('"' + $ModelPath + '"'), "--host", "127.0.0.1", "--port", $Port, "-c", $Context,
 "--parallel", "1", "-ngl", $GpuLayers, "-fa", "on", "-ctk", $CacheType, "-ctv", $CacheType,
 "--threads", "6", "--threads-batch", "6", "--jinja", "--no-context-shift",
 "--cache-ram", "0", "--metrics", "--fit", "off", "--load-mode", "none", "-b", $Batch, "-ub", $MicroBatch)
$start = [DateTime]::UtcNow
$server = Start-Process -FilePath $executable -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $RunDirectory "stdout.log") -RedirectStandardError (Join-Path $RunDirectory "stderr.log")
$metadata = @{ started_at=$start.ToString("o"); pid=$server.Id; process_start_time=$server.StartTime.ToUniversalTime().ToString("o"); executable=$executable; model_path=$ModelPath; arguments=$arguments; context=$Context; cache_type=$CacheType; gpu_layers=$GpuLayers; port=$Port; memory_method="Windows Process WorkingSet64 and PeakWorkingSet64; private bytes; sampled each second"; gpu_memory_peak_bytes=$null; gpu_memory_missing_reason="No per-process hardware counter collected; allocation estimates remain in server log" }
$metadata.log_storage=@{directory=$RunDirectory;writer="Windows";durability="Flush(true) on native Windows filesystem; no WSL UNC write"}
$metadata.batch=$Batch
$metadata.micro_batch=$MicroBatch
$metadata.guards=@{minimum_available_bytes=$MinimumAvailableBytes;memory_consecutive_samples=3;maximum_edge_c=$MaximumEdgeC;maximum_hotspot_c=$MaximumHotspotC;missing_sensor_consecutive_samples=3;thresholds_are="User-requested experimental operating limits, not vendor specifications or a diagnosis"}
$metadata.measurement=@{interval_seconds=1;temperatures="AMD ADL PMLog, Celsius";gpu_memory="Windows GPUProcessMemory for owned server PID";power="AMD ASIC sensor W, not whole-PC power or energy"}
$metadata.Remove("gpu_memory_missing_reason")
$metadata.guards.pause_hotspot_c=$PauseHotspotC
$metadata.guards.resume_hotspot_c=$ResumeHotspotC
$metadata.pause_utility_sha256=$pauseProof.sha256
Save-DurableJson (Join-Path $RunDirectory "launch.json") $metadata
$metadata | ConvertTo-Json -Depth 10 -Compress
$stream = [System.IO.StreamWriter]::new((Join-Path $RunDirectory "resources.jsonl"), $true, [System.Text.UTF8Encoding]::new($false))
$stream.AutoFlush=$true
$lowMemory=0
$missingSensors=0
$abortReason=$null
$paused=$false
$pausedSince=$null
$pausedSeconds=0.0
$pauseCount=0
$monitorStage="initialization"
$lastDurableSampleUtc=$null
try {
 while (-not $server.HasExited) {
  $server.Refresh()
  $available=[long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
  $temperatures=@($sensors.Read())
  $usable=@($temperatures | Where-Object { $null -ne $_.edge_c -and $null -ne $_.hotspot_c })
  if ($usable.Count -eq 0) { $missingSensors++ } else { $missingSensors=0 }
  $gpuDedicated=$null
  $gpuShared=$null
  $gpuError=$null
  try {
   $counters=@(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory | Where-Object { $_.Name -like "pid_$($server.Id)_*" })
   if ($counters.Count -gt 0) {
    $gpuDedicated=[long]($counters | Measure-Object DedicatedUsage -Sum).Sum
    $gpuShared=[long]($counters | Measure-Object SharedUsage -Sum).Sum
   }
  } catch { $gpuError=$_.Exception.Message }
  $observedPauseSeconds=$pausedSeconds
  if ($paused) { $observedPauseSeconds+=([DateTime]::UtcNow-$pausedSince).TotalSeconds }
  $row=@{thermal_paused=$paused;thermal_paused_seconds=$observedPauseSeconds;thermal_pause_count=$pauseCount;utc=[DateTime]::UtcNow.ToString("o");pid=$server.Id;working_set_bytes=$server.WorkingSet64;peak_working_set_bytes=$server.PeakWorkingSet64;private_bytes=$server.PrivateMemorySize64;cpu_seconds=$server.TotalProcessorTime.TotalSeconds;system_available_bytes=$available;gpu_dedicated_bytes=$gpuDedicated;gpu_shared_bytes=$gpuShared;gpu_counter_error=$gpuError;gpu_sensors=$temperatures}
  $monitorStage="write_resource_sample"
  $stream.WriteLine(($row | ConvertTo-Json -Depth 10 -Compress))
  $stream.Flush()
  $monitorStage="flush_resource_sample_to_disk"
  $stream.BaseStream.Flush($true)
  $lastDurableSampleUtc=$row.utc
  $monitorStage="resource_guards_and_thermal_control"
  if ($available -lt $MinimumAvailableBytes) { $lowMemory++ } else { $lowMemory=0 }
  if ($lowMemory -ge 3) { $abortReason="available_ram_below_operational_limit" }
  if ($usable | Where-Object { $_.edge_c -ge $MaximumEdgeC -or $_.hotspot_c -ge $MaximumHotspotC }) { $abortReason="gpu_temperature_operational_limit" }
  if ($missingSensors -ge 3) { $abortReason="gpu_temperature_measurement_lost" }
  if ($abortReason) {
   Save-DurableJson (Join-Path $RunDirectory "resource_abort.json") @{at=[DateTime]::UtcNow.ToString("o");reason=$abortReason;last_sample=$row}
   if (-not $server.HasExited) { $server.Kill() }
   break
  }
  if (-not $paused -and ($usable | Where-Object { $_.hotspot_c -ge $PauseHotspotC })) {
   $pauseOutput=(& $pauseExecutable -accepteula -nobanner $server.Id 2>&1 | Out-String)
   if ($LASTEXITCODE -ne 0) { throw "Cannot pause owned server: $pauseOutput" }
   $paused=$true
   $pausedSince=[DateTime]::UtcNow
   $pauseCount++
   Save-DurableJson (Join-Path $RunDirectory ("pause_"+$pauseCount+".json")) @{at=$pausedSince.ToString("o");action="suspend_owned_inference_process";pid=$server.Id;output=$pauseOutput}
  } elseif ($paused -and $usable.Count -gt 0 -and -not ($usable | Where-Object { $_.hotspot_c -gt $ResumeHotspotC })) {
   $pauseOutput=(& $pauseExecutable -accepteula -nobanner -r $server.Id 2>&1 | Out-String)
   if ($LASTEXITCODE -ne 0) { throw "Cannot resume owned server: $pauseOutput" }
   $pausedSeconds+=([DateTime]::UtcNow-$pausedSince).TotalSeconds
   $paused=$false
   Save-DurableJson (Join-Path $RunDirectory ("resume_"+$pauseCount+".json")) @{at=[DateTime]::UtcNow.ToString("o");action="resume_owned_inference_process";pid=$server.Id;output=$pauseOutput;total_pause_seconds=$pausedSeconds}
  }
  Start-Sleep -Seconds 1
 }
} catch {
 $abortReason="monitor_failure"
 $rootError=$_.Exception.GetBaseException()
 Save-DurableJson (Join-Path $RunDirectory "monitor_error.json") @{at=[DateTime]::UtcNow.ToString("o");error=$_.Exception.Message;operation=$monitorStage;resource_path=(Join-Path $RunDirectory "resources.jsonl");last_durable_sample_utc=$lastDurableSampleUtc;exception_type=$rootError.GetType().FullName;hresult=$rootError.HResult}
 throw
} finally {
 if (-not $server.HasExited) { $server.Kill() }
 $server.WaitForExit()
 $stream.Dispose()
 $sensors.Dispose()
 $exitPausedSeconds=$pausedSeconds
 if ($paused) { $exitPausedSeconds+=([DateTime]::UtcNow-$pausedSince).TotalSeconds }
 Save-DurableJson (Join-Path $RunDirectory "exit.json") @{ended_at=[DateTime]::UtcNow.ToString("o");exit_code=$server.ExitCode;abort_reason=$abortReason;thermal_pause_count=$pauseCount;thermal_paused_seconds=$exitPausedSeconds;last_durable_sample_utc=$lastDurableSampleUtc}
}
