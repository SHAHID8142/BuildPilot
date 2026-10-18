# AUDIT-OPENCODE-20261018-0844 — Independent adversarial audit of BuildPilot

**Auditor:** OpenCode (independent, read-only)
**Tree audited:** working tree at `main` / `fa7a9c6`, with 9 modified + 2 untracked files
**Repo state note:** the tree was **already dirty** when the audit began
(`.github/expected-test-modules.txt`, `.github/workflows/sps-ci.yml`, `USER-GUIDE.md`,
`framework/sps2/governance/{import_exceptions,legacy_exceptions}.py`,
`framework/sps2/tools/gen_law_test.py`, `scripts/sps-lesson.sh`,
`skill/sps/scripts/sps-lesson.sh`, `uninstall.sh` modified; `test_manifest_anchor.py`,
`test_gen_law_test_approval.py` untracked). These are an in-flight fix batch for the
five prior findings. **No tracked file was modified by this audit**; `git status --short`
is byte-identical before and after. One temporary `git worktree` (detached, `/tmp`) was
created to test the committed state and has been removed.

---

## CROSS-CHECK against the five prior MAJOR findings

The two latest prior audits could not be located: `reports/` (100 files) and every branch
in `git log --all` contain **no `AUDIT-OPENCODE-*` report and no report containing a
"5 MAJOR" verdict**. The five items were therefore re-derived from current source rather
than copied.

| Prior finding | Status against CURRENT code | Evidence |
|---|---|---|
| lesson auto-push | **FIXED** | `scripts/sps-lesson.sh:110-123` requires a typed `yes`; EOF/non-TTY fails closed |
| manifest self-hash anchor | **FIXED** | 3-file minimum, empirically derived (probe below) |
| `gen_law_test` injection | **FIXED** | 17 hostile ledgers blocked or repr-safe |
| uninstall allowlist gap | **PARTIALLY FIXED** | allowlist is now a superset; but `sps-seo` + 17 roots survive → M-2 |
| provenance CI no-op | **NOT FIXED** | exits 0 on a fresh runner; nothing auto-pins → M-3 |

### Anchor minimal-edit-set probe (the question asked)

