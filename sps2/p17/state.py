#!/usr/bin/env python3
"""P17 project-local state: paths, identifiers, atomic writes, control state.

Project-local state lives in the repository, never in machine-global
directories (.sps/GOVERNANCE.md section 9, P7 project-local boundary):

  .sps/tasks/p17/<TASK-P17-NNNN>/   record.json, plan.json, transcripts,
                                    approval.json, state.json (attempt
                                    journal), integrity.json, run.lock
  .sps/evidence/P17/                EV-P17-NNN evidence records
  .sps/p17/                         control state (real-agent enablement)

The real-agent enablement state is DISABLED unless a matching recorded
decision says otherwise. GATE-P17-4 is OPEN, so the default must fail closed:
absent or disabled means real-agent execution is refused before any probe or
process spawn (REQ-P17-05, SEC-P17-02, SEC-P17-10).

Retry and in-flight bookkeeping lives in state.json (durable attempt journal)
rather than in the schema-conformant task record, because the approved record
schema has no such field and must not be amended by implementation code.

Standard library only. No network, no global writes, no dependency.
"""
import contextlib
import hashlib
import json
import os
import re
import time

try:                                            # POSIX advisory locking
    import fcntl
except ImportError:                             # pragma: no cover
    fcntl = None

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

TASKS_DIR = os.path.join(".sps", "tasks", "p17")
EVIDENCE_DIR = os.path.join(".sps", "evidence", "P17")
CONTROL_DIR = os.path.join(".sps", "p17")
ENABLEMENT_FILE = "real-agent-execution.json"
USAGE_LOG = os.path.join(".sps", "tasks", "p17", "usage.log")
COUNTER_NAME = ".next-task-id"
INTEGRITY_NAME = "integrity.json"
RUN_LOCK_NAME = "run.lock"

TASK_ID_RE = re.compile(r"^TASK-P17-(\d{4})$")
EVIDENCE_ID_RE = re.compile(r"^EV-P17-(\d{3})$")
STEP_ID_RE = re.compile(r"^STEP-(\d{1,4})$")

DEFAULT_ROOT = REPO_ROOT
RETRY_BOUND = 2

# Bounded capture: per stream. 8 MiB keeps the transcript human-reviewable and
# the memory cost of a runaway agent finite. The ORIGINAL stream is always
# retained on disk and digested, so truncation never destroys evidence.
OUTPUT_CAP_BYTES = 8 * 1024 * 1024


class StateError(Exception):
    """Any project-local state failure. Never silently ignored."""


class LockUnavailable(StateError):
    """A required lock is held by another process, or locking is impossible."""


