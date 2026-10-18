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

# Confinement guard: a deletion target must resolve inside an allowlisted
# agent-skill root. Manifest-controlled values are never trusted directly.
function Test-SafeUninstallTarget([string]$Path) {
    # Reject symlinked/reparse-point targets: a linked skill dir must not be
    # followed out of the allowlisted root.
    $item = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue -Force
    if ($item -and ($item.LinkType)) { return $false }
    $parentItem = Get-Item -LiteralPath (Split-Path -Parent $Path) -ErrorAction SilentlyContinue -Force
    if ($parentItem -and ($parentItem.LinkType)) { return $false }
    $candidate = [IO.Path]::GetFullPath($Path)
    # Covers every installer sync root plus the rules dirs. Keep in sync with
    # install.ps1's $syncRoots and uninstall.sh's UNINSTALL_ROOTS.
    $roots = @(
        (Join-Path $env:USERPROFILE ".agents\skills"),
        (Join-Path $env:USERPROFILE ".config\agents\skills"),
        (Join-Path $env:USERPROFILE ".claude\skills"),
        (Join-Path $env:USERPROFILE ".claude\rules"),
        (Join-Path $env:USERPROFILE ".cursor\skills"),
        (Join-Path $env:USERPROFILE ".cursor\rules"),
        (Join-Path $env:USERPROFILE ".codex\skills"),
        (Join-Path $env:USERPROFILE ".gemini\skills"),
        (Join-Path $env:USERPROFILE ".gemini\config\skills"),
        (Join-Path $env:USERPROFILE ".gemini\antigravity\skills"),
        (Join-Path $env:USERPROFILE ".gemini\antigravity-cli\skills"),
        (Join-Path $env:USERPROFILE ".windsurf\skills"),
        (Join-Path $env:USERPROFILE ".antigravity\skills"),
        (Join-Path $env:USERPROFILE ".codeium\windsurf\skills"),
        (Join-Path $env:USERPROFILE ".config\opencode\skills"),
        (Join-Path $env:USERPROFILE ".cline\skills"),
        (Join-Path $env:USERPROFILE ".roo\skills"),
        (Join-Path $env:USERPROFILE ".kiro\skills"),
        (Join-Path $env:USERPROFILE ".amp\skills"),
        (Join-Path $env:USERPROFILE ".github\skills"),
        (Join-Path $env:USERPROFILE ".config\goose\skills"),
        (Join-Path $env:USERPROFILE ".goose\skills"),
        (Join-Path $env:USERPROFILE ".crush\skills"),
        (Join-Path $env:USERPROFILE ".config\trae\skills"),
        (Join-Path $env:USERPROFILE ".trae\skills"),
        (Join-Path $env:USERPROFILE ".junie\skills"),
        (Join-Path $env:USERPROFILE ".config\junie\skills"),
        (Join-Path $env:USERPROFILE ".zed\skills"),
        (Join-Path $env:USERPROFILE ".openclaw\skills"),
        (Join-Path $env:USERPROFILE ".droid\skills"),
        (Join-Path $env:USERPROFILE ".qoder\skills"),
        (Join-Path $env:USERPROFILE ".kilocode\skills"),
        (Join-Path $env:USERPROFILE ".warp\plugins\skills"),
        (Join-Path $env:USERPROFILE ".grok\skills"),
        (Join-Path $env:USERPROFILE ".hermes\skills"),
        (Join-Path $env:USERPROFILE ".autohand\skills"),
        (Join-Path $env:USERPROFILE ".zeroclaw\skills")
    )
    foreach ($root in $roots) {
        $fullRoot = [IO.Path]::GetFullPath($root + [IO.Path]::DirectorySeparatorChar)
        if ($candidate.StartsWith($fullRoot, [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Remove-ConstrainedItem([string]$Path) {
    if (Test-SafeUninstallTarget $Path) {
        Remove-Item -Recurse -Force $Path
        return $true
    }
    info "refusing non-conforming delete target: $Path"
    return $false
}

function Remove-AgentSkill($name) {
    # Scan every allowlisted root (derived from the Test-SafeUninstallTarget
    # root list so the two can never drift). The old hand-written path list
    # covered only ~18 roots, leaving goose/crush/trae/junie/zed/openclaw/
    # droid/qoder/kilocode/warp/grok/hermes/autohand/zeroclaw installs behind.
    $roots = @(
        "$env:USERPROFILE\.agents\skills",
        "$env:USERPROFILE\.config\agents\skills",
        "$env:USERPROFILE\.claude\skills",
        "$env:USERPROFILE\.claude\rules",
        "$env:USERPROFILE\.cursor\skills",
        "$env:USERPROFILE\.cursor\rules",
        "$env:USERPROFILE\.codex\skills",
        "$env:USERPROFILE\.gemini\skills",
        "$env:USERPROFILE\.gemini\config\skills",
        "$env:USERPROFILE\.gemini\antigravity\skills",
        "$env:USERPROFILE\.gemini\antigravity-cli\skills",
        "$env:USERPROFILE\.windsurf\skills",
        "$env:USERPROFILE\.antigravity\skills",
        "$env:USERPROFILE\.codeium\windsurf\skills",
        "$env:USERPROFILE\.config\opencode\skills",
        "$env:USERPROFILE\.cline\skills",
        "$env:USERPROFILE\.roo\skills",
        "$env:USERPROFILE\.kiro\skills",
        "$env:USERPROFILE\.amp\skills",
        "$env:USERPROFILE\.github\skills",
        "$env:USERPROFILE\.config\goose\skills",
        "$env:USERPROFILE\.goose\skills",
        "$env:USERPROFILE\.crush\skills",
        "$env:USERPROFILE\.config\trae\skills",
        "$env:USERPROFILE\.trae\skills",
        "$env:USERPROFILE\.junie\skills",
        "$env:USERPROFILE\.config\junie\skills",
        "$env:USERPROFILE\.zed\skills",
        "$env:USERPROFILE\.openclaw\skills",
        "$env:USERPROFILE\.droid\skills",
        "$env:USERPROFILE\.qoder\skills",
        "$env:USERPROFILE\.kilocode\skills",
        "$env:USERPROFILE\.warp\plugins\skills",
        "$env:USERPROFILE\.grok\skills",
        "$env:USERPROFILE\.hermes\skills",
        "$env:USERPROFILE\.autohand\skills",
        "$env:USERPROFILE\.zeroclaw\skills"
    )
    $found = $false
    foreach ($root in $roots) {
        foreach ($leaf in @($name, "$name.mdc")) {
            $target = Join-Path $root $leaf
            if (Test-Path -LiteralPath $target) {
                if (Remove-ConstrainedItem $target) { $found = $true }
            }
        }
    }
    if ($found) { removed $name }
}

function Get-AgentArgs {
    # Full registry of the `skills` CLI — must match install.ps1 Get-AgentArgs.
    # The old 6-agent default left catalog copies in the other agents behind.
    if ($Agents -eq "*") { return @("--agent","claude-code","--agent","cursor","--agent","codex","--agent","antigravity","--agent","antigravity-cli","--agent","windsurf","--agent","github-copilot","--agent","opencode","--agent","cline","--agent","roo","--agent","kiro-cli","--agent","amp","--agent","goose","--agent","crush","--agent","trae","--agent","junie","--agent","zed","--agent","openclaw","--agent","droid","--agent","qoder","--agent","kilo","--agent","warp","--agent","universal") }
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
# Fallback when the manifest is gone (standalone uninstall). Must stay a
# superset of install.ps1's $script:ManagedSkills (initial @("sps") plus the
# two += batches). When the manifest exists it is parsed below and takes
# precedence.
$managedSkills = @("sps","sps-cms","sps-seo","hallmark","impeccable","design-taste-frontend","webapp-testing","web-design-guidelines","vercel-react-best-practices","vercel-composition-patterns","karpathy-guidelines","agent-browser","ai-seo","copywriting","deploy-to-vercel","verification-before-completion","astro-framework","webgpu-claude-skill","firecrawl","supabase","supabase-postgres-best-practices","prisma-database-setup","prisma-client-api","prisma-cli","vercel-react-native-skills","sleek-design-mobile-apps","fact-check","grill-me","caveman","taste-skill")
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
# Keep in sync with install.ps1's $syncRoots. The installer syncs sps,
# sps-cms AND sps-seo (Sync-CoreSkill); the old loop removed only the first
# two, so sps-seo survived every uninstall.
$defaultSyncPaths = @(
    "$env:USERPROFILE\.claude\skills",
    "$env:USERPROFILE\.cursor\skills",
    "$env:USERPROFILE\.codex\skills",
    "$env:USERPROFILE\.agents\skills",
    "$env:USERPROFILE\.config\agents\skills",
    "$env:USERPROFILE\.gemini\config\skills",
    "$env:USERPROFILE\.gemini\skills",
    "$env:USERPROFILE\.gemini\antigravity\skills",
    "$env:USERPROFILE\.gemini\antigravity-cli\skills",
    "$env:USERPROFILE\.codeium\windsurf\skills",
    "$env:USERPROFILE\.windsurf\skills",
    "$env:USERPROFILE\.config\opencode\skills",
    "$env:USERPROFILE\.cline\skills",
    "$env:USERPROFILE\.roo\skills",
    "$env:USERPROFILE\.kiro\skills",
    "$env:USERPROFILE\.amp\skills",
    "$env:USERPROFILE\.github\skills",
    "$env:USERPROFILE\.config\goose\skills",
    "$env:USERPROFILE\.goose\skills",
    "$env:USERPROFILE\.crush\skills",
    "$env:USERPROFILE\.config\trae\skills",
    "$env:USERPROFILE\.trae\skills",
    "$env:USERPROFILE\.junie\skills",
    "$env:USERPROFILE\.config\junie\skills",
    "$env:USERPROFILE\.zed\skills",
    "$env:USERPROFILE\.openclaw\skills",
    "$env:USERPROFILE\.droid\skills",
    "$env:USERPROFILE\.qoder\skills",
    "$env:USERPROFILE\.kilocode\skills",
    "$env:USERPROFILE\.warp\plugins\skills",
    "$env:USERPROFILE\.grok\skills",
    "$env:USERPROFILE\.hermes\skills",
    "$env:USERPROFILE\.autohand\skills",
    "$env:USERPROFILE\.zeroclaw\skills"
)
if ($syncPaths.Count -eq 0) { $syncPaths = $defaultSyncPaths }
$coreSyncSkills = @("sps", "sps-cms", "sps-seo")
foreach ($destRoot in ($syncPaths + $defaultSyncPaths | Select-Object -Unique)) {
    if (-not $destRoot) { continue }
    foreach ($skillName in $coreSyncSkills) {
        $skillPath = Join-Path $destRoot $skillName
        if (Test-Path -LiteralPath $skillPath) {
            if (Remove-ConstrainedItem $skillPath) { removed "$skillPath" }
        }
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
if (Test-Path $graphifySkill) { if (Remove-ConstrainedItem $graphifySkill) { removed "graphify skill" } }

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
