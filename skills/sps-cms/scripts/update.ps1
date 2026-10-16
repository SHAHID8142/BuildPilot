# ==============================================================================
# ⚡ SPS-CMS Universal PowerShell Updater for Windows
# ==============================================================================

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Write-Host "⚡ [SPS-CMS] Updating to latest release on Windows..." -ForegroundColor Cyan

Invoke-Expression (Invoke-RestMethod -Uri "https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.ps1")
