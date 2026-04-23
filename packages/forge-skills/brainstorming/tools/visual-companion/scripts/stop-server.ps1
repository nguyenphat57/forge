param(
  [Parameter(Mandatory = $true)]
  [string]$SessionDir
)

$ErrorActionPreference = "Stop"
$StateDir = Join-Path $SessionDir "state"
$PidFile = Join-Path $StateDir "server.pid"
$LogFile = Join-Path $StateDir "server.log"

if (-not (Test-Path -LiteralPath $PidFile)) {
  '{"status":"not_running"}'
  exit 0
}

$ServerPid = [int](Get-Content -LiteralPath $PidFile -Raw)
try {
  Stop-Process -Id $ServerPid -ErrorAction SilentlyContinue
  for ($i = 0; $i -lt 20; $i++) {
    if (-not (Get-Process -Id $ServerPid -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Milliseconds 100
  }
  if (Get-Process -Id $ServerPid -ErrorAction SilentlyContinue) {
    Stop-Process -Id $ServerPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 100
  }
  if (Get-Process -Id $ServerPid -ErrorAction SilentlyContinue) {
    '{"status":"failed","error":"process still running"}'
    exit 1
  }
} finally {
  Remove-Item -LiteralPath $PidFile, $LogFile, "$LogFile.err" -Force -ErrorAction SilentlyContinue
}

$TempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$FullSession = [IO.Path]::GetFullPath($SessionDir)
if ($FullSession.StartsWith($TempRoot, [StringComparison]::OrdinalIgnoreCase) -and
    (Split-Path -Leaf $FullSession).StartsWith("forge-visual-companion-")) {
  Remove-Item -LiteralPath $FullSession -Recurse -Force -ErrorAction SilentlyContinue
}

'{"status":"stopped"}'
