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

MANIFEST_RELATIVE_PATH = "sps2/governance/p10-p9-import-exception-manifest.json"
EXPECTED_SCHEMA = "sps2.p10-p9-import-exception-manifest/v1"
EXPECTED_DECISION_ID = "DEC-7302"
EXPECTED_MANIFEST_SHA256 = "d8dd50395689de0325c29fd55ea959205bee17b9a606b84b236fd3f044f22448"
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
    "domain/seo",
    "sps2/tools/seo_audit.py",
    "sps2/tools/rollback_seo.py",
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
        if not isinstance(module, str) or not module.startswith("domain.seo."):
            raise ValueError("exception module is outside the P9 SEO engine")
        if not isinstance(symbols, list) or not symbols or any(not isinstance(symbol, str) or not symbol for symbol in symbols):
            raise ValueError("exception symbols are malformed")
        if (record["file"], module) in seen:
            raise ValueError("duplicate manifest file/module record")
        seen.add((record["file"], module))
        if record["authorization"] != EXPECTED_DECISION_ID:
            raise ValueError("exception authorization mismatch")
    return manifest


def _is_dynamic_import(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name) and node.func.id == "__import__":
        return True
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "importlib"
    )


def _contains_domain_seo_string(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and re.search(r"(?:^|\.)domain\.seo(?:\.|$)", child.value)
        for child in ast.walk(node)
    )


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

            symbol_counts: dict[str, int] = {}
            for node in ast.walk(tree):
                if _is_dynamic_import(node):
                    if _contains_domain_seo_string(node):
                        violations.append(
                            f"{relative}:{node.lineno}: dynamic domain.seo import is forbidden"
                        )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "domain.seo" or alias.name.startswith("domain.seo."):
                            violations.append(
                                f"{relative}:{node.lineno}: module import '{alias.name}' is forbidden"
                            )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module
                    if node.level:
                        continue
                    if module != "domain.seo" and not module.startswith("domain.seo."):
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
