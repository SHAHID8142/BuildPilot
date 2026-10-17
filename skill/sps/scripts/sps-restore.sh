#!/usr/bin/env bash
# sps-restore.sh — one-command rollback of an installed SPS skill (T-26)
# Usage:
#   bash scripts/sps-restore.sh                 # interactive: list skills + backups, pick
#   bash scripts/sps-restore.sh <skill>         # e.g. sps — list that skill's backups, pick
#   bash scripts/sps-restore.sh <skill> <n>     # e.g. sps 2 — preview 2nd-newest backup
#   bash scripts/sps-restore.sh <skill> <n> --yes   # actually replace
#
# Backups live in ~/.sps/backups/<skill>/<timestamp>/ (written by install.sh's
# backup_existing_skill, which keeps the last 3 per skill). This tool lists
# them, previews the chosen one, and with --yes copies it into every install
# destination (install.sh's SYNC_PATHS, read from ~/.sps/install-manifest.env
# when present, else the built-in default paths). It runs sps-doctor.sh at the
# end and prints its summary. Backups are NEVER deleted; replace = copy over.
# Conventions: set -euo pipefail; TTY-gated ANSI; deps = bash only.
set -euo pipefail

if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_DIM=$'\033[2m'; C_END=$'\033[0m'
else
  C_OK=""; C_WARN=""; C_DIM=""; C_END=""
fi

BACKUP_ROOT="$HOME/.sps/backups"
MANIFEST="$HOME/.sps/install-manifest.env"

# SYNC_PATHS for the requested skill: manifest first (matches the installer
# that made the backups), then the built-in default list.
sync_paths() {
  if [ -f "$MANIFEST" ] && grep -q '^SYNC_PATHS=' "$MANIFEST"; then
    grep '^SYNC_PATHS=' "$MANIFEST" | head -1 | cut -d= -f2- | tr ',' '\n'
    return 0
  fi
  printf '%s\n' \
    "$HOME/.claude/skills" "$HOME/.cursor/skills" "$HOME/.codex/skills" \
    "$HOME/.agents/skills" "$HOME/.config/agents/skills" \
    "$HOME/.gemini/config/skills" "$HOME/.gemini/skills" \
    "$HOME/.gemini/antigravity/skills" "$HOME/.gemini/antigravity-cli/skills" \
    "$HOME/.codeium/windsurf/skills" "$HOME/.windsurf/skills" \
    "$HOME/.config/opencode/skills" "$HOME/.cline/skills" "$HOME/.roo/skills" \
    "$HOME/.kiro/skills" "$HOME/.amp/skills" "$HOME/.github/skills" \
    "$HOME/.config/goose/skills" "$HOME/.goose/skills" "$HOME/.crush/skills" \
    "$HOME/.config/trae/skills" "$HOME/.trae/skills" "$HOME/.junie/skills" \
    "$HOME/.config/junie/skills" "$HOME/.zed/skills" "$HOME/.openclaw/skills" \
    "$HOME/.droid/skills" "$HOME/.qoder/skills" "$HOME/.kilocode/skills" \
    "$HOME/.warp/plugins/skills" "$HOME/.grok/skills" "$HOME/.hermes/skills" \
    "$HOME/.autohand/skills" "$HOME/.zeroclaw/skills"
}

skill="${1:-}"
pick="${2:-}"
yes_flag="no"
for a in "$@"; do [ "$a" = "--yes" ] && yes_flag="yes"; done

echo "SPS restore — rollback an installed skill from ~/.sps/backups/"
echo ""

# --- no skill arg: show available skills ---------------------------------------
if [ -z "$skill" ]; then
  if [ ! -d "$BACKUP_ROOT" ]; then
    echo "no backups yet — ~/.sps/backups/ does not exist (created by install.sh on upgrade)"
    exit 0
  fi
  echo "Available skills with backups:"
  for d in "$BACKUP_ROOT"/*/; do
    [ -d "$d" ] || continue
    n="$(ls -1d "$d"*/ 2>/dev/null | wc -l | tr -d ' ')"
    echo "  $(basename "$d")  ($n backup(s))"
  done
  echo ""
  echo "usage: sps-restore.sh <skill> [index] [--yes]"
  exit 0
fi

