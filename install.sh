#!/usr/bin/env bash
# Shahid Personal SkillSet install (Mac / Linux) — single unified installer.
# Installs /sps + the complete curated skill stack on every detected host.
# Usage:
#   bash install.sh                 # interactive confirm when TTY
#   bash install.sh --yes           # non-interactive
#   bash install.sh --no-extras     # core-only: skip third-party skills/plugins/tools
#   bash install.sh --force         # replace managed skills even if their
#                                   # pre-replace backup fails (no safety copy)
#   bash install.sh --agents claude-code,cursor --yes
#   bash install.sh --agents '*' --yes   # every host in the skills CLI registry
#                                        # (claude-code, cursor, codex, antigravity,
#                                        # windsurf, opencode, goose, crush, trae,
#                                        # junie, zed, openclaw, droid, qoder, …)
#
# Prefer one-command bootstrap:
#   curl -fsSL https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.sh | bash

set -uo pipefail

export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=accept-new"
export GIT_CLONE_PROTECTION_ACTIVE=false
export npm_config_yes=true
export CI="${CI:-1}"
export npm_config_cache="${HOME}/.sps/npm-cache"
export NPX_NO_UPDATE_NOTIFIER=1

NETWORK_TIMEOUT=90
AGENTS="*"
ASSUME_YES=false
NO_EXTRAS=false
FORCE_SKIP_BACKUP=false
INTERACTIVE=false
MANIFEST="$HOME/.sps/install-manifest.env"
MANAGED_SKILLS=("sps" "sps-cms" "sps-seo")
CLAUDE_PLUGINS=()
CLAUDE_MARKETPLACES=()
USE_CONTEXT7=0
USE_GRAPHIFY=0
SYNC_PATHS=(
  "$HOME/.claude/skills"
  "$HOME/.cursor/skills"
  "$HOME/.codex/skills"
  "$HOME/.agents/skills"
  "$HOME/.config/agents/skills"
  "$HOME/.gemini/config/skills"
  "$HOME/.gemini/skills"
  "$HOME/.gemini/antigravity/skills"
  "$HOME/.gemini/antigravity-cli/skills"
  "$HOME/.codeium/windsurf/skills"
  "$HOME/.windsurf/skills"
  "$HOME/.config/opencode/skills"
  "$HOME/.cline/skills"
  "$HOME/.roo/skills"
  "$HOME/.kiro/skills"
  "$HOME/.amp/skills"
  "$HOME/.github/skills"
  "$HOME/.config/goose/skills"
  "$HOME/.goose/skills"
  "$HOME/.crush/skills"
  "$HOME/.config/trae/skills"
  "$HOME/.trae/skills"
  "$HOME/.junie/skills"
  "$HOME/.config/junie/skills"
  "$HOME/.zed/skills"
  "$HOME/.openclaw/skills"
  "$HOME/.droid/skills"
  "$HOME/.qoder/skills"
  "$HOME/.kilocode/skills"
  "$HOME/.warp/plugins/skills"
  "$HOME/.grok/skills"
  "$HOME/.hermes/skills"
  "$HOME/.autohand/skills"
  "$HOME/.zeroclaw/skills"
)

if [ -t 1 ]; then
  CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  RED='\033[0;31m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
else
  CYAN=''; GREEN=''; YELLOW=''; RED=''; BOLD=''; DIM=''; NC=''
fi
INSTALLED=0; FAILED=0; STEP=0; TOTAL_STEPS=1
LOG_DIR="$HOME/.sps"
LOG="$LOG_DIR/install.log"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="unknown"
[[ -f "$REPO/skill/sps/VERSION" ]] && VERSION="$(tr -d '[:space:]' < "$REPO/skill/sps/VERSION")"
START_TS=$SECONDS

