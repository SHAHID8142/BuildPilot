#!/usr/bin/env bash
# Secret-safety negative test.
# Plants a SYNTHETIC, obviously fake credential-shaped value in a temp fixture,
# proves the scanner detects it, proves the value is never echoed, removes the
# fixture, and proves the repository returns to a clean state.
#
# The real credential is never used, read or printed here.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPS2="$(cd "$HERE/.." && pwd)"
SCAN="$HERE/scan_secrets.py"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sps2sec-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

FAIL=0; PASSN=0
ok()   { echo "  PASS  $*"; PASSN=$((PASSN+1)); }
bad()  { echo "  FAIL  $*"; FAIL=$((FAIL+1)); }

# Synthetic value: obviously fake, deterministic, never a real credential.
FAKE='sk-or-v1-FAKEFAKEFAKE0000000000000000000000'

echo "Secret-safety negative test (synthetic fixture only)"

# 1. baseline: repo must be clean
if python3 "$SCAN" "$SPS2" --quiet; then
  ok "baseline: sps2/ is clean before the fixture is planted"
else
  bad "baseline: sps2/ was already dirty"
fi

# 2. plant the synthetic fixture
mkdir -p "$TMP/fixture"
printf '{"env":{"ANTHROPIC_AUTH_TOKEN":"%s"}}\n' "$FAKE" > "$TMP/fixture/settings.json"
printf 'token: %s\n' "$FAKE" > "$TMP/fixture/plain.txt"

# 3. the scanner MUST detect it
OUT=$(python3 "$SCAN" "$TMP" 2>&1); RC=$?
if [ "$RC" -eq 1 ]; then
  ok "scanner exits non-zero on the unsafe fixture"
else
  bad "scanner did not fail on the unsafe fixture (rc=$RC)"
fi

# 4. detection reports metadata only
if printf '%s' "$OUT" | grep -q 'SECRET_LIKE'; then
  ok "scanner reported the finding"
else
  bad "scanner produced no finding line"
fi
if printf '%s' "$OUT" | grep -q 'sha256_16='; then
  ok "scanner reported a fingerprint instead of the value"
else
  bad "scanner did not report a fingerprint"
fi

# 5. THE CRITICAL ASSERTION: the value must never appear in scanner output
if printf '%s' "$OUT" | grep -qF "$FAKE"; then
  bad "SECURITY DEFECT: scanner echoed the secret value"
else
  ok "scanner never echoed the secret value"
fi

# 6. a JSON-shaped value must be detected too
if printf '%s' "$OUT" | grep -q 'ANTHROPIC_AUTH_TOKEN_ASSIGNMENT'; then
  ok "credential-shaped JSON assignment detected"
else
  bad "credential-shaped JSON assignment not detected"
fi

# 7. remove the fixture and prove the repository is clean again
rm -rf "$TMP/fixture"
if python3 "$SCAN" "$TMP" --quiet; then
  ok "fixture removed; scan returns clean"
else
  bad "scan still dirty after fixture removal"
fi
if python3 "$SCAN" "$SPS2" --quiet; then
  ok "repository returned to its original safe state"
else
  bad "repository is still dirty after the test"
fi

# 8. proof the fixture value is nowhere in the repository outside the
#    self-referential test file that defines it by construction
if grep -rqF "$FAKE" "$SPS2" \
   --exclude=test-secret-safety.sh --exclude=scan_secrets.py 2>/dev/null; then
  bad "synthetic value leaked into the repository"
else
  ok "synthetic value confined to the self-referential test file"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "== SECRET-SAFETY TEST PASSED: $PASSN checks, 0 failed =="
  exit 0
fi
echo "== SECRET-SAFETY TEST FAILED: $PASSN passed, $FAIL failed =="
exit 1