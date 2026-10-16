#!/usr/bin/env bash
# Shahid Personal SkillSet install (Mac / Linux) — single unified installer.
# Installs /sps + the complete curated skill stack on every detected host.
# Usage:
#   bash install.sh                 # interactive confirm when TTY
#   bash install.sh --yes           # non-interactive
#   bash install.sh --agents claude-code,cursor --yes
#
# Prefer one-command bootstrap:
#   curl -fsSL https://raw.githubusercontent.com/SHAHID8142/Shahid-Personal-SkillSet/main/get-sps.sh | bash

set -uo pipefail

export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=no"
export GIT_CLONE_PROTECTION_ACTIVE=false
export npm_config_yes=true
export CI="${CI:-1}"
export npm_config_cache="${HOME}/.sps/npm-cache"
export NPX_NO_UPDATE_NOTIFIER=1

NETWORK_TIMEOUT=90
AGENTS="*"
ASSUME_YES=false
INTERACTIVE=false
MANIFEST="$HOME/.sps/install-manifest.env"
MANAGED_SKILLS=("sps" "sps-cms")
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
)

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
INSTALLED=0; FAILED=0; STEP=0; TOTAL_STEPS=1
LOG_DIR="$HOME/.sps"
LOG="$LOG_DIR/install.log"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="unknown"
[[ -f "$REPO/skills/sps/VERSION" ]] && VERSION="$(tr -d '[:space:]' < "$REPO/skills/sps/VERSION")"
START_TS=$SECONDS

usage() {
  cat <<'EOF'
Usage: bash install.sh [--agents '*'|list] [--yes] [--interactive]

Single unified install: /sps orchestrator + complete curated skill stack
(design taste, CMS engine, testing, SEO/copy, deploy, backend, mobile, security,
token efficiency) for every detected agent host.

One-command (clone/pull + install):
  curl -fsSL https://raw.githubusercontent.com/SHAHID8142/Shahid-Personal-SkillSet/main/get-sps.sh | bash

Update:
  bash scripts/sps-update.sh --yes     (or: get-sps.sh, which pulls + reinstalls)

Uninstall:
  bash uninstall.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agents|-a)  AGENTS="${2:-}"; shift 2 ;;
    --yes|-y)     ASSUME_YES=true; shift ;;
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
  local bar
  bar="$(printf '%0.s█' $(seq 1 "$filled" 2>/dev/null) 2>/dev/null || true)"
  local pad
  pad="$(printf '%0.s░' $(seq 1 "$empty" 2>/dev/null) 2>/dev/null || true)"
  printf "${DIM}[%s%s] %s/%s${NC}" "$bar" "$pad" "$cur" "$total"
}

compute_total_steps() {
  TOTAL_STEPS=28
  if have claude; then TOTAL_STEPS=$((TOTAL_STEPS + 16)); fi
  if have uv || have pip; then TOTAL_STEPS=$((TOTAL_STEPS + 1)); fi
}

build_agent_args() {
  AGENT_ARGS=()
  if [[ "$AGENTS" == "*" ]]; then
    AGENT_ARGS=(
      --agent "claude-code" --agent "cursor" --agent "codex"
      --agent "antigravity" --agent "antigravity-cli"
      --agent "windsurf" --agent "github-copilot" --agent "opencode"
      --agent "cline" --agent "roo" --agent "kiro-cli" --agent "amp"
      --agent "universal"
    )
    return
  fi
  IFS=',' read -r -a _agents <<< "$AGENTS"
  for agent in "${_agents[@]}"; do
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
  mkdir -p "$HOME/.sps"
  cat > "$MANIFEST" <<EOF
PROFILE=all
AGENTS=$AGENTS
MANAGED_SKILLS=$managed
CLAUDE_PLUGINS=$claude_plugins
CLAUDE_MARKETPLACES=$claude_marketplaces
USE_CONTEXT7=$USE_CONTEXT7
USE_GRAPHIFY=$USE_GRAPHIFY
SYNC_PATHS=$(IFS=,; echo "${SYNC_PATHS[*]}")
SPS_VERSION=$VERSION
EOF
}

