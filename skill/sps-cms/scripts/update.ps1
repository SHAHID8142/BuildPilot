# ==============================================================================
# ⚡ SPS-CMS Universal PowerShell Updater for Windows
# ==============================================================================
# Security (audit m-7): never Invoke-Expression a remote script. Download to a
# temp file first so the user can inspect it, and require an explicit yes
# (or -Yes) before executing fetched code.

param(
    [switch]$Yes
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$scriptUrl = "https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.ps1"
Write-Host "⚡ [SPS-CMS] Fetching latest release updates..." -ForegroundColor Cyan

$tmp = New-TemporaryFile
Rename-Item $tmp ($tmp.FullName + ".ps1")
$tmp = $tmp.FullName + ".ps1"
try {
    Invoke-WebRequest -Uri $scriptUrl -OutFile $tmp
    Write-Host "downloaded installer → $tmp ($((Get-Item $tmp).Length) bytes)"
    Write-Host "review it:  notepad $tmp"
    if (-not $Yes) {
        $confirm = Read-Host "Run the downloaded sps-cms installer now? (yes/no)"
        if ($confirm -notmatch '^(y|Y|yes|YES)$') {
            Write-Host "Aborted — nothing was run. Install manually: pwsh -File $tmp"
            exit 0
        }
    }
    # pwsh (PowerShell 7+) is not present on default Windows installs, which
    # ship only Windows PowerShell 5.1 — fall back to it (install.ps1 header
    # claims 5.1+ compatibility; audit finding).
    $shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
    & $shell -NoProfile -File $tmp
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "✨ [SPS-CMS] Update complete!" -ForegroundColor Cyan
} finally {
    Remove-Item $tmp -ErrorAction SilentlyContinue
}
