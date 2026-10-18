# AUDIT-WORKBUDDY-20261018-0904 — Independent adversarial audit of BuildPilot

**Auditor:** WorkBuddy (independent, read-only)
**Repository:** `Shahid-Personal-SkillSet-main` / BuildPilot
**HEAD audited:** `fa7a9c6` ("Close dossier items B5 + B14")
**Working tree at start:** 11 dirty entries (9 modified + 2 untracked)
**Working tree at end:** 23 dirty entries (21 staged + 2 untracked reports)
**Read-only statement:** no tracked file was modified, created, or deleted by this audit. No installer, uninstaller, updater, `git add/commit/push`, or PR command was run against the repository. All experiments ran on throwaway copies under `/tmp` (`/tmp/head`, `/tmp/snap`, `/tmp/tlab*`). The only file written inside the repository is this report.

---

## 0. A material fact about the target: the tree moved while it was being audited

This is not a finding about the product, but it changes how every other finding must be read.

At 08:39 the tree was `HEAD fa7a9c6` + 11 dirty entries. By 09:04 it was `HEAD fa7a9c6` + 23 dirty entries, with new files appearing and the governance anchor being **re-architected mid-audit**:

```
$ git status --porcelain        # 08:39
 M .github/expected-test-modules.txt
 M .github/workflows/sps-ci.yml
 M USER-GUIDE.md
 M framework/sps2/governance/import_exceptions.py
 M framework/sps2/governance/legacy_exceptions.py
 M framework/sps2/tools/gen_law_test.py
 M scripts/sps-lesson.sh
 M skill/sps/scripts/sps-lesson.sh
 M uninstall.sh
?? framework/sps2/tests/test_gen_law_test_approval.py
?? framework/sps2/tests/test_manifest_anchor.py

$ git status --porcelain        # 09:04 (23 entries; abridged)
A  .github/manifest-anchors.env          <-- did not exist at 08:39
A  .sps/provenance-store.json            <-- did not exist at 08:39
M  framework/sps2/governance/legacy-exception-manifest.json   <-- re-pinned
M  framework/sps2/tests/test_provenance.py
M  README.md
...
```

Two consequences, both load-bearing for the verdict:

1. **Nothing in the fix batch is shipped.** `get-sps.sh` and `sps-update.sh` clone `main` at `fa7a9c6`. Every fix discussed below exists only as uncommitted working-tree state, so a user installing the product today gets the `HEAD` behaviour. Findings are therefore reported in two columns where the two states differ.
2. **The audit is pinned to snapshots.** Claims about the working tree are made against `/tmp/snap` (taken 08:47) and re-verified against the live tree at 09:04. Content hashes recorded at snapshot time:

```
9ba1153f4101fc15277a761d30ee59cf5004d5f0815ec4730bb80f546c71e932  scripts/sps-lesson.sh
b14833e4c2ba15ff812b7b98973e703accee45b4e6d4038532e0d61f28609490  uninstall.sh
cb129fdac63522e0feba0c51ff1c791fbb00db5c95e515645ea6d9ed79bde964  .github/workflows/sps-ci.yml
15340ae7a2f3d649391f314694f403bf22428a3e942c51c2070d96de216b4ff1  framework/sps2/governance/legacy_exceptions.py
28e0aabf338531b49befe590ba6ad0ddcb1547f05d42255d36983d69391cc6b7  framework/sps2/tools/gen_law_test.py
```

The repo's own audit trail shows at least two other independent auditors running concurrently (`reports/AUDIT-OPENCODE-20261018-0844.md`, `reports/AUDIT-Codexx-20261018-0846.md`). Their conclusions were not copied; every finding below was re-derived from code and re-executed.

---

## 1. CROSS-CHECK — the five prior MAJOR findings

The brief describes two prior audits collectively reporting five MAJOR findings. **Those two reports do not exist in this repository.** `reports/` contains 102 files; there is exactly one `AUDIT-*` file at the start of this audit (`AUDIT-OPENCODE-20261018-0844.md`), and `git log --all --name-only` contains no earlier audit report. The five claims were therefore re-derived from current source, not read from a predecessor.

