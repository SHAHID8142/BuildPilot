# ==============================================================================
# ⚡ SPS-CMS Universal PowerShell Uninstaller for Windows
# ==============================================================================

$SkillName = "sps-cms"
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

Write-Host "🗑️ [SPS-CMS] Uninstalling from all Windows agent directories..." -ForegroundColor Yellow

foreach ($Target in $TargetDirs) {
    if (Test-Path $Target) {
        Remove-Item -Path $Target -Recurse -Force
        Write-Host "  ❌ Removed: $Target" -ForegroundColor Red
    }
}

Write-Host "✨ [SPS-CMS] Successfully uninstalled from Windows." -ForegroundColor Green
