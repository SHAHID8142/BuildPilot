#!/usr/bin/env python3
"""Fail-closed, content-pinned legacy exception checker for DEC-7301."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

MANIFEST_RELATIVE_PATH = "framework/sps2/governance/legacy-exception-manifest.json"
EXPECTED_SCHEMA = "sps2.legacy-exception-manifest/v1"
EXPECTED_DECISION_ID = "DEC-7301"
# Updated 2026-10-17 under the User-approved BuildPilot restructure (paths+hashes of
# moved legacy files; DEC-7301 authorization itself unchanged). Amended same day by
# DEC-7305: 22 exceptions, then 23 (skill-search.sh + its scripts/ mirror). Re-pinned
# 2026-10-18 (tests/CI audit fix, T-20): expected-test-modules.txt regenerated
# (53 modules), sps-ci.yml gains validator-battery + permissions/concurrency +
# MIN_TESTS 1210, smoke-sps.sh (+ mirror) gains shell-tool smoke coverage. Re-pinned again
# 2026-10-18 (shell-scripts audit fixes): installer arg-loop/symlink/color fixes in
# install.sh, uninstall.sh, get-sps.sh, sps-status.sh, sps-doctor.sh, sps-update.sh,
# sps-hygiene.sh, bootstrap-sps.sh (+ mirrors).
# Dual anchor (audit fix 2026-10-18): the same canonical SHA-256 is pinned in
# .github/workflows/sps-ci.yml (validator-battery job) and cross-checked by
# framework/sps2/tests/test_manifest_anchor.py. A coordinated tamper must now
# edit the manifest, this constant, AND the workflow before anything passes.
# Accepted residual: repo write still reaches all three; final detection is
# git history + PR review.
EXPECTED_MANIFEST_SHA256 = "c32e9e53ba7f40f12e7110d40d4da56cc4cb79a9b25816f201500b01a4d21e2b"
EXPECTED_EXCEPTION_COUNT = 59  # DEC-7301 as amended by DEC-7305 (lesson channel, status dashboard, ecosystem scan, law-log ledger, hygiene checker: scripts+mirrors+tsv+workflow; +2 sps-cms updater scripts, consent+scan batch 2026-10-18)
EXPECTED_AUTHORIZATIONS = {"DEC-7201", "DEC-7305"}  # ratified authorizing decisions
TOP_LEVEL_FIELDS = {
    "schema",
    "decision_id",
    "baseline_commit",
    "exception_count",
    "exceptions",
    "related_test_artifacts",
    "explicitly_excluded_paths",
}
EXCEPTION_FIELDS = {
    "path",
    "expected_blob",
    "expected_mode",
    "sha256",
    "authorization",
    "reason",
}
TEST_ARTIFACT_FIELDS = {"path", "sha256", "authorization", "reason"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(root: Path, value: str, label: str) -> Path:
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
    _relative_path(root, MANIFEST_RELATIVE_PATH, "manifest")
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
    if sha256_bytes(canonical_json(parsed)) != EXPECTED_MANIFEST_SHA256:
        raise ValueError("manifest SHA-256 does not match DEC-7301")
    manifest = parsed
    if not isinstance(manifest, dict) or set(manifest) != TOP_LEVEL_FIELDS:
        raise ValueError("manifest fields do not exactly match DEC-7301")
    if manifest["schema"] != EXPECTED_SCHEMA:
        raise ValueError("manifest schema mismatch")
    if manifest["decision_id"] != EXPECTED_DECISION_ID:
        raise ValueError("manifest decision_id mismatch")
    if not isinstance(manifest["baseline_commit"], str) or len(manifest["baseline_commit"]) != 40:
        raise ValueError("manifest baseline_commit is not a 40-character object ID")
    if manifest["exception_count"] != EXPECTED_EXCEPTION_COUNT:
        raise ValueError("manifest exception_count does not match DEC-7301 as amended")
    if not isinstance(manifest["exceptions"], list) or len(manifest["exceptions"]) != EXPECTED_EXCEPTION_COUNT:
        raise ValueError("manifest exceptions count does not match DEC-7301 as amended")
    if not isinstance(manifest["related_test_artifacts"], list) or len(manifest["related_test_artifacts"]) != 1:
        raise ValueError("manifest must contain exactly one test artifact")
    if not isinstance(manifest["explicitly_excluded_paths"], list) or len(manifest["explicitly_excluded_paths"]) != 4:
        raise ValueError("manifest must explicitly exclude exactly four check-update paths")

    seen: set[str] = set()
    for record in manifest["exceptions"]:
        if not isinstance(record, dict) or set(record) != EXCEPTION_FIELDS:
            raise ValueError("exception record fields do not exactly match DEC-7301")
        path_value = record["path"]
        _relative_path(root, path_value, "exception path")
        if path_value in seen:
            raise ValueError(f"duplicate exception path: {path_value}")
        seen.add(path_value)
        if record["authorization"] not in EXPECTED_AUTHORIZATIONS:
            raise ValueError(f"exception authorization mismatch: {path_value}")
        if not isinstance(record["reason"], str) or not record["reason"].strip():
            raise ValueError(f"exception reason is empty: {path_value}")
        if not isinstance(record["expected_blob"], str) or len(record["expected_blob"]) != 40:
            raise ValueError(f"exception blob is malformed: {path_value}")
        if record["expected_mode"] not in ("100644", "100755"):
            raise ValueError(f"exception mode is invalid: {path_value}")
        if not isinstance(record["sha256"], str) or len(record["sha256"]) != 64:
            raise ValueError(f"exception SHA-256 is malformed: {path_value}")

    artifact = manifest["related_test_artifacts"][0]
    if not isinstance(artifact, dict) or set(artifact) != TEST_ARTIFACT_FIELDS:
        raise ValueError("test artifact fields do not exactly match DEC-7301")
    _relative_path(root, artifact["path"], "test artifact path")
    if artifact["authorization"] != "DEC-7201":
        raise ValueError("test artifact authorization mismatch")
    if not isinstance(artifact["sha256"], str) or len(artifact["sha256"]) != 64:
        raise ValueError("test artifact SHA-256 is malformed")

    excluded = manifest["explicitly_excluded_paths"]
    if len(set(excluded)) != 4 or any(not isinstance(item, str) for item in excluded):
        raise ValueError("explicitly excluded paths are malformed")
    for path_value in excluded:
        _relative_path(root, path_value, "excluded path")
    return manifest


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise ValueError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _git_optional(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _worktree_mode(path: Path) -> str:
    mode = path.lstat().st_mode
    return "100755" if mode & stat.S_IXUSR else "100644"


def verify_legacy_exceptions(root: Path) -> list[str]:
    """Verify the pinned exception paths; return deterministic violation strings."""
    try:
        manifest = load_manifest(root)
    except (OSError, ValueError) as exc:
        return [f"legacy manifest: {exc}"]

    violations: list[str] = []
    baseline = manifest["baseline_commit"]
    for record in manifest["exceptions"]:
        path_value = record["path"]
        path = _relative_path(root, path_value, "exception path")
        try:
            mode = path.lstat().st_mode
        except OSError:
            violations.append(f"{path_value}: missing or unreadable worktree file")
            continue
        if not stat.S_ISREG(mode):
            violations.append(f"{path_value}: worktree path is not a regular file")
            continue

        try:
            tracked = _git_optional(root, "ls-files", "--error-unmatch", "--", path_value)
            if tracked is None:
                violations.append(f"{path_value}: path is not tracked")
                continue
            worktree_blob = _git(root, "hash-object", "--path", path_value, "--", path_value).strip()
            stage_blob = _git_optional(root, "rev-parse", f":{path_value}")
            baseline_blob = _git_optional(root, "rev-parse", f"{baseline}:{path_value}")
            if worktree_blob != record["expected_blob"]:
                violations.append(f"{path_value}: worktree blob mismatch")
            if sha256_file(path) != record["sha256"]:
                violations.append(f"{path_value}: worktree SHA-256 mismatch")
            if _worktree_mode(path) != record["expected_mode"]:
                violations.append(f"{path_value}: worktree mode mismatch")
            if stage_blob is None:
                violations.append(f"{path_value}: missing stage-0 entry")
            elif stage_blob not in {baseline_blob, record["expected_blob"]}:
                violations.append(f"{path_value}: stage-0 blob is neither baseline nor expected")
            if baseline_blob is None and stage_blob is not None:
                # Absent at baseline is only legitimate for a file the
                # manifest ADDS (stage-0 carries its expected content); for
                # any file that existed at baseline this is a deletion.
                if stage_blob != record["expected_blob"]:
                    violations.append(f"{path_value}: missing authority-baseline blob")
        except (OSError, ValueError) as exc:
            violations.append(f"{path_value}: git integrity check failed: {exc}")

    try:
        status_output = _git(
            root,
            "diff",
            "--name-status",
            baseline,
            "--",
            *[record["path"] for record in manifest["exceptions"]],
        )
        for line in status_output.splitlines():
            fields = line.split("\t", 1)
            status = fields[0] if fields else ""
            # "M" = modified legacy file (the manifest's original semantics).
            # "A" = a file the manifest explicitly ADDS as a pinned exception
            # (absent at baseline). Both are authorized; anything else
            # (D = deleted, R/T = rename/typechange, C = copy) is a violation.
            if status not in ("M", "A"):
                violations.append(f"legacy exception status is not a modification: {line}")
    except ValueError as exc:
        violations.append(f"legacy exception status check failed: {exc}")
    return sorted(violations)


def verify_legacy_repository(
    root: Path,
    baseline: str,
    pathspec: list[str],
    exclude_prefixes: list[str] | None = None,
) -> list[str]:
    """Return all changed or untracked legacy paths not covered by DEC-7301."""
    exclude_prefixes = exclude_prefixes or []
    violations = verify_legacy_exceptions(root)
    exempt: set[str] = set()
    if violations == []:
        # The manifest passed every integrity check, so its exception list is
        # authoritative for the diff exemption. If manifest integrity FAILED,
        # the failure is already recorded in `violations` (fail-closed): the
        # diff exemption is withheld and every changed path is reported.
        try:
            manifest_exceptions = load_manifest(root)["exceptions"]
        except ValueError:
            manifest_exceptions = []
        exempt = set(record["path"] for record in manifest_exceptions)
    try:
        diff = _git(root, "diff", "--name-only", baseline, "--", *pathspec)
    except ValueError as exc:
        return [f"legacy repository diff failed: {exc}"]
    for path_value in diff.splitlines():
        normalized = Path(path_value).as_posix()
        if any(normalized == prefix or normalized.startswith(prefix) for prefix in exclude_prefixes):
            continue
        if normalized not in exempt:
            violations.append(f"legacy modified: {normalized}")
    try:
        untracked = _git(root, "ls-files", "--others", "--exclude-standard", "--", *pathspec)
    except ValueError as exc:
        violations.append(f"legacy untracked check failed: {exc}")
    else:
        for path_value in untracked.splitlines():
            normalized = Path(path_value).as_posix()
            if any(normalized == prefix or normalized.startswith(prefix) for prefix in exclude_prefixes):
                continue
            if normalized not in exempt:
                violations.append(f"legacy untracked: {normalized}")
    return sorted(violations)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--pathspec", action="append", default=[])
    parser.add_argument("--exclude-prefix", action="append", default=[])
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.pathspec:
        violations = verify_legacy_repository(
            root, args.baseline, args.pathspec, args.exclude_prefix
        )
    else:
        violations = verify_legacy_exceptions(root)
    for violation in violations:
        print(violation, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
