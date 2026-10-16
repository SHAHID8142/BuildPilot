#!/usr/bin/env bash
# Shahid Personal SkillSet — Uninstaller (Mac / Linux)
# ─────────────────────────────────────────────────────
# Removes /sps and the curated profile installs from all supported agents.
# By default, this removes ~/.sps/ personal data too.
#
# Usage: bash uninstall.sh
#        bash uninstall.sh --keep-personal
#        bash uninstall.sh --agents claude-code,cursor

set -uo pipefail
export npm_config_cache="${HOME}/.sps/npm-cache"
export NPX_NO_UPDATE_NOTIFIER=1

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
ok()      { echo -e "${GREEN}✓${NC} $*"; }
info()    { echo -e "${YELLOW}→${NC} $*"; }
removed() { echo -e "${RED}−${NC} $*"; }
section() { echo ""; echo -e "${BOLD}── $* ──${NC}"; }

KEEP_PERSONAL=false
AGENTS="*"
ASSUME_YES=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-personal)
      KEEP_PERSONAL=true
      shift
      ;;
    --yes|-y)
      ASSUME_YES=true
      shift
      ;;
    --agents|-a)
      AGENTS="${2:-}"
      shift 2
      ;;
    --all)
      KEEP_PERSONAL=false
      shift
      ;;
    --help|-h)
      echo "Usage: bash uninstall.sh [--keep-personal] [--yes] [--agents '*'|agent1,agent2]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

echo ""
echo -e "\033[0;36m\033[1m╔══════════════════════════════════════════════════════════════════╗\033[0m"
echo -e "\033[0;36m\033[1m║\033[0m  Shahid Personal SkillSet — Uninstaller                          \033[0;36m\033[1m║\033[0m"
echo -e "\033[0;36m\033[1m╚══════════════════════════════════════════════════════════════════╝\033[0m"
echo ""

echo -e "${RED}This will remove /sps and everything installed by the SPS installer.${NC}"
$KEEP_PERSONAL || echo -e "${RED}It will also remove ~/.sps/ personal data and the install manifest.${NC}"
if ! $ASSUME_YES; then
  read -p "Are you sure? (yes/no): " confirm
  [[ "$confirm" != "yes" ]] && echo "Aborted." && exit 0
fi

# ── Remove npx-installed skills (from ~/.agents/skills/) ─────────────────────
section "Removing globally installed skills"

remove_agent_skill() {
  local name="$1"
  local found=false
  local paths=(
    "$HOME/.agents/skills/$name"
    "$HOME/.config/agents/skills/$name"
    "./.agents/skills/$name"
    "$HOME/.claude/skills/$name"
    "./.claude/skills/$name"
    "$HOME/.cursor/skills/$name"
    "$HOME/.cursor/rules/$name.mdc"
    "./.cursor/rules/$name.mdc"
    "./.cursor/skills/$name"
    "$HOME/.codex/skills/$name"
    "./.codex/skills/$name"
    "$HOME/.gemini/skills/$name"
    "./.gemini/skills/$name"
    "$HOME/.gemini/config/skills/$name"
    "$HOME/.gemini/antigravity/skills/$name"
    "./.gemini/antigravity/skills/$name"
    "$HOME/.gemini/antigravity-cli/skills/$name"
    "./.gemini/antigravity-cli/skills/$name"
    "$HOME/.windsurf/skills/$name"
    "./.windsurf/skills/$name"
    "$HOME/.antigravity/skills/$name"
    "./.antigravity/skills/$name"
  )
  for p in "${paths[@]}"; do
    if [ -e "$p" ]; then
      rm -rf "$p" && found=true
    fi
  done
  $found && removed "$name" || true
}

# Core orchestrator
build_agent_args() {
  REMOVE_AGENT_ARGS=()
  if [[ "$AGENTS" == "*" ]]; then
    REMOVE_AGENT_ARGS=(--agent "claude-code" --agent "cursor" --agent "codex" --agent "antigravity" --agent "antigravity-cli" --agent "universal")
    return
  fi
  IFS=',' read -r -a _agents <<< "$AGENTS"
  for agent in "${_agents[@]}"; do
    [[ -n "$agent" ]] && REMOVE_AGENT_ARGS+=(--agent "$agent")
  done
}

MANIFEST="$HOME/.sps/install-manifest.env"
MANAGED_SKILLS=(sps hallmark impeccable design-taste-frontend sps-cms webapp-testing web-design-guidelines vercel-react-best-practices vercel-composition-patterns karpathy-guidelines agent-browser ai-seo copywriting deploy-to-vercel verification-before-completion astro-framework webgpu-claude-skill firecrawl supabase supabase-postgres-best-practices prisma-database-setup prisma-client-api prisma-cli vercel-react-native-skills sleek-design-mobile-apps fact-check grill-me caveman taste-skill)
CLAUDE_PLUGINS=(universal-build-orchestrator@shahid-personal-skillset ui-ux-pro-max@ui-ux-pro-max-skill engineering-skills@claude-code-skills engineering-advanced-skills@claude-code-skills marketing-skills@claude-code-skills a11y-audit@claude-code-skills docker-development@claude-code-skills)
CLAUDE_MARKETPLACES=(shahid-personal-skillset ui-ux-pro-max-skill claude-code-skills)
USE_CONTEXT7=0
USE_GRAPHIFY=0
SYNC_PATHS=()

