#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# ⚡ SPS-CMS Skill Updater
# ==============================================================================
# Security (audit m-7): never pipe a remote script straight into bash. Download
# to a temp file first so the user can inspect it, and require an explicit yes
# (or --yes) before executing fetched code.

SCRIPT_URL="https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.sh"

ASSUME_YES=false
for a in "$@"; do
  case "$a" in
    --yes|-y) ASSUME_YES=true ;;
    *) echo "unknown option: $a (usage: update.sh [--yes])" >&2; exit 1 ;;
  esac
done

echo "⚡ [SPS-CMS] Fetching latest release updates..."
TMP="$(mktemp -t sps-cms-install-XXXXXX.sh)"
trap 'rm -f "$TMP"' EXIT
curl -fsSL "$SCRIPT_URL" -o "$TMP"
echo "downloaded installer → $TMP ($(wc -c < "$TMP" | tr -d ' ') bytes)"
echo "review it:  less $TMP"
if [ "$ASSUME_YES" != "true" ]; then
  read -r -p "Run the downloaded sps-cms installer now? (yes/no): " confirm
  case "${confirm:-no}" in
    y|Y|yes|YES) ;;
    *) echo "Aborted — nothing was run. Install manually: bash $TMP"; exit 0 ;;
  esac
fi
bash "$TMP"
echo "✨ [SPS-CMS] Update complete!"
