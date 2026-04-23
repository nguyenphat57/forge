[CmdletBinding()]
param(
    [switch]$Persist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Set-ForgeUtf8Session {
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)

    try {
        & "$env:SystemRoot\System32\chcp.com" 65001 > $null
    }
    catch {
        Write-Verbose "Unable to switch the active console code page to 65001."
    }

    [Console]::InputEncoding = $utf8NoBom
    [Console]::OutputEncoding = $utf8NoBom
    $global:OutputEncoding = $utf8NoBom
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
}

function Add-ForgeUtf8ProfileBlock {
    $profilePath = $PROFILE.CurrentUserAllHosts
    $profileDir = Split-Path -Parent $profilePath

    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }

    $marker = "# Forge Codex UTF-8 defaults"
    $block = @'
# Forge Codex UTF-8 defaults
$ForgeCodexUtf8 = [System.Text.UTF8Encoding]::new($false)
try {
    & "$env:SystemRoot\System32\chcp.com" 65001 > $null
} catch {
}
[Console]::InputEncoding = $ForgeCodexUtf8
[Console]::OutputEncoding = $ForgeCodexUtf8
$OutputEncoding = $ForgeCodexUtf8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
'@

    $existing = ""
    if (Test-Path $profilePath) {
        $existing = Get-Content -Raw $profilePath
    }

    if ($existing -match [regex]::Escape($marker)) {
        return $profilePath
    }

    $prefix = if ($existing.Trim().Length -gt 0) { "`r`n" } else { "" }
    Add-Content -Path $profilePath -Value ($prefix + $block + "`r`n") -Encoding utf8
    return $profilePath
}

Set-ForgeUtf8Session

$lines = @(
    "Forge Codex UTF-8 session defaults applied.",
    "- Code page: 65001 requested",
    "- Console input/output encoding: UTF-8",
    "- PYTHONUTF8=1",
    "- PYTHONIOENCODING=utf-8"
)

if ($Persist) {
    $profilePath = Add-ForgeUtf8ProfileBlock
    $lines += "- Persisted to PowerShell profile: $profilePath"
}
else {
    $lines += "- Persisted to PowerShell profile: no"
}

$lines -join "`n"
