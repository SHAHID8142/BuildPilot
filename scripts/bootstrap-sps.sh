#!/usr/bin/env bash
# Bootstrap project-local .sps/ memory from SPS templates.
# Usage:
#   bash scripts/bootstrap-sps.sh [target-project-dir]
#   bash scripts/bootstrap-sps.sh --force [target-project-dir]

set -euo pipefail

FORCE=false
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force|-f) FORCE=true; shift ;;
    --help|-h)
      echo "Usage: bash scripts/bootstrap-sps.sh [--force] [target-dir]"
      exit 0
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$REPO/skills/sps/templates"
VERSION="$(tr -d '[:space:]' < "$REPO/skills/sps/VERSION" 2>/dev/null || echo "unknown")"
TARGET="${TARGET:-$PWD}"
DEST="$TARGET/.sps"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Template directory missing: $TEMPLATE_DIR" >&2
  exit 1
fi

if [[ -L "$DEST" ]]; then
  echo "Refusing symlinked SPS destination: $DEST" >&2
  exit 1
fi
if [[ -e "$DEST" && ! -d "$DEST" ]]; then
  echo "SPS destination is not a directory: $DEST" >&2
  exit 1
fi

# Preflight every path this script writes before copying any template. In
# particular, --force must never follow a file symlink into user data.
for name in profile.md handoff.md mistakes.md agent.md audit-report.md plan.md \
            content-model.md cms-foundation.md cms-debt.md design-system.md \
            architecture.md section-registry.md changelog-sps.md; do
  if [[ -L "$DEST/$name" ]]; then
    echo "Refusing symlinked template destination: $DEST/$name" >&2
    exit 1
  fi
done
if [[ -L "$DEST/section-todos" || -L "$DEST/section-todos/README.md" ]]; then
  echo "Refusing symlinked section-todos destination: $DEST/section-todos" >&2
  exit 1
fi

mkdir -p "$DEST"

copy_template() {
  local name="$1"
  local dest="$DEST/$name"
  if [[ -f "$dest" && "$FORCE" != true ]]; then
    echo "keep  $dest"
    return
  fi
  cp "$TEMPLATE_DIR/$name" "$dest"
  # Stamp version into newly written agent/profile/handoff when placeholders exist
  if [[ "$name" == "agent.md" || "$name" == "profile.md" || "$name" == "handoff.md" ]]; then
    if grep -q "Skill version:" "$dest"; then
      tmp="$(mktemp)"
      sed "s/Skill version:.*/Skill version: $VERSION/" "$dest" > "$tmp"
      mv "$tmp" "$dest"
    fi
  fi
  echo "write $dest"
}

copy_template "profile.md"
copy_template "handoff.md"
copy_template "mistakes.md"
copy_template "agent.md"
copy_template "audit-report.md"
copy_template "plan.md"
copy_template "content-model.md"
copy_template "cms-foundation.md"
copy_template "cms-debt.md"
copy_template "design-system.md"
copy_template "architecture.md"
copy_template "section-registry.md"
copy_template "changelog-sps.md"

mkdir -p "$DEST/section-todos"
if [[ ! -f "$DEST/section-todos/README.md" || "$FORCE" == true ]]; then
  cat > "$DEST/section-todos/README.md" <<EOF
# Section todos

Create one file per section using skills/sps/TODO-FORMAT.md
EOF
  echo "write $DEST/section-todos/README.md"
fi

# Root mirrors (append lock if files missing or lack lock)
GEMINI_LOCK_BLOCK='## /sps lock (required)

This project is under `/sps` orchestration. Antigravity must NOT use a host-default
scaffold workflow instead of `/sps`.

Before any code:
1. Read `./.sps/profile.md` and `./.sps/handoff.md`
2. Read the SPS Method Card from the installed `sps` skill (`METHOD-CARD.md`)
3. Build work requires an approved `./.sps/plan.md` — zero code before plan approval
4. Follow CMS-coupled section delivery when CMS is enabled (engine skill: sps-cms)
5. Stop for approval after each section Definition of Done; user manually checks each section

Commands: `/sps` · `/sps audit` · `/sps sync` · `/sps doctor`

## SPS behavioral rules (required, Karpathy)

1. Think before coding: state assumptions, enumerate interpretations, ask if ambiguous.
2. Simplicity first: deliver the minimum code the task requires; no speculative features.
3. Surgical changes: edit only what the request requires; never refactor unrelated code.
4. Goal-driven execution: define visible success criteria and verify them before claiming done.
5. Never claim verification that was not actually run (no "should pass").'

LOCK_BLOCK='## /sps lock
This project uses `/sps` as the master workflow.
Read `./.sps/profile.md`, `./.sps/handoff.md`, and the SPS Method Card before
building. Do not replace `/sps` with a host-default scaffolding workflow.
Build work requires an approved `./.sps/plan.md` (zero code before plan approval).
CMS-enabled sections must ship storefront + CMS controls together (engine: sps-cms).
Each section ends with a user manual check before the next section starts.'

for root_file in AGENTS.md GEMINI.md CLAUDE.md; do
  target="$TARGET/$root_file"
  block="$LOCK_BLOCK"
  [[ "$root_file" == "GEMINI.md" ]] && block="$GEMINI_LOCK_BLOCK"
  if [[ ! -f "$target" ]]; then
    printf '%s\n' "$block" > "$target"
    echo "write $target"
  elif ! grep -q "/sps lock" "$target"; then
    printf '\n%s\n' "$block" >> "$target"
    echo "append $target"
  else
    echo "keep  $target"
  fi
done

echo "Bootstrapped $DEST (SPS $VERSION)"
echo "Next: open the project in your agent and run /sps (or /sps audit, /sps sync)"