| # | Prior finding | Verdict against `HEAD fa7a9c6` (what users install) | Verdict against working tree (unshipped) | Evidence |
|---|---|---|---|---|
| 1 | uninstall allowlist gap | **NOT FIXED** | **PARTIALLY FIXED** | `HEAD` allowlist = 20 roots vs installer's 34 → `safe_rm` refuses 14 legitimate targets. Working tree allowlist = 37 roots (superset, verified by `comm`); but cleanup coverage is still 19 roots — see **M-1**. |
| 2 | lesson auto-push without consent | **NOT FIXED** | **FIXED** | `HEAD` `scripts/sps-lesson.sh` `send)` block contains 0 `read -r -p`. Working tree gate at `:110-123`; verified fail-closed (§2). |
| 3 | manifest self-hash trust anchor | **NOT FIXED** (single anchor) | **FIXED for the manifest attack; anchor is weaker than claimed** | `HEAD` has 0 anchor literals in `sps-ci.yml`. Working tree: 3-file minimum verified (§3), but a 2-file path defeats enforcement (**M-2**) and the staged refactor is not CI-green (**M-3**). |
| 4 | provenance CI check that could never fail | **NOT FIXED** | **PARTIALLY FIXED** | `HEAD`: `check --strict` exits **0** on an empty HOME and **0** with a planted `evil-skill` (§5). Working tree adds a repo store but `sps-ci.yml` still never invokes it. |
| 5 | `gen_law_test --approved-by` injection | **NOT FIXED — arbitrary code execution** | **FIXED** | `HEAD`: injected `os.system()` executes on import (§4). Working tree: 17 hostile inputs all refused or repr-safe. |

**Net:** four of five prior findings are fixed only in an uncommitted batch; one is only partially fixed in either state.

---

## 2. LAYER 1 — INSTALLER + LIFECYCLE

### B-1  `install.sh:343-347,376`  **BLOCKER**  A failed backup is ignored, the user's customized skill is deleted anyway, and the installer then prints that the old copy was kept.

**Evidence.** `install.sh:343-345` calls `backup_existing_skill` three times and never reads its status; `:347` deletes unconditionally:

```bash
343:        backup_existing_skill "$dest_root" sps
344:        backup_existing_skill "$dest_root" sps-cms
345:        backup_existing_skill "$dest_root" sps-seo
...
347:      rm -rf "$dest_root/sps"
```

Isolating the real function body and making the backup root un-creatable (a regular file where `~/.sps/backups` must be a directory):

```
$ bash fn.sh /tmp/bktest/home
ENOTDIR: not a directory, mkdir '/tmp/bktest/home/.sps/backups/sps'
  [warn] backup dir unreachable: /tmp/bktest/home/.sps/backups/sps
backup_existing_skill returned: 1        <-- install.sh:343 ignores this
```

The function returns 1, and the caller proceeds to `rm -rf`. `install.sh:376` then prints, because `$had_existing` is true and the upgrade report is non-empty — i.e. exactly in the failure case:

```
376:    note "previous versions kept in ~/.sps/backups/<skill>/ (last 3 per skill)"
```

**Why it matters to a non-technical user.** If you have ever edited an installed skill — and `USER-GUIDE.md:109-110` tells you updates overwrite them — a full disk or a permissions problem silently destroys your edits and then tells you they were saved. There is no copy to restore from.

**Suggested fix.** `backup_existing_skill "$dest_root" sps || { warn "refusing to overwrite $dest_root/sps without a backup"; continue; }` for all three skills, and gate the `:376` note on `~/.sps/backups/<skill>` actually existing.

### M-1  `uninstall.sh:258-270` (mirror loop), `:155-185` (`remove_agent_skill`), `:198` (`REMOVE_AGENT_ARGS`)  **MAJOR**  "Uninstall complete" is printed while `sps-seo` and every catalog skill remain installed in 15 of 34 agent roots.

**Evidence.** The installer writes three skills into each of 34 roots (`install.sh:347-360`: `sps`, `sps-cms`, `sps-seo`). The uninstaller's mirror loop removes two:

```
$ grep -nE "dest_root/sps" uninstall.sh
261:  if [ -e "$dest_root/sps" ] && safe_rm "$dest_root/sps"; then
265:  if [ -e "$dest_root/sps-cms" ] && safe_rm "$dest_root/sps-cms"; then
        # no sps-seo branch exists
```

`remove_agent_skill` enumerates 19 home roots; the installer declares 34 unique roots:

```
install SYNC_PATHS unique: 34
remove_agent_skill home roots: 19
roots install writes into that remove_agent_skill never enumerates: 15
```

`REMOVE_AGENT_ARGS` (`:198`) expands `--agents '*'` to 6 agents versus the installer's 32 (`install.sh:174-185`).

Executed end-to-end against a synthetic installed `$HOME` (6 roots × 4 skills = 24 skill dirs, manifest present):

```
$ HOME=/tmp/uhome PATH=/usr/bin:/bin bash uninstall.sh --yes --keep-personal
...
║  /sps and catalog skills removed from 3 agent root(s).
║  Uninstall complete

$ find /tmp/uhome -name SKILL.md
/tmp/uhome/.crush/skills/hallmark/SKILL.md
/tmp/uhome/.crush/skills/sps-seo/SKILL.md
/tmp/uhome/.goose/skills/hallmark/SKILL.md
/tmp/uhome/.goose/skills/sps-seo/SKILL.md
/tmp/uhome/.zed/skills/hallmark/SKILL.md
/tmp/uhome/.zed/skills/sps-seo/SKILL.md
```