sync_core_skill() {
  local src="$REPO/skills/sps"
  local cms_src="$REPO/skills/sps-cms"
  if [ ! -d "$src" ]; then
    warn "skills/sps not found - run from repo root"
    return
  fi
  for dest_root in "${SYNC_PATHS[@]}"; do
    if mkdir -p "$dest_root" 2>/dev/null; then
      rm -rf "$dest_root/sps"
      cp -R "$src" "$dest_root/"
      if [ -d "$REPO/scripts" ]; then
        mkdir -p "$dest_root/sps/scripts"
        cp -R "$REPO/scripts/"* "$dest_root/sps/scripts/"
      fi
      if [ -d "$cms_src" ]; then
        rm -rf "$dest_root/sps-cms"
        cp -R "$cms_src" "$dest_root/"
      fi
      ok "synced /sps & /sps-cms → ${dest_root/#$HOME/\~}"
    else
      warn "could not sync → ${dest_root/#$HOME/\~}"
    fi
  done
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
  printf "${GREEN}${BOLD}║${NC}  Install: %-46s ${GREEN}${BOLD}║${NC}\n" "complete stack (all)"
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
step "/sps core skill" npx skills add "$REPO" -g --copy -y "${AGENT_ARGS[@]}"

MANAGED_SKILLS+=(hallmark impeccable design-taste-frontend webapp-testing web-design-guidelines vercel-react-best-practices vercel-composition-patterns karpathy-guidelines agent-browser ai-seo copywriting deploy-to-vercel verification-before-completion)
step "hallmark" npx skills add nutlope/hallmark -g -y "${AGENT_ARGS[@]}"
step "impeccable" npx skills add pbakaus/impeccable -g -y "${AGENT_ARGS[@]}"
step "design-taste-frontend (taste-skill v2)" npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -g -y "${AGENT_ARGS[@]}"
step "webapp-testing" npx skills add https://github.com/anthropics/skills --skill webapp-testing -g -y "${AGENT_ARGS[@]}"
step "web-design-guidelines" npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines -g -y "${AGENT_ARGS[@]}"
step "vercel-react-best-practices" npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices -g -y "${AGENT_ARGS[@]}"
step "vercel-composition-patterns" npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-composition-patterns -g -y "${AGENT_ARGS[@]}"
step "karpathy-guidelines" npx skills add https://github.com/forrestchang/andrej-karpathy-skills --skill karpathy-guidelines -g -y "${AGENT_ARGS[@]}"
step "agent-browser" npx skills add https://github.com/vercel-labs/agent-browser -g -y "${AGENT_ARGS[@]}"
step "ai-seo" npx skills add https://github.com/coreyhaines31/marketingskills --skill ai-seo -g -y "${AGENT_ARGS[@]}"
step "copywriting" npx skills add https://github.com/coreyhaines31/marketingskills --skill copywriting -g -y "${AGENT_ARGS[@]}"
step "deploy-to-vercel" npx skills add https://github.com/vercel-labs/agent-skills --skill deploy-to-vercel -g -y "${AGENT_ARGS[@]}"
step "verification-before-completion" npx skills add https://github.com/obra/superpowers --skill verification-before-completion -g -y "${AGENT_ARGS[@]}"

MANAGED_SKILLS+=(astro-framework webgpu-claude-skill firecrawl supabase supabase-postgres-best-practices prisma-database-setup prisma-client-api prisma-cli vercel-react-native-skills sleek-design-mobile-apps fact-check grill-me caveman)
step "astro-framework" npx skills add withastro/astro -g -y "${AGENT_ARGS[@]}"
step "webgpu-claude-skill" npx skills add dgreenheck/webgpu-claude-skill -g -y "${AGENT_ARGS[@]}"
step "firecrawl" npx skills add firecrawl/firecrawl -g -y "${AGENT_ARGS[@]}"
step "supabase" npx skills add https://github.com/supabase/agent-skills --skill supabase -g -y "${AGENT_ARGS[@]}"
step "supabase-postgres-best-practices" npx skills add https://github.com/supabase/agent-skills --skill supabase-postgres-best-practices -g -y "${AGENT_ARGS[@]}"
step "prisma-database-setup" npx skills add https://github.com/prisma/skills --skill prisma-database-setup -g -y "${AGENT_ARGS[@]}"
step "prisma-client-api" npx skills add https://github.com/prisma/skills --skill prisma-client-api -g -y "${AGENT_ARGS[@]}"
step "prisma-cli" npx skills add https://github.com/prisma/skills --skill prisma-cli -g -y "${AGENT_ARGS[@]}"
step "vercel-react-native-skills" npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-native-skills -g -y "${AGENT_ARGS[@]}"
step "sleek-design-mobile-apps" npx skills add https://github.com/sleekdotdesign/agent-skills --skill sleek-design-mobile-apps -g -y "${AGENT_ARGS[@]}"
step "fact-check" npx skills add https://github.com/jwynia/agent-skills --skill fact-check -g -y "${AGENT_ARGS[@]}"
step "grill-me" npx skills add https://github.com/mattpocock/skills --skill grill-me -g -y "${AGENT_ARGS[@]}"
step "caveman" npx skills add https://github.com/mattpocock/skills --skill caveman -g -y "${AGENT_ARGS[@]}"

if have claude; then
  CLAUDE_MARKETPLACES+=(shahid-personal-skillset ui-ux-pro-max-skill claude-code-skills)
  CLAUDE_PLUGINS+=(universal-build-orchestrator@shahid-personal-skillset ui-ux-pro-max@ui-ux-pro-max-skill engineering-skills@claude-code-skills engineering-advanced-skills@claude-code-skills marketing-skills@claude-code-skills a11y-audit@claude-code-skills docker-development@claude-code-skills)
  step "/sps Claude marketplace" claude plugin marketplace add "$REPO"
  step "/sps Claude plugin" claude plugin install universal-build-orchestrator@shahid-personal-skillset --scope project
  step "ui-ux-pro-max marketplace" claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
  step "ui-ux-pro-max" claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill --scope project
  step "claude-code-skills marketplace" claude plugin marketplace add alirezarezvani/claude-skills
  step "engineering-skills" claude plugin install engineering-skills@claude-code-skills --scope project
  step "engineering-advanced-skills" claude plugin install engineering-advanced-skills@claude-code-skills --scope project
  step "marketing-skills" claude plugin install marketing-skills@claude-code-skills --scope project
  step "a11y-audit" claude plugin install a11y-audit@claude-code-skills --scope project
  step "docker-development" claude plugin install docker-development@claude-code-skills --scope project
  CLAUDE_MARKETPLACES+=(trailofbits)
  CLAUDE_PLUGINS+=(differential-review@trailofbits static-analysis@trailofbits ask-questions-if-underspecified@trailofbits insecure-defaults@trailofbits)
  step "Trail of Bits marketplace" claude plugin marketplace add trailofbits/skills
  step "ToB differential-review" claude plugin install differential-review@trailofbits --scope user
  step "ToB static-analysis" claude plugin install static-analysis@trailofbits --scope user
  step "ToB ask-questions" claude plugin install ask-questions-if-underspecified@trailofbits --scope user
  step "ToB insecure-defaults" claude plugin install insecure-defaults@trailofbits --scope user
  USE_CONTEXT7=1
  step "Context7 MCP" add_context7
else
  warn "Claude extras skipped because claude CLI was not found"
fi

if have uv; then
  USE_GRAPHIFY=1
  step "graphify" bash -c 'uv tool install graphifyy && graphify install'
elif have pip; then
  USE_GRAPHIFY=1
  step "graphify (pip)" bash -c 'pip install graphifyy && graphify install'
else
  warn "graphify skipped because neither uv nor pip is available"
fi

section "Shared setup"
seed_global_memory
ok "seeded ~/.sps personal defaults / mistakes / learned index"
sync_core_skill
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
