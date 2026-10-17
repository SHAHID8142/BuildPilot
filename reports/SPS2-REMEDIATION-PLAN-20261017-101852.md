# SPS2 Remediation Planning Round — Plan and Review Only

**Timestamp:** 2026-10-17 10:18:52 +06  
**Filename suffix:** `20261017-101852`  
**Mode:** read-only investigation and planning only  
**Branch:** `build/roadmap-p3-completion`  
**HEAD:** `c49f3852e1c31d0136269c80fe58201b059af3ec`

## 1. Worktree Baseline

| Item | Value |
|---|---:|
| Staged files | 0 |
| Modified tracked files | 39 |
| Untracked porcelain entries | 26 |
| Total porcelain entries | 65 |
| Expanded untracked files | 180 |
| Stashes | 0 |

The only intended filesystem change from this round is this new report. No implementation, staging, commit, push, network operation, CI change, deployment, publication, merge, release, cleanup, or protected-record modification was performed.

## 2. TODO Ledger

| ID | Package | Status | Evidence |
|---|---|---|---|
| P-0 | Baseline and preservation check | DONE | Live Git state and protected hashes inspected. |
| P-1 | Scanner evasion hardening plan | DONE | `sps2/governance/import_exceptions.py:105-139`, `:142-259`; temporary scanner probe. |
| P-2 | Installer SSH host-key plan | DONE | `install.sh:15`; `install.ps1:9`. |
| P-3 | Uninstaller path confinement plan | DONE | `uninstall.sh:70-103`, `:126-175`; `uninstall.ps1:43-73`, `:95-147`. |
| P-4 | Snapshot/rollback guarantees plan | DONE | `sps2/tools/rollback_seo.py:234-327`, `:330-392`, `:395-506`. |
| P-5 | Independent Claude review | **NOT STARTED** | This environment exposes Codex only; Claude has not run. Do not treat this report as Claude review. |

## 3. Confirmed Defects Versus Hypotheses

| Area | Classification | Evidence |
|---|---|---|
| Scanner dynamic-import evasion | **Confirmed defect** | Temporary probe showed `getattr(importlib, "import_module")("domain.seo.model")` and `importlib.__dict__["import_module"]("domain.seo.model")` both return `ok=true` with no violation. |
| Installer SSH host-key bypass | **Confirmed defect** | Both installers explicitly set `StrictHostKeyChecking=no`. |
| Uninstaller manifest-path escape | **Confirmed defect** | Manifest values are split and joined into paths without containment validation before recursive deletion. |
| Snapshot atomicity | **Confirmed defect** | `create_snapshot` documents atomicity but writes directly into the destination and publishes the manifest in place. |
| Snapshot manifest strictness | **Confirmed defect** | Restore accepts non-integer `file_count`, non-list `files`, and malformed entry shapes. |
| Partial rollback failure handling | **Hypothesis / deferred risk** | `execute_rollback` calls `unlink()` without catching per-file errors; the exact recovery behavior after mid-loop failure is not demonstrated. |
| Snapshot file TOCTOU | **Hypothesis / deferred risk** | lstat/read and copy operations are not a single atomic transaction; exploitability depends on concurrent writer timing. |
| Rehearsal success | **Policy-blocked, not a false green** | Current rehearsal correctly fails and attributes the block to the dynamic `domain.seo` import. |

## 4. Work Package 1 — Scanner Evasion Hardening

### Affected code

- `sps2/governance/import_exceptions.py`
  - `_is_dynamic_import()` at lines 105-121
  - `_contains_domain_seo_string()` at lines 124-139
  - `scan_import_exceptions()` at lines 142-259
- Tests: `sps2/tests/test_round26_governance_contracts.py`, `TestImportExceptionContract`

### Demonstrated failure

The scanner recognizes only callables that are a `Name` equal to `__import__` or `import_module`, or an `Attribute` named `import_module`. It misses callable expressions:

```python
getattr(importlib, "import_module")("domain.seo.model")
importlib.__dict__["import_module"]("domain.seo.model")
```

Both were confirmed to return `ok=true` with no violation in a temporary synthetic manifest.

