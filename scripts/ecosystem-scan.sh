#!/usr/bin/env bash
# ecosystem-scan.sh — nightly skill-ecosystem scan (read-only). Watches the 13
# SKILL-ROUTER.md domains for fresher upstream skills, vets candidates through
# trust gates, writes ONE markdown report. NOTHING is installed/modified/removed
# — proposals are data, not verdicts (DYNAMIC-SKILLS.md, TOOL-CONSENT.md).
# Exit 0 always, except: missing output-dir argument -> exit 1.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TSV="$SCRIPT_DIR/ecosystem-domains.tsv"

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
  echo "usage: ecosystem-scan.sh <output-dir>" >&2
  exit 1
fi
OUT_DIR="$1"
if [ ! -d "$OUT_DIR" ]; then
  echo "ecosystem-scan: output dir '$OUT_DIR' does not exist" >&2
  exit 1
fi

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_VERSION="$(tr -d '[:space:]' < "$REPO_ROOT/skill/sps/VERSION" 2>/dev/null || echo "unknown")"
BUNDLED_REPO="SHAHID8142/BuildPilot"
BUNDLED_RAW_VERSION_URL="https://raw.githubusercontent.com/$BUNDLED_REPO/main/skill/sps/VERSION"

NOW_EPOCH="$(date +%s)"
# Portable UTC stamps: macOS BSD date and GNU date disagree on -u handling
# with some format strings; python3 is the one formatter both trust.
DATE_UTC="$(python3 -c 'from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"))')"
REPORT="$OUT_DIR/ECOSYSTEM-SCAN-$(python3 -c 'from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))').md"

# Vet-gate thresholds
FRESH_DAYS=90    # pushed_at within 90 days
MIN_AGE_DAYS=30  # repo created_at >= 30 days ago
MIN_STARS=50     # stars >= 50 OR installs >= 200
MIN_INSTALLS=200

# Conflict-banned families (SKILL-ROUTER.md). Candidates matching these are
# rejected regardless of popularity. obra/superpowers is exempt ONLY for the
# verification domain's own primary skill (verification-before-completion).
BANNED_PATTERNS='superpowers|hallmark|ui-ux-pro-max|gpt-taste|taste-skill.*gpt|high-end-visual-design|minimalist-ui|minimalist-skill|industrial-brutalist-ui'

# API error counter is file-based: per-domain scans run in subshells (failure
# containment), so an in-memory counter would lose their increments.
API_ERRORS_FILE="$(mktemp)"

api_error() { echo 1 >> "$API_ERRORS_FILE"; }
api_error_count() { wc -l < "$API_ERRORS_FILE" | tr -d ' '; }

mkdir -p "$OUT_DIR"

# --- Helpers (defensive: untrusted API data never crashes the scan) ---

# gh_get <url> — curl GET with auth header when GITHUB_API_TOKEN is set.
gh_get() {
  local url="$1"
  if [ -n "${GITHUB_API_TOKEN:-}" ]; then
    curl -fsSL --max-time 10 -H "Authorization: Bearer $GITHUB_API_TOKEN" \
         -H "Accept: application/vnd.github+json" "$url" 2>/dev/null
  else
    curl -fsSL --max-time 10 -H "Accept: application/vnd.github+json" "$url" 2>/dev/null
  fi
}

# repo_field <owner/repo> <field> — repo metadata field; "unknown" if malformed.
# Metadata is fetched once per repo per run (keeps the 60/hr anon core limit).
REPO_CACHE="$(mktemp)"
repo_field() {
  local repo="$1" field="$2" json
  # Cache line = "TAB repo TAB json-on-one-line" (newlines stripped on store).
  json="$(grep -F "	$repo	" "$REPO_CACHE" 2>/dev/null | head -1 | cut -f3)"
  if [ -z "$json" ]; then
    json="$(gh_get "https://api.github.com/repos/$repo")" || { api_error; echo unknown; return; }
    printf '\t%s\t%s\n' "$repo" "$(printf '%s' "$json" | tr '\n' ' ')" >> "$REPO_CACHE"
  fi
  printf '%s' "$json" | python3 -c "
import json, sys
field = sys.argv[1]
try:
    d = json.load(sys.stdin)
    v = d.get(field, 'unknown')
    if v is None:
        v = 'null'
    print(v)
except Exception:
    print('unknown')
" "$field"
}

