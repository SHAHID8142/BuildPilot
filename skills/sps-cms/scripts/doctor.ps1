# ==============================================================================
# ⚡ SPS-CMS Doctor for Windows PowerShell (Health Check & Diagnostics)
# ==============================================================================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🩺 [SPS-CMS Doctor] Running System & Project Diagnostics on Windows..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# 1. Check Project Root Lock
if ((Test-Path ".\.sps-cms\lock.json") -or (Test-Path ".\GEMINI.md") -or (Test-Path ".\AGENTS.md")) {
    Write-Host "  ✅ Project Root Lock: DETECTED" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Project Root Lock: NOT FOUND (Run /sps-cms scaffold to lock)" -ForegroundColor Yellow
}

# 2. Check Schema Config
if ((Test-Path ".\src\config\cms.config.ts") -or (Test-Path ".\cms.config.ts")) {
    Write-Host "  ✅ CMS Schema Config: DETECTED" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ CMS Schema Config: NOT FOUND" -ForegroundColor Yellow
}

# 3. Check Upload Directory
$UploadDir = ".\public\uploads"
if (Test-Path $UploadDir) {
    Write-Host "  ✅ Uploads Directory ($UploadDir): DETECTED" -ForegroundColor Green
} else {
    Write-Host "  ℹ️  Uploads Directory: Will be created on first upload." -ForegroundColor Cyan
}

# 4. Check Environment File
if (Test-Path ".\.env") {
    Write-Host "  ✅ Environment File (.env): DETECTED" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Environment File (.env): MISSING (Create .env with DB credentials)" -ForegroundColor Yellow
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✨ Diagnostics completed." -ForegroundColor Green