def now():
    """ISO-8601 UTC timestamp, second precision, with Z suffix."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def today():
    """ISO-8601 date (UTC)."""
    return time.strftime("%Y-%m-%d", time.gmtime())


def tasks_root(root=None):
    return os.path.join(root or DEFAULT_ROOT, TASKS_DIR)


def evidence_root(root=None):
    return os.path.join(root or DEFAULT_ROOT, EVIDENCE_DIR)


def control_root(root=None):
    return os.path.join(root or DEFAULT_ROOT, CONTROL_DIR)


def enablement_path(root=None):
    return os.path.join(control_root(root), ENABLEMENT_FILE)


def ensure_dirs(root=None):
    for d in (tasks_root(root), evidence_root(root), control_root(root)):
        if not os.path.isdir(d):
            os.makedirs(d)


def task_dir(task_id, root=None):
    return os.path.join(tasks_root(root), task_id)


def _highest_existing(root=None):
    highest = 0
    directory = tasks_root(root)
    if os.path.isdir(directory):
        for name in os.listdir(directory):
            m = TASK_ID_RE.match(name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest


def next_task_id(root=None):
    """Next unused TASK-P17-NNNN by scan (kept for compatibility).

    Slice 2 uses allocate_task_id(), which is monotonic and lock-protected.
    """
    ensure_dirs(root)
    return "TASK-P17-%04d" % (_highest_existing(root) + 1)


# ---------------------------------------------------------------- locking ---
def require_locking():
    """Fail closed when the platform cannot provide a reliable lock."""
    if fcntl is None or not hasattr(fcntl, "flock"):      # pragma: no cover
        raise StateError(
            "per-task locking requires fcntl.flock (POSIX). This platform "
            "cannot provide the concurrency guarantee the execution contract "
            "requires, so execution fails closed rather than running "
            "unprotected.")


@contextlib.contextmanager
def file_lock(path, blocking=False):
    """Advisory exclusive lock on a lock file. Raises LockUnavailable.

    Two separate open() calls in the same process conflict too, so an
    in-process double invocation is rejected exactly like a second process.
    """
    require_locking()
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    handle = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
        try:
            fcntl.flock(handle, flags)
        except OSError as exc:
            raise LockUnavailable(
                "lock %s is held by another run (%s); refusing to execute "
                "concurrently" % (os.path.basename(path), exc.strerror))
        yield handle
    finally:
        try:
            fcntl.flock(handle, fcntl.LOCK_UN)
        except OSError:                                  # pragma: no cover
            pass
        os.close(handle)


def run_lock(task_id, root=None):
    """Exclusive per-task run lock. A second concurrent run is rejected."""
    return file_lock(os.path.join(task_dir(task_id, root), RUN_LOCK_NAME))


def intake_lock(root=None, attempts=250, delay=0.02):
    """Exclusive project-local intake lock: no duplicate identifiers.

    Allocation must SERIALISE rather than reject: concurrent intakes queue for
    a bounded time and each is then allocated its own identifier. If the lock
    cannot be taken within the bound, intake fails closed rather than risking
    a duplicate.
    """
    path = os.path.join(tasks_root(root), COUNTER_NAME + ".lock")
    return _queued_lock(path, attempts, delay)


@contextlib.contextmanager
def _queued_lock(path, attempts, delay):
    require_locking()
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    handle = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        for remaining in range(attempts, 0, -1):
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if remaining == 1:
                    raise LockUnavailable(
                        "intake lock %s could not be acquired within the "
                        "bound (%s); refusing to allocate an identifier that "
                        "might duplicate" % (os.path.basename(path),
                                              exc.strerror))
                time.sleep(delay)
        yield handle
    finally:
        try:
            fcntl.flock(handle, fcntl.LOCK_UN)
        except OSError:                                  # pragma: no cover
            pass
        os.close(handle)


def _counter_path(root=None):
    return os.path.join(tasks_root(root), COUNTER_NAME)


def allocate_task_id(root=None):
    """Allocate a TASK-P17-NNNN that is never reused, under the intake lock.

    Monotonic: the counter only ever increases, so an identifier consumed by a
    failed intake is not handed out again. Concurrent intake cannot duplicate.
    """
    ensure_dirs(root)
    with intake_lock(root):
        path = _counter_path(root)
        counter = 0
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    counter = int((handle.read().strip() or "0"))
            except (ValueError, OSError):
                counter = 0
        allocated = max(counter, _highest_existing(root)) + 1
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(str(allocated) + "\n")
        os.replace(tmp, path)
        return "TASK-P17-%04d" % allocated


def discard_task_dir(task_id, root=None):
    """Remove a task directory created by a failed intake.

    Cleanup failures are reported, never hidden.
    """
    import shutil
    path = task_dir(task_id, root)
    try:
        shutil.rmtree(path)
        return True, None
    except OSError as exc:
        return False, "cleanup of %s failed: %s" % (path, exc)


# ------------------------------------------------------- integrity sidecar ---
def integrity_path(task_id, root=None):
    return os.path.join(task_dir(task_id, root), INTEGRITY_NAME)


def read_integrity(task_id, root=None):
    path = integrity_path(task_id, root)
    if not os.path.exists(path):
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def write_integrity(task_id, data, root=None):
    write_json(integrity_path(task_id, root), data)


# ---------------------------------------------------------- attempt journal ---
def validate_journal(data, task_id):
    """Fail closed on an inconsistent attempt journal.

    A journal that cannot be trusted must never be silently replaced by an
    empty one: that would reset the retry bound and erase the history of
    attempts that may have produced side effects.
    """
    if not isinstance(data, dict):
        raise StateError("attempt journal for %s is not an object" % task_id)
    attempts = data.get("attempts", [])
    if not isinstance(attempts, list):
        raise StateError("attempt journal for %s has a non-list 'attempts' "
                         "field" % task_id)
    for index, entry in enumerate(attempts):
        if not isinstance(entry, dict):
            raise StateError("attempt journal for %s: entry %d is not an "
                             "object" % (task_id, index))
        if isinstance(entry.get("attempt"), bool) or \
                not isinstance(entry.get("attempt"), int):
            raise StateError("attempt journal for %s: entry %d has no integer "
                             "attempt number" % (task_id, index))
    bound = data.get("retry_bound", RETRY_BOUND)
    if isinstance(bound, bool) or not isinstance(bound, int) or bound < 1:
        raise StateError("attempt journal for %s has an invalid retry_bound "
                         "%r" % (task_id, bound))
    return data


def stage_state(task_id, root=None):
    """The durable attempt journal (state.json).

    A MISSING journal is an empty journal. An existing but unreadable or
    inconsistent journal is a hard failure (fail closed), never a reset.
    """
    path = os.path.join(task_dir(task_id, root), "state.json")
    if not os.path.exists(path):
        return {"task_id": task_id, "attempts": [], "retry_bound": RETRY_BOUND,
                "created_at": now()}
    try:
        data = read_json(path)
    except Exception as exc:
        raise StateError("attempt journal for %s is unreadable (%s); refusing "
                         "to run because the attempt history cannot be trusted"
                         % (task_id, exc))
    return validate_journal(data, task_id)


def record_attempt(task_id, attempt, root=None):
    """Append one journal entry and persist it before returning."""
    data = stage_state(task_id, root)
    data.setdefault("attempts", []).append(attempt)
    data["updated_at"] = now()
    write_json(os.path.join(task_dir(task_id, root), "state.json"), data)
    return data


def attempts_used(task_id, root=None):
    """Number of execution attempts that were STARTED (durable history).

    An attempt is counted once: an entry that begins an attempt (phase
    "started") and, for compatibility with journals written before Slice 2,
    an entry with no phase at all. Bookkeeping entries that close an attempt
    ("finished", "aborted") do not start one, so a normal attempt - which
    writes started then finished - consumes exactly one slot of the bound.
    """
    journal = stage_state(task_id, root)
    return len([a for a in (journal.get("attempts") or [])
                if a.get("phase") in (None, "started")])


def incomplete_attempt(task_id, root=None):
    """Return the newest attempt whose start has no matching finish.

    Its presence means a previous run died between spawn and record write.
    """
    journal = stage_state(task_id, root)
    started, finished = {}, {}
    for entry in (journal.get("attempts") or []):
        number = entry.get("attempt")
        if entry.get("phase") == "started":
            started[number] = entry
        elif entry.get("phase") in ("finished", "aborted"):
            finished[number] = entry
    for number in sorted(started, reverse=True):
        if number not in finished:
            return started[number]
    return None


# --------------------------------------------------------------- io helpers ---
def write_json(path, payload):
    """Atomic-ish write: temp file in the same directory, then replace."""
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp, path)


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path):
    """Streamed digest of a file: never loads the whole artefact in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def next_evidence_id(root=None):
    ensure_dirs(root)
    highest = 0
    for name in os.listdir(evidence_root(root)):
        if name.endswith(".json"):
            m = EVIDENCE_ID_RE.match(name[:-5])
            if m:
                highest = max(highest, int(m.group(1)))
    return "EV-P17-%03d" % (highest + 1)


