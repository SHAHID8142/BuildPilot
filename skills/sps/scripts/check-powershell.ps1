# SPS PowerShell syntax check (Windows / pwsh)
# Usage:
#   pwsh -NoProfile -File scripts/check-powershell.ps1
#
# If pwsh is not installed, Mac/Linux contributors can skip this and rely on
# scripts/smoke-sps.sh which reports SKIP.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$files = @(
    (Join-Path $repo "install.ps1"),
    (Join-Path $repo "uninstall.ps1"),
    (Join-Path $repo "get-sps.ps1"),
    (Join-Path $repo "scripts\check-update.ps1"),
    (Join-Path $repo "scripts\update-sps.ps1")
)

foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        Write-Host "FAIL  missing $file" -ForegroundColor Red
        exit 1
    }
    $errors = $null
    $tokens = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($file, [ref]$tokens, [ref]$errors)
    if ($errors -and $errors.Count -gt 0) {
        Write-Host "FAIL  parse errors in $file" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        exit 1
    }
    Write-Host "PASS  parsed $file" -ForegroundColor Green
}

Write-Host "PASS  PowerShell syntax check" -ForegroundColor Green
