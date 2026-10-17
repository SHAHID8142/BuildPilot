#!/usr/bin/env bash
set -e

# ==============================================================================
# ⚡ SPS-CMS Universal Multi-Agent Skill Installer
# Compatible with macOS, Linux, WSL, and Windows (Git Bash)
# Installs to: Antigravity, Claude Code, Cursor, Windsurf, OpenCode, Codex, etc.
# ==============================================================================

SKILL_NAME="sps-cms"
REPO_URL="https://github.com/SHAHID8142/sps-cms"
TMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'sps-cms')

cleanup() {
  if [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ [SPS-CMS] Universal Skill Installer (v1.1.0)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 Fetching latest release from $REPO_URL..."

# Clone or download
if command -v git >/dev/null 2>&1; then
  git clone --depth 1 "$REPO_URL.git" "$TMP_DIR/$SKILL_NAME" 2>/dev/null || {
    echo "⚠️  Git clone failed, falling back to tarball download..."
    mkdir -p "$TMP_DIR/$SKILL_NAME"
    curl -fsSL "$REPO_URL/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP_DIR/$SKILL_NAME" --strip-components=1
  }
else
  mkdir -p "$TMP_DIR/$SKILL_NAME"
  curl -fsSL "$REPO_URL/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP_DIR/$SKILL_NAME" --strip-components=1
fi

# List of all standard target paths across modern coding agents
TARGET_DIRS=(
  "$HOME/.gemini/config/skills/$SKILL_NAME"
  "$HOME/.claude/skills/$SKILL_NAME"
  "$HOME/.cursor/skills/$SKILL_NAME"
  "$HOME/.windsurf/skills/$SKILL_NAME"
  "$HOME/.codeium/windsurf/skills/$SKILL_NAME"
  "$HOME/.config/opencode/skills/$SKILL_NAME"
  "$HOME/.agents/skills/$SKILL_NAME"
)

INSTALLED_COUNT=0

for TARGET in "${TARGET_DIRS[@]}"; do
  # Ensure target directory exists
  mkdir -p "$TARGET"
  
  # Copy files cleanly
  cp -R "$TMP_DIR/$SKILL_NAME/"* "$TARGET/"
  
  # Ensure scripts are executable
  if [ -d "$TARGET/scripts" ]; then
    chmod +x "$TARGET/scripts/"*.sh 2>/dev/null || true
  fi
  
  echo "  ✅ Installed to: $TARGET"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ [SPS-CMS] Successfully installed across $INSTALLED_COUNT agent paths!"
echo "🚀 Ready to use in:"
echo "   • Antigravity (Google DeepMind) → ~/.gemini/config/skills/sps-cms"
echo "   • Claude Code (Anthropic)       → ~/.claude/skills/sps-cms"
echo "   • Cursor IDE                    → ~/.cursor/skills/sps-cms"
echo "   • Windsurf / Cascade            → ~/.windsurf/skills/sps-cms"
echo "   • OpenCode / Codex / Copilot    → ~/.agents/skills/sps-cms"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