candidate_field() {
  local blob="$1" field="$2"
  printf '%s' "$blob" | python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    v = d.get(sys.argv[2], 'unknown')
    if v is None: v = 'null'
    print(v)
except Exception:
    print('unknown')
" "$field"
}

days_between() {
  python3 -c "
import sys
try:
    print(max(0, int(($NOW_EPOCH - int(sys.argv[1])) / 86400)))
except Exception:
    print('unknown')
" "$1"
}

iso_to_epoch() {
  python3 -c "
import sys
from datetime import datetime, timezone
try:
    s = sys.argv[1].replace('Z', '+00:00')
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    print(int(dt.timestamp()))
except Exception:
    print('unknown')
" "$1"
}

# github_search <query> — skill-search.sh's pattern; JSON blobs, top 5.
github_search() {
  local q_enc
  q_enc="$(printf '%s' "$1" | sed 's/ /%20/g')"
  sleep 3   # throttle: GitHub search rate limit (auth: 30 req/min, anon: 10)
  gh_get "https://api.github.com/search/repositories?q=${q_enc}+claude+skill&sort=updated&per_page=5" \
    | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for r in d.get('items', [])[:5]:
        print(json.dumps({
            'full_name': r.get('full_name'),
            'stars': r.get('stargazers_count'),
            'pushed_at': r.get('pushed_at'),
            'created_at': r.get('created_at'),
            'archived': r.get('archived'),
            'license': (r.get('license') or {}).get('spdx_id') if isinstance(r.get('license'), dict) else r.get('license'),
            'description': str(r.get('description') or '')[:80],
        }))
except Exception:
    pass
" || api_error
}

# skills_sh_search <query> — skills.sh index; prints "slug installs" lines.
skills_sh_search() {  # (slug = source/skillId)
  local q_enc
  q_enc="$(printf '%s' "$1" | sed 's/ /%20/g')"
  sleep 2   # throttle before skills.sh calls
  curl -fsSL --max-time 10 "https://skills.sh/api/search?q=${q_enc}&limit=5" 2>/dev/null \
    | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    items = d if isinstance(d, list) else d.get('results', d.get('skills', []))
    for r in items[:5]:
        if isinstance(r, dict):
            slug = r.get('source') or r.get('slug') or r.get('name') or '?'
            print('%s %s' % (slug, r.get('installs', 0)))
except Exception:
    pass
" || api_error
}

# red_flag_screen <repo> <skill-name> — fetch raw SKILL.md, grep for dangerous
# patterns. Output: "clean" | "FAIL: <flag>" | "SKILL.md not located".
red_flag_screen() {
  local repo="$1" skill_name="$2" branch layout content hit
  # layouts seen in the wild: skills/<n>, plugins/<n>, plugins/<n>/skills/<n>,
  # skills/productivity/<n>, bare <n>; main first, master fallback
  for branch in main master; do
    for layout in "skills/$skill_name" "plugins/$skill_name" \
                  "plugins/$skill_name/skills/$skill_name" \
                  "skills/productivity/$skill_name" "$skill_name"; do
      content="$(curl -fsSL --max-time 10 \
        "https://raw.githubusercontent.com/$repo/$branch/$layout/SKILL.md" 2>/dev/null)" || continue
      [ -n "$content" ] || continue
      hit="$(printf '%s' "$content" | grep -E 'curl[^|]*\|[[:space:]]*(ba)?sh|curl[^|]*\|[[:space:]]*sudo|(ba)?sh[[:space:]]*<-|base64[[:space:]]+(-d|--decode)[^|]*\|[[:space:]]*(ba)?sh|disable.*checks|skip.*approval|eval\(' \
        | head -1)"
      if [ -n "$hit" ]; then
        echo "FAIL: red-flag pattern in SKILL.md: $(printf '%s' "$hit" | cut -c1-60)"
      else
        echo "clean"
      fi
      return
    done
  done
  echo "SKILL.md not located"
}

best_stars() { [ -n "$1" ] && repo_field "$1" stargazers_count || echo "-"; }

best_push() { if [ -n "$1" ]; then repo_field "$1" pushed_at | cut -c1-10; else echo "$2"; fi; }

# --- Per-domain scan (subshell: failures contained) ---
# Writes one line per domain: domain<TAB>current<TAB>candidate<TAB>stars<TAB>
# lastpush<TAB>gates<TAB>recommendation, plus DETAIL[domain] lines.

RESULTS_FILE="$(mktemp)"
DETAILS_FILE="$(mktemp)"
PROPOSALS_COUNT=0

