#!/usr/bin/env bash
# sps-copycheck.sh — thin wrapper for the COPY-GATE validator (check_copy.py).
# Usage:
#   bash scripts/sps-copycheck.sh [project-dir] [--mode advisory|deployment]
#   (project defaults to the current directory; mode defaults to advisory)
# Deployment mode exits 1 on any CRITICAL — this is the gate run.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="."
MODE="advisory"
for arg in "$@"; do
  case "$arg" in
    --mode) ;;  # flag token, value comes next
    advisory|deployment) MODE="$arg" ;;
    --mode=*) MODE="${arg#--mode=}" ;;
    *) PROJECT="$arg" ;;
  esac
done
exec python3 "$SCRIPT_DIR/../framework/sps2/tools/check_copy.py" "$PROJECT" --mode "$MODE"
