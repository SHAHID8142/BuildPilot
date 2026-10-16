# Shahid Personal SkillSet - Uninstaller (Windows PowerShell)
# -------------------------------------------------------------
# Removes /sps and the curated profile installs from all supported agents.
# By default, this removes ~/.sps/ personal data too.
#
# Usage: .\uninstall.ps1
#        .\uninstall.ps1 -KeepPersonal
#        .\uninstall.ps1 -Agents "claude-code,cursor"

param(
    [switch]$KeepPersonal,
    [switch]$Yes,
    [string]$Agents = "*"
)

$ErrorActionPreference = "Continue"
$env:npm_config_cache = Join-Path $env:USERPROFILE ".sps\npm-cache"
$env:NPX_NO_UPDATE_NOTIFIER = "1"

function ok($msg)      { Write-Host "  [OK] $msg" -ForegroundColor Green }
function info($msg)    { Write-Host "   --> $msg" -ForegroundColor Yellow }
function removed($msg) { Write-Host "   [-] $msg" -ForegroundColor Red }
function section($msg) { Write-Host ""; Write-Host "-- $msg --" -ForegroundColor Cyan }

Write-Host ""
Write-Host "+==================================================================+" -ForegroundColor Magenta
Write-Host "|         Shahid Personal SkillSet - Uninstaller (Windows)         |" -ForegroundColor Magenta
Write-Host "+==================================================================+" -ForegroundColor Magenta
Write-Host ""

Write-Host "This will remove /sps and everything installed by the SPS installer." -ForegroundColor Red
if (-not $KeepPersonal) {
    Write-Host "It will also delete $env:USERPROFILE\.sps\" -ForegroundColor Red
}
if (-not $Yes) {
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -ne "yes") { Write-Host "Aborted."; exit 0 }
}

# -- Remove agent-installed skills ---------------------------------------------
section "Removing globally installed skills"

function Remove-AgentSkill($name) {
    $paths = @(
        "$env:USERPROFILE\.agents\skills\$name",
        "$env:USERPROFILE\.config\agents\skills\$name",
        ".\.agents\skills\$name",
        "$env:USERPROFILE\.claude\skills\$name",
        ".\.claude\skills\$name",
        "$env:USERPROFILE\.cursor\skills\$name",
        "$env:USERPROFILE\.cursor\rules\$name.mdc",
        ".\.cursor\rules\$name.mdc",
        ".\.cursor\skills\$name",
        "$env:USERPROFILE\.codex\skills\$name",
        ".\.codex\skills\$name",
        "$env:USERPROFILE\.gemini\skills\$name",
        ".\.gemini\skills\$name",
        "$env:USERPROFILE\.gemini\config\skills\$name",
        "$env:USERPROFILE\.gemini\antigravity\skills\$name",
        ".\.gemini\antigravity\skills\$name",
        "$env:USERPROFILE\.gemini\antigravity-cli\skills\$name",
        ".\.gemini\antigravity-cli\skills\$name",
        "$env:USERPROFILE\.windsurf\skills\$name",
        ".\.windsurf\skills\$name",
        "$env:USERPROFILE\.antigravity\skills\$name",
        ".\.antigravity\skills\$name"
    )
    $found = $false
    foreach ($p in $paths) {
        if (Test-Path $p) { Remove-Item -Recurse -Force $p; $found = $true }
    }
    if ($found) { removed $name }
}

function Get-AgentArgs {
    if ($Agents -eq "*") { return @("--agent","claude-code","--agent","cursor","--agent","codex","--agent","antigravity","--agent","antigravity-cli","--agent","universal") }
    $args = @()
    foreach ($agent in ($Agents -split ",")) {
        if ($agent.Trim()) {
            $args += "--agent"
            $args += $agent.Trim()
        }
    }
    return $args
}

$manifestPath = "$env:USERPROFILE\.sps\install-manifest.env"
$managedSkills = @("sps","hallmark","impeccable","design-taste-frontend","sps-cms","webapp-testing","web-design-guidelines","vercel-react-best-practices","vercel-composition-patterns","karpathy-guidelines","agent-browser","ai-seo","copywriting","deploy-to-vercel","verification-before-completion","astro-framework","webgpu-claude-skill","firecrawl","supabase","supabase-postgres-best-practices","prisma-database-setup","prisma-client-api","prisma-cli","vercel-react-native-skills","sleek-design-mobile-apps","fact-check","grill-me","caveman","taste-skill")
$claudePlugins = @("universal-build-orchestrator@shahid-personal-skillset","ui-ux-pro-max@ui-ux-pro-max-skill","engineering-skills@claude-code-skills","engineering-advanced-skills@claude-code-skills","marketing-skills@claude-code-skills","a11y-audit@claude-code-skills","docker-development@claude-code-skills")
$claudeMarketplaces = @("shahid-personal-skillset","ui-ux-pro-max-skill","claude-code-skills")
$useContext7 = 0
$useGraphify = 0
$syncPaths = @()