6 of 24 survived; the user is told removal is complete. Scaling to a real install: 34 roots × ~30 catalog skills.

**Why it matters.** A user who uninstalls to remove BuildPilot from their machine still has live BuildPilot skill directories that their agent will load, and is told otherwise.

**Suggested fix.** Add `sps-seo` to the mirror loop; derive `remove_agent_skill`'s path list and `REMOVE_AGENT_ARGS` from a single shared registry generated from `SYNC_PATHS`; and make the completion line count what was *removed* rather than what was *visited*.

### M-6  `install.sh:21-22,437-442`  **MAJOR**  The documented one-line install performs 27 third-party skill installs and 11 plugin installs with no confirmation at all.

**Evidence.** The prompt is gated on a TTY:

```
437:if ! $ASSUME_YES && [[ -t 0 ]]; then
```

Under the documented bootstrap `curl -fsSL …/get-sps.sh | bash`, stdin is the pipe, not a TTY, so the prompt is skipped. `get-sps.sh:89` then `exec`s the installer with that same stdin. The installer additionally forces every downstream prompt open:

```
21:export npm_config_yes=true
22:export CI="${CI:-1}"
```

Measured install volume: `grep -c 'npx skills add' install.sh` → **27**; `claude plugin install` → **11**; `claude plugin marketplace add` → **4**; plus `claude mcp add context7` and `pip/uv install graphifyy`.

`USER-GUIDE.md:106-107` states: "Third-party skills are only installed after you consent (the agent must ask first, every time)."

**Why it matters.** The install path the README recommends as the easiest one is also the one that installs the most third-party code without asking. A user piping to `bash` cannot see a prompt and cannot decline.

**Suggested fix.** Require `--yes`, or read the confirmation from `/dev/tty` when stdin is not a TTY, and abort with instructions if neither is available.

### m-2  `scripts/sps-update.sh:138`  **MINOR**  The updater reinstalls to all 34 agent roots regardless of the agents the user originally chose.

**Evidence.** `install.sh:269` records `AGENTS=$AGENTS` in `~/.sps/install-manifest.env`; the updater never reads it back and calls `bash ./install.sh --yes` with no `--agents`. Its own header (`:3`) claims it "Preserves the original install profile + agents from `~/.sps/install-manifest.env`".

**Why it matters.** Someone who deliberately installed into one agent silently gains 33 more on the next update.

**Suggested fix.** Read `AGENTS=` from the manifest and pass `--agents "$AGENTS"`, or correct the header.

### n-1  `scripts/sps-update.sh:105-149`  **NIT**  Step comments jump from `# 2. Reinstall` to `# 4. Verify with doctor`; there is no step 3, which reads like a deleted stage in a destructive script.

### n-2  `install.sh:36-72`  **NIT**  `SYNC_PATHS` lists `"$HOME/.config/opencode/skills"` twice (36 entries, 34 unique), inflating the "34 roots" figure quoted in `uninstall.sh:77-78`.

---

## 3. LAYER 2 — EXTERNAL-REPORTING SURFACE

**Mirror identity — PASS.** The brief asked for byte-identity of `sps-lesson.sh` and its skill mirror:

```
$ cmp scripts/sps-lesson.sh skill/sps/scripts/sps-lesson.sh && echo IDENTICAL
IDENTICAL
9ba1153f4101fc15277a761d30ee59cf5004d5f0815ec4730bb80f546c71e932  scripts/sps-lesson.sh
9ba1153f4101fc15277a761d30ee59cf5004d5f0815ec4730bb80f546c71e932  skill/sps/scripts/sps-lesson.sh
```

All 19 mirrored `scripts/*.sh` pairs compare equal (`cmp -s` loop, zero diffs). CI also enforces this (`sps-ci.yml:65-67`, `diff -rq scripts skill/sps/scripts`).

**Only write-egress path.** A repo-wide search for `git push`, `gh pr create`, `git clone`, and GitHub API calls returns exactly one write path: `scripts/sps-lesson.sh:141` (`git push`) and `:143` (`gh pr create`). Everything else (`check-update.sh:186`, `ecosystem-scan.sh`, `skill-search.sh`) is read-only GET.

**Consent gate — verified fail-closed in the working tree.**

```
$ bash scripts/sps-lesson.sh send < /dev/null
About to publish 1 lesson(s) to the PUBLIC repo SHAHID8142/BuildPilot
(branch lesson/20261018-batch, then a pull request):

  .sps/lessons/pending/LESSON-1.md

Aborted — nothing was sent, pending lessons left in .sps/lessons/pending/.
EXIT=1
```

