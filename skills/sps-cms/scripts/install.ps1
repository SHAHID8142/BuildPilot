# ==============================================================================
# ⚡ SPS-CMS Universal PowerShell Installer for Windows
# Compatible with Windows 7, 8, 10, 11 (PowerShell 3.0, 5.1, 7+)
# ==============================================================================

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$SkillName = "sps-cms"
$RepoZipUrl = "https://github.com/SHAHID8142/sps-cms/archive/refs/heads/main.zip"
$TempZip = Join-Path $env:TEMP "sps-cms-main.zip"
$TempExtract = Join-Path $env:TEMP "sps-cms-extract"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "⚡ [SPS-CMS] Universal Windows Skill Installer (v1.3.0)" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📥 Downloading latest release from GitHub..." -ForegroundColor Yellow

try {
    # Download zip file
    Invoke-WebRequest -Uri $RepoZipUrl -OutFile $TempZip -UseBasicParsing

    # Clean extract directory if exists
    if (Test-Path $TempExtract) {
        Remove-Item -Path $TempExtract -Recurse -Force
    }

    # Extract Archive
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force

    $ExtractedFolder = Join-Path $TempExtract "sps-cms-main"

    # Define all target paths across Windows AI agent environments
    $UserProfile = $env:USERPROFILE
    $TargetDirs = @(
        (Join-Path $UserProfile ".gemini\config\skills\$SkillName"),
        (Join-Path $UserProfile ".claude\skills\$SkillName"),
        (Join-Path $UserProfile ".cursor\skills\$SkillName"),
        (Join-Path $UserProfile ".windsurf\skills\$SkillName"),
        (Join-Path $UserProfile ".codeium\windsurf\skills\$SkillName"),
        (Join-Path $UserProfile ".config\opencode\skills\$SkillName"),
        (Join-Path $UserProfile ".agents\skills\$SkillName")
    )

    $InstalledCount = 0

    foreach ($Target in $TargetDirs) {
        if (-not (Test-Path $Target)) {
            New-Item -ItemType Directory -Path $Target -Force | Out-Null
        }

        Copy-Item -Path "$ExtractedFolder\*" -Destination $Target -Recurse -Force
        Write-Host "  ✅ Installed to: $Target" -ForegroundColor Green
        $InstalledCount++
    }

    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "✨ [SPS-CMS] Successfully installed across $InstalledCount agent paths on Windows!" -ForegroundColor Green
    Write-Host "🚀 Ready to use in Antigravity, Claude Code, Cursor, Windsurf, Codex on Windows." -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

} catch {
    Write-Host "❌ Installation failed: $_" -ForegroundColor Red
} finally {
    # Cleanup
    if (Test-Path $TempZip) { Remove-Item -Path $TempZip -Force -ErrorAction SilentlyContinue }
    if (Test-Path $TempExtract) { Remove-Item -Path $TempExtract -Recurse -Force -ErrorAction SilentlyContinue }
}
