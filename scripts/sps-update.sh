#!/usr/bin/env bash
# SPS update — update SPS to the latest version on this machine.
# Preserves the original install profile + agents from ~/.sps/install-manifest.env.
#
# Usage:
#   bash scripts/sps-update.sh --check      # check only, no changes
#   bash scripts/sps-update.sh --yes        # update if available (auto)
#   bash scripts/sps-update.sh --force      # reinstall even when up to date (repair)
#   bash scripts/sps-update.sh              # interactive prompt
#
# Exit codes:
#   0 = up to date or updated successfully
#   1 = update available (--check) or update failed
#   2 = offline / cannot reach repo

set -uo pipefail

REPO_URL="${SPS_REPO_URL:-https://github.com/SHAHID8142/BuildPilot.git}"
REPO_DIR="${SPS_REPO_DIR:-$HOME/.sps/src/BuildPilot}"
BRANCH="${SPS_BRANCH:-main}"
MANIFEST="$HOME/.sps/install-manifest.env"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODE="prompt"
for arg in "$@"; do
  case "$arg" in
    --check) MODE="check" ;;
    --yes|-y) MODE="auto" ;;
    --force|-f) MODE="force" ;;
    *) echo "unknown option: $arg (usage: sps-update.sh [--check|--yes|--force])" >&2; exit 1 ;;
  esac
done

if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'
  BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BOLD=''; DIM=''; NC=''
fi
ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
warn() { echo -e "  ${YELLOW}!${NC} $*"; }
bad()  { echo -e "  ${RED}✗${NC} $*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

checker() {
  # prefer sibling check script; else repo clone copy; else fail closed
  local check=""
  for cand in "$ROOT/scripts/check-update.sh" "$REPO_DIR/scripts/check-update.sh"; do
    if [[ -f "$cand" ]]; then check="$cand"; break; fi
  done
  if [[ -n "$check" ]]; then
    bash "$check" "$@"
    return $?
  fi
  # No inline remote check (removed Round 26A): a missing check-update.sh
  # means a broken or pre-cache install; fail closed without any network
  # request rather than trust unvalidated remote VERSION data.
  echo "SPS version check: check-update.sh not found; cannot check (installed: $(grep '^SPS_VERSION=' "$MANIFEST" 2>/dev/null | cut -d= -f2 || echo unknown))" >&2
  return 2
}

echo ""
echo -e "${BOLD}SPS updater${NC}"

if [[ "$MODE" != "check" ]]; then
  if [[ -d "$REPO_DIR/.git" ]]; then
    if ! status="$(git -C "$REPO_DIR" status --porcelain=v1 2>/dev/null)"; then
      bad "Cannot verify the source worktree; refusing to update."
      exit 1
    fi
    if [[ -n "$status" ]]; then
      bad "Local changes present in $REPO_DIR; refusing to update."
      echo "Commit, stash, or remove them manually, then retry."
      exit 1
    fi
  elif [[ -e "$REPO_DIR" ]]; then
    bad "Destination exists but is not a Git worktree; refusing to delete it."
    exit 1
  fi
fi

if [[ "$MODE" == "check" ]]; then
  checker --force
  exit $?
fi

checker
rc=$?
if [[ $rc -eq 2 ]]; then
  bad "Offline — cannot check for updates. Try later."
  exit 2
fi
if [[ $rc -eq 0 && "$MODE" != "force" ]]; then
  ok "Nothing to do."
  exit 0
fi

if [[ "$MODE" == "prompt" ]]; then
  read -r -p "Update SPS now? [Y/n] " confirm
  case "${confirm:-Y}" in
    n|N|no|NO) echo "Aborted."; exit 0 ;;
  esac
fi

# 1. Get latest source (clone or pull)
if ! have git; then
  bad "git required to update. Install git and retry."
  exit 1
fi
mkdir -p "$(dirname "$REPO_DIR")"
if [[ -d "$REPO_DIR/.git" ]]; then
  echo -e "${DIM}Pulling latest source:${NC} $REPO_DIR"
  if ! git -C "$REPO_DIR" fetch --prune origin "$BRANCH"; then
    bad "Fetch failed; source left unchanged."
    exit 1
  fi
  if ! git -C "$REPO_DIR" checkout "$BRANCH" 2>/dev/null; then
    bad "Checkout failed; source left unchanged."
    exit 1
  fi
  if ! git -C "$REPO_DIR" pull --ff-only origin "$BRANCH"; then
    bad "Fast-forward pull failed; source left unchanged."
    exit 1
  fi
else
  echo -e "${DIM}Cloning source:${NC} $REPO_URL"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$REPO_DIR" || { bad "clone failed"; exit 1; }
fi
ok "Source updated"

# 2. Reinstall with same choices (single unified install — no profiles)
if ! cd "$REPO_DIR"; then
  bad "Cannot enter the updated source directory; reinstall stopped."
  exit 1
fi
VERSION="$(tr -d '[:space:]' < "$REPO_DIR/skill/sps/VERSION" 2>/dev/null || echo "unknown")"
echo -e "${DIM}Installing SPS v${VERSION}…${NC}"
# Preserve the agents selection recorded at install time (m-4): the manifest
# stores the original --agents value; without this, a user who installed with
# e.g. --agents claude-code,cursor would silently get AGENTS='*' (every host).
UPDATE_AGENT_ARGS=()
if [[ -f "$MANIFEST" ]]; then
  _saved_agents="$(grep '^AGENTS=' "$MANIFEST" 2>/dev/null | cut -d= -f2- | tr -d '[:space:]')"
  if [[ -n "$_saved_agents" && "$_saved_agents" != "*" ]]; then
    UPDATE_AGENT_ARGS=(--agents "$_saved_agents")
    echo -e "${DIM}Preserving agents selection:${NC} $_saved_agents"
  fi
  # Preserve a core-only choice (m-4): a user who installed --no-extras must
  # not get 26 third-party skills + 11 plugins pulled in by the update's
  # --yes (which would otherwise read as full extras consent). Older
  # manifests without the field default to extras (the historical behavior).
  _saved_extras="$(grep '^INSTALL_EXTRAS=' "$MANIFEST" 2>/dev/null | cut -d= -f2-)"
  if [[ "$_saved_extras" == "false" ]]; then
    UPDATE_EXTRAS_ARGS=(--no-extras)
    echo -e "${DIM}Preserving core-only install (no third-party extras)${NC}"
  else
    UPDATE_EXTRAS_ARGS=()
  fi
fi
bash ./install.sh --yes "${UPDATE_EXTRAS_ARGS[@]+${UPDATE_EXTRAS_ARGS[@]}}" "${UPDATE_AGENT_ARGS[@]+${UPDATE_AGENT_ARGS[@]}}"
rc=$?
if [[ $rc -ne 0 ]]; then
  bad "Reinstall failed (exit $rc). See ~/.sps/install.log"
  exit 1
fi

# 3. Verify with doctor
echo ""
if [[ -f "$REPO_DIR/scripts/sps-doctor.sh" ]]; then
  bash "$REPO_DIR/scripts/sps-doctor.sh"
fi

echo ""
ok "SPS updated. Restart your agent session so the new skill body loads."
exit 0
