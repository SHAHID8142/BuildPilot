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

if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BOLD=''; NC=''
fi
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
      if [[ $# -lt 2 || -z "$AGENTS" ]]; then echo "missing value for --agents" >&2; exit 1; fi
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
  read -r -p "Are you sure? (yes/no): " confirm
  [[ "$confirm" != "yes" ]] && echo "Aborted." && exit 0
fi

# ── Remove npx-installed skills (from ~/.agents/skills/) ─────────────────────
section "Removing globally installed skills"

# Confinement guard: a deletion target must resolve inside an allowlisted
# agent-skill root. Manifest-controlled values are never trusted directly.
# Superset of the installer's SYNC_PATHS (install.sh:36-71; 34 unique roots)
# plus the two intentional
# rules dirs ($HOME/.claude/rules, $HOME/.cursor/rules) which install.sh
# never syncs but remove_agent_skill cleans. Keep in sync by hand: every
# SYNC_PATHS entry must appear in this list. Verify with:
#   diff <(sed -n '36,71p' install.sh | grep -o '"\$HOME/[^"]*"' | tr -d '"' | sort -u) \
#        <(printf '%s\n' "${UNINSTALL_ROOTS[@]}" | sort -u) | grep -v '^<'
UNINSTALL_ROOTS=(
  "$HOME/.agents/skills"
  "$HOME/.config/agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.claude/rules"
  "$HOME/.cursor/skills"
  "$HOME/.cursor/rules"
  "$HOME/.codex/skills"
  "$HOME/.gemini/skills"
  "$HOME/.gemini/config/skills"
  "$HOME/.gemini/antigravity/skills"
  "$HOME/.gemini/antigravity-cli/skills"
  "$HOME/.windsurf/skills"
  "$HOME/.antigravity/skills"
  "$HOME/.codeium/windsurf/skills"
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
is_safe_uninstall_target() {
  local candidate="$1"
  # Reject if the target itself or its immediate parent is a symlink:
  # a symlinked skill dir must not be followed out of the root.
  if [ -L "$candidate" ] || [ -L "$(dirname "$candidate")" ]; then
    return 1
  fi
  local real
  real="$(cd "$(dirname "$candidate")" 2>/dev/null && pwd -P)" || return 1
  [ -n "$real" ] || return 1
  local root real_root
  for root in "${UNINSTALL_ROOTS[@]}"; do
    real_root="$(cd "$root" 2>/dev/null && pwd -P)" || continue
    case "$real/" in
      "$real_root/"|"$real_root"/*) return 0 ;;
    esac
  done
  return 1
}
safe_rm() {
  local target="$1"
  if is_safe_uninstall_target "$target"; then
    rm -rf "$target"
    record_cleaned_root "$(dirname "$target")"
    return 0
  fi
  info "refusing non-conforming delete target: $target"
  return 1
}

# Truthful banner accounting: every successful guarded deletion records the
# agent root it came from; the final count is the number of distinct roots.
CLEANED_ROOT_PATHS=()
record_cleaned_root() {
  local raw="$1" abs existing
  [[ -z "$raw" ]] && return 0
  abs="$(cd "$raw" 2>/dev/null && pwd -P)" || return 0
  for existing in "${CLEANED_ROOT_PATHS[@]:-}"; do
    [[ "$existing" == "$abs" ]] && return 0
  done
  CLEANED_ROOT_PATHS+=("$abs")
}

remove_agent_skill() {
  local name="$1"
  local found=false
  local root candidate
  # Every allowlisted root, derived from UNINSTALL_ROOTS so this scan list
  # can never drift out of sync with the confinement guard. The old
  # hand-written path list covered only ~18 of the 36 roots, leaving
  # goose/crush/trae/junie/zed/openclaw/droid/qoder/kilocode/warp/grok/
  # hermes/autohand/zeroclaw installs behind. The .mdc probe clears rule
  # files in the rules dirs.
  for root in "${UNINSTALL_ROOTS[@]}"; do
    for candidate in "$root/$name" "$root/$name.mdc"; do
      if [ -e "$candidate" ] && safe_rm "$candidate"; then
        found=true
      fi
    done
  done
  # Project-local mirrors the installer/agents may have created in the repo.
  # safe_rm still refuses these unless the cwd resolves inside an allowlisted
  # root — same guard behavior as before.
  for root in \
    "./.agents/skills" "./.claude/skills" "./.cursor/skills" "./.cursor/rules" \
    "./.codex/skills" "./.gemini/skills" "./.gemini/antigravity/skills" \
    "./.gemini/antigravity-cli/skills" "./.windsurf/skills" "./.antigravity/skills"
  do
    for candidate in "$root/$name" "$root/$name.mdc"; do
      if [ -e "$candidate" ] && safe_rm "$candidate"; then
        found=true
      fi
    done
  done
  $found && removed "$name" || true
}

# Core orchestrator
build_agent_args() {
  REMOVE_AGENT_ARGS=()
  if [[ "$AGENTS" == "*" || -z "$AGENTS" ]]; then
    # Full registry of the `skills` CLI — must match install.sh build_agent_args
    # (install.sh:174-185). The old 6-agent default left catalog copies in the
    # other ~27 agents behind after "uninstall complete".
    REMOVE_AGENT_ARGS=(
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
  for agent in "${_agents[@]}"; do
    [[ -n "$agent" ]] && REMOVE_AGENT_ARGS+=(--agent "$agent")
  done
}

MANIFEST="$HOME/.sps/install-manifest.env"
# Fallback when the manifest is gone (standalone uninstall). Must stay a
# superset of install.sh's MANAGED_SKILLS (install.sh:31 + += at 457 and 472).
# When the manifest exists it is parsed below and takes precedence, so a
# future installer change automatically narrows this to exactly what was
# installed.
MANAGED_SKILLS=(sps sps-cms sps-seo hallmark impeccable design-taste-frontend webapp-testing web-design-guidelines vercel-react-best-practices vercel-composition-patterns karpathy-guidelines agent-browser ai-seo copywriting deploy-to-vercel verification-before-completion astro-framework webgpu-claude-skill firecrawl supabase supabase-postgres-best-practices prisma-database-setup prisma-client-api prisma-cli vercel-react-native-skills sleek-design-mobile-apps fact-check grill-me caveman taste-skill)
CLAUDE_PLUGINS=(universal-build-orchestrator@shahid-personal-skillset ui-ux-pro-max@ui-ux-pro-max-skill engineering-skills@claude-code-skills engineering-advanced-skills@claude-code-skills marketing-skills@claude-code-skills a11y-audit@claude-code-skills docker-development@claude-code-skills)
CLAUDE_MARKETPLACES=(shahid-personal-skillset ui-ux-pro-max-skill claude-code-skills)
USE_CONTEXT7=0
USE_GRAPHIFY=0
SYNC_PATHS=()
CLEANED_ROOT_PATHS=()
CLEANED_ROOTS=0

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
  npx skills remove "${MANAGED_SKILLS[@]:-}" -g -y "${REMOVE_AGENT_ARGS[@]:-}" >/dev/null 2>&1 || true
fi

for skill in "${MANAGED_SKILLS[@]:-}"; do
  [ -n "$skill" ] || continue
  remove_agent_skill "$skill"
done
remove_agent_skill "universal-build-orchestrator"

# Always clear installer-mirrored /sps roots (even if CLI remove missed them).
# The installer syncs all three core skills (sps, sps-cms, sps-seo — see
# install.sh sync_core_skill:347-360) into every SYNC_PATHS root; the old
# loop removed only sps and sps-cms, so sps-seo survived every uninstall.
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
if ((${#SYNC_PATHS[@]} == 0)); then
  SYNC_PATHS=("${DEFAULT_SYNC_PATHS[@]}")
fi
# CORE_SYNC_SKILLS must mirror install.sh sync_core_skill's three synced
# skills. Every deletion still goes through safe_rm (allowlist-guarded).
CORE_SYNC_SKILLS=(sps sps-cms sps-seo)
# Dedupe: manifest SYNC_PATHS may overlap DEFAULT_SYNC_PATHS.
for dest_root in "${SYNC_PATHS[@]:-}" "${DEFAULT_SYNC_PATHS[@]}"; do
  [[ -z "$dest_root" ]] && continue
  _seen=false
  for _prev in "${_DEDUPED_SYNC_ROOTS[@]:-}"; do
    [[ "$_prev" == "$dest_root" ]] && _seen=true && break
  done
  $_seen && continue
  _DEDUPED_SYNC_ROOTS+=("$dest_root")
done
for dest_root in "${_DEDUPED_SYNC_ROOTS[@]}"; do
  _root_cleaned=false
  for skill_name in "${CORE_SYNC_SKILLS[@]}"; do
    if [ -e "$dest_root/$skill_name" ] && safe_rm "$dest_root/$skill_name"; then
      removed "${dest_root/#$HOME/\~}/$skill_name"
      _root_cleaned=true
    fi
  done
  $_root_cleaned && record_cleaned_root "$dest_root"
done
CLEANED_ROOTS=${#CLEANED_ROOT_PATHS[@]}

# ── Remove Claude plugin system skills ───────────────────────────────────────
section "Removing Claude plugins"

if command -v claude >/dev/null 2>&1; then
  if ((${#CLAUDE_PLUGINS[@]})); then
    for plugin in "${CLAUDE_PLUGINS[@]:-}"; do
      claude plugin uninstall "$plugin" --scope project >/dev/null 2>&1 && removed "$plugin" || true
    done
  fi

  # Remove marketplaces
  if ((${#CLAUDE_MARKETPLACES[@]})); then
    for mkt in "${CLAUDE_MARKETPLACES[@]:-}"; do
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
  safe_rm "$HOME/.claude/skills/graphify"
  safe_rm "$HOME/.config/agents/skills/graphify"
  removed "graphify skill"
fi

# ── Remove personal data ──────────────────────────────────────────────────────
if ! $KEEP_PERSONAL; then
  # Preserve skill backups by default: install.sh promises a restore path in
  # ~/.sps/backups/<skill>/, so a full uninstall must not silently destroy it.
  if [ -d "$HOME/.sps/backups" ]; then
    mv "$HOME/.sps/backups" "$HOME/.sps-backups-uninstalled" \
      && info "skill backups preserved at ~/.sps-backups-uninstalled (delete manually if unwanted)"
  fi
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
printf '║%-66s║\n' "  /sps and catalog skills removed from ${CLEANED_ROOTS} agent root(s)."
echo "║  (Roots that were never installed are simply absent — that's     ║"
echo "║   expected, not a failure.)                                      ║"
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
