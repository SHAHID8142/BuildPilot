# SPS update (Windows) - update SPS to the latest version on this machine.
# Preserves the original install profile + agents from ~\.sps\install-manifest.env.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\update-sps.ps1 -Check
#   powershell -ExecutionPolicy Bypass -File scripts\update-sps.ps1 -Yes
#   powershell -ExecutionPolicy Bypass -File scripts\update-sps.ps1 -Force
#
# Exit codes:
#   0 = up to date or updated successfully
#   1 = update available (-Check) or update failed
#   2 = offline / cannot reach repo

param([switch]$Check, [switch]$Yes, [switch]$Force)

$ErrorActionPreference = "Stop"
# Source-repo location: SPS_REPO_DIR env override (parity with the bash
# updater), else the default install path.
$repoDir = if ($env:SPS_REPO_DIR) { $env:SPS_REPO_DIR } else { Join-Path $HOME ".sps\src\BuildPilot" }
$repoUrl = "https://github.com/SHAHID8142/BuildPilot.git"
$branch = "main"
$manifest = Join-Path $HOME ".sps\install-manifest.env"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Checker {
    $check = $null
    foreach ($cand in @((Join-Path $scriptRoot "check-update.ps1"), (Join-Path $repoDir "scripts\check-update.ps1"))) {
        if (Test-Path $cand) { $check = $cand; break }
    }
    if ($check) {
        & powershell -ExecutionPolicy Bypass -File $check -Force
        return $LASTEXITCODE
    }
    return 2
}

Write-Host ""
Write-Host "SPS updater" -ForegroundColor Cyan

if (-not $Check) {
    if (Test-Path (Join-Path $repoDir ".git")) {
        $status = & git -C $repoDir status --porcelain=v1 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Cannot verify the source worktree; refusing to update." -ForegroundColor Red
            exit 1
        }
        if ($status) {
            Write-Host "Local changes present in $repoDir; refusing to update." -ForegroundColor Red
            Write-Host "Commit, stash, or remove them manually, then retry."
            exit 1
        }
    } elseif (Test-Path $repoDir) {
        Write-Host "Destination exists but is not a Git worktree; refusing to delete it." -ForegroundColor Red
        exit 1
    }
}

if ($Check) {
    $rc = Checker
    exit $rc
}

$rc = Checker
if ($rc -eq 2) {
    Write-Host "Offline - cannot check for updates. Try later." -ForegroundColor Red
    exit 2
}
if ($rc -eq 0 -and -not $Force) {
    Write-Host "Nothing to do."
    exit 0
}

if (-not $Yes -and -not $Force) {
    $confirm = Read-Host "Update SPS now? [Y/n]"
    if ($confirm -match '^[Nn]') { Write-Host "Aborted."; exit 0 }
}

# 1. Get latest source
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git required to update. Install git and retry." -ForegroundColor Red
    exit 1
}
New-Item -ItemType Directory -Force -Path (Split-Path $repoDir) | Out-Null
if (Test-Path (Join-Path $repoDir ".git")) {
    Write-Host "Pulling latest source: $repoDir"
    $status = & git -C $repoDir status --porcelain=v1 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Cannot verify the source worktree; refusing to update." -ForegroundColor Red
        exit 1
    }
    if ($status) {
        Write-Host "Local changes present in $repoDir; refusing to update." -ForegroundColor Red
        Write-Host "Commit, stash, or remove them manually, then retry."
        exit 1
    }
    Push-Location $repoDir
    git fetch --prune origin $branch
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Host "fetch failed" -ForegroundColor Red; exit 1 }
    git checkout $branch 2>$null
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Host "Checkout failed; source left unchanged." -ForegroundColor Red
        exit 1
    }
    git pull --ff-only origin $branch
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Host "Fast-forward pull failed; source left unchanged." -ForegroundColor Red
        exit 1
    }
    Pop-Location
} else {
    Write-Host "Cloning source: $repoDir"
    if (Test-Path $repoDir) {
        Write-Host "Destination exists but is not a Git worktree; refusing to delete it." -ForegroundColor Red
        exit 1
    }
    git clone --depth 1 --branch $branch $repoUrl $repoDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Clone failed; the destination may be partially created. Inspect it and remove it manually if needed." -ForegroundColor Red
        exit 1
    }
}
Write-Host "Source updated" -ForegroundColor Green

# 2. Reinstall with same choices (single unified install — no profiles)
Set-Location $repoDir
$versionFile = Join-Path $repoDir "skill\sps\VERSION"
$version = if (Test-Path $versionFile) { (Get-Content $versionFile -Raw).Trim() } else { "unknown" }
Write-Host "Installing SPS v$version..."
# Preserve the choices recorded at install time: the manifest stores the
# original -Agents value and whether third-party extras were installed.
# Without this, a user who installed with -NoExtras would get 26 third-party
# skills + 11 plugins pulled in by the update's -Yes (which install.ps1
# reads as full extras consent), and a custom -Agents selection would
# silently reset to all hosts. Older manifests without the fields default
# to the historical behavior (all agents, extras on).
$installArgs = @("-Yes")
if (Test-Path $manifest) {
    $savedAgents = ""
    $savedExtras = ""
    foreach ($line in (Get-Content $manifest -ErrorAction SilentlyContinue)) {
        if     ($line -like "AGENTS=*")        { $savedAgents = $line.Substring("AGENTS=".Length).Trim() }
        elseif ($line -like "INSTALL_EXTRAS=*") { $savedExtras = $line.Substring("INSTALL_EXTRAS=".Length).Trim() }
    }
    if ($savedAgents -and $savedAgents -ne "*") {
        $installArgs += @("-Agents", $savedAgents)
        Write-Host "Preserving agents selection: $savedAgents"
    }
    if ($savedExtras -eq "false") {
        $installArgs += "-NoExtras"
        Write-Host "Preserving core-only install (no third-party extras)"
    }
}
& powershell -ExecutionPolicy Bypass -File (Join-Path $repoDir "install.ps1") @installArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "Reinstall failed (exit $LASTEXITCODE). See ~\.sps\install.log" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "SPS updated. Restart your agent session so the new skill body loads." -ForegroundColor Green
exit 0
