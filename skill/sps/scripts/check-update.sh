#!/usr/bin/env bash
# SPS check-update — compare installed version against the latest release.
# Offline-safe: cached 24h in ~/.sps/update-state.env; --force bypasses cache.
#
# Usage:
#   bash scripts/check-update.sh            # cached check (24h TTL)
#   bash scripts/check-update.sh --force    # fresh network check
#
# Exit codes:
#   0 = up to date
#   1 = update available
#   2 = offline / cannot check (non-fatal)

set -uo pipefail

RAW_VERSION_URL="https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/skill/sps/VERSION"
STATE_FILE="$HOME/.sps/update-state.env"
TTL_SECONDS=86400
FORCE=false

for arg in "$@"; do
  [[ "$arg" == "--force" || "$arg" == "-f" ]] && FORCE=true
done

GREEN='\033[0;32m'; YELLOW='\033[1;33m'
DIM='\033[2m'; BOLD='\033[1m'; NC='\033[0m'

# The state file is written with a temp file + atomic rename so a crash,
# disk-full, or concurrent run can never leave a torn record behind: a
# partially-written STATUS line would otherwise be read back as an empty
# status and mis-scored as "up to date" on the next cached run.
write_state() {
  local tmp
  tmp="$(mktemp "$HOME/.sps/update-state.XXXXXX")" || return 1
  printf 'CHECKED_AT=%s\nSTATUS=%s\nLATEST=%s\n' "$1" "$2" "$3" > "$tmp" \
    && mv -f "$tmp" "$STATE_FILE"
}

installed_version() {
  local manifest="$HOME/.sps/install-manifest.env"
  if [[ -f "$manifest" ]]; then
    local v
    v="$(grep '^SPS_VERSION=' "$manifest" | head -1 | cut -d= -f2)"
    [[ -n "$v" ]] && { echo "$v"; return; }
  fi
  local cand
  for cand in "$HOME/.sps/src/BuildPilot/skill/sps/VERSION" \
              "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/skill/sps/VERSION"; do
    if [[ -f "$cand" ]]; then
      tr -d '[:space:]' < "$cand"
      return
    fi
  done
  echo "unknown"
}

is_valid_version() {
  # Remote content is untrusted input. Accept strict semver-ish
  # MAJOR.MINOR.PATCH with an optional -PRERELEASE suffix only; anything
  # else is treated as "cannot determine latest", never as a version.
  # Each component is capped at 9 digits: is_greater compares through bash
  # 64-bit arithmetic, and a longer run (e.g. 2^63 as MAJOR) would wrap and
  # invert the comparison.
  printf '%s' "$1" | grep -Eq '^[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}(-[0-9A-Za-z.-]+)?$'
}

is_valid_cached_state() {
  local latest="$1" status="$2"
  case "$status" in
    up-to-date|update-available|offline) ;;
    *) return 1 ;;
  esac
  if [[ "$status" == "offline" ]]; then
    [[ -z "$latest" || "$latest" == "unknown" ]]
  else
    is_valid_version "$latest"
  fi
}

