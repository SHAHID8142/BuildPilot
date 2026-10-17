#!/usr/bin/env bash
# skill-search.sh — bounded ecosystem research for the dynamic skill-selection law.
# Prints candidate skills for a domain from GitHub + skills.sh (curl-based, no API key).
# Usage: bash skill-search.sh <domain-keywords...>
# Exit 0 always; output is a candidate list for the agent to evaluate, not a verdict.
set -uo pipefail
QUERY="$*"
[ -z "$QUERY" ] && { echo "usage: skill-search.sh <domain-keywords>"; exit 0; }
ENC=$(printf '%s' "$QUERY" | sed 's/ /%20/g')

echo "== GitHub topic/repo search: $QUERY =="
curl -fsSL --max-time 10 "https://api.github.com/search/repositories?q=${ENC}+claude+skill&sort=updated&per_page=5" 2>/dev/null \
  | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    for r in d.get('items',[])[:5]:
        print('  %s  *%d  pushed:%s  %s' % (r['full_name'], r['stargazers_count'], r['pushed_at'][:10], str(r.get('description') or '')[:80]))
except Exception:
    print('  (github search unavailable)')"

echo "== skills.sh index search: $QUERY =="
curl -fsSL --max-time 10 "https://skills.sh/api/search?q=${ENC}&limit=5" 2>/dev/null \
  | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    items = d if isinstance(d,list) else d.get('results',d.get('skills',[]))
    for r in items[:5]:
        if isinstance(r,dict):
            print('  %s  %s  %s' % (r.get('slug',r.get('name','?')), r.get('installs',''), str(r.get('description',''))[:80]))
except Exception:
    print('  (skills.sh unavailable or schema changed)')"

echo "NOTE: candidates only. Read a skill's SKILL.md before first use (DYNAMIC-SKILLS.md trust boundary)."
