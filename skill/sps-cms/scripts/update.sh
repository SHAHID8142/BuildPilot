#!/usr/bin/env bash
set -e

# ==============================================================================
# ⚡ SPS-CMS Skill Updater
# ==============================================================================

echo "⚡ [SPS-CMS] Fetching latest release updates..."
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.sh | bash
echo "✨ [SPS-CMS] Update complete!"
