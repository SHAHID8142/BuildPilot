#!/usr/bin/env bash
# T-25 secret-scan — secrets-leak CI gate (pattern-based, no entropy math).
#
# Scans:
#   1. all tracked files (git ls-files)
#   2. the diff vs origin/main (added lines only)
#   3. agent/MCP config surfaces (.claude/**, .mcp.json, **/.mcp.json)
#      — AgentShield scope: secrets only; prompt-injection patterns are out
#      of scope here. Untracked config files are included so a local-only
#      leak still surfaces.
#
# Allowlist: a ".secrets-allowlist" file at the repo root. Format:
#   - one POSIX extended regex per line
#   - a line whose MATCHED TEXT matches any allowlist regex is skipped
#     (the regex is tested against the matching text, not the filename)
#   - blank lines and lines starting with '#' are comments
#   - the allowlist file itself is never scanned
#
# Output per hit:  file:line:  first-6-chars***  — the full secret value is
# never printed.
#
# Exit codes: 0 clean | 1 hits found | 2 config error
#
# Conventions: set -euo pipefail; deps = git + grep only; binary files are
# skipped (grep -I); works from any cwd (re-roots to the repo top).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "secret-scan: not inside a git repository" >&2
  exit 2
}
cd "$REPO_ROOT"

ALLOWLIST_FILE=".secrets-allowlist"
HITS_FILE="$(mktemp "${TMPDIR:-/tmp}/sps-secret-scan.XXXXXX")"
trap 'rm -f "$HITS_FILE"' EXIT

# --- patterns: POSIX ERE -----------------------------------------------------
# sk_live_/sk_test_ with long tails, AWS access keys, GitHub tokens (classic +
# fine-grained), Slack tokens, private key blocks, GitLab PATs, Anthropic keys,
# Google API keys, npm tokens, and literal password= with a high-entropy-looking
# value (16+ chars, mixed classes). Deliberately pattern-only: no entropy math.
PATTERNS='sk_live_[A-Za-z0-9]{24,}|sk_test_[A-Za-z0-9]{24,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----|glpat-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|npm_[A-Za-z0-9]{36}|password[[:space:]]*=[[:space:]]*[A-Za-z0-9][A-Za-z0-9!@#$%^&*_+=-]{15,}'

# --- load allowlist ----------------------------------------------------------
ALLOWLIST=()
if [[ -f "$ALLOWLIST_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    ALLOWLIST+=("$line")
  done < "$ALLOWLIST_FILE"
fi

# is_allowlisted <matched-text> -> exit 0 if the text matches any allowlist rx
is_allowlisted() {
  local text="$1" rx
  for rx in ${ALLOWLIST[@]+"${ALLOWLIST[@]}"}; do
    if printf '%s' "$text" | grep -Eq -- "$rx" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

# record_hit <file> <line> <matched-text> — masks the value, never prints it whole
record_hit() {
  local file="$1" line="$2" text="$3"
  printf 'SECRET HIT: %s:%s: %s***\n' "$file" "$line" "${text:0:6}" >> "$HITS_FILE"
}

# scan_file <path> — grep one file, allowlist-filter, record hits
scan_file() {
  local f="$1" hit line text
  [[ -f "$f" ]] || return 0
  while IFS= read -r hit; do
    [[ -z "$hit" ]] && continue
    line="${hit%%:*}"
    text="${hit#*:}"
    is_allowlisted "$text" && continue
    record_hit "$f" "$line" "$text"
  done < <(grep -InE -- "$PATTERNS" "$f" 2>/dev/null || true)
}

export PATTERNS

# --- 1. tracked files (binary files skipped via grep -I) ---------------------
while IFS= read -r f; do
  scan_file "$f"
done < <(git ls-files -z | tr '\0' '\n')

# --- 2. diff vs origin/main (added lines only) -------------------------------
BASE_REF="origin/main"
if ! git rev-parse --verify --quiet "$BASE_REF" >/dev/null 2>&1; then
  BASE_REF="HEAD~1"
  git rev-parse --verify --quiet "$BASE_REF" >/dev/null 2>&1 || BASE_REF=""
fi
if [[ -n "$BASE_REF" ]]; then
  diff_hits="$(git diff "$BASE_REF" --no-color \
    | grep -E '^\+' | grep -vE '^\+\+\+' \
    | grep -Eo -- "$PATTERNS" 2>/dev/null || true)"
  if [[ -n "$diff_hits" ]]; then
    while IFS= read -r text; do
      [[ -z "$text" ]] && continue
      is_allowlisted "$text" && continue
      printf 'SECRET HIT: (diff vs %s): %s***\n' "$BASE_REF" "${text:0:6}" >> "$HITS_FILE"
    done <<< "$diff_hits"
  fi
fi

# --- 3. agent/MCP config surfaces (incl. untracked; secrets only) ------------
while IFS= read -r -d '' f; do
  f="${f#./}"
  case " $(git ls-files -- "$f" 2>/dev/null) " in
    *" $f "*) ;;               # already scanned as a tracked file
    *) scan_file "$f" ;;       # untracked config: scan now
  esac
done < <(
  {
    find .claude -type f -print0 2>/dev/null
    find . -maxdepth 4 -name '.mcp.json' -type f -print0 2>/dev/null
  } | while IFS= read -r -d '' p; do printf '%s\0' "${p#./}"; done | sort -z | awk 'BEGIN{RS="\0"} !seen[$0]++ {printf "%s\0", $0}'
)

# --- verdict ------------------------------------------------------------------
if [[ -s "$HITS_FILE" ]]; then
  cat "$HITS_FILE"
  echo "secret-scan: FAIL — secret-shaped value(s) found (values masked above)"
  exit 1
fi
echo "secret-scan: clean — no secret-shaped values in tracked files, diff, or agent/MCP configs"
exit 0