usage() {
  cat <<'EOF'
Usage: bash install.sh [--agents '*'|list] [--yes] [--no-extras] [--force] [--interactive]

Single unified install: /sps orchestrator + complete curated skill stack
(design taste, CMS engine, testing, SEO/copy, deploy, backend, mobile, security,
token efficiency) for every detected agent host.

Options:
  --yes         non-interactive; also consents to all third-party installs
  --no-extras   core-only install: skip third-party skills, plugins,
                MCP servers and CLI tools (/sps + sps-cms + sps-seo only)

One-command (clone/pull + install):
  curl -fsSL https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.sh | bash

Update:
  bash scripts/sps-update.sh --yes     (or: get-sps.sh, which pulls + reinstalls)

Uninstall:
  bash uninstall.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agents|-a)
      AGENTS="${2:-}"
      if [[ $# -lt 2 || -z "$AGENTS" ]]; then echo "missing value for --agents" >&2; exit 1; fi
      shift 2 ;;
    --yes|-y)     ASSUME_YES=true; shift ;;
    --no-extras)  NO_EXTRAS=true; shift ;;
    --force|-f)   FORCE_SKIP_BACKUP=true; shift ;;
    --interactive|-i) INTERACTIVE=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1"; usage; exit 1 ;;
  esac
done

have() { command -v "$1" >/dev/null 2>&1; }
section() { echo ""; echo -e "${BOLD}${CYAN}── $* ──${NC}"; }
note()    { echo -e "${DIM}  $*${NC}"; }
ok()      { echo -e "  ${GREEN}✓${NC} $*"; }
warn()    { echo -e "  ${YELLOW}!${NC} $*"; }
bad()     { echo -e "  ${RED}✗${NC} $*"; }

banner() {
  echo ""
  echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}${BOLD}║${NC}  ${BOLD}Shahid Personal SkillSet${NC}   v${VERSION}                     ${CYAN}${BOLD}║${NC}"
  echo -e "${CYAN}${BOLD}║${NC}  Project-scoped /sps workflow for many AI agents         ${CYAN}${BOLD}║${NC}"
  echo -e "${CYAN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

detect_hosts() {
  echo -e "${BOLD}Detected hosts${NC}"
  [[ -d "$HOME/.claude" || $(have claude && echo 1) ]] && ok "Claude" || warn "Claude not detected"
  [[ -d "$HOME/.cursor" ]] && ok "Cursor" || warn "Cursor not detected"
  [[ -d "$HOME/.codex" ]] && ok "Codex" || warn "Codex not detected"
  [[ -d "$HOME/.gemini" ]] && ok "Gemini / Antigravity" || warn "Gemini / Antigravity not detected"
  echo ""
}

compute_total_steps() {
  TOTAL_STEPS=28
  if have claude; then TOTAL_STEPS=$((TOTAL_STEPS + 16)); fi
  if have uv || have pip; then TOTAL_STEPS=$((TOTAL_STEPS + 1)); fi
}

progress_bar() {
  local cur="$1" total="$2"
  [[ "$total" -lt 1 ]] && total=1
  local width=22
  local filled=$(( cur * width / total ))
  (( filled > width )) && filled=$width
  local empty=$(( width - filled ))
  local bar="" pad=""
  if (( filled > 0 )); then
    bar="$(printf '%0.s█' $(seq 1 "$filled") 2>/dev/null || true)"
  fi
  if (( empty > 0 )); then
    pad="$(printf '%0.s░' $(seq 1 "$empty") 2>/dev/null || true)"
  fi
  printf "${DIM}[%s%s] %s/%s${NC}" "$bar" "$pad" "$cur" "$total"
}

build_agent_args() {
  AGENT_ARGS=()
  if [[ "$AGENTS" == "*" ]]; then
    # Full registry of the `skills` CLI (vercel-labs/skills). `universal`
    # last: it copies into ~/.agents/skills, which every other agent also
    # reads, so per-agent links take precedence.
    AGENT_ARGS=(
      --agent "claude-code" --agent "cursor" --agent "codex"
      --agent "antigravity" --agent "antigravity-cli"
      --agent "windsurf" --agent "github-copilot" --agent "opencode"
      --agent "cline" --agent "roo" --agent "kiro-cli" --agent "amp"
      --agent "goose" --agent "crush" --agent "trae" --agent "junie"
      --agent "zed" --agent "openclaw" --agent "droid" --agent "qoder"
      --agent "kilo" --agent "warp" --agent "devin" --agent "replit"
      --agent "adal" --agent "augment" --agent "continue" --agent "grok"
      --agent "openhands" --agent "rovodev" --agent "zcode"
      --agent "universal"
    )
    return
  fi
  IFS=',' read -r -a _agents <<< "$AGENTS"
  for agent in "${_agents[@]+${_agents[@]}}"; do
    [[ -n "$agent" ]] && AGENT_ARGS+=(--agent "$agent")
  done
}

