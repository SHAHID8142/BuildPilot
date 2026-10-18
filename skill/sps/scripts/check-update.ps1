# SPS check-update (Windows) - compare installed version against the latest release.
# Cached 24h in ~\.sps\update-state.env; -Force bypasses cache.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\check-update.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\check-update.ps1 -Force
#
# Exit codes:
#   0 = up to date
#   1 = update available
#   2 = offline / cannot check (non-fatal)

param([switch]$Force)

$ErrorActionPreference = "SilentlyContinue"
# Windows PowerShell 5.1 with .NET < 4.8 does not negotiate TLS 1.2 by
# default; GitHub raw requires TLS 1.2+, so every check would silently
# degrade to "offline". Pin the protocol before the first request. On
# PowerShell 7+ this line is a no-op (TLS 1.2+ is already the default).
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$rawUrl = "https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/skill/sps/VERSION"
$stateFile = Join-Path $HOME ".sps\update-state.env"
$ttlSeconds = 86400

function Test-VersionFormat {
    # Remote content is untrusted input. Accept strict semver-ish
    # MAJOR.MINOR.PATCH with an optional -PRERELEASE suffix only.
    # Each component is capped at 9 digits: Test-GreaterVersion compares
    # through [int64] arithmetic, and a longer run (e.g. 2^63 as MAJOR)
    # would throw or wrap and invert the comparison.
    param([string]$Value)
    return ($Value -match '^[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}(-[0-9A-Za-z.-]+)?$')
}

function Test-NumericIdentifierGreater {
    param([string]$A, [string]$B)
    # Numeric prerelease identifiers are unbounded; compare normalized
    # strings so no Int64 cast can wrap or throw.
    $aNormalized = $A.TrimStart([char]48)
    $bNormalized = $B.TrimStart([char]48)
    if (-not $aNormalized) { $aNormalized = "0" }
    if (-not $bNormalized) { $bNormalized = "0" }
    if ($aNormalized.Length -gt $bNormalized.Length) { return $true }
    if ($aNormalized.Length -lt $bNormalized.Length) { return $false }
    return ([string]::CompareOrdinal($aNormalized, $bNormalized) -gt 0)
}

function Test-GreaterVersion {
    # Returns $true when semantic version A is strictly greater than B,
    # including prerelease precedence. This matches the bash port.
    param([string]$A, [string]$B)
    if (-not (Test-VersionFormat $A) -or -not (Test-VersionFormat $B)) { return $false }
    $aCore = ($A -split '-', 2)[0] -split '\.'
    $bCore = ($B -split '-', 2)[0] -split '\.'
    for ($i = 0; $i -lt 3; $i++) {
        $av = [int64]$aCore[$i]
        $bv = [int64]$bCore[$i]
        if ($av -gt $bv) { return $true }
        if ($av -lt $bv) { return $false }
    }

    $aPrerelease = if ($A.Contains("-")) { ($A -split '-', 2)[1] } else { $null }
    $bPrerelease = if ($B.Contains("-")) { ($B -split '-', 2)[1] } else { $null }
    if (-not $aPrerelease -and $bPrerelease) { return $true }
    if ($aPrerelease -and -not $bPrerelease) { return $false }
    if ($aPrerelease -eq $bPrerelease) { return $false }

    $aParts = @($aPrerelease -split '\.')
    $bParts = @($bPrerelease -split '\.')
    $count = [Math]::Max($aParts.Count, $bParts.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $av = if ($i -lt $aParts.Count) { $aParts[$i] } else { $null }
        $bv = if ($i -lt $bParts.Count) { $bParts[$i] } else { $null }
        if (-not $av) { return $false }
        if (-not $bv) { return $true }
        $aNumeric = $av -match '^[0-9]+$'
        $bNumeric = $bv -match '^[0-9]+$'
        if ($aNumeric -and $bNumeric) {
            if (Test-NumericIdentifierGreater -A $av -B $bv) { return $true }
            if (Test-NumericIdentifierGreater -A $bv -B $av) { return $false }
        } elseif ($aNumeric) {
            return $false
        } elseif ($bNumeric) {
            return $true
        } else {
            $comparison = [string]::CompareOrdinal($av, $bv)
            if ($comparison -gt 0) { return $true }
            if ($comparison -lt 0) { return $false }
        }
    }
    return $false
}

function Write-State {
    # The state file is written with a temp file + atomic rename so a crash,
    # disk-full, or concurrent run can never leave a torn record behind: a
    # partially-written STATUS line would otherwise be read back as an empty
    # status and mis-scored as "up to date" on the next cached run.
    param([string]$CheckedAt, [string]$Status, [string]$Latest)
    $tmp = Join-Path (Split-Path $stateFile) ([System.IO.Path]::GetRandomFileName())
    Set-Content -Path $tmp -Value "CHECKED_AT=$CheckedAt`nSTATUS=$Status`nLATEST=$Latest"
    Move-Item -Force -Path $tmp -Destination $stateFile
}

