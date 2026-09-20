param(
 [Parameter(Mandatory=$true)][string]$ModelPath,
 [Parameter(Mandatory=$true)][string]$ExpectedSha256,
 [Parameter(Mandatory=$true)][long]$ExpectedSize
)
$ErrorActionPreference = "Stop"
# WSL can inherit a PSModulePath from another PowerShell edition.
Import-Module "$PSHOME\Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1"
$started = [DateTime]::UtcNow
$item = Get-Item -LiteralPath $ModelPath
if ($item.Length -ne $ExpectedSize) { throw "Model weight size mismatch: $($item.Length) vs $ExpectedSize" }
$algorithm = [System.Security.Cryptography.SHA256]::Create()
$source = [System.IO.File]::OpenRead($ModelPath)
try { $observed = [BitConverter]::ToString($algorithm.ComputeHash($source)).Replace("-", "").ToLowerInvariant() }
finally { $source.Dispose(); $algorithm.Dispose() }
@{
 method="Windows .NET SHA256.ComputeHash streaming on the native model path";
 path=$item.FullName;sha256=$observed;size_bytes=$item.Length;
 expected_sha256=$ExpectedSha256;valid=($observed -eq $ExpectedSha256);
 started_at=$started.ToString("o");ended_at=[DateTime]::UtcNow.ToString("o");
 elapsed_seconds=([DateTime]::UtcNow-$started).TotalSeconds
} | ConvertTo-Json -Compress
if ($observed -ne $ExpectedSha256) { exit 1 }