run_timeout() {
  local secs="$1"; shift
  local out_file="$1"; shift
  "$@" >"$out_file" 2>&1 &
  local cmd_pid=$!
  ( sleep "$secs"; kill -TERM "$cmd_pid" 2>/dev/null; sleep 2; kill -KILL "$cmd_pid" 2>/dev/null ) >/dev/null 2>&1 &
  local watch_pid=$!
  wait "$cmd_pid" 2>/dev/null; local rc=$?
  kill -TERM "$watch_pid" 2>/dev/null; wait "$watch_pid" 2>/dev/null
  return $rc
}

step() {
  local label="$1"; shift
  STEP=$((STEP+1))
  local start=$SECONDS
  local tmp_out="$LOG_DIR/.step.out"
  printf "  "
  progress_bar "$STEP" "$TOTAL_STEPS"
  printf "  ${YELLOW}%s${NC} ... " "$label"
  : > "$tmp_out"
  if run_timeout "$NETWORK_TIMEOUT" "$tmp_out" "$@"; then
    cat "$tmp_out" >> "$LOG"
    echo -e "${GREEN}done${NC} ${DIM}($((SECONDS-start))s)${NC}"
    INSTALLED=$((INSTALLED+1))
  else
    cat "$tmp_out" >> "$LOG"
    echo -e "${RED}failed${NC} ${DIM}($((SECONDS-start))s)${NC}"
    echo -e "${YELLOW}     >${NC} $(tail -n 1 "$tmp_out" 2>/dev/null)"
    FAILED=$((FAILED+1))
    echo "FAILED: $label" >> "$LOG"
  fi
}

# ── third-party consent gate ────────────────────────────────────────────────
# One gate for the whole third-party batch (skills + plugins + tools).
# --yes IS the consent (itemized summary still printed for the log);
# interactive mode asks once; --no-extras or a decline keeps core-only.
THIRD_PARTY_SKILLS=26
THIRD_PARTY_PLUGINS=11
INSTALL_EXTRAS=true

extras_step() {
  if [ "$INSTALL_EXTRAS" = true ]; then step "$@"; fi
}

consent_extras() {
  if [ "$NO_EXTRAS" = true ]; then
    INSTALL_EXTRAS=false
    warn "--no-extras: skipping $THIRD_PARTY_SKILLS third-party skills + $THIRD_PARTY_PLUGINS plugins (core-only install)"
    return
  fi
  note "third-party content: $THIRD_PARTY_SKILLS skills (vercel-labs/skills registry + community repos) + $THIRD_PARTY_PLUGINS plugins (shahid-personal-skillset, ui-ux-pro-max-skill, claude-code-skills, trailofbits marketplaces) + Context7 MCP + graphify"
  if [ "$ASSUME_YES" = true ]; then
    ok "consent via --yes — third-party skills + plugins will be installed"
    return
  fi
  if [ "$INTERACTIVE" = true ] && ! [ -t 0 ]; then
    bad "--interactive requested but stdin is not a terminal"
    exit 1
  fi
  if [ -t 0 ]; then
    printf "Install these %s third-party skills + %s plugins? [yes/no] " "$THIRD_PARTY_SKILLS" "$THIRD_PARTY_PLUGINS"
    read -r confirm
    case "${confirm:-no}" in
      y|Y|yes|YES) ok "consent granted — third-party skills + plugins will be installed" ;;
      *) INSTALL_EXTRAS=false
         warn "declined — skipping third-party skills + plugins (core install continues)" ;;
    esac
  else
    INSTALL_EXTRAS=false
    warn "non-interactive without --yes — skipping third-party skills + plugins (pass --yes to install them)"
  fi
}

seed_global_memory() {
  if [ ! -f "$HOME/.sps/personal-defaults.md" ]; then
    if [ -f "$REPO/templates/personal-defaults.md" ]; then
      cp "$REPO/templates/personal-defaults.md" "$HOME/.sps/personal-defaults.md"
    else
      cat > "$HOME/.sps/personal-defaults.md" <<'EOF'
# SPS Personal Defaults

Only put rules here when the user explicitly says they should apply across
future projects.
EOF
    fi
  fi

  [ -f "$HOME/.sps/global-mistakes.md" ] || cat > "$HOME/.sps/global-mistakes.md" <<'EOF'
# SPS Global Mistakes

Use this file only for mistakes that should not be repeated across projects.
EOF

  [ -f "$HOME/.sps/learned/INDEX.md" ] || cat > "$HOME/.sps/learned/INDEX.md" <<'EOF'
# SPS Learned Topics

Shared research notes saved here.
EOF
}