function Get-InstalledVersion {
    $manifest = Join-Path $HOME ".sps\install-manifest.env"
    if (Test-Path $manifest) {
        $line = Select-String -Path $manifest -Pattern '^SPS_VERSION=' | Select-Object -First 1
        if ($line) { return ($line.Line -split '=')[1].Trim() }
    }
    $cand = Join-Path $HOME ".sps\src\BuildPilot\skill\sps\VERSION"
    if (Test-Path $cand) { return (Get-Content $cand -Raw).Trim() }
    return "unknown"
}

$installed = Get-InstalledVersion
if ($installed -ne "unknown" -and -not (Test-VersionFormat $installed)) {
    Write-Host "SPS installed version is malformed; treating as unknown"
    $installed = "unknown"
}

# 1. Cached state fresh enough?
if (-not $Force -and (Test-Path $stateFile)) {
    $last = $null; $latest = $null; $status = $null
    foreach ($line in Get-Content $stateFile) {
        $parts = $line -split '=', 2
        if ($parts[0] -eq "CHECKED_AT") {
            # CHECKED_AT is untrusted state: reject anything but a sane
            # epoch-seconds value (<= 12 digits) so a hostile or corrupt
            # state file cannot freeze the cache forever. The explicit
            # regex precedes the cast: the SilentlyContinue preference
            # would otherwise turn a failed cast into a silent $null.
            $raw = [string]$parts[1]
            if ($raw -match '^[0-9]{1,12}$') { $last = [int64]$raw }
        }
        elseif ($parts[0] -eq "LATEST") { $latest = $parts[1] }
        elseif ($parts[0] -eq "STATUS") { $status = $parts[1] }
    }
    $now = [int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    # A future CHECKED_AT has no legitimate use: any value past `now` would
    # extend the cache's authority beyond the TTL (a state file written at
    # now+TTL-1 stays authoritative for ~2x TTL). Reject it outright.
    if ($last -and (($now - $last) -lt $ttlSeconds) -and ($last -le $now)) {
        if (-not $latest) { $latest = "unknown" }
        $statusValid = ($status -eq "up-to-date") -or ($status -eq "update-available") -or ($status -eq "offline")
        if ($status -eq "offline") {
            $latestValid = (-not $latest) -or ($latest -eq "unknown")
        } else {
            $latestValid = Test-VersionFormat $latest
        }
        if ($statusValid -and $latestValid) {
            if ($status -eq "offline") { exit 2 }
            $cachedStatus = "update-available"
            if ($installed -ne "unknown") {
                if (($installed -eq $latest) -or (Test-GreaterVersion -A $installed -B $latest)) {
                    $cachedStatus = "up-to-date"
                }
            }
            Write-Host "SPS installed: $installed | latest: $latest | status: $cachedStatus (cached)"
            if ($cachedStatus -eq "update-available") { exit 1 }
            exit 0
        }
        Write-Host "SPS update state is corrupt (cached version/status); ignoring cache"
        $last = $null
    }
}

# 2. Fresh check
$latest = ""
try {
    $latest = (Invoke-WebRequest -Uri $rawUrl -UseBasicParsing -TimeoutSec 10).Content.Trim()
} catch { $latest = "" }

New-Item -ItemType Directory -Force -Path (Split-Path $stateFile) | Out-Null
if (-not $latest -or $latest -eq "unknown") {
    Write-Host "SPS version check: offline (installed $installed)"
    Write-State -CheckedAt ([int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) -Status "offline" -Latest "unknown"
    exit 2
}

# Remote VERSION is untrusted input: a malformed value is "cannot determine
# latest", never evidence that the installed version is up to date.
if (-not (Test-VersionFormat $latest)) {
    Write-Host "SPS version check: remote VERSION is malformed ($latest); treating as unavailable"
    Write-State -CheckedAt ([int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) -Status "offline" -Latest "unknown"
    exit 2
}

if ($installed -eq $latest) {
    Write-Host "SPS is up to date (v$installed)" -ForegroundColor Green
    Write-State -CheckedAt ([int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) -Status "up-to-date" -Latest $latest
    exit 0
}

if (Test-GreaterVersion -A $installed -B $latest) {
    # local install is ahead of remote (dev build) — treat as up to date
    Write-Host "SPS is up to date (local v$installed > remote v$latest)" -ForegroundColor Green
    Write-State -CheckedAt ([int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) -Status "up-to-date" -Latest $latest
    exit 0
}

Write-Host "SPS update available: v$installed -> v$latest" -ForegroundColor Yellow
Write-Host "Run: powershell -ExecutionPolicy Bypass -File scripts\update-sps.ps1 -Yes"
Write-State -CheckedAt ([int64][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) -Status "update-available" -Latest $latest
exit 1
