param([Parameter(Mandatory=$true)][string]$ManifestPath)
$ErrorActionPreference = "Stop"
$plan = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
foreach ($job in $plan.jobs) {
    if (Test-Path -LiteralPath $job.output) { throw "Token output already exists: $($job.output)" }
    # Native Windows file streams need the extended UNC prefix for long artifact paths.
    $nativeInput = $job.input
    if ($nativeInput.StartsWith("//")) {
        $nativeInput = '\\?\UNC\' + $nativeInput.Substring(2).Replace('/', '\')
    }
    try {
        # Windows PowerShell treats native stderr warnings as ErrorRecords.
        # Preserve them in the log and use the actual process exit code.
        $ErrorActionPreference = "Continue"
        $tokens = & $plan.executable --model $plan.model --file $nativeInput --offline --no-bos --no-escape --ids 2> $job.stderr
        $tokenizerExit = $LASTEXITCODE
    } finally { $ErrorActionPreference = "Stop" }
    if ($tokenizerExit -ne 0) { throw "Tokenizer failed: $($job.input)" }
    $tokens | Set-Content -LiteralPath $job.output -Encoding UTF8
}
Write-Output ("Tokenized {0} files without inference." -f $plan.jobs.Count)