write_manifest() {
  local managed="" claude_plugins="" claude_marketplaces=""
  if ((${#MANAGED_SKILLS[@]})); then
    managed=$(IFS=,; echo "${MANAGED_SKILLS[*]}")
  fi
  if ((${#CLAUDE_PLUGINS[@]})); then
    claude_plugins=$(IFS=,; echo "${CLAUDE_PLUGINS[*]}")
  fi
  if ((${#CLAUDE_MARKETPLACES[@]})); then
    claude_marketplaces=$(IFS=,; echo "${CLAUDE_MARKETPLACES[*]}")
  fi
  # Core-only reinstall: keep the previous manifest's extras records so
  # uninstall still knows about extras installed by an earlier full run.
  # (Only fill fields this run left empty; never drop what's already there.)
  if [ "$INSTALL_EXTRAS" = false ] && [ -f "$MANIFEST" ]; then
    local prev_managed prev_plugins prev_mp
    prev_managed=$(sed -n 's/^MANAGED_SKILLS=//p' "$MANIFEST" | head -1)
    prev_plugins=$(sed -n 's/^CLAUDE_PLUGINS=//p' "$MANIFEST" | head -1)
    prev_mp=$(sed -n 's/^CLAUDE_MARKETPLACES=//p' "$MANIFEST" | head -1)
    [ -z "$managed" ] && managed="$prev_managed"
    [ -z "$claude_plugins" ] && claude_plugins="$prev_plugins"
    [ -z "$claude_marketplaces" ] && claude_marketplaces="$prev_mp"
  fi
  mkdir -p "$HOME/.sps"
  cat > "$MANIFEST" <<EOF
PROFILE=all
AGENTS=$AGENTS
MANAGED_SKILLS=$managed
CLAUDE_PLUGINS=$claude_plugins
CLAUDE_MARKETPLACES=$claude_marketplaces
USE_CONTEXT7=$USE_CONTEXT7
USE_GRAPHIFY=$USE_GRAPHIFY
SYNC_PATHS=$(IFS=,; echo "${SYNC_PATHS[*]:-}")
SPS_VERSION=$VERSION
# Whether this run installed third-party extras — sps-update.sh reads this
# to preserve a core-only choice across updates (m-4: "preserves the
# original install profile" means extras consent too, not just agents).
INSTALL_EXTRAS=$INSTALL_EXTRAS
EOF
}

# Back up an existing managed skill dir before replacing it. Keeps the last
# N=3 backups per skill in ~/.sps/backups/<skill>/<timestamp>/ so a bad update
# (or a user-customized skill) can always be restored. Returns 0 if a backup
# was made, 1 if there was nothing to back up or the backup failed.
backup_existing_skill() {
  local dest_root="$1" name="$2"
  local existing="$dest_root/$name"
  [ -d "$existing" ] || return 1
  local backup_root="$HOME/.sps/backups/$name"
  # Stamp includes a dest-root hash so two hosts synced in the same second
  # never overwrite each other's backups.
  local stamp
  stamp="$(date +%Y%m%d-%H%M%S)-$(printf '%s' "$dest_root" | shasum | cut -c1-6)-$$"
  while [ -e "$backup_root/$stamp" ]; do   # collision => suffix, never nest
    stamp="${stamp}-x"
  done
  mkdir -p "$backup_root" || { warn "backup dir unreachable: $backup_root"; return 1; }
  cp -R "$existing" "$backup_root/$stamp" || { warn "backup failed for $name"; return 1; }
  # Prune to the 3 most recent backups. Bounded loop: if rm fails (e.g.
  # permissions) the count never drops, so bail out instead of spinning.
  local old
  local guard=0
  while [ "$(ls -1 "$backup_root" 2>/dev/null | wc -l | tr -d ' ')" -gt 3 ] && [ "$guard" -lt 10 ]; do
    old="$(ls -1dt "$backup_root"/* 2>/dev/null | tail -1)"
    [ -n "$old" ] && rm -rf "$old"
    guard=$((guard + 1))
  done
  ok "backed up existing $name → ~/.sps/backups/$name/$stamp"
  return 0
}

# Read the VERSION of an already-installed skill (empty if absent/unknown).
installed_skill_version() {
  local vfile="$1/sps/VERSION"
  [ -f "$vfile" ] && tr -d '[:space:]' < "$vfile" || true
}

sync_core_skill() {
  local src="$REPO/skill/sps"
  local cms_src="$REPO/skill/sps-cms"
  local seo_src="$REPO/skill/sps-seo"
  if [ ! -d "$src" ]; then
    warn "skills/sps not found - run from repo root"
    return
  fi
  local upgrade_report="$HOME/.sps/last-upgrade.txt"
  mkdir -p "$HOME/.sps"
  : > "$upgrade_report"
  # Populated later (line ~527) by the pre-install scan; declared here because
  # the backup loop below reads it and set -u treats an unset array as an error.
  PRE_EXISTING_SPS=()
  local had_existing=false
  local backup_ok_any=false
  local sync_aborted=false
  for dest_root in "${SYNC_PATHS[@]+${SYNC_PATHS[@]}}"; do
    if mkdir -p "$dest_root" 2>/dev/null; then
      # Version detection + backup BEFORE the destructive replace.
      # Per-skill gate: a missing sps dir must not skip backups of
      # sps-cms/sps-seo (they'd be wiped unbacked below).
      # Only roots that had sps BEFORE this install started count as an
      # upgrade path — the npx skills-add step creates sps copies in agent
      # dirs mid-run, and treating those as "existing installs" would churn
      # backups on a fresh machine.
      local prev_ver=""
      local is_pre_existing=false
      for _pre in "${PRE_EXISTING_SPS[@]+${PRE_EXISTING_SPS[@]}}"; do
        [ -n "$_pre" ] && [ "$_pre" = "$dest_root" ] && is_pre_existing=true
      done
      # Fail-safe replace: each managed skill is deleted only after its own
      # backup succeeded (or there was nothing to back up). A failed backup
      # aborts that skill's replacement so local customizations survive.
      local replace_sps=true replace_cms=true replace_seo=true
      if [ "$is_pre_existing" = true ] || [ -d "$dest_root/sps-cms" ] || [ -d "$dest_root/sps-seo" ]; then
        had_existing=true
        prev_ver="$(installed_skill_version "$dest_root")"
        local skill
        for skill in sps sps-cms sps-seo; do
          [ -d "$dest_root/$skill" ] || continue
          if backup_existing_skill "$dest_root" "$skill"; then
            backup_ok_any=true
          elif [ "$FORCE_SKIP_BACKUP" = true ]; then
            warn "--force: replacing $skill in ${dest_root/#$HOME/\~} WITHOUT a backup"
          else
            bad "backup failed for $skill — NOT replacing in ${dest_root/#$HOME/\~}; your existing copy is untouched. Fix the backup destination or use --force to skip backup."
            sync_aborted=true
            case "$skill" in
              sps)     replace_sps=false ;;
              sps-cms) replace_cms=false ;;
              sps-seo) replace_seo=false ;;
            esac
          fi
        done
      fi
      if [ "$replace_sps" = true ]; then
        rm -rf "$dest_root/sps"
        cp -R "$src" "$dest_root/"
        if [ -d "$REPO/scripts" ]; then
          mkdir -p "$dest_root/sps/scripts"
          cp -R "$REPO/scripts/"* "$dest_root/sps/scripts/"
        fi
      fi
      if [ "$replace_cms" = true ] && [ -d "$cms_src" ]; then
        rm -rf "$dest_root/sps-cms"
        cp -R "$cms_src" "$dest_root/"
      fi
      if [ "$replace_seo" = true ] && [ -d "$seo_src" ]; then
        rm -rf "$dest_root/sps-seo"
        cp -R "$seo_src" "$dest_root/"
      fi
      if [ "$replace_sps" = false ]; then
        printf 'kept %s: sps NOT replaced (backup failed)\n' "${dest_root/#$HOME/\~}" >> "$upgrade_report"
      elif [ -n "$prev_ver" ] && [ "$prev_ver" != "$VERSION" ]; then
        printf 'upgraded %s: %s → %s\n' "${dest_root/#$HOME/\~}" "$prev_ver" "$VERSION" >> "$upgrade_report"
      elif [ -z "$prev_ver" ]; then
        printf 'installed %s: %s (fresh)\n' "${dest_root/#$HOME/\~}" "$VERSION" >> "$upgrade_report"
      else
        printf 'reinstalled %s: %s (same version)\n' "${dest_root/#$HOME/\~}" "$VERSION" >> "$upgrade_report"
      fi
      if [ "$replace_sps" = true ]; then
        if [ "$replace_cms" = true ] && [ "$replace_seo" = true ]; then
          ok "synced /sps & /sps-cms & /sps-seo → ${dest_root/#$HOME/\~}"
        else
          ok "synced /sps → ${dest_root/#$HOME/\~} (cms/seo kept: backup failed)"
        fi
      fi
    else
      warn "could not sync → ${dest_root/#$HOME/\~}"
    fi
  done
  if [ "$had_existing" = true ] && [ -s "$upgrade_report" ]; then
    section "Upgrade report"
    cat "$upgrade_report"
    # Only promise kept backups when at least one backup actually succeeded.
    if [ "$backup_ok_any" = true ]; then
      note "previous versions kept in ~/.sps/backups/<skill>/ (last 3 per skill)"
      note "restore: rm -rf <dest>/<skill> && cp -R ~/.sps/backups/<skill>/<stamp> <dest>/<skill>"
    fi
  fi
  [ "$sync_aborted" = true ] && return 1
  return 0
}

add_context7() {
  local out
  out=$(claude mcp add --scope project context7 -- npx -y @upstash/context7-mcp 2>&1)
  local rc=$?
  if [ $rc -ne 0 ] && printf '%s' "$out" | grep -q "already exists"; then
    echo "MCP server context7 already exists"
    return 0
  fi
  printf '%s\n' "$out"
  return $rc
}

print_success_card() {
  local elapsed=$((SECONDS - START_TS))
  echo ""
  echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}${BOLD}║${NC}  ${BOLD}Install complete${NC}                                         ${GREEN}${BOLD}║${NC}"
  echo -e "${GREEN}${BOLD}╠════════════════════════════════════════════════════════════╣${NC}"
  local stack_label="complete stack (all)"
  [ "$INSTALL_EXTRAS" = false ] && stack_label="core only (no third-party extras)"
  printf "${GREEN}${BOLD}║${NC}  Install: %-46s ${GREEN}${BOLD}║${NC}\n" "$stack_label"
  printf "${GREEN}${BOLD}║${NC}  Version: %-47s ${GREEN}${BOLD}║${NC}\n" "$VERSION"
  printf "${GREEN}${BOLD}║${NC}  Time:    %-47s ${GREEN}${BOLD}║${NC}\n" "${elapsed}s"
  printf "${GREEN}${BOLD}║${NC}  Steps:   %-47s ${GREEN}${BOLD}║${NC}\n" "$INSTALLED ok / $FAILED failed"
  echo -e "${GREEN}${BOLD}╠════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${GREEN}${BOLD}║${NC}  ${BOLD}Next steps${NC}                                              ${GREEN}${BOLD}║${NC}"
  echo -e "${GREEN}${BOLD}║${NC}  1. Open any project in your agent                       ${GREEN}${BOLD}║${NC}"
  echo -e "${GREEN}${BOLD}║${NC}  2. Run:  /sps                                           ${GREEN}${BOLD}║${NC}"
  echo -e "${GREEN}${BOLD}║${NC}  3. Old project?  /sps audit                             ${GREEN}${BOLD}║${NC}"
  echo -e "${GREEN}${BOLD}║${NC}  4. CMS debt?     /sps sync                              ${GREEN}${BOLD}║${NC}"
  echo -e "${GREEN}${BOLD}║${NC}  5. Health check: bash scripts/sps-doctor.sh             ${GREEN}${BOLD}║${NC}"
  echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  note "Log: $LOG"
  note "Source: $REPO"
}

# ── main ─────────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR/learned"
: > "$LOG"

# Snapshot which dest roots already carry a real SPS install BEFORE the npx
# skills-add step runs — otherwise sync_core_skill mistakes the npx-created
# copy for a previous install and "backs it up" on a fresh machine.
PRE_EXISTING_SPS=()
for _root in "${SYNC_PATHS[@]+${SYNC_PATHS[@]}}"; do
  [ -d "$_root/sps" ] && PRE_EXISTING_SPS+=("$_root")
done

banner
detect_hosts

echo -e "${BOLD}Plan${NC}"
ok "install  = complete stack (sps + all curated skills)"
ok "agents  = $AGENTS"
ok "version = $VERSION"
echo ""

if ! $ASSUME_YES && [[ -t 0 ]]; then
  read -r -p "Continue install? [Y/n] " confirm
  case "${confirm:-Y}" in
    n|N|no|NO) echo "Aborted."; exit 0 ;;
  esac
fi

section "Prerequisites"
have node   && ok "Node.js $(node -v)" || { bad "Node.js required: https://nodejs.org"; exit 1; }
have npx    && ok "npx available"      || { bad "npx required (ships with Node.js)"; exit 1; }
have claude && ok "claude CLI found"   || warn "claude CLI not found — Claude extras will be skipped"
have uv     && ok "uv found"           || warn "uv not found — graphify may use pip"
have pip    && ok "pip found"          || warn "pip not found"
build_agent_args
compute_total_steps
note "Planned steps: $TOTAL_STEPS"

section "Installing"
step "/sps core skill" npx skills add "$REPO" -g --copy -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"

consent_extras
if [ "$INSTALL_EXTRAS" = false ]; then
  # Core-only: no further step calls happen (everything below is gated), so
  # the total becomes the current step count — the bar reads complete.
  TOTAL_STEPS=$STEP
fi

if [ "$INSTALL_EXTRAS" = true ]; then MANAGED_SKILLS+=(hallmark impeccable design-taste-frontend webapp-testing web-design-guidelines vercel-react-best-practices vercel-composition-patterns karpathy-guidelines agent-browser ai-seo copywriting deploy-to-vercel verification-before-completion); fi
extras_step "hallmark" npx skills add nutlope/hallmark -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "impeccable" npx skills add pbakaus/impeccable -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "design-taste-frontend (taste-skill v2)" npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "webapp-testing" npx skills add https://github.com/anthropics/skills --skill webapp-testing -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "web-design-guidelines" npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "vercel-react-best-practices" npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "vercel-composition-patterns" npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-composition-patterns -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "karpathy-guidelines" npx skills add https://github.com/forrestchang/andrej-karpathy-skills --skill karpathy-guidelines -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "agent-browser" npx skills add https://github.com/vercel-labs/agent-browser -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "ai-seo" npx skills add https://github.com/coreyhaines31/marketingskills --skill ai-seo -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "copywriting" npx skills add https://github.com/coreyhaines31/marketingskills --skill copywriting -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "deploy-to-vercel" npx skills add https://github.com/vercel-labs/agent-skills --skill deploy-to-vercel -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "verification-before-completion" npx skills add https://github.com/obra/superpowers --skill verification-before-completion -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"

if [ "$INSTALL_EXTRAS" = true ]; then MANAGED_SKILLS+=(astro-framework webgpu-claude-skill firecrawl supabase supabase-postgres-best-practices prisma-database-setup prisma-client-api prisma-cli vercel-react-native-skills sleek-design-mobile-apps fact-check grill-me caveman); fi
extras_step "astro-framework" npx skills add withastro/astro -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "webgpu-claude-skill" npx skills add dgreenheck/webgpu-claude-skill -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "firecrawl" npx skills add firecrawl/firecrawl -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "supabase" npx skills add https://github.com/supabase/agent-skills --skill supabase -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "supabase-postgres-best-practices" npx skills add https://github.com/supabase/agent-skills --skill supabase-postgres-best-practices -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "prisma-database-setup" npx skills add https://github.com/prisma/skills --skill prisma-database-setup -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "prisma-client-api" npx skills add https://github.com/prisma/skills --skill prisma-client-api -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "prisma-cli" npx skills add https://github.com/prisma/skills --skill prisma-cli -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "vercel-react-native-skills" npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-native-skills -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "sleek-design-mobile-apps" npx skills add https://github.com/sleekdotdesign/agent-skills --skill sleek-design-mobile-apps -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "fact-check" npx skills add https://github.com/jwynia/agent-skills --skill fact-check -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "grill-me" npx skills add https://github.com/mattpocock/skills --skill grill-me -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"
extras_step "caveman" npx skills add https://github.com/mattpocock/skills --skill caveman -g -y "${AGENT_ARGS[@]+${AGENT_ARGS[@]}}"

if have claude; then
  if [ "$INSTALL_EXTRAS" = true ]; then
    CLAUDE_MARKETPLACES+=(shahid-personal-skillset ui-ux-pro-max-skill claude-code-skills)
    CLAUDE_PLUGINS+=(universal-build-orchestrator@shahid-personal-skillset ui-ux-pro-max@ui-ux-pro-max-skill engineering-skills@claude-code-skills engineering-advanced-skills@claude-code-skills marketing-skills@claude-code-skills a11y-audit@claude-code-skills docker-development@claude-code-skills)
  fi
  extras_step "/sps Claude marketplace" claude plugin marketplace add "$REPO"
  extras_step "/sps Claude plugin" claude plugin install universal-build-orchestrator@shahid-personal-skillset --scope project
  extras_step "ui-ux-pro-max marketplace" claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
  extras_step "ui-ux-pro-max" claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill --scope project
  extras_step "claude-code-skills marketplace" claude plugin marketplace add alirezarezvani/claude-skills
  extras_step "engineering-skills" claude plugin install engineering-skills@claude-code-skills --scope project
  extras_step "engineering-advanced-skills" claude plugin install engineering-advanced-skills@claude-code-skills --scope project
  extras_step "marketing-skills" claude plugin install marketing-skills@claude-code-skills --scope project
  extras_step "a11y-audit" claude plugin install a11y-audit@claude-code-skills --scope project
  extras_step "docker-development" claude plugin install docker-development@claude-code-skills --scope project
  if [ "$INSTALL_EXTRAS" = true ]; then
    CLAUDE_MARKETPLACES+=(trailofbits)
    CLAUDE_PLUGINS+=(differential-review@trailofbits static-analysis@trailofbits ask-questions-if-underspecified@trailofbits insecure-defaults@trailofbits)
  fi
  extras_step "Trail of Bits marketplace" claude plugin marketplace add trailofbits/skills
  extras_step "ToB differential-review" claude plugin install differential-review@trailofbits --scope user
  extras_step "ToB static-analysis" claude plugin install static-analysis@trailofbits --scope user
  extras_step "ToB ask-questions" claude plugin install ask-questions-if-underspecified@trailofbits --scope user
  extras_step "ToB insecure-defaults" claude plugin install insecure-defaults@trailofbits --scope user
  if [ "$INSTALL_EXTRAS" = true ]; then USE_CONTEXT7=1; fi
  extras_step "Context7 MCP" add_context7
else
  warn "Claude extras skipped because claude CLI was not found"
fi

if have uv; then
  if [ "$INSTALL_EXTRAS" = true ]; then USE_GRAPHIFY=1; fi
  extras_step "graphify" bash -c 'uv tool install graphifyy && graphify install'
elif have pip; then
  if [ "$INSTALL_EXTRAS" = true ]; then USE_GRAPHIFY=1; fi
  extras_step "graphify (pip)" bash -c 'pip install graphifyy && graphify install'
else
  warn "graphify skipped because neither uv nor pip is available"
fi

section "Shared setup"
seed_global_memory
ok "seeded ~/.sps personal defaults / mistakes / learned index"
if ! sync_core_skill; then
  warn "one or more managed skills were NOT replaced (backup failed) — see messages above"
fi
write_manifest
ok "wrote install manifest → ~/.sps/install-manifest.env"

section "Host verification"
[ -f "$HOME/.claude/skills/sps/SKILL.md" ] && ok "/sps on Claude" || bad "/sps missing on Claude"
[ -f "$HOME/.cursor/skills/sps/SKILL.md" ] && ok "/sps on Cursor" || bad "/sps missing on Cursor"
[ -f "$HOME/.codex/skills/sps/SKILL.md" ] && ok "/sps on Codex" || bad "/sps missing on Codex"
[ -d "$HOME/.gemini/config/skills/sps" ] && ok "/sps on Gemini/Antigravity" || bad "/sps missing on Gemini/Antigravity"

print_success_card

# Portable core is the sync of /sps. Optional npx skill adds may fail on network
# or agent-id drift; do not fail the whole install if mirrors are healthy.
if [[ -f "$HOME/.claude/skills/sps/SKILL.md" && -f "$HOME/.cursor/skills/sps/SKILL.md" ]]; then
  if ((FAILED > 0)); then
    warn "Some optional skill installs failed ($FAILED). /sps mirrors are OK — see $LOG"
  fi
  exit 0
fi

if ((FAILED > 0)); then
  exit 1
fi
