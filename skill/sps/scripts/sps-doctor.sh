#!/usr/bin/env bash
# SPS doctor — check whether /sps is installed across agents.
# Usage: bash scripts/sps-doctor.sh [optional-project-dir]
#        bash scripts/sps-doctor.sh --fix   # auto-repair broken mirrors via reinstall

set -euo pipefail

if [ -t 1 ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; CYAN=''; BOLD=''; DIM=''; NC=''
fi
PROJECT=""
FIX=false
for arg in "$@"; do
  if [[ "$arg" == "--fix" || "$arg" == "-f" ]]; then
    FIX=true
  else
    # Non-flag argument = project dir (never wiped by seeing --fix).
    PROJECT="$arg"
  fi
done
PROJECT="${PROJECT:-${SPS_PROJECT_DIR:-}}"

echo ""
echo -e "${CYAN}${BOLD}SPS Doctor${NC}"
echo -e "${DIM}Checking /sps presence, mirrors, and basics${NC}"
echo ""

ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
bad()  { echo -e "  ${RED}✗${NC} $*"; }
warn() { echo -e "  ${YELLOW}!${NC} $*"; }
info() { echo -e "  ${DIM}- $*${NC}"; }

MISSING=0

REPO_REF="$HOME/.sps/src/BuildPilot"
[[ -d "$REPO_REF" ]] || REPO_REF="$HOME/.sps/src/Shahid-Personal-SkillSet"  # pre-rename installs
SCRIPT_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="unknown"
if [[ -f "$REPO_REF/skill/sps/VERSION" ]]; then
  VERSION="$(tr -d '[:space:]' < "$REPO_REF/skill/sps/VERSION")"
elif [[ -f "$SCRIPT_REPO/skill/sps/VERSION" ]]; then
  VERSION="$(tr -d '[:space:]' < "$SCRIPT_REPO/skill/sps/VERSION")"
fi
info "SPS version reference: $VERSION"

command -v node >/dev/null && ok "Node.js $(node -v)" || bad "Node.js missing"
command -v npx  >/dev/null && ok "npx available" || bad "npx missing"
command -v git  >/dev/null && ok "git available" || bad "git missing"
command -v claude >/dev/null && ok "claude CLI found" || info "claude CLI not found (optional)"

echo ""
echo -e "${BOLD}Host skill paths${NC}"
check_skill() {
  local label="$1" path="$2"
  if [[ -f "$path/SKILL.md" ]]; then
    local ver="?"
    [[ -f "$path/VERSION" ]] && ver="$(tr -d '[:space:]' < "$path/VERSION")"
    ok "$label ($ver)  ${path/#$HOME/\~}"
  else
    bad "$label missing  ${path/#$HOME/\~}"
    MISSING=$((MISSING + 1))
  fi
}

check_skill "Claude" "$HOME/.claude/skills/sps"
check_skill "Cursor" "$HOME/.cursor/skills/sps"
check_skill "Codex" "$HOME/.codex/skills/sps"
check_skill "Agents" "$HOME/.agents/skills/sps"
check_skill "Config agents" "$HOME/.config/agents/skills/sps"
check_skill "Gemini config" "$HOME/.gemini/config/skills/sps"
check_skill "Gemini skills" "$HOME/.gemini/skills/sps"
check_skill "Antigravity" "$HOME/.gemini/antigravity/skills/sps"
check_skill "Antigravity CLI" "$HOME/.gemini/antigravity-cli/skills/sps"
check_skill "Windsurf" "$HOME/.codeium/windsurf/skills/sps"
check_skill "OpenCode" "$HOME/.config/opencode/skills/sps"

echo ""
if [[ -f "$HOME/.sps/install-manifest.env" ]]; then
  ok "Install manifest present"
  info "$(grep '^PROFILE=' "$HOME/.sps/install-manifest.env" || true) (complete unified install)"
  info "$(grep '^SPS_VERSION=' "$HOME/.sps/install-manifest.env" || true)"
else
  bad "Install manifest missing (run get-sps.sh / install.sh)"
fi

if [[ -d "$HOME/.sps/src/BuildPilot/.git" ]]; then
  ok "Source clone at ~/.sps/src/BuildPilot"
else
  info "No source clone yet — use: curl .../get-sps.sh | bash"
fi

echo ""
echo -e "${BOLD}Managed skills${NC}"
check_skill "sps-cms (mandatory CMS engine)" "$HOME/.claude/skills/sps-cms"
check_skill "sps-seo (technical SEO standard)" "$HOME/.claude/skills/sps-seo"
check_skill "taste-skill v2 (design-taste-frontend)" "$HOME/.claude/skills/design-taste-frontend"
check_skill "agent-browser" "$HOME/.claude/skills/agent-browser"
check_skill "ai-seo" "$HOME/.claude/skills/ai-seo"
check_skill "copywriting" "$HOME/.claude/skills/copywriting"
check_skill "verification-before-completion" "$HOME/.claude/skills/verification-before-completion"

echo ""
echo -e "${BOLD}Update status${NC}"
if [[ -x "$SCRIPT_REPO/scripts/check-update.sh" ]]; then
  bash "$SCRIPT_REPO/scripts/check-update.sh" || true
elif [[ -x "$REPO_REF/scripts/check-update.sh" ]]; then
  bash "$REPO_REF/scripts/check-update.sh" || true
else
  info "check-update.sh not found (older install) — update with get-sps.sh"
fi

if [[ -n "$PROJECT" && -d "$PROJECT" ]]; then
  echo ""
  echo -e "${BOLD}Project checks:${NC} $PROJECT"
  [[ -d "$PROJECT/.sps" ]] && ok ".sps/ present" || bad ".sps/ missing (run bootstrap or /sps)"
  for f in profile.md handoff.md agent.md content-model.md cms-debt.md; do
    [[ -f "$PROJECT/.sps/$f" ]] && ok ".sps/$f" || info ".sps/$f missing"
  done
  for f in AGENTS.md GEMINI.md CLAUDE.md; do
    if [[ -f "$PROJECT/$f" ]] && grep -q "/sps lock" "$PROJECT/$f"; then
      ok "$f has /sps lock"
    elif [[ -f "$PROJECT/$f" ]]; then
      bad "$f exists but missing /sps lock block"
    else
      info "$f missing"
    fi
  done

  # Context-budget checks (CONTEXT-BUDGET.md): .sps hot files must stay small
  # enough that a resuming agent never burns a session re-reading history.
  echo ""
  echo -e "${BOLD}Context budget (.sps hot files):${NC}"
  budget_fail=0
  check_budget() { # file max_lines max_bytes
    local f="$PROJECT/.sps/$1" maxl=$2 maxb=$3 lines=0 bytes=0
    [[ -f "$f" ]] || return 0
    lines=$(wc -l < "$f" | tr -d ' ')
    bytes=$(wc -c < "$f" | tr -d ' ')
    if (( bytes > maxb * 150 / 100 || lines > maxl * 150 / 100 )); then
      bad ".sps/$1 OVER BUDGET: ${lines}L/${bytes}B (budget ${maxl}L/${maxb}B) — archive old entries to .sps/archive/ (CONTEXT-BUDGET.md)"
      budget_fail=$((budget_fail+1))
    elif (( bytes > maxb * 90 / 100 || lines > maxl * 90 / 100 )); then
      warn ".sps/$1 near budget: ${lines}L/${bytes}B (budget ${maxl}L/${maxb}B) — plan an archive pass"
    else
      ok ".sps/$1 ${lines}L/${bytes}B within budget"
    fi
  }
  check_budget handoff.md 150 8192
  check_budget agent.md 60 4096
  check_budget profile.md 120 8192
  check_budget plan.md 300 24576
  check_budget task-queue.md 80 6144
  check_budget audit-report.md 200 16384
  if (( budget_fail > 0 )); then
    bad "$budget_fail .sps file(s) over context budget — archive per CONTEXT-BUDGET.md rule 2"
  fi
fi

# T-29: third-party skill provenance (scripts/sps-provenance.sh).
# Optional content pinning of third-party skills (bundled sps/sps-cms/sps-seo are
# manifest-governed and skipped). Report-only here: drift count when pinned,
# an info hint when not pinned yet — never a failure.
if [[ -f "$HOME/.sps/provenance.json" ]]; then
  prov_out="$(bash "$SCRIPT_REPO/scripts/sps-provenance.sh" check 2>/dev/null || true)"
  prov_drift="$(printf '%s\n' "$prov_out" | grep -c '^PROVENANCE-DRIFT:' || true)"
  if [[ "$prov_drift" -gt 0 ]]; then
    bad "skill provenance: $prov_drift third-party skill(s) changed since pin — review with scripts/sps-provenance.sh check"
  else
    ok "skill provenance: no drift in pinned third-party skills"
  fi
else
  info "provenance not pinned yet — run scripts/sps-provenance.sh pin (optional)"
fi

echo ""
echo -e "${BOLD}Next commands${NC}"
info "Update SPS:       bash scripts/sps-update.sh --yes   (or --check)"
info "Install/update:  curl -fsSL https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.sh | bash"
info "Doctor again:     bash scripts/sps-doctor.sh [project-dir]"
info "In a project:     /sps  |  /sps audit  |  /sps sync  |  /sps doctor"

if [[ "$FIX" == true ]]; then
  echo ""
  if [[ $MISSING -gt 0 ]]; then
    echo -e "${YELLOW}${BOLD}--fix: $MISSING broken/missing installs found — repairing via forced reinstall…${NC}"
    if [[ -x "$SCRIPT_REPO/scripts/sps-update.sh" ]]; then
      bash "$SCRIPT_REPO/scripts/sps-update.sh" --force
    elif [[ -x "$REPO_REF/scripts/sps-update.sh" ]]; then
      bash "$REPO_REF/scripts/sps-update.sh" --force
    else
      echo -e "${RED}✗ sps-update.sh not found — reinstall manually with get-sps.sh${NC}"
    fi
    echo -e "${YELLOW}Re-run doctor to confirm everything is green.${NC}"
  else
    ok "--fix: nothing to repair."
  fi
fi
echo ""
