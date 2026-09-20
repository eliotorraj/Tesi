param([Parameter(Mandatory=$true)][string]$ModelPath,[string]$RunRoot=(Join-Path $env:LOCALAPPDATA "QwenPrototype\runs"),[int]$Port=8089,[int]$Threads=6)
$ErrorActionPreference="Stop"
& (Join-Path $PSScriptRoot "verify-model.ps1") -ModelPath $ModelPath
if (Get-Process -Name llama-server -ErrorAction SilentlyContinue) { throw "Un server e gia attivo; fermarlo prima di avviarne un altro." }
$free=[long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
if ($free -lt 9GB) { throw "Servono almeno 9 GiB liberi prima della prova CPU. Disponibili: $free byte." }
$executable=Join-Path $PSScriptRoot "runtime\cpu\llama-server.exe"
if (-not(Test-Path -LiteralPath $executable)) { throw "Preparare runtime\cpu seguendo README.md." }
$directory=Join-Path $RunRoot ([DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss")+"-"+[guid]::NewGuid().ToString("N").Substring(0,8))
New-Item -ItemType Directory -Path $directory | Out-Null
$arguments=@("-m",('"'+$ModelPath+'"'),"--host","127.0.0.1","--port",$Port,"-c",16384,"--parallel",1,"--device","none","-ngl",0,"-fa","on","-ctk","q8_0","-ctv","q8_0","--threads",$Threads,"--threads-batch",$Threads,"--jinja","--no-context-shift","--cache-ram",0,"--metrics","--fit","off","--load-mode","none","-b",128,"-ub",64)
$process=$null
$stream=$null
$reason="initialization_failure"
try {
$process=Start-Process -FilePath $executable -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $directory "stdout.log") -RedirectStandardError (Join-Path $directory "stderr.log")
@{at=[DateTime]::UtcNow.ToString("o");pid=$process.Id;profile="laptop_cpu_technical";context=16384;model=$ModelPath;arguments=$arguments;available_before_bytes=$free;minimum_start_available_bytes=9GB;abort_below_available_bytes=2GB;gpu_used=$false;npu_used=$false;memory_budget_is_estimate=$true} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $directory "launch.json")
Write-Host "Server CPU: http://127.0.0.1:$Port - registri: $directory - Ctrl+C termina il server posseduto"
$stream=[System.IO.StreamWriter]::new((Join-Path $directory "resources.jsonl"),$true,[System.Text.UTF8Encoding]::new($false));$stream.AutoFlush=$true
$low=0;$reason="process_exit"
 while(-not $process.HasExited){
  $process.Refresh();$available=[long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
  @{at=[DateTime]::UtcNow.ToString("o");available_bytes=$available;working_set_bytes=$process.WorkingSet64;peak_working_set_bytes=$process.PeakWorkingSet64;private_bytes=$process.PrivateMemorySize64;cpu_seconds=$process.TotalProcessorTime.TotalSeconds} | ConvertTo-Json -Compress | ForEach-Object { $stream.WriteLine($_) }
  if($available -lt 2GB){$low++}else{$low=0}
  if($low -ge 3){$reason="available_ram_below_2_GiB";break}
  Start-Sleep -Seconds 1
 }
}finally{
 if($null -ne $process){if(-not $process.HasExited){$process.Kill()};$process.WaitForExit()}
 if($null -ne $stream){$stream.Dispose()}
 @{at=[DateTime]::UtcNow.ToString("o");reason=$reason;exit_code=$(if($null -ne $process){$process.ExitCode}else{$null})} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $directory "exit.json")
}
