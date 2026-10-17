#!/usr/bin/env bash
set -e

# ==============================================================================
# ⚡ SPS-CMS Skill Uninstaller
# ==============================================================================

SKILL_NAME="sps-cms"

TARGET_DIRS=(
  "$HOME/.gemini/config/skills/$SKILL_NAME"
  "$HOME/.claude/skills/$SKILL_NAME"
  "$HOME/.cursor/skills/$SKILL_NAME"
  "$HOME/.windsurf/skills/$SKILL_NAME"
  "$HOME/.codeium/windsurf/skills/$SKILL_NAME"
  "$HOME/.config/opencode/skills/$SKILL_NAME"
  "$HOME/.agents/skills/$SKILL_NAME"
)

echo "🗑️ [SPS-CMS] Removing skill from all agent directories..."

for TARGET in "${TARGET_DIRS[@]}"; do
  if [ -d "$TARGET" ]; then
    rm -rf "$TARGET"
    echo "  ❌ Removed: $TARGET"
  fi
done

echo "✨ [SPS-CMS] Successfully uninstalled from all agent environments."