def real_agent_enablement(root=None):
    """Read the real-agent enablement state. Missing or unreadable = DISABLED.

    Returns the parsed state, or a fail-closed DISABLED default when the
    file is absent. The file is never created claiming authorization: it is
    created DISABLED if absent, so the on-disk state always matches the
    fail-closed default (GATE-P17-4 OPEN).
    """
    path = enablement_path(root)
    if not os.path.exists(path):
        ensure_dirs(root)
        disabled = {
            "schema": "sps2.p17-real-agent-enablement/v1",
            "enabled": False,
            "gate": "GATE-P17-4",
            "state": "OPEN",
            "decision_ref": None,
            "reviewed_at": None,
            "note": "Real-agent execution is disabled. GATE-P17-4 is OPEN: no "
                    "reviewed preventive isolation mechanism exists. This file "
                    "records DISABLED and claims no authorization.",
            "written_by": "sps2/p17/state.py",
            "written_at": now(),
        }
        write_json(path, disabled)
        return disabled
    try:
        data = read_json(path)
    except Exception:
        return {
            "schema": "sps2.p17-real-agent-enablement/v1",
            "enabled": False,
            "gate": "GATE-P17-4",
            "state": "OPEN",
            "decision_ref": None,
            "note": "Enablement file unreadable; failing closed to DISABLED.",
        }
    if not isinstance(data, dict):
        return {"enabled": False, "gate": "GATE-P17-4", "state": "OPEN",
                "decision_ref": None,
                "note": "Enablement file malformed; failing closed to DISABLED."}
    # A file claiming enablement without a matching decision reference is
    # treated as DISABLED (GATE-P17-4 requires an explicit recorded decision).
    if data.get("enabled") and not data.get("decision_ref"):
        data = dict(data)
        data["enabled"] = False
        data["note"] = "Enablement claimed without a decision reference; " \
                       "failing closed to DISABLED."
    return data


def log_usage(entry, root=None):
    """Append one usage-observation line (D-P17-7: local log only, no network)."""
    ensure_dirs(root)
    path = os.path.join(root or DEFAULT_ROOT, USAGE_LOG)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