if [ -f "$MANIFEST" ]; then
  while IFS='=' read -r key value; do
    case "$key" in
      MANAGED_SKILLS) IFS=',' read -r -a MANAGED_SKILLS <<< "$value" ;;
      CLAUDE_PLUGINS) IFS=',' read -r -a CLAUDE_PLUGINS <<< "$value" ;;
      CLAUDE_MARKETPLACES) IFS=',' read -r -a CLAUDE_MARKETPLACES <<< "$value" ;;
      USE_CONTEXT7) USE_CONTEXT7="$value" ;;
      USE_GRAPHIFY) USE_GRAPHIFY="$value" ;;
      SYNC_PATHS) IFS=',' read -r -a SYNC_PATHS <<< "$value" ;;
    esac
  done < "$MANIFEST"
fi

build_agent_args

if command -v npx >/dev/null 2>&1; then
  section "Removing skills via Skills CLI"
  npx skills remove "${MANAGED_SKILLS[@]}" -g -y "${REMOVE_AGENT_ARGS[@]}" >/dev/null 2>&1 || true
fi

for skill in "${MANAGED_SKILLS[@]}"; do
  remove_agent_skill "$skill"
done
remove_agent_skill "universal-build-orchestrator"

# Always clear installer-mirrored /sps roots (even if CLI remove missed them)
section "Removing mirrored /sps sync paths"
DEFAULT_SYNC_PATHS=(
  "$HOME/.claude/skills"
  "$HOME/.cursor/skills"
  "$HOME/.codex/skills"
  "$HOME/.agents/skills"
  "$HOME/.config/agents/skills"
  "$HOME/.gemini/config/skills"
  "$HOME/.gemini/skills"
  "$HOME/.gemini/antigravity/skills"
  "$HOME/.gemini/antigravity-cli/skills"
)
if ((${#SYNC_PATHS[@]} == 0)); then
  SYNC_PATHS=("${DEFAULT_SYNC_PATHS[@]}")
fi
for dest_root in "${SYNC_PATHS[@]}" "${DEFAULT_SYNC_PATHS[@]}"; do
  [[ -z "$dest_root" ]] && continue
  if [ -e "$dest_root/sps" ]; then
    rm -rf "$dest_root/sps" && removed "${dest_root/#$HOME/\~}/sps"
  fi
  if [ -e "$dest_root/sps-cms" ]; then
    rm -rf "$dest_root/sps-cms" && removed "${dest_root/#$HOME/\~}/sps-cms"
  fi
done

# ── Remove Claude plugin system skills ───────────────────────────────────────
section "Removing Claude plugins"

if command -v claude >/dev/null 2>&1; then
  if ((${#CLAUDE_PLUGINS[@]})); then
    for plugin in "${CLAUDE_PLUGINS[@]}"; do
      claude plugin uninstall "$plugin" --scope project >/dev/null 2>&1 && removed "$plugin" || true
    done
  fi

  # Remove marketplaces
  if ((${#CLAUDE_MARKETPLACES[@]})); then
    for mkt in "${CLAUDE_MARKETPLACES[@]}"; do
      claude plugin marketplace remove "$mkt" >/dev/null 2>&1 && removed "marketplace: $mkt" || true
    done
  fi

  # Remove Context7 MCP
  if [[ "$USE_CONTEXT7" == "1" ]]; then
    claude mcp remove context7 --scope project >/dev/null 2>&1 && removed "Context7 MCP" || true
  fi
else
  info "claude CLI not found — skipping Claude plugin removal"
fi

# ── Remove graphify ───────────────────────────────────────────────────────────
section "Removing graphify"
if command -v uv >/dev/null 2>&1; then
  [[ "$USE_GRAPHIFY" == "1" ]] && uv tool uninstall graphifyy >/dev/null 2>&1 && removed "graphify (uv)" || true
elif command -v pip >/dev/null 2>&1; then
  [[ "$USE_GRAPHIFY" == "1" ]] && pip uninstall graphifyy -y >/dev/null 2>&1 && removed "graphify (pip)" || true
fi
# Remove graphify skill file
if [ -e "$HOME/.claude/skills/graphify" ] || [ -e "$HOME/.config/agents/skills/graphify" ]; then
  rm -rf "$HOME/.claude/skills/graphify" "$HOME/.config/agents/skills/graphify"
  removed "graphify skill"
fi

# ── Remove personal data ──────────────────────────────────────────────────────
if ! $KEEP_PERSONAL; then
  section "Removing personal data (~/.sps/)"
  rm -rf "$HOME/.sps" && removed "~/.sps/ (profile, mistakes, learned)" || true
else
  section "Personal data kept"
  ok "~/.sps/ kept intact (profile, mistakes, learned topics)"
  info "To also remove personal data: bash uninstall.sh"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    Uninstall complete                             ║"
echo "║                                                                  ║"
echo "║  All /sps skills and catalog skills removed.                     ║"
if ! $KEEP_PERSONAL; then
echo "║  Personal data (~/.sps/) also removed.                           ║"
else
echo "║  Your profile, mistakes, and learned topics are still at         ║"
echo "║  ~/.sps/ — they're yours to keep or delete manually.             ║"
fi
echo "║                                                                  ║"
echo "║  To reinstall: bash install.sh                                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
