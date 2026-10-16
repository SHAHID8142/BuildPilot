#!/usr/bin/env bash
set -e

# ==============================================================================
# ⚡ SPS-CMS Doctor (Health Check & Diagnostics)
# ==============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🩺 [SPS-CMS Doctor] Running System & Project Diagnostics..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Check Project Root Lock
if [ -f "./.sps-cms/lock.json" ] || [ -f "GEMINI.md" ] || [ -f "AGENTS.md" ]; then
  echo "  ✅ Project Root Lock: DETECTED"
else
  echo "  ⚠️ Project Root Lock: NOT FOUND (Run /sps-cms scaffold to lock)"
fi

# 2. Check Schema Config
if [ -f "./src/config/cms.config.ts" ] || [ -f "./cms.config.ts" ]; then
  echo "  ✅ CMS Schema Config: DETECTED"
else
  echo "  ⚠️ CMS Schema Config: NOT FOUND"
fi

# 3. Check Local Upload Directory & Permissions
UPLOAD_DIR="./public/uploads"
if [ -d "$UPLOAD_DIR" ]; then
  if [ -w "$UPLOAD_DIR" ]; then
    echo "  ✅ Uploads Directory ($UPLOAD_DIR): WRITABLE"
  else
    echo "  ❌ Uploads Directory ($UPLOAD_DIR): NOT WRITABLE (Check permissions)"
  fi
else
  echo "  ℹ️  Uploads Directory: Will be created on first upload."
fi

# 4. Check Environment Variables
if [ -f ".env" ]; then
  echo "  ✅ Environment File (.env): DETECTED"
else
  echo "  ⚠️ Environment File (.env): MISSING (Create .env with DB credentials)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Diagnostics completed."
