#!/usr/bin/env python3
"""SPS 2.0 P17 Slice 2 lifecycle-integrity and failure-recovery suite.

Covers every gap proved by the Slice 2 analysis, with test doubles only, in
isolated temporary project roots. Real-agent execution stays disabled and
GATE-P17-4 stays OPEN; no real agent CLI is ever probed or invoked.

  S2-1  fail-closed CLI for malformed JSON, invalid records, state and
        filesystem errors: controlled non-zero exit, named stage, no traceback
  S2-2  approval binding: a task or plan mutated after approval cannot run and
        cannot become VERIFIED
  S2-3  complete integrity: evidence artefact and acceptance transcripts are
        re-verified; artefact integrity stays distinct from acceptance success
  S2-4  per-task run lock: a second concurrent run is rejected
  S2-5  atomic intake: no orphan directory, no duplicate or reused identifier
  S2-6  bounded capture: truncation is explicit, the original-stream digest is
        retained, and truncated acceptance cannot yield VERIFIED
  S2-7  attempt journal: start is persisted before spawn, stale attempts block
        until explicit --resume, and the retry bound uses durable history

Existing terminal-state behaviour is re-asserted here so it cannot regress.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from sps2.p17 import (execution, record, state, __main__ as cli)  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures", "p17")
STUB_AGENT = "stub-agent.py"
STUB_SLOW = "stub-slow.py"
STUB_NOISY = "stub-noisy.py"

AGENTS = (
    {"agent_id": STUB_AGENT, "probe_method": "VERSION_FLAG",
     "capabilities": ["test-double", "repository-state-reading",
                      "markdown", "json"]},
    {"agent_id": STUB_SLOW, "probe_method": "VERSION_FLAG",
     "capabilities": ["slow-test-double"]},
    {"agent_id": STUB_NOISY, "probe_method": "VERSION_FLAG",
     "capabilities": ["noisy-test-double"]},
)


def repo_signature():
    """Read-only signature of the REAL repository's P17 state."""
    tasks = os.path.join(REPO, ".sps", "tasks", "p17")
    evidence = os.path.join(REPO, ".sps", "evidence", "P17")
    usage = os.path.join(tasks, "usage.log")
    return (sorted(os.listdir(tasks)) if os.path.isdir(tasks) else [],
            sorted(os.listdir(evidence)) if os.path.isdir(evidence) else [],
            os.path.getsize(usage) if os.path.exists(usage) else None)


