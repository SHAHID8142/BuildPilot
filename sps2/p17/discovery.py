#!/usr/bin/env python3
"""P17 runtime agent discovery (REQ-P17-03 / SEC-P17-02).

Availability is determined by an EXECUTED runtime probe. A tool documented in
the repository but absent at runtime is reported unavailable and can never be
selected. Nothing is ever assumed available.

PROBE COMMAND RESTRICTION (added at implementation): a probe may only read a
version or help surface. Probing an allowlisted executable with any other
argument is rejected before any process is spawned. Probing is still a process
execution, so a production-purpose allowlist is refused outright while
GATE-P17-4 is OPEN - no probe and no execution, in either case.

EXECUTABLE RESOLUTION (fail-closed pinning): an allowlisted NAME is never
resolved against the ambient PATH. PATH order is influenceable and a
same-named executable placed earlier in PATH would otherwise shadow the
approved one. Each entry is resolved either by an explicit absolute
`pinned_path` or by a name lookup confined to the allowlist's configured
`trusted_roots`. Missing configuration, a pin that is missing/not a file/not
executable, or a resolution that escapes the trusted roots all fail closed. The
resolved executable's SHA-256 is recorded at discovery and re-verified
immediately before spawning, which detects substitution between those two
moments. That check does NOT close the residual window in which a privileged
local process could swap the file after verification and before exec, and no
unprivileged stdlib-only mechanism can; this is a detection control, not a
prevention guarantee.

The discovery snapshot records, per allowlist entry: agent_id, availability,
version, probe method, probed-at timestamp, the resolved absolute path, the
resolution mode, the trusted roots, and the executable digest.

Standard library only. No network.
"""
import hashlib
import os
import shutil

from . import execution, state

ALLOWED_PROBE_METHODS = ("VERSION_FLAG", "HELP_FLAG")
PROBE_TIMEOUT_SECONDS = 10

# Resolution modes. An allowlisted NAME is never resolved against the ambient
# PATH: ambient PATH order is attacker-influenceable and a same-named
# executable earlier in PATH would silently shadow the approved one. Either the
# absolute path is pinned explicitly, or resolution is confined to operator-
# configured trusted roots. Missing configuration fails closed.
RESOLUTION_PINNED = "PINNED_PATH"
RESOLUTION_TRUSTED_ROOT = "TRUSTED_ROOT"


class DiscoveryError(Exception):
    """Discovery could not be performed as specified."""


def allowlist_path(root=None):
    return os.path.join(root or state.DEFAULT_ROOT, "sps2", "p17", "allowlist.json")