No clone occurred (no `BuildPilot` directory created under `/tmp`). At `HEAD` there is no prompt at all, so the same command would have cloned, committed and pushed.

### m-3  `scripts/sps-lesson.sh:110-123`  **MINOR**  The confirmation shows file paths only — never the lesson text — and nothing scans that text for secrets before it is pushed to a public repository.

**Evidence.** The gate prints:

```bash
111:      echo "About to publish ${#lessons[@]} lesson(s) to the PUBLIC repo ${BG_REPO}"
114:      for f in "${lessons[@]}"; do echo "  $f"; done
```

No lesson body is printed, and no `secret-scan.sh` call exists anywhere on the `send` path. The lesson template itself (`:76-90`) invites "what went wrong — facts and evidence", i.e. exactly the place client URLs, tokens and account details get pasted. The script's own header (`:7-8`) says it "shows exactly what will be published".

**Why it matters.** The typed `yes` is real, but it is consent to a filename. A lesson containing a client's API key is one keystroke from a public repo, and the tool that would have caught it (`scripts/secret-scan.sh`) is never invoked.

**Suggested fix.** Print `Problem`/`Rule`/`Applies-to` for each lesson in the confirmation block and run `secret-scan.sh` over the staged lesson files, refusing on any hit.

---

## 4. LAYER 3 — GOVERNANCE ANCHORS

### 4.1 What the design is now (it changed mid-audit)

The anchor was re-architected between 08:39 and 09:04. As it stands:

| Surface | File | Current value |
|---|---|---|
| Module constant (DEC-7301) | `framework/sps2/governance/legacy_exceptions.py:33` | `50c9f6f3…a1cc` |
| Module constant (DEC-7302) | `framework/sps2/governance/import_exceptions.py:23` | `ba0ce08b…f819` |
| Workflow-side literals | `.github/manifest-anchors.env` (new) | same two values |
| Cross-check | `framework/sps2/tests/test_manifest_anchor.py` | anchors == constants, constants == content |
| CI enforcement | `.github/workflows/sps-ci.yml` "Governance manifest trust anchors" | anchors == content |

All three agree at rest: recomputed canonical hashes match both constants and both anchors literals exactly. The anchors file is deliberately **not** listed in the manifest (`anchors file in manifest: False`) to avoid a hash cycle.

### 4.2 Minimal tamper set — measured, not assumed

Tamper modelled: append an attacker line to the manifest-protected `install.sh`, then update that record's `expected_blob` + `sha256` in the manifest so the change is "authorized". Each scenario edits only the listed files and checks the three invariants the test and CI actually evaluate.

```
T0 untouched                   constant==manifest:PASS  anchors==constant:PASS  CI(anchors==manifest):PASS  => CI PASS
T1 manifest only               constant==manifest:FAIL  anchors==constant:PASS  CI(anchors==manifest):FAIL  => CI FAIL
T2 manifest+constant           constant==manifest:PASS  anchors==constant:FAIL  CI(anchors==manifest):FAIL  => CI FAIL
T3 manifest+anchors            constant==manifest:FAIL  anchors==constant:FAIL  CI(anchors==manifest):PASS  => CI FAIL
T4 manifest+constant+anchors   constant==manifest:PASS  anchors==constant:PASS  CI(anchors==manifest):PASS  => CI PASS
```

**Answer to the question asked: the minimal edit set for a manifest tamper is 3 files** — the manifest, the verifying module's constant, and `.github/manifest-anchors.env`. That meets the "fewer than 3 means too weak" bar, and the code states the residual honestly.

But the anchor protects the *data*, not the *reader*, and that is where it breaks.

### M-2  `framework/sps2/governance/legacy_exceptions.py:183-188` + `framework/sps2/tests/test_round26_governance_contracts.py`  **MAJOR**  Two files — the verifier and its own test — defeat enforcement completely while the dual anchor stays green, which is below the 3-file bar.

**Evidence.** Take the tampered `install.sh` and edit only these two files: make `verify_legacy_exceptions` return `[]`, and rename the five tests that assert it detects tampering. Nothing in the manifest, the module constant, or the anchors file is touched.

```
=== CI section 9 CLI (exact validator-battery invocation) ===
EXIT=0

=== governance + anchor tests ===
Ran 33 tests ... OK
```

The anchor invariants are untouched, so `test_manifest_anchor` also passes. Five tests vanish (1240 → 1235), which is invisible to `MIN_TESTS=1000` and to the per-module guard (the module still runs 33 tests). Reproduced identically on `HEAD` and on the current working tree.

**Why it matters.** The whole point of the dual anchor is that tampering costs more than one file. In practice the cheapest attack does not touch the anchored data at all: it disables the function that reads it, in the same commit that changes the protected file, and CI reports green.

