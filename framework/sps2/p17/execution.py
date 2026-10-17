#!/usr/bin/env python3
"""P17 controlled local subprocess execution (SEC-P17-04 / REQ-P17-05).

Controls:
  - argv-only execution with shell=False. No shell string is ever accepted.
  - bounded timeout on every execution (timeout_seconds >= 1).
  - reliable process-TERMINATION of the whole process tree: the child is
    started in its own session (start_new_session=True), so on timeout the
    entire group is signalled and reaped, not just the direct child.
  - BOUNDED capture (Slice 2, SEC-P17-04/REQ-P17-05). The child's streams are
    written by the kernel to files on disk, never accumulated in memory, so a
    runaway agent cannot exhaust host memory. At most OUTPUT_CAP_BYTES per
    stream are retained in the transcript; the digest of the ORIGINAL stream
    is always computed by streaming the file.
  - exit status recorded verbatim.
  - EXPLICIT_ALLOWLIST environment (PREVENTIVE P3): a minimal, explicitly
    constructed environment. The parent environment is never inherited.

TRANSACTION SEMANTICS OF CAPTURE (exact, because truncation must never be
mistaken for full evidence):
  original stream  -> written in full to <name>.full on disk
  original digest  -> sha256 over the COMPLETE original stream, computed by
                      streaming the file (never held in memory)
  transcript       -> scrubbed, first OUTPUT_CAP_BYTES of the original stream,
                      followed by an explicit [TRUNCATED] marker naming the
                      omitted byte count and the original-stream digest
  retention        -> the .full file is DELETED once its digest is computed,
                      so no raw, unscrubbed agent output is left at rest.
                      The original BYTES are therefore not retained; what is
                      retained is the original-stream DIGEST plus the scrubbed,
                      bounded prefix. Code and reports must not describe this
                      as "full evidence".
  digest recorded  -> sha256 of the TRANSCRIPT bytes actually written, so the
                      record's digest can be re-derived from the file on disk.

The executed process is NOT confined at the OS level (SEC-P17-05 G1/G2).
Only runner-mediated prevention and post-execution detection exist here.

Standard library only. No network. No shell. No dependency.
"""
import hashlib
import os
import signal
import subprocess
import sys
import tempfile

from . import scrub

# POSIX only. Windows has no process groups; slice 1 fails closed there
# (documented limitation, plan section 17 assumption 1).
IS_POSIX = os.name == "posix"

# The explicit PATH is COMPUTED, never inherited: only the directory holding
# the interpreter that runs this implementation is granted. The executable
# itself is always launched by ABSOLUTE path (selection["resolved_path"]),
# because discovery resolves the allowlisted name once with shutil.which and
# the resolved path is what runs; no name lookup is needed to select or start
# it, so no machine-global system directory is required here.
#
# Machine-global directories are deliberately NOT granted. A child that needs
# to spawn a helper by name is exactly the case GATE-P17-4's mechanism
# security review must adjudicate, under the P6 project-local boundary rule
# that forbids machine-global path literals inside framework/sps2/. Nothing else is
# passed through, so environment secrets held by the parent process never
# reach the child (SEC-P17-06).
MINIMAL_PATH = [os.path.dirname(os.path.abspath(sys.executable))]

MINIMAL_ENV = {
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONIOENCODING": "utf-8",
}

# Per-stream retention limit. 8 MiB keeps a transcript reviewable and the
# memory cost finite; the original-stream digest is unaffected by this cap.
OUTPUT_CAP_BYTES = 8 * 1024 * 1024
HEAD_BYTES = 4096          # probe/version reads only


class ExecutionError(Exception):
    """Execution could not be performed as specified."""


class PlatformUnsupported(ExecutionError):
    """The platform cannot provide the required process control."""


def require_posix():
    if not IS_POSIX:
        raise PlatformUnsupported(
            "this implementation requires POSIX process groups for bounded "
            "timeout with process-tree termination; platform is %r. Slice 1 "
            "fails closed on unsupported platforms (no silent degradation)."
            % os.name)


def build_environment(p17_workspace=None, extra=None):
    """PREVENTIVE P3: explicit minimal environment. No parent inheritance."""
    env = dict(MINIMAL_ENV)
    env["PATH"] = os.pathsep.join([p for p in MINIMAL_PATH if p])
    if p17_workspace:
        env["P17_WORKSPACE"] = p17_workspace
    if extra:
        env.update(extra)
    return env


def _kill_process_tree(proc):
    """Terminate the whole process group, then reap.

    With start_new_session the child leads its own session and process group,
    so signalling -pgid reaches every descendant it spawned. This is what
    makes "reliable process termination" real rather than best effort for the
    direct child alone.
    """
    killed = []
    if IS_POSIX:
        try:
            pgid = os.getpgid(proc.pid)
        except OSError:
            pgid = None
        if pgid is not None:
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(pgid, sig)
                    killed.append(sig.name)
                    break
                except OSError:
                    continue
    if proc.poll() is None:
        try:
            proc.kill()
            killed.append("SIGKILL-direct")
        except OSError:
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    return killed