### Minimal proposed change

In `_is_dynamic_import()`, fail closed when a `Call` node's callable is itself a dynamic-loader expression:

```python
def _is_dynamic_import(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False

    function = node.func
    if isinstance(function, ast.Name) and function.id in {"__import__", "import_module"}:
        return True
    if isinstance(function, ast.Attribute) and function.attr == "import_module":
        return True
    if isinstance(function, (ast.Call, ast.Subscript)):
        return True
    return False
```

This does not add any import exception or alter DEC-7302 policy. It only strengthens detection of forbidden dynamic imports.

### Tests needed

1. Positive failure test for `getattr(importlib, "import_module")("domain.seo.model")`.
2. Positive failure test for `importlib.__dict__["import_module"]("domain.seo.model")`.
3. Positive failure test for a user-defined wrapper that returns `importlib.import_module` and is then called.
4. Negative test proving benign static imports remain allowed.
5. Negative test proving unrelated dynamic imports of non-`domain.seo` modules remain allowed.
6. Regression test that the live scanner still reports the known `p10_runtime_gate.py` violation exactly once.

### Risks

- Overbroad callable detection could flag unrelated higher-order functions.
- Restricting the rule to calls whose callable is itself a `Call` or `Subscript` keeps the false-positive surface narrow but is not a complete general-purpose dynamic-import analyzer.
- Future obfuscation through `eval`, metaprogramming, or generated code remains out of scope.

### Rollback approach

Revert only `_is_dynamic_import()` and the added scanner tests. No manifest or decision-record change is required.

### Acceptance criteria

1. Both confirmed evasion forms fail closed.
2. Existing live approved imports remain exactly eight.
3. Existing scanner tests pass.
4. New negative and positive tests pass.
5. No exception manifest, validator baseline, or decision record changes.

## 5. Work Package 2 — Installer SSH Host-Key Verification

### Affected code

- `install.sh:15`
- `install.ps1:9`

Both currently set:

```text
StrictHostKeyChecking=no
```

### Demonstrated failure

A machine-in-the-middle can present an unknown host key during a Git SSH operation, and the installer accepts it without user confirmation. This defeats host identity verification for any SSH-based Git access used by the installer.

### Minimal proposed change

Use fail-closed SSH behavior:

```bash
export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=accept-new"
```

PowerShell equivalent:

```powershell
$env:GIT_SSH_COMMAND = "ssh -oBatchMode=yes -oStrictHostKeyChecking=accept-new"
```

`accept-new` accepts only unknown hosts on first use and still rejects changed host keys. If stricter behavior is desired, use `yes`, but that may break first-time installation unless the host key is already known.

### Tests needed

1. Static test asserting neither installer contains `StrictHostKeyChecking=no`.
2. Static test asserting both contain `StrictHostKeyChecking=accept-new`.
3. If runtime coverage is available, test a changed host key is rejected.
4. Static test ensuring `GIT_CLONE_PROTECTION_ACTIVE=false` is separately reviewed or removed; it is not part of this minimal change but is a related hardening candidate.

### Risks

- First-time installs to a new host will prompt or record a new host key.
- Batch mode may cause failure if interactive host-key confirmation is required.
- Users with preexisting compromised `known_hosts` entries are not protected by this change alone.

### Rollback approach

Revert the two environment assignments to their prior values only if the user explicitly accepts the insecure behavior. Otherwise preserve fail-closed behavior and document the prerequisite.

### Acceptance criteria

1. No installer enables `StrictHostKeyChecking=no`.
2. Changed host keys are rejected.
3. First-use behavior is explicit and documented.
4. Bash and PowerShell forms remain consistent.

## 6. Work Package 3 — Uninstaller Path Confinement

### Affected code

- `uninstall.sh`
  - `remove_agent_skill()` at lines 70-103
  - manifest parsing at lines 126-137
  - mirror deletion at lines 167-175
- `uninstall.ps1`
  - `Remove-AgentSkill()` at lines 43-73
  - manifest parsing at lines 95-110
  - mirror deletion at lines 135-147

### Demonstrated failure