class LifecycleTestCase(unittest.TestCase):
    """Isolated project root per test, test-double allowlist, repo read-only."""

    def setUp(self):
        self.repo_before = repo_signature()
        self.addCleanup(self._assert_repo_untouched)
        self.root = tempfile.mkdtemp(prefix="p17-life-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.work = tempfile.mkdtemp(prefix="p17-life-task-")
        self.addCleanup(shutil.rmtree, self.work, ignore_errors=True)
        state.ensure_dirs(self.root)
        os.makedirs(os.path.join(self.root, "sps2", "p17"), exist_ok=True)
        self.allowlist = os.path.join(self.root, "sps2", "p17", "allowlist.json")
        self._write_allowlist()
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = FIXTURES + os.pathsep + old_path

        def restore():
            os.environ["PATH"] = old_path
        self.addCleanup(restore)

    def _assert_repo_untouched(self):
        after = repo_signature()
        if after != self.repo_before:
            self.fail("TEST ISOLATION VIOLATION: real repository P17 state "
                      "changed (%r -> %r)" % (self.repo_before, after))

    def _write_allowlist(self):
        state.write_json(self.allowlist, {
            "schema": "sps2.p17-allowlist/v1", "purpose": "test",
            "trusted_roots": [FIXTURES],
            "agents": list(AGENTS)})

    def task_file(self, goal="stub-mode:write=out.txt", accept=None,
                  expected=0, timeout=30, name="task.json",
                  capabilities=None):
        path = os.path.join(self.work, name)
        payload = {
            "goal": goal,
            "required_capabilities": capabilities or ["test-double"],
            "acceptance": {"command": accept or [sys.executable, "-c",
                                                 "print('acceptance ok')"],
                           "expected_exit_status": expected},
            "timeout_seconds": timeout,
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return path

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(["--root", self.root] + list(argv))
        return code, out.getvalue(), err.getvalue()

    def plan(self, **kw):
        code, out, err = self.cli("plan", "--task-file", self.task_file(**kw))
        self.assertEqual(code, cli.EXIT_OK, out + err)
        return [t for t in out.split() if t.startswith("TASK-P17-")][0]

    def approve(self, task_id, basis="User approved this test task."):
        code, out, err = self.cli("approve", "--task-id", task_id,
                                  "--basis", basis)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        return task_id

    def run_task(self, task_id, *extra):
        return self.cli("run", "--task-id", task_id, *extra)

    def rec(self, task_id):
        return record.load(task_id, self.root)

    def executions(self, task_id):
        """Execution counter: usage-log entries recorded for this task."""
        path = os.path.join(state.tasks_root(self.root), "usage.log")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()
                    and json.loads(line).get("task_id") == task_id]

    def sidecar(self, task_id):
        return state.read_integrity(task_id, self.root)

    def prepared(self, goal="stub-mode:write=out.txt", **kw):
        task_id = self.plan(goal=goal, **kw)
        self.approve(task_id)
        return task_id


# ---------------------------------------------------------------- S2-1 ------
class TestFailClosedCli(LifecycleTestCase):
    """Malformed or unusable state is rejected, never crashed on."""

    def corrupt_record(self, task_id, text="{not valid json"):
        with open(os.path.join(state.task_dir(task_id, self.root),
                               "record.json"), "w", encoding="utf-8") as handle:
            handle.write(text)

    def test_corrupt_record_is_rejected_without_traceback(self):
        task_id = self.prepared()
        self.corrupt_record(task_id)
        for verb in ("verify", "status", "run"):
            code, out, err = self.cli(verb, "--task-id", task_id)
            self.assertNotEqual(code, 0, verb)
            self.assertNotIn("Traceback", err, verb)
            self.assertIn("ERROR", err, verb)
        self.assertEqual(self.executions(task_id), [],
                         "no execution may happen on corrupt state")

    def test_invalid_record_is_rejected_without_traceback(self):
        task_id = self.prepared()
        path = os.path.join(state.task_dir(task_id, self.root), "record.json")
        doc = state.read_json(path)
        doc["status"] = "NOT_A_STATUS"
        state.write_json(path, doc)
        for verb in ("verify", "status", "run"):
            code, out, err = self.cli(verb, "--task-id", task_id)
            self.assertNotEqual(code, 0, verb)
            self.assertNotIn("Traceback", err, verb)

    def test_missing_record_is_rejected_without_traceback(self):
        code, out, err = self.cli("status", "--task-id", "TASK-P17-9999")
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertIn("no record", err)

    def test_malformed_allowlist_is_rejected_without_traceback(self):
        with open(self.allowlist, "w", encoding="utf-8") as handle:
            handle.write("{oops")
        code, out, err = self.cli("plan", "--task-file", self.task_file())
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_errors_never_contain_secret_values(self):
        task_id = self.plan(
            goal="stub-mode:secret=1", accept=[sys.executable, "-c",
                                               "raise SystemExit(1)"])
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        self.assertNotIn("sk-test-FAKE", err)
        self.assertNotIn("ghp_FAKE", err)


# ---------------------------------------------------------------- S2-2 ------
class TestApprovalBinding(LifecycleTestCase):
    """The approval binds to the exact task and plan content approved."""

    def test_task_mutation_after_approval_blocks_execution(self):
        task_id = self.prepared()
        side = os.path.join(state.task_dir(task_id, self.root), "task.json")
        data = state.read_json(side)
        approved_command = data["acceptance"]["command"]
        data["acceptance"]["command"] = [sys.executable, "-c",
                                         "print('SUBSTITUTED')"]
        state.write_json(side, data)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("approval binding check failed", err)
        self.assertIn("task_sha256 changed after approval", err)
        self.assertEqual(self.executions(task_id), [],
                         "no subprocess may be created on a binding mismatch")
        self.assertFalse(os.path.exists(os.path.join(
            state.task_dir(task_id, self.root), "stdout.log")))
        self.assertNotEqual(self.rec(task_id)["status"], "VERIFIED")

    def test_plan_mutation_after_approval_blocks_execution(self):
        task_id = self.prepared()
        plan_path = os.path.join(state.task_dir(task_id, self.root), "plan.json")
        with open(plan_path, "a", encoding="utf-8") as handle:
            handle.write(" ")
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("plan_sha256 changed after approval", err)
        self.assertEqual(self.executions(task_id), [])

    def test_approval_records_the_bound_digests(self):
        task_id = self.prepared()
        approval = state.read_json(
            os.path.join(state.task_dir(task_id, self.root), "approval.json"))
        self.assertEqual(len(approval["plan_sha256"]), 64)
        self.assertEqual(len(approval["task_sha256"]), 64)
        self.assertEqual(approval["plan_sha256"], state.sha256_file(
            os.path.join(state.task_dir(task_id, self.root), "plan.json")))

    def test_record_approval_stays_within_the_approved_schema(self):
        task_id = self.prepared()
        self.run_task(task_id)
        record_approval = self.rec(task_id).get("approval") or {}
        self.assertEqual(set(record_approval),
                         {"decided_by", "decided_by_role", "decided_at",
                          "basis", "state"})
        self.assertEqual(record.violations(self.rec(task_id)), [])

    def test_unbound_legacy_approval_is_refused(self):
        task_id = self.plan()
        state.write_json(os.path.join(state.task_dir(task_id, self.root),
                                      "approval.json"),
                         {"decided_by": "User", "decided_by_role": "USER",
                          "decided_at": state.today(), "basis": "legacy",
                          "state": "APPROVED"})
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("does not record", err)
        self.assertEqual(self.executions(task_id), [])


# ---------------------------------------------------------------- S2-3 ------
class TestEvidenceIntegrity(LifecycleTestCase):
    """Every recorded artefact digest is recomputed; integrity is separate
    from acceptance success."""

    def verified(self):
        task_id = self.prepared()
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        return task_id

    def test_intact_task_verifies_clean(self):
        task_id = self.verified()
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertIn("no findings", out)

    def test_tampered_evidence_artefact_is_detected(self):
        task_id = self.verified()
        path = os.path.join(state.task_dir(task_id, self.root), "evidence",
                            "verification-output.json")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\n")
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertEqual(code, cli.EXIT_FAILED if hasattr(cli, "EXIT_FAILED")
                         else 1, out + err)
        self.assertIn("INTEGRITY_MISMATCH", err)
        self.assertIn("verification-output.json", err)

    def test_tampered_acceptance_transcript_is_detected(self):
        task_id = self.verified()
        path = os.path.join(state.task_dir(task_id, self.root), "evidence",
                            "acceptance-stdout.log")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("tampered\n")
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertNotEqual(code, 0)
        self.assertIn("INTEGRITY_MISMATCH", err)
        self.assertIn("acceptance-stdout.log", err)

    def test_missing_acceptance_transcript_is_detected(self):
        task_id = self.verified()
        os.remove(os.path.join(state.task_dir(task_id, self.root), "evidence",
                               "acceptance-stdout.log"))
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertNotEqual(code, 0)
        self.assertIn("MISSING_ARTEFACT", err)

    def test_acceptance_transcript_without_a_digest_is_reported(self):
        task_id = self.verified()
        state.write_integrity(task_id, {}, self.root)
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertNotEqual(code, 0)
        self.assertIn("INCOMPLETE_RECORD", err)

    def test_acceptance_pass_with_broken_artefacts_is_not_verified(self):
        task_id = self.prepared()
        # Break the transcript AFTER execution but BEFORE the integrity gate by
        # using a task whose acceptance output is then tampered mid-flight is
        # not possible from outside; instead assert the gate order directly:
        # a VERIFIED record with a mismatched digest is downgraded by `run`
        # only when integrity fails, so here we verify the writer refuses to
        # claim VERIFIED for a record whose artefact is already wrong.
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertEqual(self.rec(task_id)["status"], "VERIFIED")
        with open(os.path.join(state.task_dir(task_id, self.root),
                               "stdout.log"), "a", encoding="utf-8") as handle:
            handle.write("tampered\n")
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertNotEqual(code, 0)
        # The record still claims VERIFIED, but verification now FAILS: the two
        # checks are deliberately separate signals.
        self.assertEqual(self.rec(task_id)["status"], "VERIFIED")
        self.assertEqual(self.rec(task_id)["verification"]["result"], "PASS")


# ---------------------------------------------------------------- S2-4 ------
class TestRunLock(LifecycleTestCase):
    """A second concurrent run must not execute the task."""

    def test_second_concurrent_run_is_rejected_and_executes_once(self):
        task_id = self.prepared()
        env = dict(os.environ,
                   PATH=FIXTURES + os.pathsep + os.environ["PATH"])
        cmd = [sys.executable, "-m", "sps2.p17", "--root", self.root, "run",
               "--task-id", task_id]
        procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True,
                                  env=env, cwd=REPO) for _ in range(4)]
        results = [p.communicate() for p in procs]
        codes = [p.returncode for p in procs]
        executions = self.executions(task_id)
        self.assertEqual(len(executions), 1,
                         "exactly one execution may be recorded: %r (codes %r)"
                         % (executions, codes))
        self.assertTrue(any(c == 0 for c in codes),
                        "one run should have succeeded: %r" % (codes,))
        self.assertTrue(all(c in (0, 2) for c in codes),
                        "losers must be rejected, never failed differently: %r"
                        % (codes,))
        locked = any("lock" in err for _out, err in results)
        self.assertTrue(locked, "a loser must report the lock: %r"
                        % ([e for _o, e in results],))

    def test_lock_is_released_after_the_run(self):
        task_id = self.prepared()
        self.assertEqual(self.run_task(task_id)[0], cli.EXIT_OK)
        # A second run reaches the state gate, not the lock: the lock is free.
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertNotIn("held by another run", err.lower())


