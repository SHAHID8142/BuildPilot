#!/usr/bin/env bash
# One-command SPS bootstrap: clone/pull repo, then install.
#
# Recommended:
#   curl -fsSL https://raw.githubusercontent.com/SHAHID8142/Shahid-Personal-SkillSet/main/get-sps.sh | bash
#
# With options:
#   curl -fsSL .../get-sps.sh | bash -s -- --yes
#   curl -fsSL .../get-sps.sh | bash -s -- --agents claude-code,cursor --yes
#
# Local:
#   bash get-sps.sh --yes

set -euo pipefail

REPO_URL="${SPS_REPO_URL:-https://github.com/SHAHID8142/Shahid-Personal-SkillSet.git}"
REPO_DIR="${SPS_REPO_DIR:-$HOME/.sps/src/Shahid-Personal-SkillSet}"
BRANCH="${SPS_BRANCH:-main}"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

banner() {
  echo ""
  echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}${BOLD}║${NC}  ${BOLD}Shahid Personal SkillSet${NC}  —  one-command setup          ${CYAN}${BOLD}║${NC}"
  echo -e "${CYAN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

have() { command -v "$1" >/dev/null 2>&1; }

banner

if ! have git; then
  echo -e "${YELLOW}git is required. Install git, then retry.${NC}"
  exit 1
fi
if ! have node || ! have npx; then
  echo -e "${YELLOW}Node.js + npx are required: https://nodejs.org${NC}"
  exit 1
fi

mkdir -p "$(dirname "$REPO_DIR")"

if [[ -d "$REPO_DIR/.git" ]]; then
  echo -e "${DIM}Updating existing clone:${NC} $REPO_DIR"
  if ! status="$(git -C "$REPO_DIR" status --porcelain=v1 2>/dev/null)"; then
    echo -e "${YELLOW}Cannot verify the source worktree; refusing to update.${NC}" >&2
    exit 1
  fi
  if [[ -n "$status" ]]; then
    echo -e "${YELLOW}Local changes present in $REPO_DIR; refusing to update.${NC}" >&2
    echo "Commit, stash, or remove them manually, then retry." >&2
    exit 1
  fi
  if ! git -C "$REPO_DIR" fetch --prune origin "$BRANCH"; then
    echo -e "${YELLOW}Fetch failed; source left unchanged.${NC}" >&2
    exit 1
  fi
  git -C "$REPO_DIR" checkout "$BRANCH"
  if ! git -C "$REPO_DIR" pull --ff-only origin "$BRANCH"; then
    echo -e "${YELLOW}Fast-forward pull failed; source left unchanged.${NC}" >&2
    exit 1
  fi
  echo -e "${GREEN}✓${NC} Repo updated"
elif [[ -e "$REPO_DIR" ]]; then
  echo -e "${YELLOW}Destination exists but is not a Git worktree; refusing to delete it.${NC}" >&2
  exit 1
else
  echo -e "${DIM}Cloning:${NC} $REPO_URL"
  echo -e "${DIM}Into:${NC}    $REPO_DIR"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
  echo -e "${GREEN}✓${NC} Repo cloned"
fi

VERSION="unknown"
if [[ -f "$REPO_DIR/skills/sps/VERSION" ]]; then
  VERSION="$(tr -d '[:space:]' < "$REPO_DIR/skills/sps/VERSION")"
fi
echo -e "${DIM}SPS version:${NC} $VERSION"
echo ""

cd "$REPO_DIR"
exec bash ./install.sh "$@"
