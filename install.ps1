param(
    [string]$Agents = "*",
    [switch]$Yes,
    [switch]$NoExtras,
    [switch]$Force,
    [switch]$Interactive
)

$ErrorActionPreference = "Continue"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GIT_SSH_COMMAND = "ssh -oBatchMode=yes -oStrictHostKeyChecking=accept-new"
$env:npm_config_yes = "true"
$env:CI = "1"
$env:npm_config_cache = Join-Path $env:USERPROFILE ".sps\npm-cache"
$env:NPX_NO_UPDATE_NOTIFIER = "1"
$NetworkTimeout = 90
$script:Start = Get-Date

$script:Installed = 0
$script:Skipped = 0
$script:StepNum = 0
$script:TotalSteps = 1
$repoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$spsHome = Join-Path $env:USERPROFILE ".sps"
$manifestPath = Join-Path $spsHome "install-manifest.env"
New-Item -ItemType Directory -Force -Path $spsHome | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $spsHome "learned") | Out-Null
$script:Log = Join-Path $spsHome "install.log"
"" | Set-Content -Path $script:Log
$script:ManagedSkills = @("sps","sps-cms","sps-seo")
$script:InstallExtras = $true
$script:CoreSyncAborted = $false
$script:ClaudePlugins = @()
$script:ClaudeMarketplaces = @()
$script:UseContext7 = 0
$script:UseGraphify = 0
$versionFile = Join-Path $repoDir "skill\sps\VERSION"
$script:Version = if (Test-Path $versionFile) { (Get-Content $versionFile -Raw).Trim() } else { "unknown" }
$syncRoots = @(
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

function note($msg)    { Write-Host "  $msg" -ForegroundColor DarkGray }
function ok($msg)      { Write-Host "  [OK] $msg" -ForegroundColor Green }
function warn($msg)    { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function section($msg) { Write-Host ""; Write-Host "-- $msg --" -ForegroundColor Cyan }
function have($cmd)    { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Get-AgentArgs {
    if ($Agents -eq "*") { return @("--agent","claude-code","--agent","cursor","--agent","codex","--agent","antigravity","--agent","antigravity-cli","--agent","windsurf","--agent","github-copilot","--agent","opencode","--agent","cline","--agent","roo","--agent","kiro-cli","--agent","amp","--agent","goose","--agent","crush","--agent","trae","--agent","junie","--agent","zed","--agent","openclaw","--agent","droid","--agent","qoder","--agent","kilo","--agent","warp","--agent","devin","--agent","replit","--agent","adal","--agent","augment","--agent","continue","--agent","grok","--agent","openhands","--agent","rovodev","--agent","zcode","--agent","universal") }
    $args = @()
    foreach ($agent in ($Agents -split ",")) {
        if ($agent.Trim()) {
            $args += "--agent"
            $args += $agent.Trim()
        }
    }
    return $args
}

function Get-AgentArgString {
    $quoted = @()
    foreach ($arg in (Get-AgentArgs)) {
        $escaped = $arg.Replace("'", "''")
        $quoted += "'$escaped'"
    }
    return ($quoted -join " ")
}

# Run a native command inside a job and THROW on nonzero exit — a completed
# PowerShell job is not a successful install otherwise (native exit codes do
# not fail jobs; QA finding). Use: Step "label" { Invoke-Native { npx ... } }
function Invoke-Native {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "command exited with code ${LASTEXITCODE}: $Command"
    }
}
# Start-Job runs the action in a fresh runspace: parent-session functions do
# not exist there, so the definition must be carried into the job explicitly
# (QA finding: every step died with CommandNotFoundException while the job
# still reported Completed).
$script:InvokeNativeDef = ${function:Invoke-Native}.ToString()

function Step {
    param([string]$Label, [scriptblock]$Action, [int]$TimeoutSec = $NetworkTimeout)
    $script:StepNum++
    $bar = "[{0}/{1}]" -f $script:StepNum, $script:TotalSteps
    Write-Host ("  {0} {1} ... " -f $bar, $Label) -NoNewline
    $start = Get-Date
    $tmpOut = Join-Path $spsHome ".step.out"
    Clear-Content -Path $tmpOut -ErrorAction SilentlyContinue

    $init = [scriptblock]::Create("function Invoke-Native { $($script:InvokeNativeDef) }")
    $job = Start-Job -InitializationScript $init -ScriptBlock $Action -Name "InstallJob"
    Wait-Job -Job $job -Timeout $TimeoutSec | Out-Null
    Receive-Job -Job $job 2>&1 | Out-File -FilePath $tmpOut -Append

    if ($job.State -eq "Completed") {
        $elapsedSec = [math]::Round((Get-Date).Subtract($start).TotalSeconds)
        Get-Content $tmpOut -ErrorAction SilentlyContinue | Add-Content -Path $script:Log
        Remove-Job $job -Force -ErrorAction SilentlyContinue
        Write-Host "done ($elapsedSec`s)" -ForegroundColor Green
        $script:Installed++
    } else {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -Force -ErrorAction SilentlyContinue
        $elapsedSec = [math]::Round((Get-Date).Subtract($start).TotalSeconds)
        Get-Content $tmpOut -ErrorAction SilentlyContinue | Add-Content -Path $script:Log
        Write-Host "failed ($elapsedSec`s)" -ForegroundColor Red
        Write-Host "   > Error snippet:" -ForegroundColor Yellow
        Get-Content $tmpOut -Tail 3 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "     $_" -ForegroundColor DarkGray }
        $script:Skipped++
        Add-Content -Path $script:Log -Value "FAILED: $Label"
        # A failed step must fail the installer: throw so the run stops with a
        # nonzero exit instead of printing "Install complete" (QA finding).
        throw "Step failed: $Label (see $tmpOut and $($script:Log))"
    }
}

function ExtrasStep {
    param([string]$Label, [scriptblock]$Action, [int]$TimeoutSec = $NetworkTimeout)
    if (-not $script:InstallExtras) { return }
    Step -Label $Label -Action $Action -TimeoutSec $TimeoutSec
}

function Grant-ExtrasConsent {
    # One gate for the whole third-party batch (skills + plugins + tools).
    # -Yes IS the consent (itemized summary still printed for the log);
    # interactive mode asks once; -NoExtras or a decline keeps core-only.
    if ($NoExtras) {
        $script:InstallExtras = $false
        warn "-NoExtras: skipping 26 third-party skills + 11 plugins (core-only install)"
        return
    }
    note "third-party content: 26 skills (vercel-labs/skills registry + community repos) + 11 plugins (shahid-personal-skillset, ui-ux-pro-max-skill, claude-code-skills, trailofbits marketplaces) + Context7 MCP + graphify"
    if ($Yes) {
        ok "consent via -Yes — third-party skills + plugins will be installed"
        return
    }
    if ([Environment]::UserInteractive) {
        $confirm = Read-Host "Install these 26 third-party skills + 11 plugins? [yes/no]"
        if ($confirm -match '^(y|Y|yes|YES)$') {
            ok "consent granted — third-party skills + plugins will be installed"
        } else {
            $script:InstallExtras = $false
            warn "declined — skipping third-party skills + plugins (core install continues)"
        }
    } else {
        $script:InstallExtras = $false
        warn "non-interactive without -Yes — skipping third-party skills + plugins (pass -Yes to install them)"
    }
}

function Seed-GlobalMemory {
    $personalDefaults = Join-Path $spsHome "personal-defaults.md"
    $globalMistakes = Join-Path $spsHome "global-mistakes.md"
    $learnedIndex = Join-Path $spsHome "learned\INDEX.md"

    if (-not (Test-Path $personalDefaults)) {
@"
# SPS Personal Defaults

Only put rules here when the user explicitly says they should apply across
future projects.

## Preferred tools
- Package manager:
- Preferred deploy:

## Preferred workflow
- Review style:
- Commit style:

## Explicit global approvals
-

## Explicit global rejections
-
"@ | Set-Content -Path $personalDefaults -Encoding UTF8
    }

    if (-not (Test-Path $globalMistakes)) {
@"
# SPS Global Mistakes

Use this file only for mistakes that should not be repeated across projects.
"@ | Set-Content -Path $globalMistakes -Encoding UTF8
    }

    if (-not (Test-Path $learnedIndex)) {
@"
# SPS Learned Topics

Shared research notes saved here.
"@ | Set-Content -Path $learnedIndex -Encoding UTF8
    }
}

function Write-Manifest {
    # Core-only reinstall: keep the previous manifest's extras records so
    # uninstall still knows about extras installed by an earlier full run.
    $prevManaged = ""; $prevPlugins = ""; $prevMp = ""
    if (-not $script:InstallExtras -and (Test-Path $manifestPath)) {
        foreach ($line in (Get-Content $manifestPath -ErrorAction SilentlyContinue)) {
            if     ($line -like "MANAGED_SKILLS=*")       { $prevManaged = $line.Substring("MANAGED_SKILLS=".Length) }
            elseif ($line -like "CLAUDE_PLUGINS=*")       { $prevPlugins = $line.Substring("CLAUDE_PLUGINS=".Length) }
            elseif ($line -like "CLAUDE_MARKETPLACES=*")  { $prevMp      = $line.Substring("CLAUDE_MARKETPLACES=".Length) }
        }
    }
    $managed = if ($script:ManagedSkills.Count) { $script:ManagedSkills -join "," } else { $prevManaged }
    $plugins = if ($script:ClaudePlugins.Count) { $script:ClaudePlugins -join "," } else { $prevPlugins }
    $mps     = if ($script:ClaudeMarketplaces.Count) { $script:ClaudeMarketplaces -join "," } else { $prevMp }
@"
PROFILE=all
AGENTS=$Agents
MANAGED_SKILLS=$managed
CLAUDE_PLUGINS=$plugins
CLAUDE_MARKETPLACES=$mps
USE_CONTEXT7=$script:UseContext7
USE_GRAPHIFY=$script:UseGraphify
SYNC_PATHS=$($syncRoots -join ",")
SPS_VERSION=$script:Version
"@ | Set-Content -Path $manifestPath -Encoding UTF8
}

function Backup-ManagedSkill {
    # Mirror of install.sh's backup_existing_skill: keep the last 3 backups
    # per skill in ~/.sps/backups/<skill>/<stamp>/ before replacing. Returns
    # $true when a backup was made, $false when there was nothing to back up
    # or the backup FAILED (caller must not delete on $false).
    param([string]$DestRoot, [string]$Name)
    $existing = Join-Path $DestRoot $Name
    if (-not (Test-Path $existing)) { return $false }
    $backupRoot = Join-Path $spsHome "backups\$Name"
    try {
        New-Item -ItemType Directory -Force -Path $backupRoot -ErrorAction Stop | Out-Null
    } catch {
        warn "backup destination unusable: $backupRoot"
        return $false
    }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $target = Join-Path $backupRoot $stamp
    if (Test-Path $target) { return $false }
    try {
        Copy-Item -Path $existing -Destination $target -Recurse -Force -ErrorAction Stop
    } catch {
        warn "backup failed for $Name in $DestRoot"
        return $false
    }
    # prune: keep last 3
    $stamps = @(Get-ChildItem -Path $backupRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($stamps.Count -gt 3) {
        $stamps | Select-Object -First ($stamps.Count - 3) | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    return $true
}

function Sync-CoreSkill {
    $src = Join-Path $repoDir "skill\sps"
    $cmsSrc = Join-Path $repoDir "skill\sps-cms"
    $seoSrc = Join-Path $repoDir "skill\sps-seo"
    if (-not (Test-Path $src)) {
        note "skills\sps not found - run from repo root"
        return
    }
    foreach ($destRoot in $syncRoots) {
        $dest = Join-Path $destRoot "sps"
        try {
            New-Item -ItemType Directory -Force -Path $destRoot -ErrorAction Stop | Out-Null
            # Fail-safe replace (mirrors install.sh): each skill is deleted
            # only after its own backup succeeded; a failed backup skips that
            # skill's replacement so local customizations survive.
            $replaceCms = $true; $replaceSeo = $true
            foreach ($pair in @(@("sps", $src), @("sps-cms", $cmsSrc), @("sps-seo", $seoSrc))) {
                $name = $pair[0]; $skillSrc = $pair[1]
                if (-not (Test-Path $skillSrc)) { continue }
                $skillDest = Join-Path $destRoot $name
                if (Test-Path $skillDest) {
                    $backedUp = Backup-ManagedSkill -DestRoot $destRoot -Name $name
                    if (-not $backedUp -and -not $Force) {
                        warn "backup failed for $name in $destRoot - NOT replacing (use -Force to skip backup)"
                        if ($name -eq "sps-cms") { $replaceCms = $false }
                        if ($name -eq "sps-seo") { $replaceSeo = $false }
                        if ($name -eq "sps") { $script:CoreSyncAborted = $true; continue }
                    }
                }
                if ($name -eq "sps-cms" -and -not $replaceCms) { continue }
                if ($name -eq "sps-seo" -and -not $replaceSeo) { continue }
                if (Test-Path $skillDest) { Remove-Item -Recurse -Force $skillDest }
                Copy-Item -Path $skillSrc -Destination $destRoot -Recurse -Force -ErrorAction Stop
                note "+ synced /$name to $destRoot"
            }
        } catch {
            note "- could not sync /sps to $destRoot"
        }
    }
}

Write-Host ""
Write-Host "+============================================================+" -ForegroundColor Cyan
Write-Host ("|  Shahid Personal SkillSet   v{0,-28}|" -f $script:Version) -ForegroundColor Cyan
Write-Host "|  Project-scoped /sps workflow for many AI agents           |" -ForegroundColor Cyan
Write-Host "+============================================================+" -ForegroundColor Cyan
Write-Host ""

Write-Host "Detected hosts" -ForegroundColor White
if ((Test-Path "$env:USERPROFILE\.claude") -or (have claude)) { ok "Claude" } else { warn "Claude not detected" }
if (Test-Path "$env:USERPROFILE\.cursor") { ok "Cursor" } else { warn "Cursor not detected" }
if (Test-Path "$env:USERPROFILE\.codex") { ok "Codex" } else { warn "Codex not detected" }
if (Test-Path "$env:USERPROFILE\.gemini") { ok "Gemini / Antigravity" } else { warn "Gemini / Antigravity not detected" }
Write-Host ""

Write-Host "Plan" -ForegroundColor White
ok "install  = complete stack (sps + all curated skills)"
ok "agents  = $Agents"
ok "version = $($script:Version)"
Write-Host ""

if (-not $Yes) {
    $confirm = Read-Host "Continue install? [Y/n]"
    if ($confirm -match '^[Nn]') { Write-Host "Aborted."; exit 0 }
}

section "Prerequisites"
if (have node) { ok "Node.js $(node -v)" } else { Write-Host "Node.js required: https://nodejs.org" -ForegroundColor Red; exit 1 }
if (have npx) { ok "npx available" } else { Write-Host "npx required (ships with Node.js)" -ForegroundColor Red; exit 1 }
if (have claude) { ok "claude CLI found" } else { warn "claude CLI not found - Claude extras will be skipped" }
if (have uv) { ok "uv found" } else { warn "uv not found - graphify may use pip" }
if (have pip) { ok "pip found" } else { warn "pip not found" }
$agentArgs = Get-AgentArgs
$agentArgsString = Get-AgentArgString

$script:TotalSteps = 28
if (have claude) { $script:TotalSteps += 16 }
if ((have uv) -or (have pip)) { $script:TotalSteps += 1 }
note "Planned steps: $($script:TotalSteps)"

section "Installing"
Step "/sps core skill" ([scriptblock]::Create("Invoke-Native { npx skills add `"$repoDir`" -g --copy -y $agentArgsString }"))

Grant-ExtrasConsent
if (-not $script:InstallExtras) {
    # Core-only: no further Step calls happen (everything below is gated),
    # so the total becomes the current step count — the bar reads complete.
    $script:TotalSteps = $script:StepNum
}

section "Complete skill stack"
if ($script:InstallExtras) { $script:ManagedSkills += @("hallmark","impeccable","design-taste-frontend","webapp-testing","web-design-guidelines","vercel-react-best-practices","vercel-composition-patterns","karpathy-guidelines","agent-browser","ai-seo","copywriting","deploy-to-vercel","verification-before-completion") }
ExtrasStep "hallmark" ([scriptblock]::Create("Invoke-Native { npx skills add nutlope/hallmark -g -y $agentArgsString }"))
ExtrasStep "impeccable" ([scriptblock]::Create("Invoke-Native { npx skills add pbakaus/impeccable -g -y $agentArgsString }"))
ExtrasStep "design-taste-frontend (taste-skill v2)" ([scriptblock]::Create("Invoke-Native { npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -g -y $agentArgsString }"))
ExtrasStep "webapp-testing" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/anthropics/skills --skill webapp-testing -g -y $agentArgsString }"))
ExtrasStep "web-design-guidelines" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines -g -y $agentArgsString }"))
ExtrasStep "vercel-react-best-practices" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices -g -y $agentArgsString }"))
ExtrasStep "vercel-composition-patterns" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-composition-patterns -g -y $agentArgsString }"))
ExtrasStep "karpathy-guidelines" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/forrestchang/andrej-karpathy-skills --skill karpathy-guidelines -g -y $agentArgsString }"))
ExtrasStep "agent-browser" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/vercel-labs/agent-browser -g -y $agentArgsString }"))
ExtrasStep "ai-seo" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/coreyhaines31/marketingskills --skill ai-seo -g -y $agentArgsString }"))
ExtrasStep "copywriting" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/coreyhaines31/marketingskills --skill copywriting -g -y $agentArgsString }"))
ExtrasStep "deploy-to-vercel" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/vercel-labs/agent-skills --skill deploy-to-vercel -g -y $agentArgsString }"))
ExtrasStep "verification-before-completion" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/obra/superpowers --skill verification-before-completion -g -y $agentArgsString }"))

if ($script:InstallExtras) { $script:ManagedSkills += @("astro-framework","webgpu-claude-skill","firecrawl","supabase","supabase-postgres-best-practices","prisma-database-setup","prisma-client-api","prisma-cli","vercel-react-native-skills","sleek-design-mobile-apps","fact-check","grill-me","caveman") }
ExtrasStep "astro-framework" ([scriptblock]::Create("Invoke-Native { npx skills add withastro/astro -g -y $agentArgsString }"))
ExtrasStep "webgpu-claude-skill" ([scriptblock]::Create("Invoke-Native { npx skills add dgreenheck/webgpu-claude-skill -g -y $agentArgsString }"))
ExtrasStep "firecrawl" ([scriptblock]::Create("Invoke-Native { npx skills add firecrawl/firecrawl -g -y $agentArgsString }"))
ExtrasStep "supabase" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/supabase/agent-skills --skill supabase -g -y $agentArgsString }"))
ExtrasStep "supabase-postgres-best-practices" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/supabase/agent-skills --skill supabase-postgres-best-practices -g -y $agentArgsString }"))
ExtrasStep "prisma-database-setup" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/prisma/skills --skill prisma-database-setup -g -y $agentArgsString }"))
ExtrasStep "prisma-client-api" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/prisma/skills --skill prisma-client-api -g -y $agentArgsString }"))
ExtrasStep "prisma-cli" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/prisma/skills --skill prisma-cli -g -y $agentArgsString }"))
ExtrasStep "vercel-react-native-skills" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-native-skills -g -y $agentArgsString }"))
ExtrasStep "sleek-design-mobile-apps" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/sleekdotdesign/agent-skills --skill sleek-design-mobile-apps -g -y $agentArgsString }"))
ExtrasStep "fact-check" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/jwynia/agent-skills --skill fact-check -g -y $agentArgsString }"))
ExtrasStep "grill-me" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/mattpocock/skills --skill grill-me -g -y $agentArgsString }"))
ExtrasStep "caveman" ([scriptblock]::Create("Invoke-Native { npx skills add https://github.com/mattpocock/skills --skill caveman -g -y $agentArgsString }"))

if (have claude) {
    section "Claude extras"
        $rd = $repoDir
        if ($script:InstallExtras) {
            $script:ClaudeMarketplaces += @("shahid-personal-skillset","ui-ux-pro-max-skill","claude-code-skills")
        $script:ClaudePlugins += @(
            "universal-build-orchestrator@shahid-personal-skillset",
            "ui-ux-pro-max@ui-ux-pro-max-skill",
            "engineering-skills@claude-code-skills",
            "engineering-advanced-skills@claude-code-skills",
            "marketing-skills@claude-code-skills",
            "a11y-audit@claude-code-skills",
            "docker-development@claude-code-skills"
        )
            $script:ClaudeMarketplaces += @("trailofbits")
            $script:ClaudePlugins += @("differential-review@trailofbits","static-analysis@trailofbits","ask-questions-if-underspecified@trailofbits","insecure-defaults@trailofbits")
        }
        ExtrasStep "Trail of Bits marketplace" { Invoke-Native {claude plugin marketplace add trailofbits/skills} }
        ExtrasStep "ToB differential-review" { Invoke-Native {claude plugin install differential-review@trailofbits --scope user} }
        ExtrasStep "ToB static-analysis" { Invoke-Native {claude plugin install static-analysis@trailofbits --scope user} }
        ExtrasStep "ToB ask-questions" { Invoke-Native {claude plugin install ask-questions-if-underspecified@trailofbits --scope user} }
        ExtrasStep "ToB insecure-defaults" { Invoke-Native {claude plugin install insecure-defaults@trailofbits --scope user} }
        ExtrasStep "/sps Claude marketplace" ([scriptblock]::Create("Invoke-Native { claude plugin marketplace add `"$rd`" }"))
        ExtrasStep "/sps Claude plugin" { Invoke-Native {claude plugin install universal-build-orchestrator@shahid-personal-skillset --scope project} }
        ExtrasStep "ui-ux-pro-max marketplace" { Invoke-Native {claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill} }
        ExtrasStep "ui-ux-pro-max" { Invoke-Native {claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill --scope project} }
        ExtrasStep "claude-code-skills marketplace" { Invoke-Native {claude plugin marketplace add alirezarezvani/claude-skills} }
        ExtrasStep "engineering-skills" { Invoke-Native {claude plugin install engineering-skills@claude-code-skills --scope project} }
        ExtrasStep "engineering-advanced-skills" { Invoke-Native {claude plugin install engineering-advanced-skills@claude-code-skills --scope project} }
        ExtrasStep "marketing-skills" { Invoke-Native {claude plugin install marketing-skills@claude-code-skills --scope project} }
        ExtrasStep "a11y-audit" { Invoke-Native {claude plugin install a11y-audit@claude-code-skills --scope project} }
        ExtrasStep "docker-development" { Invoke-Native {claude plugin install docker-development@claude-code-skills --scope project} }
        if ($script:InstallExtras) { $script:UseContext7 = 1 }
        ExtrasStep "Context7 MCP" {
            $out = claude mcp add --scope project context7 -- npx -y @upstash/context7-mcp 2>&1
            if ($LASTEXITCODE -ne 0 -and $out -match "already exists") {
                Write-Output "MCP server context7 already exists"
            } else {
                if ($LASTEXITCODE -ne 0) { throw $out }
                Write-Output $out
            }
        }
} else {
    note "Claude extras skipped because claude CLI was not found"
}

section "Optional research tools"
if (have uv) {
    if ($script:InstallExtras) { $script:UseGraphify = 1 }
    ExtrasStep "graphify" { Invoke-Native {uv tool install graphifyy; graphify install} }
} elseif (have pip) {
    if ($script:InstallExtras) { $script:UseGraphify = 1 }
    ExtrasStep "graphify (pip)" { Invoke-Native {pip install graphifyy; graphify install} }
} else {
    note "graphify skipped because neither uv nor pip is available"
}

section "Shared setup"
Seed-GlobalMemory
note "Seeded ~/.sps/personal-defaults.md, ~/.sps/global-mistakes.md, and ~/.sps/learned/INDEX.md"
Sync-CoreSkill
Write-Manifest
note "Wrote install manifest to ~/.sps/install-manifest.env"

section "Host verification"
if (Test-Path "$env:USERPROFILE\.claude\skills\sps\SKILL.md") { ok "/sps on Claude" } else { warn "/sps missing on Claude" }
if (Test-Path "$env:USERPROFILE\.cursor\skills\sps\SKILL.md") { ok "/sps on Cursor" } else { warn "/sps missing on Cursor" }
if (Test-Path "$env:USERPROFILE\.codex\skills\sps\SKILL.md") { ok "/sps on Codex" } else { warn "/sps missing on Codex" }
if (Test-Path "$env:USERPROFILE\.gemini\config\skills\sps") { ok "/sps on Gemini/Antigravity" } else { warn "/sps missing on Gemini/Antigravity" }

$elapsed = [math]::Round((Get-Date).Subtract($script:Start).TotalSeconds)
$stackLabel = "complete stack (all)"
if (-not $script:InstallExtras) { $stackLabel = "core only (no third-party extras)" }
Write-Host ""
Write-Host "+============================================================+" -ForegroundColor Green
Write-Host "|  Install complete                                          |" -ForegroundColor Green
Write-Host ("|  Install: {0,-46}|" -f $stackLabel) -ForegroundColor Green
Write-Host ("|  Version: {0,-47}|" -f $script:Version) -ForegroundColor Green
Write-Host ("|  Time:    {0,-47}|" -f "${elapsed}s") -ForegroundColor Green
Write-Host "|  Next: open a project and run  /sps                        |" -ForegroundColor Green
Write-Host "|        old project?            /sps audit                  |" -ForegroundColor Green
Write-Host "+============================================================+" -ForegroundColor Green
Write-Host ""
note "Log: $script:Log"

# Portable core is the sync of /sps. Optional skill/plugin installs may fail
# on network or agent-id drift; do not fail the whole install if the core
# mirrors are healthy (same semantics as install.sh).
$coreOk = (Test-Path "$env:USERPROFILE\.claude\skills\sps\SKILL.md") -and
          (Test-Path "$env:USERPROFILE\.cursor\skills\sps\SKILL.md")
if ($coreOk) {
    if ($script:Skipped -gt 0 -or $script:CoreSyncAborted) {
        warn "Some optional installs failed ($($script:Skipped)). /sps mirrors OK - see $($script:Log)"
    }
    exit 0
}
if ($script:Skipped -gt 0) {
    exit 1
}
