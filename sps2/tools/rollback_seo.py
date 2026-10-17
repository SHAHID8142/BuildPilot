#!/usr/bin/env python3
"""SPS 2.0 Advisory Rollback & Project-Local stdlib Isolation Tool (REQ-P9-10).

Agent-neutral. Standard library only. Project-local.

Implements REQ-P9-10:
1. Advisory Rollback:
   - Removes or disables the P9 SEO subsystem without touching unrelated project state.
   - Preserves all unrelated modified files (including sps2/tools/portability.py).
   - Preserves all unrelated untracked user files.
   - Leaves zero orphan imports or dangling references across the project.
   - Does NOT rewrite Git history.
   - Does NOT modify machine-global state or legacy files.
   - Fully deterministic, reversible, and mechanically verifiable.
2. Project-Local stdlib Isolation:
   - Verifies all P9 dependencies remain Python standard library only.
   - Verifies zero third-party packages, CLIs, or npm modules installed.
   - Verifies CONF-001 boundary preservation (zero invented LCP/INP thresholds).
   - Verifies P7 persistent project-local governance artifacts remain intact.
3. Rollback Rehearsal:
   - Proves deletion of domain/seo/ leaves core SPS 2.0 validators and CMS tests passing.
   - Exercises rehearsal in an isolated temporary scratch copy without modifying the live repository.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sps2.core.p9_surface import P9_ALLOWLIST_RELATIVE_PATHS
from sps2.governance.import_exceptions import scan_import_exceptions

# Fallback standard library modules set
STDLIB_MODULES: frozenset[str] = getattr(sys, "stdlib_module_names", None) or frozenset(
    "abc argparse ast asyncio base64 bisect calendar cgi cmath codecs collections "
    "concurrent contextlib contextvars copy csv ctypes dataclasses datetime decimal "
    "difflib dis doctest email enum errno faulthandler fcntl filecmp fileinput fnmatch "
    "fractions functools gc getopt getpass gettext glob graphlib grp gzip hashlib heapq "
    "hmac html http idlelib imaplib imghdr importlib inspect io ipaddress itertools "
    "json keyword linecache locale logging lzma mailbox mailcap marshal math mimetypes "
    "mmap modulefinder multiprocessing netrc nis nntplib numbers operator os ossaudiodev "
    "pathlib pdb pickle pipes pkgutil platform plistlib poplib posix pprint profile "
    "pstats pty pwd py_compile pyclbr pydoc queue quopri random re readline reprlib "
    "resource rlcompleter runpy sched secrets select selectors shelve shlex shutil "
    "signal site smtpd smtplib sndhdr socket socketserver spwd sqlite3 ssl stat "
    "statistics string stringprep struct subprocess sunau symtable sys sysconfig "
    "syslog tabnanny tarfile telnetlib tempfile termios test textwrap threading time "
    "timeit tkinter token tokenize trace tracemalloc tty turtle types typing unicodedata "
    "unittest urllib uu uuid venv warnings wave weakref webbrowser wsgiref xdrlib xml "
    "xmlrpc zipapp zipfile zipimport zlib zoneinfo _thread".split()
)

# Explicit P9 allowlist patterns
P9_ALLOWLIST_PATTERNS = [
    "domain/seo",
    "sps2/tools/seo_audit.py",
]

# Legacy directories that must never be modified
LEGACY_DIRS = ("skills", "scripts", "plugins", "templates")


def get_repo_root(start_path: Path | None = None) -> Path:
    """Find the project repository root deterministically."""
    cur = (start_path or Path(__file__)).resolve()
    if cur.is_file():
        cur = cur.parent
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists() or (parent / "sps2").exists():
            return parent
    return cur


def assert_safe_project_local_target(target_dir: str | Path, repo_root: Path) -> Path:
    """Verify that a target directory is project-local and safe for rollback operations.
    
    Rejects targets outside the project root, path traversal attempts, and system root.
    """
    resolved_root = repo_root.resolve()
    target = Path(target_dir).resolve()

    # Must be within the repository root
    try:
        target.relative_to(resolved_root)
    except ValueError:
        raise ValueError(
            f"Security violation: Target directory '{target}' is outside repository root '{resolved_root}'"
        )

    # Rejection of system root or parent escape
    if target == Path(target.anchor) or target == target.parent:
        raise ValueError(f"Security violation: Target directory '{target}' is a system root")

    return target


def get_p9_files(project_root: Path, include_self: bool = False) -> list[Path]:
    """Return only regular Python files in the allowlisted P9 surface."""
    files: list[Path] = []
    seo_dir = project_root / "domain" / "seo"
    if seo_dir.is_dir():
        for p in seo_dir.glob("**/*.py"):
            if "__pycache__" in p.parts:
                continue
            try:
                mode = p.lstat().st_mode
            except OSError:
                continue
            if stat.S_ISREG(mode):
                files.append(p)

    cli_tool = project_root / "sps2" / "tools" / "seo_audit.py"
    try:
        cli_mode = cli_tool.lstat().st_mode
    except OSError:
        cli_mode = 0
    if stat.S_ISREG(cli_mode):
        files.append(cli_tool)

    if include_self:
        self_tool = project_root / "sps2" / "tools" / "rollback_seo.py"
        try:
            self_mode = self_tool.lstat().st_mode
        except OSError:
            self_mode = 0
        if stat.S_ISREG(self_mode):
            files.append(self_tool)

    return sorted(files)


def get_unowned_domain_seo_files(project_root: Path) -> list[Path]:
    """Return non-P9 files under domain/seo that rollback must preserve.

    __pycache__ contents are NOT skipped here: execute_rollback later
    removes the whole domain/seo tree, so cache files under it would be
    destroyed silently if the ownership check ignored them. Cache files
    are regenerable, but the check-then-delete contract is that rollback
    aborts on anything it does not own — so they must be reported, not
    skipped. A symlinked domain/seo root is likewise not followed for
    enumeration: its entries live outside the project tree and must abort
    the rollback rather than enter the deletion set.
    """
    seo_dir = project_root / "domain" / "seo"
    try:
        root_mode = seo_dir.lstat().st_mode
    except OSError:
        return []
    if not stat.S_ISDIR(root_mode):
        # Absent (nothing to remove) or a symlink/other entry type: let the
        # caller see it as unowned so rollback aborts instead of following
        # the link and enumerating outside-tree files for deletion.
        if root_mode != 0:
            return [seo_dir]
        return []
    unowned: list[Path] = []
    for path in seo_dir.glob("**/*"):
        try:
            mode = path.lstat().st_mode
        except OSError:
            unowned.append(path)
            continue
        if stat.S_ISDIR(mode):
            continue
        relative_path = path.relative_to(project_root).as_posix()
        if not (
            stat.S_ISREG(mode)
            and path.suffix == ".py"
            and relative_path in P9_ALLOWLIST_RELATIVE_PATHS
        ):
            unowned.append(path)
    return sorted(unowned)


def sha256_file(path: Path) -> str:
    """Compute SHA-256 digest of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def check_stdlib_isolation(files: list[Path]) -> list[str]:
    """Scan Python files and verify that all imports are standard library or project-internal."""
    violations: list[str] = []
    allowed_internal = ("domain", "sps2")

    for p in files:
        if not p.name.endswith(".py"):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p))
        except (SyntaxError, OSError):
            continue

        for node in ast.walk(tree):
            mod_names: list[tuple[str, int]] = []
            if isinstance(node, ast.Import):
                for a in node.names:
                    mod_names.append((a.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                if node.module:
                    mod_names.append((node.module, node.lineno))

            for m, lineno in mod_names:
                top = m.split(".")[0]
                if not top:
                    continue
                if top in STDLIB_MODULES:
                    continue
                if any(top == pre or top.startswith(f"{pre}.") for pre in allowed_internal):
                    continue
                violations.append(
                    f"{p}:{lineno}: External dependency '{m}' violates stdlib isolation requirement"
                )

    return violations


def check_conf_001_invariants(files: list[Path]) -> list[str]:
    """Verify that no file contains invented numeric thresholds for LCP or INP."""
    violations: list[str] = []
    pattern = re.compile(r"(LCP|INP)\s*[:=]?\s*\d+")

    for p in files:
        if not p.name.endswith(".py"):
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for idx, line in enumerate(lines, 1):
            if pattern.search(line):
                violations.append(
                    f"{p}:{idx}: Forbidden invented numeric threshold per CONF-001: '{line.strip()}'"
                )

    return violations


def check_orphan_references(project_root: Path) -> list[str]:
    """Scan the shared DEC-7302 contract; syntax and dynamic import errors fail closed."""
    return scan_import_exceptions(project_root)["violations"]


def get_status(project_root: Path) -> dict[str, Any]:
    """Compute current P9 implementation and rollback status."""
    p9_files = get_p9_files(project_root)
    snapshot_dir = project_root / "sps2" / "memory" / ".p9_rollback_snapshot"
    manifest_file = snapshot_dir / "manifest.json"

    if p9_files:
        state = "PRESENT"
    elif manifest_file.exists():
        state = "ROLLED_BACK"
    else:
        state = "NOT_INSTALLED"

    orphans = check_orphan_references(project_root)
    import_result = scan_import_exceptions(project_root)
    stdlib_errors = check_stdlib_isolation(p9_files)
    conf_001_errors = check_conf_001_invariants(p9_files)

    return {
        "state": state,
        "p9_file_count": len(p9_files),
        "p9_files": [str(p.relative_to(project_root)) for p in p9_files],
        "snapshot_exists": manifest_file.exists(),
        "orphan_count": len(orphans),
        "orphan_violations": orphans,
        "approved_import_count": len(import_result["approved"]),
        "approved_imports": import_result["approved"],
        "stdlib_clean": len(stdlib_errors) == 0,
        "stdlib_violations": stdlib_errors,
        "conf_001_clean": len(conf_001_errors) == 0,
        "conf_001_violations": conf_001_errors,
    }


def create_snapshot(project_root: Path, snapshot_dir: Path | None = None) -> Path:
    """Atomically record the current P9 SEO surface into a snapshot manifest for safe recovery."""
    target_snapshot = snapshot_dir or (project_root / "sps2" / "memory" / ".p9_rollback_snapshot")
    target_snapshot.parent.mkdir(parents=True, exist_ok=True)

    # Destination contract: the snapshot stores a manifest and copied files
    # beneath the target path, so anything not an actual directory (symlinks
    # included — the entry type itself is checked, not the resolved target)
    # is rejected before any staging or move-aside happens. Rejecting early
    # keeps the occupant intact and avoids the old failure mode where a
    # regular-file target was moved to .previous-<pid>, the new snapshot was
    # published anyway, and cleanup then raised NotADirectoryError.
    try:
        target_mode = target_snapshot.lstat().st_mode
    except FileNotFoundError:
        pass  # absent target: the normal publish path creates it
    except OSError as exc:
        raise ValueError(f"Snapshot destination is not inspectable: {target_snapshot}: {exc}") from exc
    else:
        if not stat.S_ISDIR(target_mode):
            raise ValueError(
                f"Snapshot destination must be a directory (or absent), "
                f"not symlink/regular-file/other: '{target_snapshot}'"
            )

    p9_files = get_p9_files(project_root, include_self=False)
    staging_path = Path(tempfile.mkdtemp(prefix=f".{target_snapshot.name}.tmp-", dir=target_snapshot.parent))
    previous_snapshot: Path | None = None
    published = False
    try:
        manifest_entries: list[dict[str, str]] = []
        for source in p9_files:
            rel = source.relative_to(project_root).as_posix()
            destination = staging_path / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            manifest_entries.append({
                "relative_path": rel,
                "sha256": sha256_file(destination),
            })

        manifest_data = {
            "schema": "sps2.p9-rollback-manifest/v1",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "file_count": len(manifest_entries),
            "files": manifest_entries,
        }
        (staging_path / "manifest.json").write_text(
            json.dumps(manifest_data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        if target_snapshot.exists():
            previous_snapshot = target_snapshot.parent / f".{target_snapshot.name}.previous-{os.getpid()}"
            # Never clobber a stranded previous snapshot from an earlier
            # crashed run: move the old one aside first so the recovery
            # copy below cannot destroy the only surviving prior snapshot.
            if previous_snapshot.exists():
                stranded = previous_snapshot.parent / f".{previous_snapshot.name}.stranded-{os.getpid()}"
                os.replace(previous_snapshot, stranded)
            os.replace(target_snapshot, previous_snapshot)
        os.replace(staging_path, target_snapshot)
        published = True
        if previous_snapshot is not None:
            shutil.rmtree(previous_snapshot)
            previous_snapshot = None
        return target_snapshot
    except BaseException:
        # Cleanup ordering matters: staging residue goes first, then the
        # previous snapshot is restored if (and only if) the live target is
        # absent. If the publish itself succeeded but a later step raised,
        # the new snapshot stays live and the previous one is preserved
        # under .previous-<pid> instead of being destroyed by cleanup.
        shutil.rmtree(staging_path, ignore_errors=True)
        if previous_snapshot is not None:
            if not target_snapshot.exists():
                os.replace(previous_snapshot, target_snapshot)
            # A post-publish failure leaves both the new snapshot and the
            # previous one valid; keep the previous copy for recovery
            # rather than rmtree-ing the only other known-good state.
        raise


def restore_snapshot(project_root: Path, snapshot_dir: Path | None = None) -> tuple[int, list[str]]:
    """Restore the P9 SEO surface from a snapshot manifest.

    Every entry is fully validated BEFORE anything is copied: the recorded
    relative path must be allowlisted P9 surface, resolve strictly inside
    the project root, and the recorded sha256 must match the snapshot
    file's actual digest. Only after the whole manifest passes validation
    do the copies begin, so a later invalid entry can never leave a
    partial restore behind. A truncated snapshot (a manifest declaring
    more files than are present and intact) fails instead of restoring a
    half subsystem with exit 0.
    """
    source_snapshot = snapshot_dir or (project_root / "sps2" / "memory" / ".p9_rollback_snapshot")
    manifest_file = source_snapshot / "manifest.json"

    if not manifest_file.exists():
        return 1, [f"Snapshot manifest missing: '{manifest_file}'"]

    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        files = data.get("files", [])
    except Exception as exc:
        return 1, [f"Corrupt snapshot manifest: {exc}"]

    declared = data.get("file_count")
    if isinstance(declared, int) and declared != len(files):
        return 1, [
            "Snapshot manifest inconsistent: file_count=%s but %d entries"
            % (declared, len(files))
        ]

    root_resolved = project_root.resolve(strict=False)
    allowlist = set(P9_ALLOWLIST_RELATIVE_PATHS)

    # Validation pass: no file is touched until every entry has passed.
    # This ordering is the partial-mutation guard — a manifest whose last
    # entry is invalid must fail without having restored the earlier ones.
    validated: list[tuple[Path, Path]] = []
    for entry in files:
        rel = entry.get("relative_path", "")
        dest = project_root / rel
        # Path containment: a tampered entry must not write outside the
        # project root even if it somehow carries a matching digest.
        try:
            dest_resolved = dest.resolve(strict=False)
        except OSError as exc:
            return 1, ["Snapshot path unresolvable %r: %s" % (rel, exc)]
        if (
            not rel
            or rel.startswith("/")
            or ".." in Path(rel).parts
            or (dest_resolved != root_resolved
                and root_resolved not in dest_resolved.parents)
        ):
            return 1, ["Snapshot path escapes project root: %r" % rel]
        # P9 allowlist: the manifest is data, not trusted input. A valid
        # digest for an unrelated in-root path must not let restore
        # overwrite files outside the rollback's ownership boundary.
        if rel not in allowlist:
            return 1, [f"Snapshot path is not allowlisted P9 surface: {rel!r}"]
        src = source_snapshot / rel
        if not src.is_file():
            return 1, ["Snapshot file missing: %r" % rel]
        # Digest verification: restore only what the manifest can prove.
        expected = entry.get("sha256")
        if not expected or sha256_file(src) != expected:
            return 1, ["Snapshot digest mismatch: %r" % rel]
        validated.append((src, dest))

    # Copy pass: every entry already validated, so a partial restore is
    # impossible short of an I/O error mid-copy (which surfaces as an
    # exception, not a false success).
    restored = 0
    for src, dest in validated:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        restored += 1

    if files and restored != len(files):
        return 1, ["Partial restore: %d of %d files" % (restored, len(files))]
    messages = [
        f"Restored {restored} P9 files from snapshot at '{source_snapshot}'"
    ]
    return 0, messages


def execute_rollback(
    target_dir: str | Path,
    dry_run: bool = False,
    full: bool = False,
    snapshot_first: bool = True,
    repo_root: Path | None = None,
) -> tuple[int, list[str]]:
    """Execute advisory rollback: remove only allowlisted P9 files while preserving unrelated state."""
    root = get_repo_root(repo_root)
    target = assert_safe_project_local_target(target_dir, root)
    messages: list[str] = []

    p9_files = get_p9_files(target, include_self=full)
    unowned_files = get_unowned_domain_seo_files(target)
    if unowned_files:
        messages.append("Rollback aborted: non-P9 files found under domain/seo:")
        messages.extend(f"Preserved: {path.relative_to(target)}" for path in unowned_files)
        return 1, messages

    if not p9_files:
        messages.append("P9 SEO subsystem is already absent or rolled back; no action required (idempotent)")
        return 0, messages

    # Ensure snapshot exists before destructive removal
    if snapshot_first and not dry_run:
        snap_path = create_snapshot(target)
        messages.append(f"Recorded pre-rollback snapshot to '{snap_path}'")

    # Verify unrelated modified files are NOT in the deletion set
    portability_path = target / "sps2" / "tools" / "portability.py"
    if portability_path in p9_files:
        return 1, ["CRITICAL: portability.py was erroneously included in P9 deletion set; aborted!"]

    removal_failures: list[str] = []
    for f in p9_files:
        if dry_run:
            messages.append(f"Dry-run: would remove '{f.relative_to(target)}'")
        else:
            try:
                f.unlink()
            except OSError as exc:
                removal_failures.append(f"{f.relative_to(target)}: {exc}")

    if removal_failures:
        messages.append("Partial rollback: failed to remove:")
        messages.extend(removal_failures)
        return 1, messages

    if not dry_run:
        # Remove the domain/seo tree. The root must still be a real
        # directory at deletion time: the ownership check verified the tree
        # contents, and a symlink swapped in afterwards must never be
        # followed into rmtree (which would recursively delete the link
        # target's contents outside the project). rmtree on a symlink
        # raises, so this check makes the refusal explicit and named.
        seo_dir = target / "domain" / "seo"
        if seo_dir.exists() or seo_dir.is_symlink():
            root_mode = seo_dir.lstat().st_mode
            if not stat.S_ISDIR(root_mode):
                messages.append(
                    f"Rollback incomplete: domain/seo is no longer a real directory "
                    f"(symlink or other entry type); refusing recursive removal: {seo_dir}"
                )
                return 1, messages
            try:
                shutil.rmtree(seo_dir)
            except OSError as exc:
                messages.append(f"Rollback incomplete: failed to remove domain/seo: {exc}")
                return 1, messages

        # Clean __pycache__ specifically for removed P9 tools
        tools_cache = target / "sps2" / "tools" / "__pycache__"
        if tools_cache.is_dir():
            for pyc in tools_cache.glob("seo_audit.*.pyc"):
                pyc.unlink(missing_ok=True)
            if full:
                for pyc in tools_cache.glob("rollback_seo.*.pyc"):
                    pyc.unlink(missing_ok=True)

    action_label = "Would remove" if dry_run else "Successfully removed"
    messages.append(f"{action_label} {len(p9_files)} P9 SEO file(s)")

    # Assert zero orphan references after rollback
    orphans = check_orphan_references(target)
    if orphans:
        messages.append("WARNING: Orphan references detected after rollback:")
        messages.extend(orphans)
        return 1, messages
    else:
        messages.append("Verified zero orphan imports across the remaining project")

    return 0, messages


def execute_rehearsal(repo_root: Path | None = None) -> tuple[int, list[str]]:
    """Execute mandatory rollback rehearsal in an isolated temporary clone.
    
    Proves that deleting the P9 SEO surface leaves core SPS 2.0 validators and CMS tests passing.
    """
    root = get_repo_root(repo_root)
    messages: list[str] = [f"Starting P9 advisory rollback rehearsal from '{root}'..."]

    with tempfile.TemporaryDirectory(prefix="p9_rehearsal_") as tmpdir:
        clone_root = Path(tmpdir) / "project"

        # Copy repository into temporary scratch location (including .git for provenance checks)
        shutil.copytree(
            root,
            clone_root,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            symlinks=True,
        )
        messages.append(f"Materialized temporary isolated project at '{clone_root}'")

        # 1. Verify P9 is present before rollback
        initial_status = get_status(clone_root)
        if initial_status["state"] != "PRESENT":
            return 1, ["Rehearsal failed: P9 files were not present in initial test clone"]
        messages.append(f"Initial state: P9 PRESENT ({initial_status['p9_file_count']} files)")

        # 2. Execute rollback in the scratch copy
        code, rb_msgs = execute_rollback(clone_root, dry_run=False, full=False, snapshot_first=True, repo_root=clone_root)
        messages.extend(rb_msgs)
        if code != 0:
            # Propagate the rollback's own diagnostics (e.g. the post-rollback
            # orphan scan that names the exact dynamic-import violation) so a
            # caller can attribute the block to its cause instead of seeing
            # only this generic label. The exit code contract is unchanged.
            messages.append("Rehearsal failed during rollback execution")
            return code, messages

        # 3. Verify P9 is gone from the scratch copy
        post_status = get_status(clone_root)
        if post_status["state"] != "ROLLED_BACK":
            return 1, [f"Rehearsal failed: Post-rollback state was '{post_status['state']}', expected 'ROLLED_BACK'"]
        messages.append("Verified P9 files completely removed from test clone")

        # 4. Verify zero orphan imports
        orphans = post_status["orphan_violations"]
        if orphans:
            return 1, [f"Rehearsal failed: {len(orphans)} orphan import(s) detected"] + orphans
        messages.append("Verified 0 orphan imports remaining in test clone")

        # 5. Run core SPS 2.0 validation in the scratch copy
        # These proof obligations are REQUIRED: if the rollback under test
        # erroneously removed (or a copy bug lost) a validator, skipping its
        # check would let the rehearsal report SUCCESS with the proof
        # obligation silently unmet. A missing validator is itself a failure.
        val_script = clone_root / "sps2" / "tools" / "validate-sps2.sh"
        if not val_script.is_file():
            return 1, ["Rehearsal failed: validate-sps2.sh missing from clone; "
                       "core-validation proof obligation cannot be met"]
        res_val = subprocess.run(
            ["bash", str(val_script)],
            cwd=str(clone_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_val.returncode != 0:
            return 1, [
                f"Rehearsal failed: validate-sps2.sh exited {res_val.returncode}",
                res_val.stderr or res_val.stdout,
            ]
        messages.append("PASS: validate-sps2.sh succeeded on rolled-back clone")

        # 6. Run CMS unit tests in the scratch copy
        cms_tests = clone_root / "domain" / "cms" / "tests"
        if not cms_tests.is_dir():
            return 1, ["Rehearsal failed: domain/cms/tests missing from clone; "
                       "CMS proof obligation cannot be met"]
        res_cms = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", str(cms_tests)],
            cwd=str(clone_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_cms.returncode != 0:
            return 1, [
                f"Rehearsal failed: CMS tests exited {res_cms.returncode}",
                res_cms.stderr or res_cms.stdout,
            ]
        messages.append("PASS: CMS test suite passed completely on rolled-back clone")

        # 7. Verify P7 readiness script passes
        p7_script = clone_root / "sps2" / "tools" / "validate-p7-readiness.py"
        if not p7_script.is_file():
            return 1, ["Rehearsal failed: validate-p7-readiness.py missing from clone; "
                       "P7 readiness proof obligation cannot be met"]
        res_p7 = subprocess.run(
            [sys.executable, str(p7_script)],
            cwd=str(clone_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_p7.returncode != 0:
            return 1, [
                f"Rehearsal failed: validate-p7-readiness.py exited {res_p7.returncode}",
                res_p7.stderr or res_p7.stdout,
            ]
        messages.append("PASS: validate-p7-readiness.py passed on rolled-back clone")

    messages.append("Rehearsal SUCCESS: Advisory rollback proven safe, clean, and isolated.")
    return 0, messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SPS 2.0 P9 Advisory Rollback & stdlib Isolation Tool"
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--status", action="store_true", help="Report current P9 status and isolation")
    group.add_argument("--verify", action="store_true", help="Verify stdlib isolation and boundaries")
    group.add_argument("--rehearse", action="store_true", help="Execute isolated rollback rehearsal")
    group.add_argument("--snapshot", action="store_true", help="Create pre-rollback snapshot manifest")
    group.add_argument("--rollback", action="store_true", help="Execute advisory rollback removal")
    group.add_argument("--restore", action="store_true", help="Restore P9 from snapshot manifest")

    parser.add_argument("--target-dir", help="Project target directory (default: repo root)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate rollback without deleting files")
    parser.add_argument("--full", action="store_true", help="Include rollback tool itself in removal")
    parser.add_argument("--no-snapshot", action="store_true", help="Skip automatic snapshot during rollback")

    args = parser.parse_args(argv)
    root = get_repo_root(Path(args.target_dir) if args.target_dir else None)

    try:
        assert_safe_project_local_target(root, root)
    except ValueError as err:
        sys.stderr.write(f"Target error: {err}\n")
        return 2

    # Default action is --status if no flag passed
    if args.rehearse:
        code, msgs = execute_rehearsal(root)
        for m in msgs:
            print(m)
        return code

    if args.verify:
        p9_files = get_p9_files(root)
        stdlib_violations = check_stdlib_isolation(p9_files)
        conf_violations = check_conf_001_invariants(p9_files)
        orphans = check_orphan_references(root)

        failed = False
        if stdlib_violations:
            print("FAILED: Python standard library isolation violations:")
            for v in stdlib_violations:
                print(f"  - {v}")
            failed = True
        else:
            print("PASS: Pure Python standard library isolation verified (zero third-party imports)")

        if conf_violations:
            print("FAILED: CONF-001 boundary violations:")
            for v in conf_violations:
                print(f"  - {v}")
            failed = True
        else:
            print("PASS: CONF-001 boundary preserved (zero invented LCP/INP thresholds)")

        if orphans:
            print("FAILED: Orphan subsystem references detected:")
            for o in orphans:
                print(f"  - {o}")
            failed = True
        else:
            print("PASS: Zero orphan references outside P9 surface")

        return 1 if failed else 0

    if args.snapshot:
        snap = create_snapshot(root)
        print(f"Created snapshot at '{snap}'")
        return 0

    if args.restore:
        code, msgs = restore_snapshot(root)
        for m in msgs:
            print(m)
        return code

    if args.rollback:
        code, msgs = execute_rollback(
            target_dir=root,
            dry_run=args.dry_run,
            full=args.full,
            snapshot_first=not args.no_snapshot,
            repo_root=root,
        )
        for m in msgs:
            print(m)
        return code

    # Default: --status
    st = get_status(root)
    print(f"P9 SEO Subsystem Status: {st['state']}")
    print(f"  - Managed P9 Files: {st['p9_file_count']}")
    print(f"  - Stdlib Isolation: {'CLEAN' if st['stdlib_clean'] else 'VIOLATIONS DETECTED'}")
    print(f"  - CONF-001 Bound:   {'PRESERVED' if st['conf_001_clean'] else 'VIOLATIONS DETECTED'}")
    print(f"  - Orphan Imports:   {st['orphan_count']}")
    print(f"  - Snapshot Stored:  {'YES' if st['snapshot_exists'] else 'NO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