Manifest-controlled `MANAGED_SKILLS` and `SYNC_PATHS` values are incorporated directly into deletion paths. A crafted manifest value such as `../../important` can escape the intended skill root. The uninstaller then recursively removes attacker-selected paths without verifying that the resolved path remains within an allowlisted agent-skill root.

### Minimal proposed change

Introduce one shared confinement helper per language.

Bash concept:

```bash
is_safe_uninstall_target() {
  local candidate="$1"
  local root
  for root in \
    "$HOME/.agents/skills" \
    "$HOME/.config/agents/skills" \
    "$HOME/.claude/skills" \
    "$HOME/.cursor/skills" \
    "$HOME/.codex/skills" \
    "$HOME/.gemini/skills" \
    "$HOME/.gemini/config/skills" \
    "$HOME/.gemini/antigravity/skills" \
    "$HOME/.gemini/antigravity-cli/skills" \
    "$HOME/.windsurf/skills" \
    "$HOME/.antigravity/skills"; do
    case "$(cd "$root" 2>/dev/null && pwd -P)/" in
      "$(cd "$(dirname "$candidate")" 2>/dev/null && pwd -P)/"/*) return 0 ;;
    esac
  done
  return 1
}
```

PowerShell concept:

```powershell
function Test-SafeUninstallTarget([string]$Path) {
    $candidate = [IO.Path]::GetFullPath($Path)
    $roots = @(
        (Join-Path $env:USERPROFILE ".agents\skills"),
        (Join-Path $env:USERPROFILE ".config\agents\skills"),
        (Join-Path $env:USERPROFILE ".claude\skills"),
        (Join-Path $env:USERPROFILE ".cursor\skills"),
        (Join-Path $env:USERPROFILE ".codex\skills"),
        (Join-Path $env:USERPROFILE ".gemini\skills"),
        (Join-Path $env:USERPROFILE ".gemini\config\skills"),
        (Join-Path $env:USERPROFILE ".gemini\antigravity\skills"),
        (Join-Path $env:USERPROFILE ".gemini\antigravity-cli\skills"),
        (Join-Path $env:USERPROFILE ".windsurf\skills"),
        (Join-Path $env:USERPROFILE ".antigravity\skills")
    )
    foreach ($root in $roots) {
        $fullRoot = [IO.Path]::GetFullPath($root + [IO.Path]::DirectorySeparatorChar)
        if ($candidate.StartsWith($fullRoot, [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}
```

Then require every deletion target to pass confinement and reject symlinks or non-regular directories where applicable.

### Tests needed

1. Positive test: a legitimate `$HOME/.claude/skills/sps` target is removable.
2. Positive test: a legitimate `$HOME/.codex/skills/sps-cms` target is removable.
3. Negative test: `../../important` is rejected.
4. Negative test: an absolute path outside every allowlisted root is rejected.
5. Negative test: a symlinked skill directory is not followed into an out-of-root destination.
6. Negative test: a malformed manifest cannot cause deletion outside an allowlisted root.
7. Cross-platform static test: Bash and PowerShell share the same root policy.

### Risks

- Overly strict confinement could leave legitimate custom skill locations installed by future versions.
- Symlink handling differs between macOS, Linux, and Windows.
- Root-relative paths in existing manifests may become invalid after the user moves their home directory.

### Rollback approach

Keep the confinement helper isolated and revert only the helper plus its call sites. Preserve the existing manifest for forensic inspection.

### Acceptance criteria

1. No manifest-controlled path can escape an allowlisted skill root.
2. Symlink traversal is rejected.
3. Both Bash and PowerShell enforce the same policy.
4. Legitimate default skill paths remain removable.
5. Focused tests cover traversal, absolute-path escape, symlink, and malformed manifest cases.

## 7. Work Package 4 — Snapshot and Rollback Guarantees

### Affected code

- `sps2/tools/rollback_seo.py`
  - `create_snapshot()` at lines 234-260
  - `restore_snapshot()` at lines 263-327
  - `execute_rollback()` at lines 330-392
  - `execute_rehearsal()` at lines 395-506
- Tests: `domain/seo/tests/test_isolation.py`