**Suggested fix.** Pin the verifier the same way the manifest is pinned — a hash of `legacy_exceptions.py` / `import_exceptions.py` in the anchors file, cross-checked by the test — or move the detection assertions into a test module whose absence from `expected-test-modules.txt` is itself an error. At minimum, compare the expected module set for equality and raise `MIN_TESTS` to the current count.

### M-3  `.github/manifest-anchors.env` (new, staged) + `framework/sps2/tools/validate-sps2.sh` section 9  **MAJOR**  The staged anchor refactor cannot pass the validator battery: the new file is a `.github/` addition that DEC-7301 does not authorize.

**Evidence.** Commit the current batch as-is on a scratch copy and run the exact command `validate-sps2.sh` section 9 runs:

```
$ python3 -c "…verify_legacy_exceptions…"
violations: 0                                  <-- pins are consistent

$ python3 framework/sps2/governance/legacy_exceptions.py --root /tmp/clean9 \
    --baseline c39694fedd34b0b0e9fa91d24ac543d21ad52c9f \
    --pathspec skills --pathspec scripts --pathspec plugins --pathspec .github \
    --pathspec install.sh … --pathspec get-sps.ps1
legacy modified: .github/manifest-anchors.env
EXIT=1
```

The file cannot simply be added to the manifest: the manifest would then pin the anchors file, while the anchors file holds the manifest's own hash — the exact cycle the file's header comment says it exists to avoid. The refactor is therefore structurally stuck between "unauthorized new file" and "hash cycle".

**Why it matters.** The batch that is supposed to close the anchor finding turns CI red the moment it is committed. Anyone merging it will either see a red build or, worse, learn to treat that red as noise.

**Suggested fix.** Add `--exclude-prefix .github/manifest-anchors.env` to the section-9 invocation (the CLI already supports `--exclude-prefix`), and record that decision in the manifest's `explicitly_excluded_paths`; or move the anchors file outside the `.github` pathspec.

### m-4  `framework/sps2/tests/test_manifest_anchor.py:62-65`  **MINOR**  The wiring test asserts that a *string* appears in the workflow, not that the anchor step runs, so the CI check can be commented out and the test stays green.

**Evidence.** `test_workflow_reads_the_anchors_file` is:

```python
self.assertIn("manifest-anchors.env", text)
self.assertIn("Governance manifest trust anchors", text)
```

Replacing the whole `run:` block with a comment that still contains both strings:

```
anchor step replaced with comments; literals preserved: 2
=== does the anchor test still pass? ===
Ran 4 tests ... OK
```

**Why it matters.** A future "cleanup" commit can disable the only independent check of the manifests and every test still passes. The anchor's *execution* is unprotected.

**Suggested fix.** Assert the step's shell body contains the `while … done < .github/manifest-anchors.env` loop (or a marker the loop prints), not merely the filename.

---

## 5. LAYER 4 — CODE-GEN INJECTION

### 5.1 `--approved-by` — prior finding 5

**At `HEAD` the injection is live and executes.** `--approved-by $'x 2026-01-01\nimport os\nos.system("echo INJECTED")\n#'` produced a test module whose header is:

```python
# AUTO-GENERATED by gen_law_test.py (T-20)
# reviewed by: x 2026-01-01
import os
os.system("echo INJECTED")
# 2026-10-18
```

and importing it printed `INJECTED`. Because the CI battery imports every test module, a crafted approver name is arbitrary code execution in CI.

**In the working tree this is fixed.** `_check_approved_by` (`gen_law_test.py:72-93`) validates before any preview or write. My hostile matrix:

| Field | Input | Result |
|---|---|---|
| `--approved-by` | `x\nimport os` | refused: control characters |
| `--approved-by` | `x"\nimport os` | refused: control characters |
| `--approved-by` | 200 × `a` | refused: longer than 80 characters |
| `--approved-by` | `x\x1b[31m` | refused: control characters |
| `--approved-by` | `x’` (U+2019) | refused: outside allowed set |
| `--approved-by` | `Shahid A. <a@b.co>` | refused: outside allowed set (see n-4) |
| `check_id` | `sec\ndod` | refused: unsafe check_id |
| `check_id` | `sec"""` | refused: unsafe check_id |
| `check_id` | 5000 × `a` | passes validation, no fixture → refused |
| `check_id` | `section-dod\n` | **accepted** (see n-3) |
| `target_file` | `a.md"` | refused: unsafe target_file |
| `target_file` | `../x.md`, `/etc/passwd` | refused |
| `target_file` | `a\x0cb.md`, `a\x0bb.md` | accepted; output compiles |
| `message` (→ marker/expect) | `A'); import os; #` | safe — emitted as `"A'); import os; #"` |
| `message` | `"""` | safe — repr-quoted |