def prepare_capture(capture_dir):
    """Create the capture scaffolding BEFORE the confinement audit window.

    The post-execution boundary diff must attribute only changes made by the
    executed process. The runner's own capture files would otherwise appear
    inside that window and be reported as agent-caused violations, so they are
    created first and are present at both ends of the diff.
    """
    if not os.path.isdir(capture_dir):
        os.makedirs(capture_dir)
    for name in ("stdout.full", "stderr.full"):
        path = os.path.join(capture_dir, name)
        with open(path, "wb"):
            pass
    return capture_dir


def run_once(argv, cwd, timeout_seconds, env=None, stdin_data=None,
             capture_dir=None):
    """Execute argv with a bounded timeout and bounded capture.

    argv must be a list (argv-only). cwd must already be validated against
    the project boundary by the caller (PREVENTIVE P2/P4).
    """
    require_posix()
    if not isinstance(argv, list) or not argv:
        raise ExecutionError("argv must be a non-empty list (no shell strings)")
    if int(timeout_seconds) < 1:
        raise ExecutionError("timeout_seconds must be >= 1")
    run_env = env if env is not None else build_environment()

    owned_dir = None
    if capture_dir is None:
        owned_dir = tempfile.mkdtemp(prefix="p17-capture-")
        capture_dir = owned_dir
    elif not os.path.isdir(capture_dir):
        os.makedirs(capture_dir)

    full_out = os.path.join(capture_dir, "stdout.full")
    full_err = os.path.join(capture_dir, "stderr.full")
    handles = [open(full_out, "wb"), open(full_err, "wb")]
    try:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=cwd,
                env=run_env,
                stdin=subprocess.PIPE if stdin_data is not None
                else subprocess.DEVNULL,
                stdout=handles[0],
                stderr=handles[1],
                shell=False,               # P1: argv-only, never shell
                start_new_session=True,   # own process group for tree kill
            )
        except OSError as exc:
            raise ExecutionError("could not spawn %r: %s" % (argv[0], exc))

        timed_out = False
        killed_with = []
        try:
            proc.wait(timeout=int(timeout_seconds))
        except subprocess.TimeoutExpired:
            timed_out = True
            killed_with = _kill_process_tree(proc)
    finally:
        for handle in handles:
            try:
                handle.close()
            except OSError:                              # pragma: no cover
                pass

    return {
        "argv": list(argv),
        "cwd": cwd,
        "timeout_seconds": int(timeout_seconds),
        "timed_out": timed_out,
        "killed_with": killed_with,
        "exit_status": None if timed_out else proc.returncode,
        "returncode": proc.returncode,
        "stdout_full": full_out,
        "stderr_full": full_err,
        "capture_dir": capture_dir,
        "owned_capture_dir": owned_dir,
        "stdout_bytes": os.path.getsize(full_out),
        "stderr_bytes": os.path.getsize(full_err),
        "stdout_sha256": sha256_file(full_out),
        "stderr_sha256": sha256_file(full_err),
        "stdout_head": read_head(full_out),
    }


def sha256_file(path):
    """Streamed digest: the file is never read into memory in full."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_head(path, limit=HEAD_BYTES):
    with open(path, "rb") as handle:
        return handle.read(limit).decode("utf-8", "replace")


def transcribe(full_path, transcript_path, cap_bytes=OUTPUT_CAP_BYTES):
    """Write a scrubbed, bounded transcript from a captured stream.

    Returns the transcript metadata: the digest is of the bytes actually
    written (so it can be re-derived from the file), alongside the original
    stream's digest and size, and the explicit truncation record.
    """
    cap_bytes = cap_bytes or OUTPUT_CAP_BYTES
    total = os.path.getsize(full_path)
    original_sha256 = sha256_file(full_path)
    with open(full_path, "rb") as handle:
        retained = handle.read(cap_bytes)
    omitted = max(0, total - len(retained))
    cleaned, removed = scrub.scrub(retained.decode("utf-8", "replace"))
    payload = cleaned.encode("utf-8")
    if omitted:
        payload += (
            "\n[TRUNCATED: %d of %d bytes omitted from this transcript; "
            "original-stream sha256=%s]\n"
            % (omitted, total, original_sha256)).encode("utf-8")
    directory = os.path.dirname(transcript_path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(transcript_path, "wb") as handle:
        handle.write(payload)
    return {
        "ref": os.path.basename(transcript_path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "original_stream_sha256": original_sha256,
        "original_stream_bytes": total,
        "original_stream_retained": False,
        "retained_bytes": len(retained),
        "truncated": bool(omitted),
        "omitted_bytes": omitted,
        "cap_bytes": cap_bytes,
        "scrubbed_classes": removed,
    }


def discard_capture(path):
    """Delete a captured raw stream. Returns (ok, detail): never silent."""
    try:
        os.remove(path)
        return True, None
    except FileNotFoundError:
        return True, None
    except OSError as exc:
        return False, "could not delete captured stream %s: %s" % (path, exc)


def write_transcript(path, data):
    """Compatibility helper for short in-memory payloads (evidence text).

    Kept for callers that already hold the bytes (probe output). The digest
    still covers exactly the bytes written.
    """
    if isinstance(data, str):
        data = data.encode("utf-8", "replace")
    cleaned, removed = scrub.scrub(data.decode("utf-8", "replace"))
    payload = cleaned.encode("utf-8")
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "wb") as handle:
        handle.write(payload)
    return {
        "ref": os.path.basename(path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "scrubbed_classes": removed,
    }