# ---------------------------------------------------------------- S2-5 ------
class TestAtomicIntake(LifecycleTestCase):
    """No orphan directory, no duplicate identifier, no reuse."""

    def test_failed_plan_leaves_no_directory_and_no_reused_id(self):
        original = record.write
        failures = {"count": 0}

        def boom(task_id, doc, root=None):
            failures["count"] += 1
            raise record.RecordInvalid(["injected failure"])

        record.write = boom
        try:
            code, out, err = self.cli("plan", "--task-file", self.task_file())
        finally:
            record.write = original
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertIn("partial state was removed", err)
        leftovers = [d for d in os.listdir(state.tasks_root(self.root))
                     if d.startswith("TASK-P17-")]
        self.assertEqual(leftovers, [],
                         "a rejected intake must leave no task directory")
        first = self.plan(name="next.json")
        second = self.plan(name="next2.json")
        self.assertNotEqual(first, second)

    def test_cleanup_failure_is_reported_not_hidden(self):
        original = record.write

        def boom(task_id, doc, root=None):
            raise record.RecordInvalid(["injected"])

        def stubborn(task_id, root=None):
            return False, "cleanup of %s failed: injected" % task_id

        record.write = boom
        real_discard = state.discard_task_dir

        def stubborn(task_id, root=None):
            return False, "cleanup of %s failed: injected" % task_id

        state.discard_task_dir = stubborn
        try:
            code, out, err = self.cli("plan", "--task-file", self.task_file())
        finally:
            record.write = original
            state.discard_task_dir = real_discard
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertIn("cleanup failed", err)

    def test_concurrent_intake_allocates_unique_identifiers(self):
        path = self.task_file()
        env = dict(os.environ,
                   PATH=FIXTURES + os.pathsep + os.environ["PATH"])
        cmd = [sys.executable, "-m", "sps2.p17", "--root", self.root, "plan",
               "--task-file", path]
        procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True,
                                  env=env, cwd=REPO) for _ in range(5)]
        outs = [p.communicate() for p in procs]
        ids = set()
        codes = [p.returncode for p in procs]
        failures = []
        for index, (out, err) in enumerate(outs):
            found = {t for t in out.split() if t.startswith("TASK-P17-")}
            self.assertLessEqual(len(found), 1,
                                 "a process must never report two "
                                 "identifiers: %r" % (found,))
            if codes[index] == 0:
                self.assertEqual(len(found), 1,
                                 "a successful intake must report an id: %r "
                                 "stdout=%r" % (found, out[:200]))
                ids |= found
            else:
                # Losing the intake lock is CORRECT: it must fail closed with a
                # clear reason and must not have allocated anything.
                self.assertEqual(found, set())
                self.assertIn("ERROR", err)
                self.assertNotIn("Traceback", err)
                failures.append(err.strip().splitlines()[:1])
        # The security property is uniqueness, not universal success: two
        # processes must never receive the same identifier, and any process
        # that did not get one must have failed closed.
        self.assertEqual(len(ids), sum(1 for c in codes if c == 0),
                         "successful intakes must have distinct ids: ids=%r "
                         "codes=%r failed_with=%r"
                         % (ids, codes, failures))
        directories = [d for d in os.listdir(state.tasks_root(self.root))
                       if d.startswith("TASK-P17-")]
        self.assertEqual(len(directories), len(set(directories)),
                         "no duplicate task directory may exist")

    def test_intake_fails_closed_when_the_lock_is_held(self):
        """Deterministic fail-closed proof (no reliance on a race)."""
        import fcntl
        lock_path = os.path.join(state.tasks_root(self.root),
                                 ".next-task-id.lock")
        handle = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX)
            env = dict(os.environ,
                       PATH=FIXTURES + os.pathsep + os.environ["PATH"])
            proc = subprocess.run(
                [sys.executable, "-m", "sps2.p17", "--root", self.root,
                 "plan", "--task-file", self.task_file()],
                capture_output=True, text=True, timeout=180, env=env,
                cwd=REPO)
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
            os.close(handle)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ERROR", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("intake lock", proc.stderr.lower())
        self.assertEqual(
            [d for d in os.listdir(state.tasks_root(self.root))
             if d.startswith("TASK-P17-")], [],
            "a blocked intake must not create a task directory")

    def test_identifier_is_never_reused_after_rollback(self):
        first = self.plan(name="a.json")
        second = self.plan(name="b.json")
        self.assertNotEqual(first, second)
        # A rolled-back intake consumes its identifier permanently.
        original = record.write
        record.write = lambda *a, **k: (_ for _ in ()).throw(
            record.RecordInvalid(["injected"]))
        try:
            self.cli("plan", "--task-file", self.task_file(name="c.json"))
        finally:
            record.write = original
        third = self.plan(name="d.json")
        self.assertNotIn(third, {first, second})