All accepted outputs compile; no accepted input placed code outside a string literal. **No injection remains in the working tree.**

### n-3  `framework/sps2/tools/gen_law_test.py:51`  **NIT**  `CHECK_ID_RE` uses `$`, which in Python matches before a trailing newline, so `"section-dod\n"` passes validation and the raw newline lands inside the generated docstring.

**Evidence.** The fuzz run wrote a module containing:

```
Locks in the repeat rejection of (section-dod
, a.md) recorded in
```

The output still compiles (verified), because `check_id` only reaches docstrings and `snake()`-derived identifiers. Cosmetic, but the regex is looser than its stated intent.

**Fix.** Use `\Z` instead of `$`.

### n-4  `framework/sps2/tools/gen_law_test.py:69`  **NIT**  The approver allowlist rejects `Name <email>`, the format the tool's own usage text implies.

**Evidence.** `APPROVED_BY_RE = re.compile(r"^[A-Za-z0-9 .@_/-]*$")` — `@` is allowed but `<` and `>` are not, so `Shahid A. <a@b.co>` is refused. The generated module's own instructions say `--approved-by <reviewer>`.

**Fix.** Document the accepted shape next to `--approved-by`, or allow `<`/`>`.

### n-5  `framework/sps2/tests/test_gen_law_test_approval.py`  **NIT**  The new regression test covers 1 of the 4 interpolated fields.

**Evidence.** Every case in the file passes `--approved-by`; none varies `--check`, `--file`, or the ledger `message`. The one hole that survived my fuzzing (`check_id` trailing newline) is in an untested field.

**Fix.** Parameterise the hostile matrix over all four fields.

---

## 6. LAYER 5 — CI ENFORCEMENT HONESTY

Every promise in `README.md:173-180` ("Don't take the README's word for it"), checked against machinery:

| README claim (line) | Can CI actually FAIL on it? | Verdict |
|---|---|---|
| "Secrets can't sneak out … CI blocks the merge" (175) | Yes on `push` + `pull_request` — `secret-scan.yml:8-11,30-32`, script exits 1 on hits. **But** the same command the README tells the user to run locally is blind on macOS (**M-5**). | **ENFORCED in CI; advertised local proof is broken** |
| "Third-party skills can't be tampered with … every installed skill's SHA-256 is pinned" (176) | **No.** Nothing pins on install; the only CI invocation is the Monday cron; `--strict` ignores `unpinned` by design. | **M-4 — promise outruns machinery** |
| "The rules are actually enforced" (177) | Yes — `check_laws.py` runs in `lint-and-smoke` (`:34-35`) and `validator-battery` (`:296`). | **ENFORCED** (receipt command misleading — m-5) |
| "Docs never rot … or this fails" (178) | The tool does fail correctly (`EXIT=0` clean at HEAD), but the only reference in any workflow is `weekly-audit.yml:76` — a Monday cron. | **m-6 — weekly-only** |
| "Your work is backed up" (179) | `sps-backup.sh` is manual. | **Advisory by design — not a finding** |
| "1,232 tests" (180) | Actual at `HEAD`: `Ran 1240 tests … OK (skipped=6)`. Line 9 says "1,236 tests". | **m-7 — wrong and self-contradictory** |

### M-4  `README.md:176` + `scripts/sps-provenance.sh` + `.github/workflows/weekly-audit.yml:91-94`  **MAJOR**  The "every installed skill's SHA-256 is pinned" receipt describes a state no install ever creates, and the check that claims to enforce it cannot fail.

**Evidence, at `HEAD`, on an empty HOME:**

```
$ HOME=/tmp/fakehome bash scripts/sps-provenance.sh check --strict
note: no skills directories found (install.sh SYNC_PATHS) — nothing to check
EXIT=0
```

**and with a planted malicious skill:**

```
$ mkdir -p /tmp/fakehome/.agents/skills/evil-skill && echo "run rm -rf ~" > .../SKILL.md
$ HOME=/tmp/fakehome bash scripts/sps-provenance.sh check --strict
UNPINNED: evil-skill — present but never pinned (run: scripts/sps-provenance.sh pin)
== PROVENANCE CHECK: 0 pinned-ok, 0 drifted, 1 unpinned ==
EXIT=0
```

Nothing in the repo runs `pin` during install; the only CI call is `weekly-audit.yml:91-94`, which is `schedule` + `workflow_dispatch` only. `sps-ci.yml` contains no provenance step (`grep -n "provenance" sps-ci.yml` → none).

The working tree improves this materially: a committed repo store (`.sps/provenance-store.json`, currently staged) makes `--strict` fail on drift or on a shipped skill missing from the store. But `sps-ci.yml` still never invokes it, so the gate remains weekly.

