param(
  [string]$ProjectDir = "",
  [string]$HostName = "127.0.0.1",
  [string]$UrlHost = "",
  [switch]$Foreground,
  [switch]$Background
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $UrlHost) {
  if ($HostName -eq "127.0.0.1" -or $HostName -eq "localhost") { $UrlHost = "localhost" }
  else { $UrlHost = $HostName }
}

$SessionId = "$PID-$(Get-Date -Format yyyyMMddHHmmss)"
if ($ProjectDir) {
  $SessionDir = Join-Path $ProjectDir ".forge-artifacts\visual-companion\$SessionId"
} else {
  $SessionDir = Join-Path ([IO.Path]::GetTempPath()) "forge-visual-companion-$SessionId"
}

$StateDir = Join-Path $SessionDir "state"
$PidFile = Join-Path $StateDir "server.pid"
$LogFile = Join-Path $StateDir "server.log"
$InfoFile = Join-Path $StateDir "server-info"
New-Item -ItemType Directory -Force -Path (Join-Path $SessionDir "content"), $StateDir | Out-Null

$OwnerPid = $PID
try {
  $ParentPid = (Get-CimInstance Win32_Process -Filter "ProcessId = $PID").ParentProcessId
  if ($ParentPid) { $OwnerPid = $ParentPid }
} catch {
  $OwnerPid = $PID
}

$env:FORGE_VISUAL_COMPANION_DIR = $SessionDir
$env:FORGE_VISUAL_COMPANION_HOST = $HostName
$env:FORGE_VISUAL_COMPANION_URL_HOST = $UrlHost
$env:FORGE_VISUAL_COMPANION_OWNER_PID = [string]$OwnerPid

if ($Foreground) {
  Set-Content -LiteralPath $PidFile -Value $PID -Encoding UTF8
  Push-Location $ScriptDir
  try { & node server.cjs }
  finally { Pop-Location }
  exit $LASTEXITCODE
}

$process = Start-Process -FilePath "node" -ArgumentList @("server.cjs") -WorkingDirectory $ScriptDir -WindowStyle Hidden -PassThru
Set-Content -LiteralPath $PidFile -Value $process.Id -Encoding UTF8

for ($i = 0; $i -lt 50; $i++) {
  if (Test-Path -LiteralPath $InfoFile) {
    $line = Get-Content -LiteralPath $InfoFile -Raw
    if ($process.HasExited) {
      '{"error":"Server started then exited. Retry with -Foreground."}'
      exit 1
    }
    $line.Trim()
    exit 0
  }
  Start-Sleep -Milliseconds 100
}

'{"error":"Server failed to start within 5 seconds"}'
exit 1