def load_allowlist(root=None):
    """Read the authoritative allowlist. It is DATA, never a code path."""
    path = allowlist_path(root)
    if not os.path.exists(path):
        raise DiscoveryError("allowlist not found at %s" % path)
    try:
        data = state.read_json(path)
    except Exception as exc:
        raise DiscoveryError("allowlist %s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict) or not isinstance(data.get("agents"), list):
        raise DiscoveryError("allowlist %s has no 'agents' list" % path)
    return data


def assert_probe_allowed(allowlist, enablement):
    """Fail closed: a production allowlist may not be probed or executed.

    GATE-P17-4 is OPEN and real-agent execution is disabled by default, so a
    production-purpose allowlist is refused before any process is spawned.
    This is prevention, not detection.
    """
    purpose = allowlist.get("purpose")
    if purpose == "production" and not enablement.get("enabled"):
        raise DiscoveryError(
            "real-agent execution is disabled (GATE-P17-4 OPEN): allowlist "
            "'%s' has purpose 'production'. No agent was probed and no "
            "process was spawned. Repository-local test doubles "
            "(purpose 'test') remain the only executable surface."
            % allowlist_path())


def _probe_argv(entry):
    """Build the probe argv for an allowlist entry, or reject the entry."""
    method = entry.get("probe_method", "VERSION_FLAG")
    if method not in ALLOWED_PROBE_METHODS:
        raise DiscoveryError(
            "agent %r declares probe_method %r which is not permitted; only "
            "%s are allowed" % (entry.get("agent_id"), method,
                                "/".join(ALLOWED_PROBE_METHODS)))
    flag = "--version" if method == "VERSION_FLAG" else "--help"
    declared = entry.get("probe_argv")
    if declared is not None:
        if not isinstance(declared, list) or not declared:
            raise DiscoveryError(
                "agent %r declares a non-list or empty probe_argv"
                % entry.get("agent_id"))
        if declared != [flag]:
            raise DiscoveryError(
                "agent %r declares probe_argv %r; only a single version/help "
                "flag %r is permitted" % (entry.get("agent_id"), declared, flag))
    return method, [flag]


def _absolute_configured(value, base_dir, what):
    """Resolve a configured path to an absolute one.

    Relative entries are resolved against the ALLOWLIST FILE'S OWN directory,
    so a repository-local allowlist stays portable while the effective value is
    always absolute before it is used for a security decision.
    """
    if not isinstance(value, str) or not value.strip():
        raise DiscoveryError("%s must be a non-empty string, got %r"
                             % (what, value))
    candidate = value if os.path.isabs(value) else os.path.join(base_dir, value)
    return os.path.realpath(candidate)


def _trusted_roots(allowlist, allowlist_file, required=True):
    """The explicitly configured trusted roots, absolute and de-duplicated.

    An ABSENT declaration is fatal only when `required` (inside resolution).
    A MALFORMED declaration is always fatal, because that is operator error
    that must never be silently tolerated.
    """
    declared = allowlist.get("trusted_roots")
    if declared is None:
        if not required:
            return []
        raise DiscoveryError(
            "allowlist declares no 'trusted_roots'. Executable names are never "
            "resolved against the ambient PATH (PATH order is influenceable "
            "and a same-named executable earlier in PATH would shadow the "
            "approved one). Configure 'trusted_roots', or pin an absolute "
            "'pinned_path' on each agent entry. Failing closed.")
    if not isinstance(declared, list) or not declared:
        raise DiscoveryError(
            "allowlist declares 'trusted_roots' as %r; a non-empty list of "
            "directories is required. Failing closed." % (declared,))
    base_dir = os.path.dirname(os.path.abspath(allowlist_file))
    roots = []
    for item in declared:
        root = _absolute_configured(item, base_dir, "trusted_roots entry")
        if not os.path.isdir(root):
            raise DiscoveryError(
                "trusted root %r (from %r) is not a directory. Failing closed."
                % (root, item))
        if root not in roots:
            roots.append(root)
    return roots


def _within(path, roots):
    """True when `path` is inside one of the trusted roots (not merely under
    a shared prefix): compares resolved directory paths."""
    for root in roots:
        if path == root:
            return True
        if path.startswith(root.rstrip(os.sep) + os.sep):
            return True
    return False


def resolve_entry(entry, allowlist, allowlist_file):
    """Resolve an allowlisted agent to an absolute, verified executable.

    Returns (absolute_path, resolution_mode, trusted_roots). Fails closed on
    missing configuration, on a pin that does not exist or is not executable,
    and on any resolution that escapes the configured trusted roots.
    """
    agent_id = entry.get("agent_id")
    base_dir = os.path.dirname(os.path.abspath(allowlist_file))
    roots = _trusted_roots(allowlist, allowlist_file)

    pinned = entry.get("pinned_path")
    if pinned is not None:
        path = _absolute_configured(pinned, base_dir,
                                    "pinned_path for agent %r" % agent_id)
        if not os.path.exists(path):
            raise DiscoveryError(
                "agent %r pins %r, which does not exist. Failing closed."
                % (agent_id, path))
        if not os.path.isfile(path):
            raise DiscoveryError(
                "agent %r pins %r, which is not a regular file. Failing closed."
                % (agent_id, path))
        if not os.access(path, os.X_OK):
            raise DiscoveryError(
                "agent %r pins %r, which is not executable. Failing closed."
                % (agent_id, path))
        if not _within(path, roots):
            raise DiscoveryError(
                "agent %r pins %r, which is outside every configured trusted "
                "root (%s). Failing closed."
                % (agent_id, path, ", ".join(roots)))
        return path, RESOLUTION_PINNED, roots

    # No pin: resolve the bare name INSIDE the trusted roots only.
    search_path = os.pathsep.join(roots)
    resolved = shutil.which(agent_id, path=search_path)
    if resolved is None:
        raise DiscoveryError(
            "agent %r was not found in any trusted root (%s). The ambient PATH "
            "is never consulted. Failing closed." % (agent_id, search_path))
    real = os.path.realpath(resolved)
    if not _within(real, roots):
        raise DiscoveryError(
            "agent %r resolved to %r, which escapes the configured trusted "
            "roots (%s). Failing closed." % (agent_id, real, ", ".join(roots)))
    return real, RESOLUTION_TRUSTED_ROOT, roots


def executable_digest(path):
    """SHA-256 of the resolved executable, or None when unreadable."""
    try:
        return state.sha256_file(path)
    except OSError:
        return None


def verify_unchanged(path, expected_digest, agent_id):
    """Re-hash the executable immediately before spawning it.

    This detects a file that changed between discovery and execution. It does
    NOT close the remaining window in which a sufficiently privileged local
    process could swap the file after this check and before the exec syscall;
    no unprivileged stdlib-only mechanism closes that window.
    """
    if not expected_digest:
        raise DiscoveryError(
            "agent %r has no recorded executable digest; refusing to execute "
            "an unverified binary. Failing closed." % agent_id)
    actual = executable_digest(path)
    if actual is None:
        raise DiscoveryError(
            "agent %r resolved to %r, which cannot be read for hashing. "
            "Failing closed." % (agent_id, path))
    if actual != expected_digest:
        raise DiscoveryError(
            "agent %r resolved to %r, whose SHA-256 changed between discovery "
            "and execution (recorded %s, now %s). The executable was "
            "substituted. Failing closed."
            % (agent_id, path, expected_digest[:12], actual[:12]))
    return actual


def probe_entry(entry, cwd, timeout_seconds=PROBE_TIMEOUT_SECONDS,
                allowlist=None, allowlist_file=None):
    """Execute a bounded, flag-only version/help probe for one entry."""
    agent_id = entry["agent_id"]
    method, flag_argv = _probe_argv(entry)
    # FAIL CLOSED: a resolution failure records the entry as UNAVAILABLE with
    # an explicit reason, which selection excludes and the CLI turns into an
    # auditable BLOCKED outcome - never a silent skip, and never an execution.
    # This is the approved semantics for an unresolvable entry (plan 12(c):
    # "allowlisted but unavailable => excluded from selection; if no
    # allowlisted agent is eligible => explicit BLOCKED outcome, no
    # fallback, ever").
    try:
        resolved, mode, roots = resolve_entry(entry, allowlist or {},
                                              allowlist_file)
    except DiscoveryError as exc:
        return {
            "agent_id": agent_id,
            "available": False,
            "version": None,
            "probe_method": method,
            "probed_at": state.now(),
            "resolved_path": None,
            "resolution_mode": None,
            "trusted_roots": [],
            "executable_sha256": None,
            "note": "resolution refused: %s" % exc,
            "resolution_error": str(exc),
        }
    record = {
        "agent_id": agent_id,
        "available": False,
        "version": None,
        "probe_method": method,
        "probed_at": state.now(),
        "resolved_path": resolved,
        "resolution_mode": mode,
        "trusted_roots": roots,
        "executable_sha256": executable_digest(resolved),
        "note": None,
        "resolution_error": None,
    }
    result = None
    try:
        result = execution.run_once([resolved] + flag_argv, cwd=cwd,
                                    timeout_seconds=timeout_seconds)
    except execution.ExecutionError as exc:
        record["note"] = "probe could not be executed: %s" % exc
        return record
    finally:
        # The probe's raw streams are never retained at rest: the version line
        # is read from the head and the capture is discarded immediately.
        if result is not None:
            for stream in ("stdout_full", "stderr_full"):
                execution.discard_capture(result.get(stream))
            if result.get("owned_capture_dir"):
                try:
                    os.rmdir(result["owned_capture_dir"])
                except OSError:
                    pass
    if result["timed_out"]:
        record["note"] = "probe timed out after %ds" % timeout_seconds
        return record
    if result["exit_status"] != 0:
        record["note"] = "probe exited %r" % (result["exit_status"],)
        return record
    out = (result.get("stdout_head") or "").strip()
    record["available"] = True
    record["version"] = out.splitlines()[0][:200] if out else "(no version output)"
    return record


def discover(allowlist, cwd, root=None, timeout_seconds=PROBE_TIMEOUT_SECONDS,
             allowlist_file=None):
    """Probe every allowlist entry; return the discovery snapshot.

    The snapshot lists every allowlist entry, available or not, so an absent
    tool is visibly recorded rather than silently missing.
    """
    state.ensure_dirs(root)
    enablement = state.real_agent_enablement(root)
    assert_probe_allowed(allowlist, enablement)
    if allowlist_file is None:
        allowlist_file = allowlist_path(root)
    entries = []
    for entry in allowlist["agents"]:
        if not isinstance(entry, dict) or not entry.get("agent_id"):
            raise DiscoveryError("allowlist contains an entry without agent_id")
        entries.append(probe_entry(entry, cwd, timeout_seconds,
                                   allowlist=allowlist,
                                   allowlist_file=allowlist_file))
    return {
        "discovered_at": state.now(),
        "allowlist_purpose": allowlist.get("purpose", "test"),
        "trusted_roots": _trusted_roots(allowlist, allowlist_file,
                                        required=False),
        "agents": entries,
        "probed_count": len(entries),
        "available_count": sum(1 for e in entries if e["available"]),
    }
