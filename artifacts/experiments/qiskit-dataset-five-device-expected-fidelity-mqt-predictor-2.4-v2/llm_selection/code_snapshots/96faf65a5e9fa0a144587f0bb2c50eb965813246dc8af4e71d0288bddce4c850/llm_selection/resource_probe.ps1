param()
$ErrorActionPreference = "Stop"
Add-Type -Path (Join-Path $PSScriptRoot "AmdSensors.cs")
$probeSensors = [AmdSensors]::new()
try {
 $probeRows = @($probeSensors.Read())
 $probeAvailable = [long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1024
 @{at=[DateTime]::UtcNow.ToString("o");system_available_bytes=$probeAvailable;gpu_sensors=$probeRows} | ConvertTo-Json -Depth 10 -Compress
} finally { $probeSensors.Dispose() }