numeric_identifier_greater() {
  local left="$1" right="$2"
  # Compare unbounded numeric prerelease identifiers without shell integer
  # conversion. Normalize leading zeroes so equal values remain equal.
  while [[ ${#left} -gt 1 && "${left:0:1}" == "0" ]]; do left="${left:1}"; done
  while [[ ${#right} -gt 1 && "${right:0:1}" == "0" ]]; do right="${right:1}"; done
  if (( ${#left} > ${#right} )); then return 0; fi
  if (( ${#left} < ${#right} )); then return 1; fi
  [[ "$left" > "$right" ]]
}

is_greater() {
  # returns 0 if a > b (numeric semver compare, including prerelease
  # precedence), 1 otherwise
  # Callers must validate both operands with is_valid_version first.
  local a="$1" b="$2"
  if ! is_valid_version "$a" || ! is_valid_version "$b"; then return 1; fi
  local a_core="${a%%-*}" b_core="${b%%-*}"
  local ai bi
  IFS='.' read -r -a ai <<< "$a_core"
  IFS='.' read -r -a bi <<< "$b_core"
  for i in 0 1 2; do
    local av="${ai[$i]:-0}" bv="${bi[$i]:-0}"
    if (( 10#$av > 10#$bv )); then return 0; fi
    if (( 10#$av < 10#$bv )); then return 1; fi
  done

  local a_prerelease="" b_prerelease=""
  [[ "$a" == *-* ]] && a_prerelease="${a#*-}"
  [[ "$b" == *-* ]] && b_prerelease="${b#*-}"
  if [[ -z "$a_prerelease" && -n "$b_prerelease" ]]; then return 0; fi
  if [[ -n "$a_prerelease" && -z "$b_prerelease" ]]; then return 1; fi
  [[ "$a_prerelease" == "$b_prerelease" ]] && return 1

  local -a a_parts b_parts
  IFS='.' read -r -a a_parts <<< "$a_prerelease"
  IFS='.' read -r -a b_parts <<< "$b_prerelease"
  local count=$(( ${#a_parts[@]} > ${#b_parts[@]} ? ${#a_parts[@]} : ${#b_parts[@]} ))
  for ((i = 0; i < count; i++)); do
    av="${a_parts[$i]:-}"
    bv="${b_parts[$i]:-}"
    if [[ -z "$av" ]]; then return 1; fi
    if [[ -z "$bv" ]]; then return 0; fi
    if [[ "$av" =~ ^[0-9]+$ && "$bv" =~ ^[0-9]+$ ]]; then
      if numeric_identifier_greater "$av" "$bv"; then return 0; fi
      if numeric_identifier_greater "$bv" "$av"; then return 1; fi
    elif [[ "$av" =~ ^[0-9]+$ ]]; then
      return 1
    elif [[ "$bv" =~ ^[0-9]+$ ]]; then
      return 0
    elif [[ "$av" < "$bv" ]]; then
      return 1
    elif [[ "$av" > "$bv" ]]; then
      return 0
    fi
  done
  return 1
}

INSTALLED="$(installed_version)"
if [[ "$INSTALLED" != "unknown" ]] && ! is_valid_version "$INSTALLED"; then
  echo "SPS installed version is malformed; treating as unknown" >&2
  INSTALLED="unknown"
fi

# 1. Cached state fresh enough?
if [[ "$FORCE" != true && -f "$STATE_FILE" ]]; then
  last=""
  last="$(grep '^CHECKED_AT=' "$STATE_FILE" 2>/dev/null | cut -d= -f2)"
  now="$(date +%s)"
  # CHECKED_AT is untrusted state: reject anything but a sane epoch-seconds
  # value (<= 12 digits), and reject ANY future value outright — a future
  # timestamp has no legitimate use, and one just under now+TTL would extend
  # the cache's authority to ~2x TTL. 10# forces base-10: a leading-zero
  # value would otherwise be read as octal (or error), which defeats exactly
  # this guard.
  if [[ -n "$last" ]] && { ! [[ "$last" =~ ^[0-9]{1,12}$ ]] || (( 10#$last > now )); }; then
    echo "SPS update state is corrupt (CHECKED_AT); ignoring cache" >&2
    last=""
  fi
  if [[ -n "$last" ]] && (( now - 10#$last < TTL_SECONDS )); then
    latest="" status=""
    latest="$(grep '^LATEST=' "$STATE_FILE" 2>/dev/null | cut -d= -f2)"
    status="$(grep '^STATUS=' "$STATE_FILE" 2>/dev/null | cut -d= -f2)"
    [[ -z "$latest" ]] && latest="unknown"
    if is_valid_cached_state "$latest" "$status"; then
      [[ "$status" == "offline" ]] && exit 2
      cached_status="update-available"
      if [[ "$INSTALLED" != "unknown" ]] && {
        [[ "$INSTALLED" == "$latest" ]] || is_greater "$INSTALLED" "$latest"
      }; then
        cached_status="up-to-date"
      fi
      echo "SPS installed: $INSTALLED | latest: $latest | status: $cached_status (cached)"
      [[ "$cached_status" == "update-available" ]] && exit 1
      exit 0
    fi
    echo "SPS update state is corrupt (cached version/status); ignoring cache" >&2
    last=""
  fi
fi

# 2. Fresh check
latest=""
if command -v curl >/dev/null 2>&1; then
  latest="$(curl -fsSL --max-time 10 "$RAW_VERSION_URL" 2>/dev/null | tr -d '[:space:]')"
fi

mkdir -p "$HOME/.sps"
if [[ -z "$latest" || "$latest" == "unknown" ]]; then
  echo "SPS version check: offline (installed $INSTALLED)" >&2
  write_state "$(date +%s)" offline unknown
  exit 2
fi

# Remote VERSION is untrusted input: a malformed value is "cannot determine
# latest", never evidence that the installed version is up to date.
if ! is_valid_version "$latest"; then
  echo "SPS version check: remote VERSION is malformed (${latest}); treating as unavailable" >&2
  write_state "$(date +%s)" offline unknown
  exit 2
fi

if [[ "$INSTALLED" == "$latest" ]]; then
  echo -e "${GREEN}${BOLD}SPS is up to date${NC} (v${INSTALLED})"
  write_state "$(date +%s)" up-to-date "$latest"
  exit 0
fi

if is_greater "$INSTALLED" "$latest"; then
  # local install is ahead of remote (dev build) — treat as up to date
  echo -e "${GREEN}${BOLD}SPS is up to date${NC} (local v${INSTALLED} > remote v${latest})"
  write_state "$(date +%s)" up-to-date "$latest"
  exit 0
fi

echo -e "${YELLOW}${BOLD}SPS update available:${NC} v${INSTALLED} → v${latest}"
echo -e "${DIM}Run: bash scripts/sps-update.sh --yes${NC}"
write_state "$(date +%s)" update-available "$latest"
exit 1