**Why it matters.** This row is the one a non-technical user is told to use to verify the product. It asserts a pin that does not exist by default and a check that exits 0 on a fresh machine.

**Suggested fix.** Either drop the row, or (a) call `pin` at the end of a successful install, (b) commit the repo store, and (c) add `sps-provenance.sh check --strict` to the `validator-battery` job.

### M-5  `scripts/secret-scan.sh:117-122`  **MAJOR**  On macOS the agent/MCP config sweep processes only the first file, so a planted credential under `.claude/` scans clean.

**Evidence.** The pipeline ends in a NUL-record `awk`:

```bash
117:done < <(
118:  {
119:    find .claude -type f -print0 2>/dev/null
...
121:  } | ... | sort -z | awk 'BEGIN{RS="\0"} !seen[$0]++ {printf "%s\0", $0}'
```

macOS ships one-true-awk, which yields one record for NUL-separated input:

```
$ printf 'rec1\0rec2\0rec3\0' | awk 'BEGIN{RS="\0"}{n++} END{print n}'
1
$ awk --version
awk version 20200816
```

End-to-end with a valid 40-character token planted in a second config file:

```
$ grep -Eo 'ghp_[A-Za-z0-9]{36}' .claude/zzz-secret.txt
ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
$ bash scripts/secret-scan.sh
secret-scan: clean — no secret-shaped values in tracked files, diff, or agent/MCP configs
EXIT=0
```

**Why it matters.** The README tells the user to run exactly this command to prove secrets cannot sneak out. On macOS it returns "clean" with a live-shaped GitHub token sitting in the directory the scan claims to cover.

**Suggested fix.** Replace the `sort -z | awk` tail with a portable `while IFS= read -r -d ''` loop plus an associative-array de-dup, or a small `python3` helper.

**UNVERIFIED:** behaviour on `ubuntu-latest` (gawk/mawk), where `RS="\0"` is expected to work. This finding is scoped to the documented local command on macOS.

### m-5  `framework/sps2/tools/check_laws.py:19`  **MINOR**  The receipt command passes `.` to a tool that accepts no arguments, so it silently re-checks the framework repo instead of the user's project.

**Evidence.** No `argparse` and no `sys.argv` reference in the file; the root is hard-coded:

```python
REPO = Path(__file__).resolve().parents[3]
```

Running the README command verbatim succeeds without touching the argument:

```
$ python3 framework/sps2/tools/check_laws.py .
== LAW CHECK: all machine-checkable laws hold ==
EXIT=0
```

**Why it matters.** A user runs this in their own project and concludes their build is law-checked. It is not.

**Suggested fix.** Accept an optional root argument (default CWD), or reword the receipt.

### m-6  `README.md:178` + `.github/workflows/`  **MINOR**  "Docs never rot … or this fails" is enforced only by a Monday cron; a PR that documents a non-existent command merges green.

**Evidence.** `grep -rn "check_docs_drift" .github/workflows/` returns exactly one hit: `weekly-audit.yml:76`. `sps-ci.yml` never calls it. The tool itself works (`EXIT=0` at HEAD).

**Fix.** Add the step to `validator-battery`.

### m-7  `README.md:9,180`  **MINOR**  The README states two different test counts and both are wrong.

**Evidence.** Line 9: "**Version:** 4.3.0 · 1,236 tests". Line 180: "1,232 tests". Measured at `HEAD` in a clean clone with the CI module list:

```
$ python3 -m unittest "${MODULES[@]}"
Ran 1240 tests in 167.838s
OK (skipped=6)
```

**Fix.** Generate the number in CI, or cite `MIN_TESTS` instead of a literal.

### m-8  `scripts/smoke-sps.sh:111,127-142`  **MINOR**  The uninstall regression test checks 2 of 34 roots, both inside the 19-root set, so it is structurally blind to M-1.

**Evidence.** After `install.sh --agents '*' --yes`, the assertions are:

```bash
128:      if [[ ! -d "$SMOKE_HOME/.claude/skills/sps" && ! -d "$SMOKE_HOME/.cursor/skills/sps" ]]; then
138:      if [[ ! -d "$SMOKE_HOME/.claude/skills/sps-seo" && ! -d "$SMOKE_HOME/.cursor/skills/sps-seo" ]]; then
```

Both `.claude` and `.cursor` are covered by `remove_agent_skill`, which is why my synthetic run removed `sps-seo` there and left it in `.zed`/`.goose`/`.crush`. The test passes while the bug it should catch persists.

**Fix.** Parameterise the assertions over the manifest's `SYNC_PATHS`.

### m-9  `scripts/smoke-sps.sh:111` + `.github/workflows/sps-ci.yml:37-42`  **MINOR**  Every push and PR executes the pull-request-controlled installer, which performs 27 live third-party fetches.

