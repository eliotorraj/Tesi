param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference = "Stop"
Import-Module "$PSHOME\Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1"
if ($RunDirectory -notmatch '^[A-Za-z]:[\\/]') { throw "Native Windows path required" }
if (Test-Path -LiteralPath $RunDirectory) { throw "Use a new probe directory; results are preserved" }
New-Item -ItemType Directory -Path $RunDirectory | Out-Null
$path=Join-Path $RunDirectory "resources.jsonl"
$stream=[System.IO.StreamWriter]::new($path,$false,[System.Text.UTF8Encoding]::new($false))
$stream.AutoFlush=$true
$started=[DateTime]::UtcNow
try {
 for ($sampleIndex=0; $sampleIndex -lt 20; $sampleIndex++) {
  $stream.WriteLine((@{kind="storage_probe_not_experiment";sample=$sampleIndex;utc=[DateTime]::UtcNow.ToString("o")} | ConvertTo-Json -Compress))
  $stream.Flush()
  $stream.BaseStream.Flush($true)
 }
} finally { $stream.Dispose() }
@{kind="storage_probe_not_experiment";path=$path;durable_writes=20;elapsed_seconds=([DateTime]::UtcNow-$started).TotalSeconds;model_loaded=$false} | ConvertTo-Json -Compress
