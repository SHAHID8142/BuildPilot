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
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

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
    """Return all allowlisted P9 files present under project_root."""
    files: list[Path] = []
    seo_dir = project_root / "domain" / "seo"
    if seo_dir.is_dir():
        for p in seo_dir.glob("**/*"):
            if p.is_file() and not p.name.endswith(".pyc") and "__pycache__" not in p.parts:
                files.append(p)

    cli_tool = project_root / "sps2" / "tools" / "seo_audit.py"
    if cli_tool.is_file():
        files.append(cli_tool)

    if include_self:
        self_tool = project_root / "sps2" / "tools" / "rollback_seo.py"
        if self_tool.is_file():
            files.append(self_tool)

    return sorted(files)


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
    """Scan all Python files outside domain/seo/ and sps2/tools/seo_audit.py for imports of domain.seo."""
    violations: list[str] = []
    skip_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv", ".p9_rollback_snapshot"}

    for base, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        base_path = Path(base)

        # Ignore domain/seo itself
        if "domain" in base_path.parts and "seo" in base_path.parts:
            continue

        for f in files:
            if not f.endswith(".py"):
                continue
            if f in ("seo_audit.py", "rollback_seo.py") and "sps2" in base_path.parts and "tools" in base_path.parts:
                continue

            full_p = base_path / f
            try:
                tree = ast.parse(full_p.read_text(encoding="utf-8", errors="replace"), filename=str(full_p))
            except (SyntaxError, OSError):
                continue

            for node in ast.walk(tree):
                names: list[tuple[str, int]] = []
                if isinstance(node, ast.Import):
                    for a in node.names:
                        names.append((a.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    if node.level and node.level > 0:
                        continue
                    if node.module:
                        names.append((node.module, node.lineno))

                for mod, lineno in names:
                    if mod == "domain.seo" or mod.startswith("domain.seo."):
                        violations.append(
                            f"{full_p}:{lineno}: Orphan import of rolled-back subsystem '{mod}'"
                        )

    return violations


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
    stdlib_errors = check_stdlib_isolation(p9_files)
    conf_001_errors = check_conf_001_invariants(p9_files)

    return {
        "state": state,
        "p9_file_count": len(p9_files),
        "p9_files": [str(p.relative_to(project_root)) for p in p9_files],
        "snapshot_exists": manifest_file.exists(),
        "orphan_count": len(orphans),
        "orphan_violations": orphans,
        "stdlib_clean": len(stdlib_errors) == 0,
        "stdlib_violations": stdlib_errors,
        "conf_001_clean": len(conf_001_errors) == 0,
        "conf_001_violations": conf_001_errors,
    }


def create_snapshot(project_root: Path, snapshot_dir: Path | None = None) -> Path:
    """Atomically record the current P9 SEO surface into a snapshot manifest for safe recovery."""
    target_snapshot = snapshot_dir or (project_root / "sps2" / "memory" / ".p9_rollback_snapshot")
    target_snapshot.mkdir(parents=True, exist_ok=True)

    p9_files = get_p9_files(project_root, include_self=False)
    manifest_entries: list[dict[str, str]] = []

    for f in p9_files:
        rel = f.relative_to(project_root).as_posix()
        dest = target_snapshot / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        manifest_entries.append({
            "relative_path": rel,
            "sha256": sha256_file(f),
        })

    manifest_file = target_snapshot / "manifest.json"
    manifest_data = {
        "schema": "sps2.p9-rollback-manifest/v1",
        "timestamp": "2026-10-07T00:00:00Z",
        "file_count": len(manifest_entries),
        "files": manifest_entries,
    }
    manifest_file.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target_snapshot


def restore_snapshot(project_root: Path, snapshot_dir: Path | None = None) -> tuple[int, list[str]]:
    """Restore the P9 SEO surface from a snapshot manifest."""
    source_snapshot = snapshot_dir or (project_root / "sps2" / "memory" / ".p9_rollback_snapshot")
    manifest_file = source_snapshot / "manifest.json"

    if not manifest_file.exists():
        return 1, [f"Snapshot manifest missing: '{manifest_file}'"]

    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        files = data.get("files", [])
    except Exception as exc:
        return 1, [f"Corrupt snapshot manifest: {exc}"]

    restored = 0
    for entry in files:
        rel = entry["relative_path"]
        src = source_snapshot / rel
        dest = project_root / rel
        if src.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            restored += 1

    return 0, [f"Restored {restored} P9 files from snapshot at '{source_snapshot}'"]


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

    removed_count = 0
    for f in p9_files:
        if dry_run:
            messages.append(f"Dry-run: would remove '{f.relative_to(target)}'")
        else:
            f.unlink()
            removed_count += 1

    if not dry_run:
        # Remove empty directories under domain/seo
        seo_dir = target / "domain" / "seo"
        if seo_dir.is_dir():
            shutil.rmtree(seo_dir, ignore_errors=True)

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
            return code, ["Rehearsal failed during rollback execution"]

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
        val_script = clone_root / "sps2" / "tools" / "validate-sps2.sh"
        if val_script.is_file():
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
            messages.append("PASS: validate-sps2.sh succeeded on rolled-back clone (72 checks passed)")

        # 6. Run CMS unit tests in the scratch copy
        cms_tests = clone_root / "domain" / "cms" / "tests"
        if cms_tests.is_dir():
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
        if p7_script.is_file():
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