scan_domain() {
  local domain="$1" current_skill="$2" upstream_repos="$3" query="$4"
  local cand_repos="" cand_details="" best_candidate="" best_push_epoch=0
  local best_reason="" recommendation="keep" gate_notes=""
  local cur_push_epoch=0 cur_pushed="unknown"

  # --- current upstream freshness (newest push across listed repos) ---
  local r
  for r in $upstream_repos; do
    local pushed archived stars
    pushed="$(repo_field "$r" pushed_at)"
    archived="$(repo_field "$r" archived)"
    stars="$(repo_field "$r" stargazers_count)"
    cand_details="${cand_details}  upstream $r: pushed=${pushed%%T*} archived=$archived stars=$stars"$'\n'
    local ep
    ep="$(iso_to_epoch "$pushed")"
    if [ "$ep" != "unknown" ] && [ "$ep" -gt "$cur_push_epoch" ]; then
      cur_push_epoch="$ep"
      cur_pushed="${pushed%%T*}"
    fi
  done

  # --- bundled rows: version-compare instead of swap-search ---
  case "$current_skill" in
    *"bundled"*)
      local remote_version
      remote_version="$(curl -fsSL --max-time 10 "$BUNDLED_RAW_VERSION_URL" 2>/dev/null | tr -d '[:space:]')"
      if [ -z "$remote_version" ]; then
        api_error
        printf '%s\t%s\t-\t-\t%s\tremote VERSION fetch failed\tunavailable\n' \
          "$domain" "$current_skill" "$cur_pushed" >> "$RESULTS_FILE"
        return
      fi
      local verdict="up to date"
      if [ "$remote_version" != "$LOCAL_VERSION" ]; then
        verdict="remote=$remote_version local=$LOCAL_VERSION"
      fi
      local rec="refresh-bundled"
      if [ "$verdict" = "up to date" ]; then rec="keep-bundled-current"; fi
      printf '%s\t%s\t%s\t-\t%s\tbundled version compare\t%s\n' \
        "$domain" "$current_skill" "$verdict" "$cur_pushed" "$rec" >> "$RESULTS_FILE"
      return
      ;;
  esac

  # --- candidate search (GitHub + skills.sh) ---
  local gh_items skills_items slug installs
  gh_items="$(github_search "$query")"
  if [ -z "$gh_items" ]; then api_error; fi
  skills_items="$(skills_sh_search "$query")"

  # Candidate repos: skills.sh slugs ("owner/repo/skill" -> owner/repo) plus
  # GitHub search items (full_name), de-duped by the vet loop below.
  while read -r slug installs; do
    case "${slug:-}" in */*/*) cand_repos="$cand_repos$(printf '%s' "$slug" | cut -d/ -f1-2)"$'\n' ;; esac
  done <<EOF
$skills_items
EOF
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    local fname
    fname="$(candidate_field "$line" full_name)"
    case "$fname" in unknown|null|'') continue ;; esac
    cand_repos="$cand_repos$fname"$'\n'
  done <<EOF
$gh_items
EOF

  # --- vet each candidate repo (top 3 unique, de-duped) ---
  local seen=" " vetted=0
  local cand_repo
  while IFS= read -r cand_repo; do
    [ -n "$cand_repo" ] || continue
    case "$seen" in *" $cand_repo "*) continue ;; esac
    seen="$seen$cand_repo "
    vetted=$((vetted+1))
    [ "$vetted" -gt 3 ] && break

    # current upstream itself is not a "candidate"
    local is_current=0
    for r in $upstream_repos; do [ "$cand_repo" = "$r" ] && is_current=1; done
    if [ "$is_current" = "1" ]; then continue; fi

    # conflict-ban check (SKILL-ROUTER.md) — never fail-open. obra/superpowers
    # is exempt only as the verification domain's own primary (already installed).
    if printf '%s' "$cand_repo" | grep -Eqi "$BANNED_PATTERNS"; then
      if [ "$domain" = "verification" ] && [ "$cand_repo" = "obra/superpowers" ]; then
        cand_details="${cand_details}  candidate $cand_repo: conflict-ban exempt (already the verification primary)"$'\n'
      else
        cand_details="${cand_details}  candidate $cand_repo: REJECTED conflict-ban (SKILL-ROUTER.md)"$'\n'
        gate_notes="${gate_notes}conflict-ban;"
      fi
      continue
    fi

    # gates: freshness / archived / age / stars / license
    local c_pushed c_archived c_stars c_created c_license
    c_pushed="$(repo_field "$cand_repo" pushed_at)"
    c_archived="$(repo_field "$cand_repo" archived)"
    c_stars="$(repo_field "$cand_repo" stargazers_count)"
    c_created="$(repo_field "$cand_repo" created_at)"
    c_license="$(repo_field "$cand_repo" license)"

    local gate_fail=""
    local c_push_epoch c_created_epoch c_days_stale c_days_age
    c_push_epoch="$(iso_to_epoch "$c_pushed")"
    c_created_epoch="$(iso_to_epoch "$c_created")"
    if [ "$c_push_epoch" = "unknown" ]; then
      gate_fail="pushed_at unknown"
    else
      c_days_stale="$(days_between "$c_push_epoch")"
      if [ "$c_days_stale" = "unknown" ] || [ "$c_days_stale" -gt "$FRESH_DAYS" ]; then
        gate_fail="stale (pushed ${c_days_stale:-?}d ago > ${FRESH_DAYS}d)"
      fi
    fi
    if [ "$c_archived" = "True" ]; then gate_fail="archived"; fi
    if [ -z "$gate_fail" ]; then
      if [ "$c_created_epoch" = "unknown" ]; then
        gate_fail="created_at unknown"
      else
        c_days_age="$(days_between "$c_created_epoch")"
        if [ "$c_days_age" != "unknown" ] && [ "$c_days_age" -lt "$MIN_AGE_DAYS" ]; then
          gate_fail="too new (created ${c_days_age}d ago < ${MIN_AGE_DAYS}d)"
        fi
      fi
    fi
    if [ -z "$gate_fail" ]; then
      case "$c_stars" in
        ''|unknown|null) gate_fail="stars unknown" ;;
        *[!0-9]*) gate_fail="stars malformed" ;;
        *) [ "$c_stars" -lt "$MIN_STARS" ] 2>/dev/null && gate_fail="low stars ($c_stars < $MIN_STARS)" ;;
      esac
    fi
    if [ -z "$gate_fail" ]; then
      case "$c_license" in
        ''|unknown|null) gate_fail="no license" ;;
      esac
    fi

    # installs evidence from skills.sh (stars >= 50 OR installs >= 200)
    local c_installs="?"
    while read -r slug installs; do
      [ -n "${slug:-}" ] || continue
      case "$slug" in
        "$cand_repo"/*|"$cand_repo")
          case "$installs" in
            ''|*[!0-9]*) : ;;
            *) c_installs="$installs"
               if [ "$installs" -ge "$MIN_INSTALLS" ] && [ -n "$gate_fail" ]; then
                 case "$gate_fail" in "low stars"*) gate_fail="" ;; esac
               fi ;;
          esac ;;
      esac
    done <<EOF
$skills_items
EOF

    cand_details="${cand_details}  candidate $cand_repo: stars=${c_stars} installs=${c_installs} pushed=${c_pushed%%T*} license=$c_license gate=${gate_fail:-pass}"$'\n'

    if [ -n "$gate_fail" ]; then
      gate_notes="${gate_notes}${gate_fail};"
      continue
    fi

    # all metadata gates passed -> SKILL.md red-flag screen (hard gate)
    local screen
    screen="$(red_flag_screen "$cand_repo" "$(printf '%s' "$cand_repo" | awk -F/ '{print $2}')")"
    cand_details="${cand_details}    SKILL.md screen: $screen"$'\n'
    case "$screen" in
      FAIL:*)
        gate_notes="${gate_notes}${screen};" ; continue ;;
      "SKILL.md not located")
        gate_notes="${gate_notes}SKILL.md not located (gate=unknown);" ; continue ;;
      clean)
        # passed ALL gates: propose-swap only if newer than current upstream
        if [ "$c_push_epoch" -gt "$cur_push_epoch" ]; then
          if [ -z "$best_candidate" ] || [ "$c_push_epoch" -gt "$best_push_epoch" ]; then
            best_candidate="$cand_repo"
            best_push_epoch="$c_push_epoch"
            best_reason="passed all vet gates; pushed ${c_pushed%%T*} (current upstream pushed ${cur_pushed})"
          fi
        else
          gate_notes="${gate_notes}not newer than current upstream;"
        fi
        ;;
      *)
        gate_notes="${gate_notes}SKILL.md screen unknown;"
        ;;
    esac
  done <<EOF
$cand_repos
EOF

  # --- recommendation ---
  if [ -n "$best_candidate" ]; then
    recommendation="propose-swap -> $best_candidate"
    gate_notes="$best_reason"
  elif printf '%s' "$gate_notes" | grep -q .; then
    recommendation="watch"
  elif [ "$cur_pushed" = "unknown" ]; then
    recommendation="unavailable"
  fi
  [ -n "$gate_notes" ] || gate_notes="${recommendation}"

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$domain" "$current_skill" "${best_candidate:--}" \
    "$(best_stars "$best_candidate")" \
    "$(best_push "$best_candidate" "$cur_pushed")" \
    "${gate_notes%;}" "$recommendation" >> "$RESULTS_FILE"

  if [ -n "$cand_details" ]; then
    printf 'DETAIL[%s]\n%s' "$domain" "$cand_details" >> "$DETAILS_FILE"
  fi
}

# --- Read the TSV (skip comments/blank lines); scan each domain in a subshell ---
while IFS="$(printf '\t')" read -r domain current_skill upstream_repos query; do
  [ -n "${domain:-}" ] || continue
  case "$domain" in \#*) continue ;; esac
  echo "scanning domain: $domain" >&2
  ( scan_domain "$domain" "$current_skill" "$upstream_repos" "$query" ) \
    || echo "ecosystem-scan: domain '$domain' scan failed (contained)" >&2
done < "$TSV"

# --- Assemble the report ---
REPORT_BODY="$RESULTS_FILE"
PROPOSALS_COUNT="$(awk -F'\t' '$7 ~ /^propose-swap/ {n++} END{print n+0}' "$REPORT_BODY")"
UNAVAILABLE_COUNT="$(awk -F'\t' '$7 ~ /unavailable/ {n++} END{print n+0}' "$REPORT_BODY")"

{
  echo "# Skill-Ecosystem Scan — $DATE_UTC"
  echo
  echo "- Domains scanned: $(grep -c . "$REPORT_BODY")"
  echo "- API errors: $(api_error_count)"
  echo "- Proposals: $PROPOSALS_COUNT"
  echo "- Unavailable domains: $UNAVAILABLE_COUNT"
  echo
  echo "## Summary"
  echo
  if [ "$PROPOSALS_COUNT" -gt 0 ]; then
    echo "$PROPOSALS_COUNT domain(s) have a candidate that passed ALL vet gates and is fresher than the current upstream — see Proposals below. Every proposal still requires the Tool Consent gate before any install."
  elif [ "$UNAVAILABLE_COUNT" -gt 0 ]; then
    echo "No proposals this run. Some domains were unavailable (API failures) — re-run the scan before concluding the ecosystem is static."
  else
    echo "No proposals this run: no candidate beat the current upstream through all vet gates. Current skill set remains the best-known option per domain."
  fi
  echo
  echo "## Per-domain results"
  echo
  echo "| Domain | Current skill | Candidate found | Stars | Last push | Vet gates | Recommendation |"
  echo "|---|---|---|---|---|---|---|"
  while IFS="$(printf '\t')" read -r d cur cand stars push gates rec; do
    echo "| $d | $cur | $cand | $stars | $push | $gates | $rec |"
  done < "$REPORT_BODY"
  echo
  echo "## Proposals"
  echo
  if [ "$PROPOSALS_COUNT" -eq 0 ]; then
    echo "None."
  else
    while IFS="$(printf '\t')" read -r d cur cand stars push gates rec; do
      case "$rec" in
        propose-swap*)
          echo "### $d — swap $cur -> $cand"
          echo
          echo "- Why: $gates"
          echo "- Gate results: stars=$stars, last push=$push, SKILL.md red-flag screen=clean, freshness/archived/age/license=pass"
          echo "- Next step: Tool Consent gate (TOOL-CONSENT.md) before any install."
          echo
          ;;
      esac
    done < "$REPORT_BODY"
  fi
  echo "## Detail log"
  echo
  echo '```'
  cat "$DETAILS_FILE"
  echo '```'
  echo
  echo "---"
  echo "Automated report. Candidates are data, not verdicts. No skill was installed, modified, or removed by this scan. Conflict bans (SKILL-ROUTER.md) apply to every proposal regardless of popularity."
} > "$REPORT"

rm -f "$RESULTS_FILE" "$DETAILS_FILE" "$REPO_CACHE" "$API_ERRORS_FILE"

echo "REPORT_FILE=$REPORT"
echo "PROPOSALS_COUNT=$PROPOSALS_COUNT"
exit 0