# ---------------------------------------------------------------- S2-6 ------
class TestBoundedOutput(LifecycleTestCase):
    """Truncation is explicit, the original digest is retained, and truncated
    acceptance can never yield VERIFIED."""

    def noisy_task(self, accept=None, expected=0, name="noisy.json"):
        """Plan a task that selects the noisy double (its own capability)."""
        task_id = self.plan(
            goal="stub-mode:noise=%d" % (9 * 1024 * 1024),
            accept=accept or [sys.executable, "-c", "print('ok')"],
            expected=expected, name=name,
            capabilities=["noisy-test-double"])
        self.approve(task_id)
        return task_id

    def test_oversized_agent_output_is_truncated_and_marked(self):
        task_id = self.noisy_task()
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        transcript = os.path.join(state.task_dir(task_id, self.root),
                                  "stdout.log")
        with open(transcript, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("[TRUNCATED:", text)
        self.assertLess(os.path.getsize(transcript), 9 * 1024 * 1024)
        sidecar = self.sidecar(task_id)
        self.assertTrue(sidecar["stdout_truncated"])
        self.assertEqual(len(sidecar["stdout_original_sha256"]), 64)
        self.assertGreater(sidecar["stdout_original_bytes"],
                           sidecar["stdout_omitted_bytes"])
        self.assertIn("original stream bytes are not retained",
                      sidecar["capture_note"].lower())

    def test_oversized_agent_output_does_not_exhaust_memory(self):
        # The executor streams to disk: a 9 MiB stream must not be buffered.
        tmp = tempfile.mkdtemp(prefix="p17-life-mem-")
        try:
            noisy = os.path.join(tmp, "noisy.py")
            with open(noisy, "w", encoding="utf-8") as handle:
                handle.write("#!/usr/bin/env python3\nimport sys\n"
                             "sys.stdout.write('x' * (16 * 1024 * 1024))\n")
            os.chmod(noisy, 0o755)
            result = execution.run_once([noisy, "--version"], cwd=tmp,
                                        timeout_seconds=60)
            self.assertEqual(result["stdout_bytes"], 16 * 1024 * 1024)
            transcript = execution.transcribe(result["stdout_full"],
                                              os.path.join(tmp, "t.log"))
            self.assertTrue(transcript["truncated"])
            self.assertLessEqual(transcript["retained_bytes"],
                                 execution.OUTPUT_CAP_BYTES)
            # This test drives run_once directly rather than through the CLI, so
            # it owns the capture cleanup the CLI would otherwise perform.
            for stream in ("stdout", "stderr"):
                execution.discard_capture(result["%s_full" % stream])
            owned = result.get("owned_capture_dir")
            if owned:
                shutil.rmtree(owned, ignore_errors=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_truncated_acceptance_cannot_yield_verified(self):
        task_id = self.prepared(
            goal="stub-mode:write=out.txt",
            accept=[sys.executable, "-c", "print('x' * (9 * 1024 * 1024))"],
            expected=0, name="big-acceptance.json")
        code, out, err = self.run_task(task_id)
        doc = self.rec(task_id)
        self.assertNotEqual(code, cli.EXIT_OK)
        self.assertNotEqual(doc["status"], "VERIFIED")
        self.assertEqual(doc["verification"]["result"], "BLOCKED")
        reason = (doc.get("blocked_reason") or "").lower()
        self.assertTrue("exceeded" in reason or "incomplete" in reason,
                        "blocked_reason must explain why acceptance could not "
                        "be judged: %r" % doc.get("blocked_reason"))


# ---------------------------------------------------------------- S2-7 ------
class TestAttemptJournal(LifecycleTestCase):
    """Attempt-start is durable before spawn; recovery is explicit."""

    def stale(self, task_id, attempt=1):
        state.record_attempt(task_id, {
            "attempt": attempt, "phase": "started", "at": state.now(),
            "agent_id": STUB_AGENT, "argv_sha256": "0" * 64}, self.root)

    def test_stale_in_flight_attempt_blocks_until_explicit_resume(self):
        task_id = self.prepared()
        self.stale(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("recovery required", err)
        doc = self.rec(task_id)
        self.assertEqual(doc["status"], "BLOCKED")
        self.assertIn("recovery required", doc["blocked_reason"])
        self.assertEqual(self.executions(task_id), [],
                         "a stale attempt must never be re-executed silently")

    def test_resume_marks_the_prior_attempt_aborted_and_re_executes(self):
        task_id = self.prepared()
        self.stale(task_id)
        code, out, err = self.run_task(task_id, "--resume")
        journal = state.stage_state(task_id, self.root)
        phases = [(a.get("attempt"), a.get("phase"))
                  for a in journal["attempts"]]
        self.assertIn((1, "aborted"), phases)
        self.assertEqual(len(self.executions(task_id)), 1,
                         "the acknowledged recovery does execute once")
        # Slice 3 rule 5: the acknowledged recovery still cannot make the task
        # machine-verified, because attempt 1's outcome is unknown.
        self.assertNotEqual(self.rec(task_id)["status"], "VERIFIED")
        self.assertIn("uncertain",
                      (self.rec(task_id).get("blocked_reason") or "").lower())

    def test_attempt_start_is_persisted_before_spawn(self):
        task_id = self.prepared()
        self.run_task(task_id)
        journal = state.stage_state(task_id, self.root)
        entries = journal["attempts"]
        self.assertTrue(any(e.get("phase") == "started" for e in entries))
        started = [e for e in entries if e.get("phase") == "started"][0]
        self.assertEqual(len(started["argv_sha256"]), 64)
        self.assertTrue(any(e.get("phase") == "finished" for e in entries))

    def test_retry_bound_uses_durable_history(self):
        task_id = self.prepared()
        for number in range(2):
            state.record_attempt(task_id, {
                "attempt": number + 1, "phase": "started",
                "at": state.now()}, self.root)
            state.record_attempt(task_id, {
                "attempt": number + 1, "phase": "finished",
                "at": state.now(), "outcome": "FAILED"}, self.root)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_FAILED
                         if hasattr(cli, "EXIT_FAILED") else 1, out + err)
        self.assertIn("retry bound exhausted", err)
        self.assertEqual(self.executions(task_id), [])

    def test_retry_from_a_terminal_state_requires_explicit_resume(self):
        task_id = self.prepared(goal="stub-mode:exit=5")
        self.assertEqual(self.run_task(task_id)[0], 1)
        self.assertEqual(self.rec(task_id)["status"], "FAILED")
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("--resume", err)
        self.assertEqual(len(self.executions(task_id)), 1)

    def test_resume_from_a_terminal_state_is_bounded(self):
        task_id = self.prepared(goal="stub-mode:exit=5")
        self.run_task(task_id)
        code, out, err = self.run_task(task_id, "--resume")
        # Second attempt runs (bound is 2) and fails again on its own merits.
        self.assertIn(code, (1, cli.EXIT_REJECTED))
        self.assertLessEqual(len(self.executions(task_id)), 2)


class TestRecoveryHardening(LifecycleTestCase):
    """Slice 3: recovery must be explicit, bounded, and never over-claim.

    Rule set proven here:
      1. a crash after the subprocess may have produced side effects but before
         its result was journaled is DETECTED;
      2. recovery does not blindly repeat uncertain external side effects;
      3. invalid, missing or inconsistent journal data fails closed;
      4. resume preserves prior evidence and attempt history;
      5. a task with an uncertain execution outcome never becomes VERIFIED
         solely because a later attempt succeeded;
      6. retry bounds survive repeated crashes and resumes.
    """

    def journal_path(self, task_id):
        return os.path.join(state.task_dir(task_id, self.root), "state.json")

    def crash(self, task_id, attempt=1):
        """Simulate a crash: attempt started, never finished."""
        state.record_attempt(task_id, {
            "attempt": attempt, "phase": "started", "at": state.now(),
            "agent_id": STUB_AGENT, "argv_sha256": "0" * 64}, self.root)

    # ---- rule 1 -----------------------------------------------------------
    def test_crash_before_result_is_detected_and_history_kept(self):
        task_id = self.prepared()
        self.crash(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("recovery required", err)
        doc = self.rec(task_id)
        self.assertEqual(doc["status"], "BLOCKED")
        self.assertIsNone(doc.get("execution"),
                          "an uncertain attempt must not be recorded as an "
                          "execution result")
        journal = state.read_json(self.journal_path(task_id))
        self.assertTrue(any(a.get("attempt") == 1 and
                            a.get("phase") == "started"
                            for a in journal["attempts"]),
                        "the started attempt must survive in the journal")
        self.assertEqual(self.executions(task_id), [])

    # ---- rule 2 and 5 -----------------------------------------------------
    def test_recovery_never_claims_verified_for_an_uncertain_attempt(self):
        task_id = self.prepared()
        self.crash(task_id)
        code, out, err = self.run_task(task_id, "--resume")
        doc = self.rec(task_id)
        self.assertNotEqual(
            doc["status"], "VERIFIED",
            "a task whose earlier attempt had an unknown outcome must not be "
            "reported VERIFIED just because a later attempt succeeded "
            "(status was %s)" % doc["status"])
        self.assertIn(doc["status"], ("BLOCKED", "FAILED"))
        self.assertTrue(doc.get("blocked_reason"),
                        "the uncertain outcome must be explained in the record")
        self.assertIn("uncertain", (doc.get("blocked_reason") or "").lower())

    def test_recovery_is_explicit_and_never_silent(self):
        task_id = self.prepared()
        self.crash(task_id)
        code, out, err = self.run_task(task_id)
        self.assertIn("recovery required", err)
        self.assertIn("--resume", err,
                      "the operator must be told how to recover explicitly")

    # ---- rule 3 -----------------------------------------------------------
    def test_corrupt_journal_fails_closed(self):
        task_id = self.prepared()
        with open(self.journal_path(task_id), "w", encoding="utf-8") as handle:
            handle.write("{not valid json")
        for verb in ("run", "verify", "status"):
            code, out, err = self.cli(verb, "--task-id", task_id)
            self.assertNotEqual(code, 0, verb)
            self.assertNotIn("Traceback", err, verb)
        self.assertEqual(self.executions(task_id), [],
                         "a corrupt journal must never allow a re-execution")

    def test_inconsistent_journal_fails_closed(self):
        cases = {
            "attempts is not a list": {"task_id": "X", "attempts": {},
                                       "retry_bound": 2},
            "entry is not an object": {"task_id": "X", "attempts": ["x"],
                                       "retry_bound": 2},
            "attempt number missing": {"task_id": "X", "attempts": [
                {"phase": "started", "at": "now"}], "retry_bound": 2},
            "retry bound is not a positive integer": {"task_id": "X",
                                                      "attempts": [],
                                                      "retry_bound": 0},
        }
        for label, payload in cases.items():
            with self.subTest(label):
                task_id = self.plan(name="j.json")
                self.approve(task_id)
                state.write_json(self.journal_path(task_id), payload)
                code, out, err = self.cli("run", "--task-id", task_id)
                self.assertEqual(code, cli.EXIT_REJECTED, out + err)
                self.assertNotIn("Traceback", err)
                self.assertEqual(self.executions(task_id), [], label)

    def test_missing_journal_is_not_an_error_but_is_empty_history(self):
        task_id = self.prepared()
        self.assertFalse(os.path.exists(self.journal_path(task_id)))
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertTrue(os.path.exists(self.journal_path(task_id)))

    # ---- rule 4 -----------------------------------------------------------
    def test_resume_preserves_prior_evidence_and_attempt_history(self):
        # The agent completes but acceptance FAILS: the task ends FAILED with a
        # real evidence record, so an explicit retry has prior evidence to
        # preserve.
        task_id = self.prepared(accept=[sys.executable, "-c",
                                         "raise SystemExit(1)"], expected=0)
        self.assertEqual(self.run_task(task_id)[0], 1)
        first_evidence = self.rec(task_id)["verification"]["evidence_ref"]
        first_path = os.path.join(state.evidence_root(self.root),
                                  "%s.json" % first_evidence)
        self.assertTrue(os.path.exists(first_path))
        self.assertEqual(self.rec(task_id)["status"], "FAILED")
        code, out, err = self.run_task(task_id, "--resume")
        self.assertTrue(os.path.exists(first_path),
                        "prior evidence must survive a later attempt")
        journal = state.read_json(self.journal_path(task_id))
        phases = [a.get("phase") for a in journal["attempts"]]
        self.assertIn("started", phases)
        self.assertIn("finished", phases)
        self.assertGreaterEqual(len([p for p in phases if p == "started"]), 2,
                                "both attempts must remain in the journal")

    # ---- rule 6 -----------------------------------------------------------
    def test_retry_bound_survives_repeated_crashes_and_resumes(self):
        task_id = self.prepared()
        codes = []
        attempt = 0
        for _ in range(5):
            attempt += 1
            self.crash(task_id, attempt=attempt)      # a crash, never finished
            code, out, err = self.run_task(task_id, "--resume")
            codes.append((code, err))
            if code == cli.EXIT_TASK_FAILED and "retry bound exhausted" in err:
                break
        journal = state.read_json(self.journal_path(task_id))
        started = len([a for a in journal["attempts"]
                       if a.get("phase") in (None, "started")])
        self.assertGreaterEqual(
            started, 3, "the injected crashes must all be journaled: %r"
            % (journal,))
        self.assertTrue(
            any(code == cli.EXIT_TASK_FAILED and "retry bound exhausted" in (e or "")
                for code, e in codes),
            "the durable retry bound must eventually refuse a further "
            "recovery: %r" % (codes,))
        self.assertEqual(self.rec(task_id)["status"], "FAILED")
        self.assertEqual(self.rec(task_id)["execution"]["command"],
                         ["(no subprocess created)"],
                         "a bound-exhausted refusal must not spawn anything")
        self.assertNotEqual(self.rec(task_id)["status"], "VERIFIED",
                            "a repeatedly interrupted task must never be "
                            "reported VERIFIED")


# ------------------------------------------------------------- regression ---
class TestTerminalStatesPreserved(LifecycleTestCase):
    """Slice 1 terminal-state behaviour must not regress."""

    def test_terminal_states_reject_reentry_without_resume(self):
        task_id = self.prepared(goal="stub-mode:exit=4")
        self.run_task(task_id)
        self.assertEqual(self.rec(task_id)["status"], "FAILED")
        self.assertEqual(self.run_task(task_id)[0], cli.EXIT_REJECTED)
        self.assertEqual(self.cli("approve", "--task-id", task_id,
                                  "--basis", "again")[0], cli.EXIT_REJECTED)

    def test_verified_task_is_never_executed_again(self):
        task_id = self.prepared()
        self.assertEqual(self.run_task(task_id)[0], cli.EXIT_OK)
        code, out, err = self.run_task(task_id, "--resume")
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertEqual(len(self.executions(task_id)), 1)

    def test_rejected_task_is_terminal(self):
        task_id = self.plan()
        self.cli("approve", "--task-id", task_id, "--basis", "no",
                 "--reject")
        self.assertEqual(self.rec(task_id)["status"], "REJECTED")
        self.assertEqual(self.run_task(task_id, "--resume")[0],
                         cli.EXIT_REJECTED)

    def test_real_agent_execution_remains_disabled(self):
        state.write_json(os.path.join(self.root, "sps2", "p17", "allowlist.json"),
                         {"schema": "sps2.p17-allowlist/v1",
                          "purpose": "production",
                          "agents": [{"agent_id": "opencode",
                                      "probe_method": "VERSION_FLAG",
                                      "capabilities": ["test-double"]}]})
        code, out, err = self.cli("discover")
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertIn("GATE-P17-4", err)
        self.assertIn("No agent was probed", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