### Demonstrated failure

`create_snapshot()` writes directly into the destination and then publishes `manifest.json` in place. An interrupted snapshot can leave a partial or malformed snapshot. `restore_snapshot()` does not strictly validate manifest shape, timestamp, source regular-file status, or entry types.

### Minimal proposed change

1. Build the snapshot in a sibling temporary directory.
2. Copy every source only after lstat confirms it is a regular file.
3. Compute and record SHA-256 after copying the snapshot copy.
4. Validate the manifest before publication.
5. Atomically replace the snapshot directory or manifest only after all entries are complete.
6. Restore only from a strictly validated manifest.
7. Require `file_count` to be an integer, `files` to be a list, and each entry to have exactly `relative_path` and `sha256`.
8. Reject non-regular snapshot sources and symlinked snapshot paths.
9. Validate the UTC timestamp format.
10. Preserve current rollback rehearsal exit semantics and the dynamic-import fail-closed behavior.

### Tests needed

1. Snapshot creation succeeds and manifest exactly matches copied files.
2. Interrupted snapshot creation does not publish a usable manifest.
3. Restore rejects non-integer `file_count`.
4. Restore rejects non-list `files`.
5. Restore rejects malformed entries and extra fields.
6. Restore rejects symlinked snapshot files.
7. Restore rejects missing or malformed timestamp.
8. Restore rejects source files changed after manifest publication.
9. Successful rollback followed by restore returns the original file set and hashes.
10. Existing digest-mismatch, path-escape, and truncated-snapshot tests continue to pass.

### Risks

- Atomic directory replacement may not be portable across all filesystems.
- A strict timestamp requirement could reject older legitimate snapshots.
- More rigorous validation may turn previously tolerated snapshots into explicit failures.
- Rollback success remains policy-blocked while the unapproved dynamic import exists.

### Rollback approach

Implement snapshot hardening as one isolated change. Keep the existing public function names and return contracts. Revert the helper and tests without touching scanner policy, manifests, or P10 gates.

### Acceptance criteria

1. No partially written snapshot is accepted as recoverable.
2. Restore fails closed on malformed manifests and non-regular sources.
3. Successful restore is byte-identical to the snapshot.
4. Existing rollback and rehearsal tests pass.
5. No rollback success is claimed while the dynamic-import violation remains.
6. P10 gate and validator baselines remain unchanged.

## 8. Sequencing and Dependencies

| Order | Package | Dependency | Rationale |
|---|---|---|---|
| 1 | Scanner hardening | None | Narrow, code-owned, and directly testable. |
| 2 | Snapshot/rollback hardening | None | Isolated helper and test change; preserves current fail-closed rehearsal. |
| 3 | Installer SSH hardening | User approval to edit installer paths | Security-only change but installer files are governance-sensitive. |
| 4 | Uninstaller confinement | User approval to edit uninstaller paths | More invasive deletion-path change requiring cross-platform tests. |

Scanner and rollback work are technically independent. Installer and uninstaller work should be reviewed together because both affect user-machine paths.

## 9. Governance Boundaries

This plan does **not** ratify DEC-7301, DEC-7302, or DEC-7303. It does **not** modify the disputed approval record or correction sidecar. It does **not** add exceptions, broaden manifests, weaken validators, change P10 gate semantics, or alter validator baselines.

The scanner hardening is a security-control fix, not adoption of DEC-7302. Snapshot hardening is a reliability fix, not a rollback-success claim. Installer and uninstaller changes require explicit approval because they affect legacy-sensitive installer paths.

## 10. Required Independent Review

Claude has **not** reviewed this plan. No Claude report exists from this session. Claude must independently inspect the live files and adversarially review:

1. whether the scanner callable-expression rule is too narrow or too broad;
2. whether `accept-new` is acceptable for SSH host-key policy;
3. whether uninstaller confinement covers all supported roots, symlink cases, and malformed manifests;
4. whether snapshot atomicity and restore strictness satisfy the intended recovery guarantee;
5. whether any proposed test normalizes the current dynamic-import violation as success.

Implementation remains prohibited until Claude's separate review and any required User authorization are complete.