skill_dir="$BACKUP_ROOT/$skill"
if [ ! -d "$skill_dir" ]; then
  echo "sps-restore: no backups for skill '$skill' in $BACKUP_ROOT" >&2
  exit 1
fi

# Newest-first list (install.sh stamps sort chronologically; -x suffixes sort after).
# Portable: no mapfile (bash 3.2 on stock macOS lacks it).
snaps=()
while IFS= read -r d; do [ -n "$d" ] && snaps+=("$d"); done < <(ls -1dt "$skill_dir"/*/ 2>/dev/null)
if [ "${#snaps[@]}" -eq 0 ]; then
  echo "sps-restore: backup dir for '$skill' is empty" >&2
  exit 1
fi

echo "Backups for '$skill' (newest first):"
i=1
for s in "${snaps[@]}"; do
  stamp="$(basename "$s")"
  files="$(find "$s" -type f 2>/dev/null | wc -l | tr -d ' ')"
  echo "  $i) $stamp  ($files files)"
  i=$((i + 1))
done
echo ""

# --- pick ----------------------------------------------------------------------
if [ -n "$pick" ]; then
  case "$pick" in
    ''|*[!0-9]*) echo "sps-restore: index must be a number, got: $pick" >&2; exit 2 ;;
  esac
  if [ "$pick" -lt 1 ] || [ "$pick" -gt "${#snaps[@]}" ]; then
    echo "sps-restore: index $pick out of range (1-${#snaps[@]})" >&2
    exit 2
  fi
else
  if [ ! -t 0 ]; then
    echo "sps-restore: pass an index (sps-restore.sh $skill 1) — not interactive here" >&2
    exit 2
  fi
  printf 'Restore which one? [1-%s] ' "${#snaps[@]}"
  read -r pick
  case "$pick" in
    ''|*[!0-9]*) echo "sps-restore: cancelled (not a number)" >&2; exit 2 ;;
  esac
  if [ "$pick" -lt 1 ] || [ "$pick" -gt "${#snaps[@]}" ]; then
    echo "sps-restore: index out of range" >&2
    exit 2
  fi
fi
chosen="${snaps[$((pick - 1))]}"
echo "PREVIEW: $skill <- $(basename "$chosen")"
echo "  contents:"
find "$chosen" -type f | head -8 | sed "s|^$chosen|    |"
[ "$(find "$chosen" -type f | wc -l | tr -d ' ')" -gt 8 ] && echo "    …"
echo ""

if [ "$yes_flag" != "yes" ]; then
  echo "sps-restore: ${C_WARN}refusing to replace installed skills without --yes${C_END} — preview only, nothing changed"
  exit 1
fi

# --- replace into every sync path -----------------------------------------------
restored=0; missing=0
while IFS= read -r dest_root; do
  [ -n "$dest_root" ] || continue
  dest="$dest_root/$skill"
  if [ ! -d "$dest_root" ]; then
    echo "  skip (host dir absent): ${dest_root/#$HOME/\~}"
    missing=$((missing + 1))
    continue
  fi
  rm -rf "$dest"
  cp -R "$chosen" "$dest"
  echo "  ${C_OK}restored${C_END} ${dest/#$HOME/\~}"
  restored=$((restored + 1))
done < <(sync_paths)

echo ""
echo "RESTORED: '$skill' from $(basename "$chosen") into $restored destination(s) ($missing host dir(s) absent)"
[ -d "$HOME/.claude/skills/sps" ] && [ "$skill" = "sps" ] && echo "  note: host-local scripts under ~/.claude/skills/sps/scripts/ were replaced too — rerun sps-update.sh if you customized them"

# --- doctor ----------------------------------------------------------------------
doctor=""
for cand in "$(pwd)/scripts/sps-doctor.sh" "$(git rev-parse --show-toplevel 2>/dev/null)/scripts/sps-doctor.sh" "$HOME/.sps/src/BuildPilot/scripts/sps-doctor.sh"; do
  [ -n "$cand" ] && [ -f "$cand" ] && doctor="$cand" && break
done
if [ -n "$doctor" ]; then
  echo ""
  echo "Running sps-doctor.sh to verify:"
  bash "$doctor" || true
else
  echo "sps-restore: sps-doctor.sh not found — verify manually (bash scripts/sps-doctor.sh)"
fi
