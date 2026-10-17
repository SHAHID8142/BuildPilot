#!/usr/bin/env python3
"""P17 directory confinement controls (SEC-P17-05).

This boundary is explicitly NOT "complete filesystem confinement". The
controls are classified into three categories that are not interchangeable.

PREVENTIVE (runner-mediated actions only)
  P1 argv-only execution with shell=False.
  P2 pre-execution path containment: every argv element that is or looks
     like a path is resolved with os.path.realpath and must fall inside the
     project boundary, else the command is rejected BEFORE any process is
     spawned. This prevents the runner from passing an escaping path. It does
     not constrain the agent process once spawned.
  P3 minimal explicit environment (see scrub.py / execution.py).
  P4 cwd set to the task workspace: convenience and relative-path default
     only. cwd is NOT a security boundary and is never claimed to be one.

DETECTION AND AUDIT (after the fact, not prevention)
  D1 post-execution boundary-tree audit: file-tree snapshots (paths + mtimes)
     before and after execution; any creation or modification outside the
     task workspace is a CONFINEMENT_VIOLATION.
  D2 transcript capture with SHA-256 digests.

GUARANTEES THAT CANNOT BE PROVIDED (stdlib only, unprivileged POSIX)
  G1 OS-level filesystem confinement of the agent process: no chroot
     (requires privileges), no namespaces, no seccomp in the stdlib.
  G2 prevention of writes outside the workspace by the agent process itself.
  Consequence: real-agent execution stays disabled by default (GATE-P17-4).

Detection is not prevention. When D1 fires the outside write has already
happened; it fails the task and preserves the audit trail, it does not block
the write.

Standard library only.
"""
import os

from . import scrub, state

# Path-like argv elements are identified structurally: anything that starts a
# path, or that contains a separator and is not a bare flag, is treated as a
# path and must resolve inside the boundary.
PATH_HINTS = ("/", "./", "../", "~/", ".\\")


class ConfinementViolation(Exception):
    """A confinement control failed. Fail closed: recorded, then raised."""

    def __init__(self, kind, detail):
        self.kind = kind
        self.detail = detail
        super(ConfinementViolation, self).__init__("%s: %s" % (kind, detail))


def looks_like_path(token):
    if not token or token.startswith("-"):
        return False
    if token.startswith(PATH_HINTS):
        return True
    return "/" in token or os.sep in token


def resolve(token, base=None):
    """Expand ~, make absolute against base, then fully resolve symlinks."""
    expanded = os.path.expanduser(token)
    if base and not os.path.isabs(expanded):
        expanded = os.path.join(base, expanded)
    return os.path.realpath(expanded)


def inside_boundary(path, boundary):
    """True when path is boundary itself or lies inside it (after resolution)."""
    try:
        real_path = os.path.realpath(path)
        real_boundary = os.path.realpath(boundary)
    except OSError:
        return False
    if real_path == real_boundary:
        return True
    return real_path.startswith(real_boundary + os.sep)


def check_argv_paths(argv, boundary, base=None, exempt=()):
    """PREVENTIVE P2: reject any path-like argv element outside the boundary.

    Returns the list of accepted path elements that were checked (for the
    record). Raises ConfinementViolation on the first escape. Nothing is
    spawned by this function, so a violation here means no process ran.
    """
    checked = []
    for index, token in enumerate(argv):
        if index in exempt or not looks_like_path(token):
            continue
        resolved = resolve(token, base)
        if not inside_boundary(resolved, boundary):
            raise ConfinementViolation(
                "PATH_ESCAPE_REJECTED",
                "argv[%d] %r resolves to %s which is outside the project "
                "boundary %s; command rejected before any process was spawned"
                % (index, token, resolved, os.path.realpath(boundary)))
        checked.append({"argv_index": index, "token": token,
                        "resolved": resolved})
    return checked


def workspace_for(task_id, root=None):
    """Create and return the task workspace inside the boundary."""
    path = os.path.join(state.task_dir(task_id, root), "workspace")
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def snapshot_tree(boundary, skip_dirs=()):
    """DETECTION D1: map relative path -> mtime_ns for files in the boundary."""
    real_boundary = os.path.realpath(boundary)
    snapshot = {}
    for dirpath, dirnames, filenames in os.walk(real_boundary):
        rel_dir = os.path.relpath(dirpath, real_boundary)
        if rel_dir == ".":
            rel_dir = ""
        parts = set(rel_dir.split(os.sep)) if rel_dir else set()
        if parts & set(skip_dirs):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, real_boundary)
            try:
                snapshot[rel] = os.stat(full).st_mtime_ns
            except OSError:
                continue
    return snapshot


# Directories whose churn is expected and cannot indicate an escape by the
# agent. Only the workspace's siblings matter for boundary auditing; these
# are excluded from the tree diff so that unrelated repository activity does
# not mask or fake a violation.
AUDIT_SKIP_DIRS = (".git", "__pycache__", ".pytest_cache")


def diff_snapshots(before, after):
    """Return the list of created / modified / removed paths."""
    created = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(p for p in set(before) & set(after)
                      if before[p] != after[p])
    changes = []
    for kind, items in (("created", created), ("modified", modified),
                        ("removed", removed)):
        for item in items:
            changes.append({"change": kind, "path": item})
    return changes


def audit_boundary(boundary, workspace, before, after, watch_pairs=None,
                   owned_prefixes=()):
    """DETECTION D1: report every change outside the task workspace.

    Changes inside the workspace are expected (the agent works there) and are
    not violations. Anything inside the boundary but outside the workspace is
    reported, EXCEPT under owned_prefixes: relative paths the runner declares
    it owns and writes itself during execution (the capture directory). Those
    are runner scaffolding, not agent behaviour, and attributing them to the
    agent would make the audit lie in the other direction.

    SCOPE LIMIT (stated, not worked around): a write entirely OUTSIDE the
    boundary is invisible to a boundary-scoped diff. To cover those, the
    caller supplies watch_pairs: a list of (label, before_snapshot,
    after_snapshot) for explicitly configured external watch paths. Slice 1
    configures no watch path by default, so an unmonitored write outside the
    boundary is NOT detected. That is exactly the guarantee this module cannot
    provide (G2), and one reason real-agent execution stays disabled
    (GATE-P17-4).
    """
    real_boundary = os.path.realpath(boundary)
    real_workspace = os.path.realpath(workspace)
    violations = []
    owned = tuple(p for p in (owned_prefixes or ()) if p)

    def is_owned(relative_path):
        return any(relative_path == p or relative_path.startswith(p + os.sep)
                   for p in owned)

    for change in diff_snapshots(before, after):
        if is_owned(change["path"]):
            continue
        full = os.path.realpath(os.path.join(real_boundary, change["path"]))
        if inside_boundary(full, real_workspace):
            continue
        violations.append({
            "change": change["change"],
            "path": change["path"],
            "outside_boundary": not inside_boundary(full, real_boundary),
        })
    for label, watch_before, watch_after in (watch_pairs or []):
        for change in diff_snapshots(watch_before, watch_after):
            violations.append({
                "change": change["change"],
                "path": change["path"],
                "watch_root": label,
                "outside_boundary": True,
            })
    return violations


def assert_no_secret_paths(violations):
    """Secret safety on violation reporting: scrub before any record is written."""
    scrubbed, _ = scrub.scrub_obj(violations)
    return scrubbed