Independent reimplementation of all three anchor surfaces
(`legacy_exceptions.EXPECTED_MANIFEST_SHA256` vs canonical manifest hash; workflow
literal vs module constant; `test_manifest_anchor.py`'s assertions), run over four
tamper scenarios on throwaway copies:

```
### scenario: T0-untouched  (files edited: [])
  legacy: A=PASS B=PASS  import: A=PASS B=PASS      ==> anchors agree: YES
### scenario: T1-manifest-only  (files edited: ['legacy-exception-manifest.json'])
  legacy: A=FAIL B=PASS  import: A=PASS B=PASS      ==> anchors agree: NO
### scenario: T2-manifest+module-constant  (files edited: [manifest, legacy_exceptions.py])
  legacy: A=PASS B=FAIL  import: A=PASS B=PASS      ==> anchors agree: NO
### scenario: T3-manifest+workflow-literal  (files edited: [manifest, sps-ci.yml])
  legacy: A=FAIL B=FAIL  import: A=PASS B=PASS      ==> anchors agree: NO
### scenario: T4-manifest+constant+workflow  (files edited: [manifest, legacy_exceptions.py, sps-ci.yml])
  legacy: A=PASS B=PASS  import: A=PASS B=PASS      ==> anchors agree: YES
```

**Minimal edit set that passes CI: 3 files** — the manifest, the verifying module's
constant, and `.github/workflows/sps-ci.yml`. Deleting the workflow anchor step outright
requires a **4th** file, because `test_manifest_anchor.py:62,85` asserts the literal is
*present* in the workflow. The prior "self-hash anchor" finding is genuinely closed, and
the residual ("anyone with repo write reaches all three") is stated honestly in the code.

---

## FINDINGS

### BLOCKER — 0

### MAJOR — 3

**M-1** `install.sh:343-348,376`  **MAJOR**  A failed skill backup is swallowed, the user's locally-customized skill is deleted anyway, and the installer still tells them their old copy is safely kept.
- **Evidence.** `install.sh:343-345` calls `backup_existing_skill` for `sps`/`sps-cms`/`sps-seo` and **ignores the return value**; line 347 then runs `rm -rf "$dest_root/sps"` unconditionally. Isolating the real function body from `install.sh` and making `~/.sps/backups` un-creatable:
  ```
  mkdir: .../.sps/backups: Not a directory
    [warn] backup dir unreachable: .../.sps/backups/sps
    function returned: 1   <-- install.sh:343 IGNORES this
  ```
  `install.sh:376` then prints `note "previous versions kept in ~/.sps/backups/<skill>/ (last 3 per skill)"` whenever `$had_existing` is true and the upgrade report is non-empty — i.e. in exactly the case where the backup failed.
- **Why it matters.** A user who edited their installed `sps` skill (the trust note invites this by saying local edits are overwritten) loses those edits with **no recoverable copy**, while the tool prints the opposite.
- **Fix.** `backup_existing_skill "$dest_root" sps || { warn "refusing to overwrite $dest_root/sps without a backup"; continue; }` for all three, and gate the line-376 note on the backups actually existing.

**M-2** `uninstall.sh:258-270` (and `uninstall.ps1:194-204`)  **MAJOR**  A "full removal" uninstall leaves the `sps-seo` skill — plus ~26 curated skills — installed in 17 of the 34 agent roots, then prints "Uninstall complete".
- **Evidence.** `install.sh:36-72` declares 34 unique `SYNC_PATHS`; `install.sh:347-360` writes `sps`, `sps-cms` **and** `sps-seo` into each. The uninstaller's mirror loop removes only two of the three:
  ```
  $ grep -n "dest_root/" uninstall.sh
  261:  if [ -e "$dest_root/sps" ] && safe_rm "$dest_root/sps"; then
  265:  if [ -e "$dest_root/sps-cms" ] && safe_rm "$dest_root/sps-cms"; then
  $ # mirror loop mentions sps-seo: False
  ```
  `remove_agent_skill` (`uninstall.sh:155-185`) enumerates only **19** home roots. The other **15** install roots are reachable only via `npx skills remove`, whose default agent set is 6 agents (`uninstall.sh:198`) versus the installer's 33 (`install.sh:174-185`):
  ```
  install SYNC_PATHS unique: 34
  remove_agent_skill home roots: 19
  roots install writes into, that remove_agent_skill never enumerates (15):
     .autohand/skills  .config/goose/skills  .config/junie/skills  .config/trae/skills
     .crush/skills  .droid/skills  .goose/skills  .grok/skills  .hermes/skills
     .junie/skills  .kilocode/skills  .openclaw/skills  .qoder/skills  .trae/skills
     .warp/plugins/skills  .zed/skills  .zeroclaw/skills
  ```
  `smoke-sps.sh:138-141` *does* assert "uninstall removed mirrored sps-seo paths" — but only against `~/.claude/skills` and `~/.cursor/skills`, 2 of the 34 roots, both in the 19-root set. The regression test is structurally blind to the 15 it misses.
- **Why it matters.** A user who uninstalls still has a live BuildPilot skill directory loaded by their agent in 17 hosts, and is told the removal is complete.
- **Fix.** Add `sps-seo` to the mirror loop (both `uninstall.sh` and `uninstall.ps1`); extend `remove_agent_skill`'s path list to the full 34; make `build_agent_args`'s `*` branch mirror `install.sh`'s registry; and parameterise `smoke-sps.sh` over the manifest's `SYNC_PATHS` instead of two hard-coded roots.

**M-3** `README.md:176` + `scripts/sps-provenance.sh:90-92,133-136,151` + `.github/workflows/weekly-audit.yml:90-93`  **MAJOR**  The receipt "Third-party skills can't be tampered with — every installed skill's SHA-256 is pinned" is false on a fresh install and the CI step that claims to check it cannot fail.
- **Evidence.** Nothing in the repo ever runs `pin` — `grep -rn "provenance.sh pin" install.sh uninstall.sh scripts/ .github/ skill/` returns only usage text and an *optional* hint (`sps-doctor.sh:169`). Executed against a `$HOME` with no pin store, and then with a planted malicious skill:
  ```
  $ HOME=.../fakehome bash scripts/sps-provenance.sh check --strict
  note: no skills directories found (install.sh SYNC_PATHS) — nothing to check
  EXIT=0
  $ .../fakehome/.agents/skills/evil-skill/SKILL.md  ("run rm -rf ~")
  UNPINNED: evil-skill — present but never pinned
  == PROVENANCE CHECK: 0 pinned-ok, 0 drifted, 1 unpinned ==
  EXIT=0
  ```
  `sps-provenance.sh:151` only fails on `drift`, so `--strict` ignores `unpinned` by design (line 14). The only CI invocation is `weekly-audit.yml:90-93`, a Monday cron — absent from `sps-ci.yml`.
- **Why it matters.** The README's trust table is the section a non-technical user is told to use to verify the product. This row asserts a pin that does not exist by default, and the guard is scheduled weekly and structurally incapable of failing on a fresh runner.
- **Fix.** Either drop the row, or make `install.sh` call `pin` at the end of a successful install and add `sps-provenance.sh check --strict` to the `validator-battery` job with a committed baseline of expected digests.

### MINOR — 14

**m-1** `uninstall.sh:198` vs `install.sh:174-185`  **MINOR**  The uninstaller's default `--agents '*'` expands to 6 agents while the installer's expands to 33, so skills installed into Goose/Crush/Trae/Zed/OpenClaw/etc. are not removed by the `skills` CLI.
- **Evidence.** `REMOVE_AGENT_ARGS=(--agent "claude-code" --agent "cursor" --agent "codex" --agent "antigravity" --agent "antigravity-cli" --agent "universal")` vs install's 33-entry `--agent` list including `goose, crush, trae, junie, zed, openclaw, droid, qoder, kilo, warp, grok`.
- **Why it matters.** Contributes to M-2: "I uninstalled and files are still there."
- **Fix.** Reuse one shared agent-registry array; have `uninstall.sh` source it from `install.sh` or a single constants file.

**m-2** `install.sh:22,437-442`  **MINOR**  The install confirmation is skipped whenever stdin is not a TTY, so the documented `curl … | bash` bootstrap never asks, and `CI=1` + `npm_config_yes=true` are exported globally to silence every downstream prompt.
- **Evidence.** `if ! $ASSUME_YES && [[ -t 0 ]]; then read -r -p "Continue install? [Y/n] " …`. Under `curl … | bash`, stdin is the script pipe, not a TTY.
- **Why it matters.** A user who runs `bash install.sh` from a script, a Makefile, or an agent shell gets ~30 network installs and 4 marketplace adds with zero confirmation.
- **Fix.** Require `--yes` (or a typed confirmation on `/dev/tty` via `read … </dev/tty`) whenever stdin is not a TTY; abort with instructions if neither is available.

**m-3** `install.sh:487-521` + `README.md:92-96`  **MINOR**  The "Trust note" enumerates three risks but omits four third-party Claude marketplaces, seven plugin installs, a network-capable MCP server, and a PyPI package installer.
- **Evidence.** `install.sh:490-506` adds `nextlevelbuilder/ui-ux-pro-max-skill`, `alirezarezvani/claude-skills`, `trailofbits/skills` + `shahid-personal-skillset` and installs 11 plugins; `:508` `claude mcp add … context7`; `:515/:518` `uv tool install graphifyy && graphify install` / `pip install graphifyy`. `grep -n "graphify\|marketplace\|context7" README.md USER-GUIDE.md` returns **nothing**.
- **Why it matters.** The note reads like a complete risk list. It isn't: three additional third-party code sources execute during install, undisclosed.
- **Fix.** Add the marketplaces, plugins, MCP server and `graphify install` to the trust note (or gate them behind an opt-in flag).

**m-4** `scripts/sps-update.sh:3` vs `:138`  **MINOR**  The updater's header claims it "Preserves the original install profile + agents from ~/.sps/install-manifest.env", but it runs `bash ./install.sh --yes` with no `--agents`.
- **Evidence.** Manifest records `AGENTS=$AGENTS` (`install.sh:269`); the updater never reads it back.
- **Why it matters.** A user who deliberately installed `--agents claude-code` silently gets all 33 agents the next time they update.
- **Fix.** Read `AGENTS=` from the manifest and pass `--agents "$AGENTS"`; correct the header either way.

**m-5** `install.sh:343-345,455-485` + `scripts/sps-restore.sh:8-11`  **MINOR**  Only the three bundled skills are ever backed up; the ~27 curated third-party skills are re-installed over whatever the user had, with no backup and no restore path.
- **Evidence.** The only `backup_existing_skill "…"` call sites are `sps`, `sps-cms`, `sps-seo`. `sps-restore.sh` reads only `~/.sps/backups/<skill>`.
- **Why it matters.** A user who customised `copywriting` or `agent-browser` loses it on every update, with no stated recovery path.
- **UNVERIFIED:** whether `npx skills add` overwrites an existing directory or skips it — I did not run the installer. The absence of backup/disclosure is verified; the overwrite behaviour is not.
- **Fix.** Extend `backup_existing_skill` to every `MANAGED_SKILLS` entry before its `npx skills add` step.

**m-6** `scripts/sps-lesson.sh:110-123` + `USER-GUIDE.md:80-81`  **MINOR**  The publication gate shows file *paths* only, while the tool's own header and the user guide both promise the user sees what is about to be published.
- **Evidence.** Header: "*without it, send shows exactly what will be published and asks first*". Code: `for f in "${lessons[@]}"; do echo "  $f"; done`. Guide: "*it first shows you every lesson that will be published*". The script prints no lesson body, and the content (client details, URLs, keys) is exactly what is being pushed to a **public** repo at line 141.
- **Why it matters.** The consent is real and correctly typed, but the user approves publication without reviewing the text being published.
- **Fix.** Print `section_snippet` for each lesson (Problem/Rule/Applies-to) in the confirmation block, and offer `--dry-run` to write the branch without pushing.

**m-7** `skill/sps-cms/scripts/update.sh:9` + `skill/sps-cms/scripts/update.ps1:8`  **MINOR**  The shipped `sps-cms` skill contains unpinned remote-script execution with no hash, no prompt, and no confirmation.
- **Evidence.** `curl -fsSL https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.sh | bash`; `Invoke-Expression (Invoke-RestMethod -Uri "…/scripts/install.ps1")`.
- **Why it matters.** Anyone running these gets arbitrary code execution from whatever `main` serves that day, with no digest to compare against.
- **Fix.** Pin a SHA-256 of the installer and verify it before execution, or delegate to the already-hash-checked `get-sps.sh` flow.

**m-8** `README.md:178` + `.github/workflows/`  **MINOR**  The "Docs never rot" receipt runs only in `weekly-audit.yml:73-76` (Monday cron); `sps-ci.yml` never invokes `check_docs_drift.py`.
- **Evidence.** `grep -rn "docs_drift" .github/workflows/` → one hit, `weekly-audit.yml:76`.
- **Why it matters.** A pull request that documents a command which does not exist merges green and is caught up to seven days later.
- **Fix.** Add `python3 framework/sps2/tools/check_docs_drift.py` to the `validator-battery` job.

**m-9** `README.md:9` and `README.md:180`  **MINOR**  The README states two different test counts, and neither matches the suite.
- **Evidence.** Line 9: "**Version:** 4.3.0 · 1,236 tests". Line 180: "1,232 tests". Actual, at `HEAD` in a clean worktree: `Ran 1240 tests in 75.548s / OK (skipped=3)`.
- **Why it matters.** The README tells the reader to run the command and count for themselves; it disagrees with itself before they start.
- **Fix.** Generate the count in CI and inject it, or cite `MIN_TESTS` instead of a literal.

**m-10** `README.md:177`  **MINOR**  The receipt command `python3 framework/sps2/tools/check_laws.py .` passes an argument the tool does not accept, and the tool only ever checks the framework repo — never a user's project.
- **Evidence.** `check_laws.py` has no `argparse`; `REPO = Path(__file__).resolve().parents[3]` (line 19) and `main()` takes no arguments, so `.` is silently discarded. Every check in the file targets `framework/domain`, `skill/sps/*.md`, or the repo's own `.sps/`.
- **Why it matters.** A user runs this in their project and concludes their build is law-checked. It is not; it re-checks BuildPilot's own documentation.
- **Fix.** Accept an optional root argument and default to CWD, or reword the receipt to say it validates the framework repo.

**m-11** `USER-GUIDE.md:104-106`  **MINOR**  "The only thing that ever leaves your machine is a lesson you explicitly confirm sending" is false.
- **Evidence.** `scripts/check-update.sh:186` runs `curl -fsSL --max-time 10 "$RAW_VERSION_URL"` on **every** `sps-doctor.sh` invocation (`sps-doctor.sh:101-107`). `scripts/ecosystem-scan.sh:59-62,160,185` queries `api.github.com` and `skills.sh`. `install.sh` performs ~30 outbound requests. No user-authored content leaves, but the absolute claim is wrong.
- **Why it matters.** Absolute privacy claims are the reason people trust a tool with their client work; an overstated one is worse than a nuanced one.
- **Fix.** Reword: "no project content or memory is ever sent; the tool does make version-check and search requests to GitHub."

**m-12** `scripts/smoke-sps.sh:108-150` + `.github/workflows/sps-ci.yml:37-42`  **MINOR**  Every CI push and PR executes the pull-request-controlled `install.sh`, which performs ~27 live `npx skills add` fetches from third-party repositories.
- **Evidence.** `sps-ci.yml:24-26` installs Node 22 → `npx` present → `smoke-sps.sh:108` runs `HOME="$SMOKE_HOME" bash "$REPO/install.sh" --agents '*' --yes` against the checked-out PR tree.
- **Why it matters.** A PR can change installer code that CI then runs with network egress. Impact is bounded (`permissions: contents: read`, no secrets, isolated `HOME`), but it is undisclosed next to a trust note that enumerates npx usage.
- **Fix.** State it in the trust note, and/or run the smoke job only on `push` to `main`, not on `pull_request`.

**m-13** `.github/workflows/sps-ci.yml:157`  **MINOR**  The zero-test floor is `MIN_TESTS=1000` against an actual 1240, so up to 240 tests can disappear without failing the count gate.
- **Evidence.** `MIN_TESTS=1000`; per-module guard (`sps-ci.yml:206-211`) only asserts `grep -qF "(${MODULE}."` — i.e. that each module ran **at least one** test.
- **Why it matters.** A refactor that silently drops a 240-test test class from one module keeps CI green.
- **Fix.** Raise `MIN_TESTS` toward the current count and additionally pin a per-module minimum, or compare the discovered module set for equality rather than subset.

**m-14** `scripts/secret-scan.sh:119-127`  **MINOR**  On macOS the agent/MCP config sweep processes only the *first* file, so a planted credential under `.claude/` scans clean.
- **Evidence.** With a valid 40-char `ghp_` token planted at `.claude/zz-audit-probe.txt`:
  ```
  $ grep -InE -- "$PATTERNS" .claude/zz-audit-probe.txt
  1:probe: ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA      # the regex DOES match
  $ bash scripts/secret-scan.sh
  secret-scan: clean — no secret-shaped values in tracked files, diff, or agent/MCP configs
  EXIT=0
  ```
  The NUL-delimited pipeline ends in `awk 'BEGIN{RS="\0"} …'`. macOS ships `awk version 20200816` (one-true-awk), which yields only the first record:
  ```
  $ printf 'rec1\0rec2\0rec3\0' | awk 'BEGIN{RS="\0"}{n++} END{print n}'
  1
  ```
  so `find .claude -type f` output is truncated after `.claude/settings.json`.
- **UNVERIFIED:** the GitHub Actions runners are `ubuntu-latest` with gawk/mawk, where `RS="\0"` is expected to behave correctly. I could not execute a Linux runner here. This finding is scoped to developers running the documented command locally on macOS.
- **Why it matters.** A macOS user — a large share of Claude Code users — gets a false "clean" for exactly the untracked-config surfaces the header says it covers.
- **Fix.** Replace the `sort -z | awk RS="\0"` tail with a portable `while IFS= read -r -d ''` loop and an associative-array de-dup, or a `python3` helper.

### NIT — 6

**n-1** `framework/sps2/tools/gen_law_test.py:51`  **NIT**  `CHECK_ID_RE`'s `$` anchor tolerates a single trailing newline, which is then emitted raw into the generated module docstring.
- **Evidence.** `re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]*$")` accepts `"section-dod\n"`; the preview prints `Locks in the repeat rejection of (section-dod` / `, skill/sps/SECTION-DOD.md)`. Verified the output is still **valid Python** (`ast.parse` OK; class name `TestLawRegressSectionDod` unaffected) because `check_id` only reaches docstrings and `snake()`-derived identifiers.
- **Why it matters.** Cosmetic only — the malformed line makes generated headers harder to read, and the regex is looser than its stated intent.
- **Fix.** Use `\Z` instead of `$` in `CHECK_ID_RE` (and note `_rel`/`_check_approved_by` already use an explicit control-character scan, which is why they are unaffected).

**n-2** `framework/sps2/tools/check_laws.py:125-126`  **NIT**  A duplicated `for law in (...)` loop is nested inside the FILE-SPLITTING `else` branch and re-tests the stale `law` variable from the previous loop.
- **Evidence.** Lines 119-126: the FILE-SPLITTING block's `elif` re-opens `if f"**{law}" not in st:` using whatever `law` last held from the line-113 loop.
- **Why it matters.** Dead code that reads as a second safety check; a future edit to the outer loop's tuple silently changes this one's meaning.
- **Fix.** Delete lines 125-126.

**n-3** `scripts/sps-update.sh:145`  **NIT**  Step numbering jumps from `# 2. Reinstall` to `# 4. Verify with doctor` — there is no step 3.
- **Why it matters.** Suggests a missing stage in a destructive script.
- **Fix.** Renumber to 3.

**n-4** `uninstall.sh:315-318`  **NIT**  `mv "$HOME/.sps/backups" "$HOME/.sps-backups-uninstalled"` nests a second backup store *inside* the first on a repeat uninstall.
- **Evidence.** `mv dir existing_dir` moves `dir` *into* `existing_dir`, producing `~/.sps-backups-uninstalled/backups/…`.
- **Why it matters.** Confusing but non-destructive — nothing is lost.
- **Fix.** Add a timestamp or uniquify loop to the destination.

**n-5** `.github/workflows/sps-ci.yml:262-288`, `framework/sps2/tests/test_manifest_anchor.py`  **NIT**  The dual anchor and its anchor test exist only in the uncommitted working tree; `HEAD` (`fa7a9c6`) has neither, so no CI run has yet exercised the fix.
- **Evidence.** `git log --all --name-only` contains no `test_manifest_anchor.py`; `git ls-files --others --exclude-standard` lists it and `test_gen_law_test_approval.py`. At `HEAD`, the battery is green: `Ran 1240 tests … OK (skipped=3)`.
- **Why it matters.** The fix is sound but unproven in CI; a reviewer reading `main` today sees the old single-anchor design.
- **Fix.** Commit the batch (manifest re-pin → constant → workflow literal, in that order, per the repo's own ordering law) and re-run CI.

**n-6** `install.sh:36-72`  **NIT**  `SYNC_PATHS` lists `"$HOME/.config/opencode/skills"` twice (36 entries, 34 unique).
- **Evidence.** Lines 48 and 64. `sed -n '36,72p' install.sh | grep -o '"\$HOME/[^"]*"' | sort -u | wc -l` → `34`.
- **Why it matters.** Harmless (the loop is idempotent), but it inflates the reported "34 roots" in `uninstall.sh:77-78` and invites drift in future edits.
- **Fix.** Delete line 64.

---

## Cross-check against README's receipts table (line by line)

| README claim (line) | Can CI actually FAIL on it? | Verdict |
|---|---|---|
| "Secrets can't sneak out … CI blocks the merge" (175) | Yes — `secret-scan.yml` runs on `push` + `pull_request`, `secret-scan.sh` exits 1 on hits | **ENFORCED** (but see m-14: macOS local runs under-scan config surfaces; branch-protection requirement is a repo setting — **UNVERIFIED** from the tree) |
| "Third-party skills can't be tampered with … every installed skill's SHA-256 is pinned" (176) | No — nothing pins by default; the only CI call is a Monday cron that exits 0 on a fresh runner | **M-3** |
| "The rules are actually enforced" (177) | Yes — `check_laws.py` runs in `lint-and-smoke` and `validator-battery` | **ENFORCED**, but the receipt command is misleading (**m-10**) |
| "Docs never rot … or this fails" (178) | The tool fails correctly, but only weekly | **m-8** |
| "Your work is backed up" (179) | No — `sps-backup.sh` is manual, by design | **Advisory by design** — not a finding |
| "1,232 tests" (180) | No | **m-9** |

Other claims checked:

- `README.md:114-115` / `USER-GUIDE.md:103` — "`/sps` never pushes, publishes, or deploys without your explicit yes." **ENFORCED.** `sps-lesson.sh:110-123` is the only push/PR path in the tree; it requires a typed `yes` (fail-closed on EOF) and only reaches `git push`/`gh pr create` at lines 141-147. `ecosystem-scan.sh` is read-only and installs nothing. Residual disclosure gap: **m-6**.
- `README.md:92-96` trust note — accurate for what it lists, incomplete (**m-3**).
- `USER-GUIDE.md:109-110` — "The installer overwrites the bundled `sps`/`sps-cms`/`sps-seo` skills on update" — accurate; but the backup behind that promise is best-effort (**M-1**) and the curated third-party skills are not mentioned (**m-5**).

## Test-battery integrity (Layer 6) — no findings

- **Module list vs tree.** `.github/expected-test-modules.txt` (53 entries incl. the 2 new) is a strict superset of `git ls-files 'test_*.py'` (51) by exactly the 2 untracked new modules. At `HEAD` the two agree exactly. The CI guard (`sps-ci.yml:185-217`) checks expected ⊆ discovered plus "≥1 test per discovered module", so a *deleted* test module fails loudly.
- **Count.** `Ran 1240 tests … OK (skipped=3)` at `HEAD`.
- **Vacuity scan.** AST walk over all 53 test files: **0** tests with a bare `pass` body. **9** tests contain no direct `assert*` — all 9 verified legitimate: 7 in `test_p5.py` delegate to `_assert_malformed_is_reported` (which itself calls `self.fail` + `assertTrue`), `test_learning.py:41` asserts by absence of exception on `_validate_entry`, `test_ssrf_redirects.py:36` likewise on `_validate_url`.
- **Skips (3).** All conditional: symlink support (`test_p10_runtime_gate.py:1342`), `ajv`/`node` availability (`test_p17_endtoend.py:214-225`). None unconditional.
- Only weak spot: **m-13** (count floor 1000 vs 1240 actual).

## UNVERIFIED items (explicitly not asserted as findings)

1. Whether `validator-battery` / `python-unittest` are configured as **required** status checks in GitHub branch protection — a repository setting, not visible in the tree. `CHANGELOG.md:38` and `.sps/handoff.md:76` both claim "4 required CI checks".
2. Whether `npx skills add` overwrites or skips an existing skill directory (**m-5**) — the installer was not executed.
3. `secret-scan.sh` behaviour on `ubuntu-latest` (**m-14**) — no Linux runner available; only macOS was measured.
4. Whether the prior audits described in the brief ever existed as files — `git log --all`, all branches, and `git stash list` contain no such report.

---

## VERDICT

**ISSUES-FOUND** — BLOCKER 0 / MAJOR 3 / MINOR 14 / NIT 6

**Where promises outrun machinery:** the three governance-era promises the README sells as machine-checked — the dual manifest anchor, the typed lesson-publication gate, and the codegen injection defence — are now genuinely enforced and survived adversarial re-derivation; what still outruns the machinery is the *installer/uninstaller lifecycle and the README's receipts table*: uninstall claims completeness while leaving skills in 15+ roots, the "every third-party skill is pinned" receipt describes a state no install ever creates, and the backup that the update-safety story rests on is best-effort whose failure is swallowed while the tool reports success.