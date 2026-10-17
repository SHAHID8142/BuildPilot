#!/usr/bin/env python3
"""Shared, fail-closed P10/P9 import-exception scanner for DEC-7302."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

MANIFEST_RELATIVE_PATH = "framework/sps2/governance/p10-p9-import-exception-manifest.json"
EXPECTED_SCHEMA = "sps2.p10-p9-import-exception-manifest/v1"
EXPECTED_DECISION_ID = "DEC-7302"
EXPECTED_MANIFEST_SHA256 = "ba0ce08bbad63224595b1bd1a1acedde66b30062be6680d25a5359bd745df819"
TOP_LEVEL_FIELDS = {
    "schema",
    "decision_id",
    "baseline_commit",
    "exception_count",
    "exceptions",
    "forbidden_import_forms",
}
EXCEPTION_FIELDS = {"file", "module", "symbols", "authorization"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
EXCLUDED_PATHS = (
    "framework/domain/seo",
    "framework/sps2/tools/seo_audit.py",
    "framework/sps2/tools/rollback_seo.py",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _safe_path(root: Path, value: str, label: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError(f"{label}: path is not a non-empty string")
    if Path(value).is_absolute() or "\\" in value:
        raise ValueError(f"{label}: path is not repository-relative POSIX")
    lexical = Path(value)
    if any(part in ("..", "") for part in lexical.parts):
        raise ValueError(f"{label}: path contains traversal or an empty component")
    resolved = root / lexical
    root_resolved = root.resolve(strict=False)
    real = Path(os.path.realpath(resolved))
    if root_resolved != real and root_resolved not in real.parents:
        raise ValueError(f"{label}: path escapes repository root")
    return resolved


def load_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / MANIFEST_RELATIVE_PATH
    _safe_path(root, MANIFEST_RELATIVE_PATH, "manifest")
    try:
        mode = manifest_path.lstat().st_mode
    except OSError as exc:
        raise ValueError(f"manifest missing or unreadable: {exc}") from exc
    if not stat.S_ISREG(mode):
        raise ValueError("manifest is not a regular file")
    raw = manifest_path.read_bytes()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"manifest is malformed: {exc}") from exc
    if hashlib.sha256(canonical_json(parsed)).hexdigest() != EXPECTED_MANIFEST_SHA256:
        raise ValueError("manifest SHA-256 does not match DEC-7302")
    manifest = parsed
    if not isinstance(manifest, dict) or set(manifest) != TOP_LEVEL_FIELDS:
        raise ValueError("manifest fields do not exactly match DEC-7302")
    if manifest["schema"] != EXPECTED_SCHEMA or manifest["decision_id"] != EXPECTED_DECISION_ID:
        raise ValueError("manifest identity mismatch")
    if manifest["exception_count"] != 4 or not isinstance(manifest["exceptions"], list) or len(manifest["exceptions"]) != 4:
        raise ValueError("manifest must contain exactly four exception records")
    baseline = manifest["baseline_commit"]
    if not isinstance(baseline, str) or len(baseline) != 40:
        raise ValueError("manifest baseline_commit is malformed")
    if not isinstance(manifest["forbidden_import_forms"], list) or not manifest["forbidden_import_forms"]:
        raise ValueError("manifest forbidden_import_forms is malformed")

    seen: set[tuple[str, str]] = set()
    for record in manifest["exceptions"]:
        if not isinstance(record, dict) or set(record) != EXCEPTION_FIELDS:
            raise ValueError("exception record fields do not exactly match DEC-7302")
        _safe_path(root, record["file"], "exception file")
        module = record["module"]
        symbols = record["symbols"]
        if not isinstance(module, str) or not module.startswith("framework.domain.seo."):
            raise ValueError("exception module is outside the P9 SEO engine")
        if not isinstance(symbols, list) or not symbols or any(not isinstance(symbol, str) or not symbol for symbol in symbols):
            raise ValueError("exception symbols are malformed")
        if (record["file"], module) in seen:
            raise ValueError("duplicate manifest file/module record")
        seen.add((record["file"], module))
        if record["authorization"] != EXPECTED_DECISION_ID:
            raise ValueError("exception authorization mismatch")
    return manifest


def _is_dynamic_loader_expression(node: ast.AST, dynamic_names: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in {"__import__", "import_module"} or node.id in dynamic_names
    if isinstance(node, ast.Attribute):
        return node.attr == "import_module"
    if isinstance(node, ast.Call):
        function = node.func
        return (
            isinstance(function, ast.Name)
            and function.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "import_module"
        )
    if isinstance(node, ast.Subscript):
        return (
            isinstance(node.slice, ast.Constant)
            and node.slice.value == "import_module"
        )
    return False


def _dynamic_loader_names(tree: ast.AST) -> set[str]:
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    dynamic_names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in assignments:
            if not _is_dynamic_loader_expression(node.value, dynamic_names):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id not in dynamic_names:
                    dynamic_names.add(target.id)
                    changed = True
    return dynamic_names


def _is_dynamic_import(node: ast.AST, dynamic_names: set[str] | None = None) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return _is_dynamic_loader_expression(
        node.func, dynamic_names if dynamic_names is not None else set()
    )


def _contains_domain_seo_string(node: ast.AST) -> bool:
    # Fail closed: a literal fragment of the forbidden namespace, or ANY
    # string concatenation inside the call (a computed module name such as
    # "domain" + ".seo.model" never holds the full literal in one constant),
    # both count. Benign dynamic imports of unrelated modules pass a plain
    # literal and no BinOp, so the false-positive surface stays narrow.
    for child in ast.walk(node):
        if isinstance(child, ast.BinOp):
            return True
        if (
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and re.search(r"(?:^|\.)domain\.seo(?:\.|$)", child.value)
        ):
            return True
    return False


def scan_import_exceptions(project_root: str | Path) -> dict[str, Any]:
    """Scan all non-excluded Python files and classify approved/orphan imports."""
    root = Path(project_root).resolve()
    try:
        manifest = load_manifest(root)
    except (OSError, ValueError) as exc:
        return {"ok": False, "approved": [], "violations": [f"import manifest: {exc}"]}

    allowed: dict[tuple[str, str], set[str]] = {}
    for record in manifest["exceptions"]:
        allowed.setdefault((record["file"], record["module"]), set()).update(record["symbols"])

    approved: list[dict[str, Any]] = []
    violations: list[str] = []
    excluded = {root / item for item in EXCLUDED_PATHS}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(item for item in dirs if item not in SKIP_DIRS)
        for filename in sorted(files):
            if not filename.endswith(".py"):
                continue
            path = Path(base) / filename
            relative = path.relative_to(root).as_posix()
            if any(path == item or item in path.parents for item in excluded):
                continue
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                violations.append(f"{relative}: lstat failed: {exc}")
                continue
            if not stat.S_ISREG(mode):
                violations.append(f"{relative}: not a regular file")
                continue
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(path))
            except (SyntaxError, OSError, ValueError, RecursionError) as exc:
                violations.append(f"{relative}: Python parse failed closed: {exc}")
                continue

            dynamic_names = _dynamic_loader_names(tree)
            symbol_counts: dict[str, int] = {}
            for node in ast.walk(tree):
                if _is_dynamic_import(node, dynamic_names):
                    if _contains_domain_seo_string(node):
                        violations.append(
                            f"{relative}:{node.lineno}: dynamic domain.seo import is forbidden"
                        )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "domain.seo" or alias.name.startswith("framework.domain.seo."):
                            violations.append(
                                f"{relative}:{node.lineno}: module import '{alias.name}' is forbidden"
                            )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module
                    if node.level:
                        # A relative import (`from ..seo.metadata import x`)
                        # carries no absolute module name, but it resolves to
                        # one against the importing file's package. Skipping
                        # it would let forbidden symbols bypass every
                        # allowlist check, so resolve it and run the same
                        # checks; an unresolvable or escaping relative import
                        # fails closed as a violation.
                        #
                        # Python semantics: level=1 is the CURRENT package.
                        # For a plain module file, the package is its
                        # directory chain (base_parts); for a package's
                        # __init__.py, the package is that same chain — so
                        # `climb = level - 1` components are dropped from
                        # base_parts in both cases.
                        base_parts = [
                            p for p in relative.split("/")[:-1] if p != "__init__.py"
                        ]
                        climb = node.level - 1
                        if climb > len(base_parts):
                            violations.append(
                                f"{relative}:{node.lineno}: relative import escapes project root"
                            )
                            continue
                        if climb:
                            base_parts = base_parts[: len(base_parts) - climb]
                        resolved = ".".join(base_parts)
                        module = f"{resolved}.{node.module}" if resolved else node.module
                    if module != "domain.seo" and not module.startswith("framework.domain.seo."):
                        continue
                    for alias in node.names:
                        if alias.name == "*":
                            violations.append(f"{relative}:{node.lineno}: star import is forbidden")
                            continue
                        symbol_counts[(module, alias.name)] = symbol_counts.get((module, alias.name), 0) + 1
                        permitted = allowed.get((relative, module), set())
                        if alias.name not in permitted:
                            violations.append(
                                f"{relative}:{node.lineno}: unapproved import {module}.{alias.name}"
                            )
                        else:
                            approved.append(
                                {
                                    "file": relative,
                                    "module": module,
                                    "symbol": alias.name,
                                    "local_alias": alias.asname or alias.name,
                                }
                            )
            for (module, symbol), count in symbol_counts.items():
                if count > 1:
                    violations.append(
                        f"{relative}: duplicate source symbol {module}.{symbol}"
                    )

    expected_pairs = set(allowed)
    observed_pairs = {(item["file"], item["module"]) for item in approved}
    for file_value, module in sorted(expected_pairs - observed_pairs):
        violations.append(f"{file_value}: approved dependency missing: {module}")
    return {
        "ok": not violations,
        "approved": approved,
        "violations": sorted(violations),
    }