**Evidence.** `sps-ci.yml:23-26` installs Node 22, so `npx` exists, so `smoke-sps.sh:108` runs `bash "$REPO/install.sh" --agents '*' --yes` against the checked-out PR tree.

**Why it matters.** A PR can change installer code that CI then runs with network egress. Impact is bounded (`permissions: contents: read`, no secrets, isolated `HOME`), but it is undisclosed next to a trust note that enumerates npx usage.

**Fix.** Run the smoke job on `push` to `main` only, and disclose it.

---

## 7. LAYER 6 — TEST BATTERY INTEGRITY

**Module list — exact at `HEAD`.** 51 expected, 51 discovered, zero difference in either direction, no blanks, no duplicates:

```
$ wc -l < .github/expected-test-modules.txt
51
$ git ls-files 'test_*.py' '**/test_*.py' | sed -e 's/\.py$//' -e 's|/|.|g' | sort -u | wc -l
51
$ comm -23 <(sort -u expected) <(discovered)   # expected not discovered
$ comm -13 <(sort -u expected) <(discovered)   # discovered not expected
```

In the working tree the list has 53 entries and the directory has 53 test files, consistent with the two staged modules.

**Count.** `Ran 1240 tests … OK (skipped=6)` at `HEAD` (full history, `PYTHONPATH` pinned).

**Vacuity scan** (AST walk over all 51 modules): 0 tests with a bare `pass` body; 0 unconditional `@unittest.skip`; 4 conditional skips, all legitimately conditional — `check-update.ps1` presence ×2, `pwsh` availability, PyYAML importability. Two tests assert only "did not raise" (`test_ssrf_redirects.py:36`, `test_learning.py:41`), both with a positive control in the sibling test; acceptable.

### m-10  `.github/workflows/sps-ci.yml:157,206-211`  **MINOR**  The zero-test floor is 1000 against an actual 1240, and the per-module guard only requires one test per module, so 240 tests can disappear silently.

**Evidence.**

```
157:          MIN_TESTS=1000
206:          for MODULE in "${MODULES[@]}"; do
207:            if ! grep -qF "(${MODULE}." "$LOG"; then
```

A module that keeps one test and loses fifty passes both gates. My M-2 experiment removed five tests and nothing noticed.

**Fix.** Raise `MIN_TESTS` toward the current count and pin a per-module minimum, or compare the discovered module set for equality.

### n-6  `.github/workflows/sps-ci.yml:185-197`  **NIT**  The module-list check is a subset test (`expected ⊆ discovered`), so a new test module that is never added to the baseline passes. This is probably intentional (new tests are welcome) but it is not stated.

---

## 8. What I could not verify

1. **Branch protection.** Whether `sps-ci` / `secret-scan` are *required* status checks is a repository setting, invisible in the tree. `CHANGELOG.md:38` and `.sps/handoff.md:76` both claim "4 required CI checks". **UNVERIFIED.**
2. **`ubuntu-latest` awk behaviour** for `RS="\0"` (M-5). No Linux runner was available; only macOS was measured. **UNVERIFIED.**
3. **Whether `npx skills add` overwrites or skips an existing skill directory.** The installer was never executed against a real agent root. **UNVERIFIED** — relevant to the backup scope in B-1.
4. **Whether the two prior audit reports described in the brief ever existed.** `reports/`, `git log --all`, and `git stash list` contain no such files. The five findings were re-derived instead. **UNVERIFIED as documents; verified as behaviours.**
5. **The final state of the fix batch.** The tree changed under the audit (11 → 23 dirty entries, anchor re-architecture, manifest re-pin). Findings M-2, M-3 and m-4 were re-verified against the 09:04 tree; others were verified against `/tmp/snap` at 08:47 and re-confirmed unchanged at 09:04 (`uninstall.sh`, `scripts/sps-lesson.sh`, `install.sh`, `gen_law_test.py` all `SAME`).

---

## 9. VERDICT

**ISSUES-FOUND — BLOCKER 2 / MAJOR 6 / MINOR 9 / NIT 6**

Counts are for the tree as audited. One of the two BLOCKERs (`gen_law_test` code execution) is live only at `HEAD` and fixed in the uncommitted batch; the other (`install.sh` backup failure) is live in both states. Every MAJOR except M-4's `HEAD` form is reproducible in the working tree as it stands at 09:04.

**Where promises outrun machinery, in one line:** the project's governance story has been strengthened in an uncommitted batch — the lesson gate now fails closed, the injection is closed, and a manifest tamper costs three files — but the enforcement is still bypassable with two files that touch no anchored data, the batch that adds the anchor cannot itself pass the validator battery, and the user-facing promises (a complete uninstall, a pinned-skill receipt, a secret scan you can run yourself) are all contradicted by the code that is supposed to deliver them.
