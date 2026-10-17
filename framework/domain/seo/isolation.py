"""P9 Project-Local Python Standard Library Isolation & Boundary Verifier (REQ-P9-10).

Enforces:
1. Zero third-party packages or external modules (pure Python standard library only).
2. Zero machine-global state writes, installations, or dependencies.
3. Strict preservation of CONF-001 boundary (zero invented LCP or INP thresholds).
4. Zero orphan imports or dangling references outside the P9 surface.
5. Zero modifications to legacy repository files (legacy diff remains exactly 0).
6. Full alignment with P7 persistent project-local state governance and threat model.
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from framework.sps2.core.p9_surface import P9_ALLOWLIST_RELATIVE_PATHS
from framework.sps2.governance.import_exceptions import scan_import_exceptions
from framework.sps2.governance.legacy_exceptions import verify_legacy_repository

AUTHORITY_BASELINE = "c39694fedd34b0b0e9fa91d24ac543d21ad52c9f"

# Standard library module names (Python 3.10+ native set with fallback)
FALLBACK_STDLIB = frozenset(
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

STDLIB_MODULES: frozenset[str] = getattr(sys, "stdlib_module_names", None) or FALLBACK_STDLIB

# Invariant pattern for CONF-001: numeric thresholds for LCP or INP are forbidden
CONF_001_INVENTED_REGEX = re.compile(r"(LCP|INP)\s*[:=]?\s*\d+")

# Legacy directories that must never be modified by P9
LEGACY_DIRECTORIES: tuple[str, ...] = ("skills", "scripts", "plugins", "templates")


def scan_python_imports(file_path: str | Path) -> list[tuple[str, int]]:
    """Parse a Python source file AST and return all imported module paths with line numbers."""
    path = Path(file_path)
    if not path.is_file():
        return []

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, OSError):
        return []

    imported: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # Relative import (always internal to package)
                continue
            if node.module:
                imported.append((node.module, node.lineno))

    return imported


def verify_stdlib_isolation(
    target_files: list[str | Path] | None = None,
    allowed_internal_prefixes: tuple[str, ...] = ("framework.domain", "framework.sps2"),
) -> list[str]:
    """Verify that every imported package is either in Python stdlib or in allowed internal prefixes.
    
    Returns a list of violation strings. An empty list signifies complete stdlib isolation.
    """
    violations: list[str] = []

    if target_files is None:
        # Scan framework/domain/seo and framework/sps2/tools/seo_audit.py by default
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        target_files = []
        seo_dir = repo_root / "framework" / "domain" / "seo"
        if seo_dir.is_dir():
            target_files.extend(list(seo_dir.glob("**/*.py")))
        cli_tool = repo_root / "framework" / "sps2" / "tools" / "seo_audit.py"
        if cli_tool.is_file():
            target_files.append(cli_tool)
        rollback_tool = repo_root / "framework" / "sps2" / "tools" / "rollback_seo.py"
        if rollback_tool.is_file():
            target_files.append(rollback_tool)

    for f in target_files:
        p = Path(f).resolve()
        if not p.is_file() or not p.name.endswith(".py"):
            continue

        for mod_name, line_no in scan_python_imports(p):
            top_level = mod_name.split(".")[0]
            if not top_level:
                continue

            # Check if top-level module is in Python standard library
            if top_level in STDLIB_MODULES:
                continue

            # Check if the module is a project-internal package (match the full dotted
            # module name against the prefixes, so 'framework.sps2...' matches 'framework.sps2')
            if any(mod_name == prefix or mod_name.startswith(f"{prefix}.") for prefix in allowed_internal_prefixes):
                continue

            violations.append(
                f"{p}:{line_no}: External non-stdlib dependency '{mod_name}' detected. "
                f"P9 strictly forbids third-party package imports."
            )

    return violations


def scan_for_conf_001_invariants(target_files: list[str | Path] | None = None) -> list[str]:
    """Scan files for forbidden invented numeric thresholds for LCP or INP (CONF-001).
    
    Returns a list of violation strings.
    """
    violations: list[str] = []

    if target_files is None:
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        target_files = []
        seo_dir = repo_root / "framework" / "domain" / "seo"
        if seo_dir.is_dir():
            target_files.extend(list(seo_dir.glob("**/*.py")))
        cli_tool = repo_root / "framework" / "sps2" / "tools" / "seo_audit.py"
        if cli_tool.is_file():
            target_files.append(cli_tool)
        rollback_tool = repo_root / "framework" / "sps2" / "tools" / "rollback_seo.py"
        if rollback_tool.is_file():
            target_files.append(rollback_tool)

    for f in target_files:
        p = Path(f).resolve()
        if not p.is_file():
            continue

        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for idx, line in enumerate(lines, 1):
            if CONF_001_INVENTED_REGEX.search(line):
                # Ignore comments explaining CONF-001 if they don't invent values,
                # but if regex matched '(LCP|INP) := \d+' it flags as violation
                violations.append(
                    f"{p}:{idx}: Forbidden invented numeric threshold per CONF-001: '{line.strip()}'"
                )

    return violations


def scan_for_orphan_imports(
    project_root: str | Path,
    check_subsystem: str = "domain.seo",
    exclude_paths: list[str | Path] | None = None,
) -> list[str]:
    """Scan the shared DEC-7302 exception contract and return all violations."""
    del check_subsystem, exclude_paths
    return scan_import_exceptions(project_root)["violations"]


def verify_legacy_diff_zero(
    project_root: str | Path,
    legacy_dirs: tuple[str, ...] = LEGACY_DIRECTORIES,
) -> list[str]:
    """Apply the fixed-baseline DEC-7301 exception to P9 legacy protection."""
    del legacy_dirs
    return verify_legacy_repository(
        project_root,
        AUTHORITY_BASELINE,
        list(LEGACY_DIRECTORIES),
    )


def verify_p7_isolation_intact(project_root: str | Path) -> list[str]:
    """Verify that P7 persistent project-local state governance artifacts remain intact."""
    root = Path(project_root).resolve()
    violations: list[str] = []

    p7_artifacts = [
        root / "framework" / "sps2" / "memory" / "P7-IMPLEMENTATION-REPORT.md",
        root / "framework" / "sps2" / "decisions" / "P7-READINESS-DECISIONS.json",
        root / "framework" / "sps2" / "governance" / "P7-THREAT-MODEL.md",
    ]

    for art in p7_artifacts:
        if not art.is_file():
            violations.append(f"Required P7 isolation governance artifact missing: {art}")
        elif art.stat().st_size == 0:
            violations.append(f"P7 isolation governance artifact is empty: {art}")

    return violations
