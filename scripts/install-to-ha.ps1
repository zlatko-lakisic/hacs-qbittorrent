# Install qBittorrent Plus integration into a Home Assistant config folder.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/install-to-ha.ps1 -ConfigRoot '\\your-ha-host\config'
#   powershell -ExecutionPolicy Bypass -File scripts/install-to-ha.ps1 -ConfigRoot 'C:\path\to\homeassistant\config'

param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigRoot
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repoRoot 'custom_components\qbittorrent_plus'
$dstRoot = Join-Path $ConfigRoot 'custom_components'
$dst = Join-Path $dstRoot 'qbittorrent_plus'

if (-not (Test-Path $src)) {
    throw "Integration source not found: $src"
}
if (-not (Test-Path $ConfigRoot)) {
    throw "Home Assistant config path not reachable: $ConfigRoot"
}

New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Path (Join-Path $src '*') -Destination $dst -Recurse -Force

Write-Host "Installed qBittorrent Plus integration to $dst"
Write-Host "Restart Home Assistant, then: Settings -> Devices & services -> Add integration -> qBittorrent Plus"