if (Test-Path $manifestPath) {
    Get-Content $manifestPath | ForEach-Object {
        if ($_ -match "^(.*?)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2]
            switch ($key) {
                "MANAGED_SKILLS" { if ($value) { $managedSkills = $value -split "," } }
                "CLAUDE_PLUGINS" { if ($value) { $claudePlugins = $value -split "," } else { $claudePlugins = @() } }
                "CLAUDE_MARKETPLACES" { if ($value) { $claudeMarketplaces = $value -split "," } else { $claudeMarketplaces = @() } }
                "USE_CONTEXT7" { $useContext7 = [int]$value }
                "USE_GRAPHIFY" { $useGraphify = [int]$value }
                "SYNC_PATHS" { if ($value) { $syncPaths = $value -split "," } }
            }
        }
    }
}

$agentArgs = Get-AgentArgs
if (Get-Command npx -ErrorAction SilentlyContinue) {
    section "Removing skills via Skills CLI"
    $skillArgs = @("skills","remove") + $managedSkills + @("-g","-y") + $agentArgs
    & npx @skillArgs 2>&1 | Out-Null
}

foreach ($s in $managedSkills) { Remove-AgentSkill $s }
Remove-AgentSkill "universal-build-orchestrator"

section "Removing mirrored /sps sync paths"
$defaultSyncPaths = @(
    "$env:USERPROFILE\.claude\skills",
    "$env:USERPROFILE\.cursor\skills",
    "$env:USERPROFILE\.codex\skills",
    "$env:USERPROFILE\.agents\skills",
    "$env:USERPROFILE\.config\agents\skills",
    "$env:USERPROFILE\.gemini\config\skills",
    "$env:USERPROFILE\.gemini\skills",
    "$env:USERPROFILE\.gemini\antigravity\skills",
    "$env:USERPROFILE\.gemini\antigravity-cli\skills"
)
if ($syncPaths.Count -eq 0) { $syncPaths = $defaultSyncPaths }
foreach ($destRoot in ($syncPaths + $defaultSyncPaths | Select-Object -Unique)) {
    if (-not $destRoot) { continue }
    $spsPath = Join-Path $destRoot "sps"
    if (Test-Path $spsPath) {
        Remove-Item -Recurse -Force $spsPath
        removed "$spsPath"
    }
    $spsCmsPath = Join-Path $destRoot "sps-cms"
    if (Test-Path $spsCmsPath) {
        Remove-Item -Recurse -Force $spsCmsPath
        removed "$spsCmsPath"
    }
}

# -- Remove Claude plugins -----------------------------------------------------
section "Removing Claude plugins"

if (Get-Command claude -ErrorAction SilentlyContinue) {
    foreach ($p in $claudePlugins) {
        claude plugin uninstall $p --scope project 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { removed $p }
    }

    foreach ($mkt in $claudeMarketplaces) {
        claude plugin marketplace remove $mkt 2>$null
        if ($LASTEXITCODE -eq 0) { removed "marketplace: $mkt" }
    }

    if ($useContext7 -eq 1) {
        claude mcp remove context7 --scope project 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { removed "Context7 MCP" }
    }
} else {
    info "claude CLI not found - skipping Claude plugin removal"
}

# -- Remove graphify -----------------------------------------------------------
section "Removing graphify"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    if ($useGraphify -eq 1) {
        uv tool uninstall graphifyy 2>$null
        if ($LASTEXITCODE -eq 0) { removed "graphify (uv)" }
    }
} elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    if ($useGraphify -eq 1) {
        pip uninstall graphifyy -y 2>$null
        if ($LASTEXITCODE -eq 0) { removed "graphify (pip)" }
    }
}
$graphifySkill = "$env:USERPROFILE\.claude\skills\graphify"
if (Test-Path $graphifySkill) { Remove-Item -Recurse -Force $graphifySkill; removed "graphify skill" }

# -- Remove personal data (only with -All) ------------------------------------
if (-not $KeepPersonal) {
    section "Removing personal data (~/.sps/)"
    $spsDir = "$env:USERPROFILE\.sps"
    if (Test-Path $spsDir) { Remove-Item -Recurse -Force $spsDir; removed "~\.sps\ (profile, mistakes, learned)" }
} else {
    section "Personal data kept"
    ok "~\.sps\ kept intact (profile, mistakes, learned topics)"
    info "To also remove personal data: .\uninstall.ps1"
}

# -- Done ----------------------------------------------------------------------
Write-Host ""
Write-Host "+==================================================================+" -ForegroundColor Green
Write-Host "|                    Uninstall complete                             |" -ForegroundColor Green
Write-Host "|                                                                  |" -ForegroundColor Green
Write-Host "|  To reinstall: powershell -ExecutionPolicy Bypass -File install.ps1  |" -ForegroundColor Green
Write-Host "+==================================================================+" -ForegroundColor Green
Write-Host ""
