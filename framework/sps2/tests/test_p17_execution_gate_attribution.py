"""P17 execution-gate approval-attribution tests (PROPOSED, NOT YET APPLIED).

GATE-P17-3 requires "Explicit User approval of that specific task execution"
with evidence "approval record in the task record (approval.state = APPROVED,
decided_by_role = USER)" (framework/sps2/requirements/P17-REQUIREMENTS.json:469-478).

The gate at framework/sps2/p17/__main__.py:379-380 enforced only `state` and
`decided_by_role`. Both are written BY THE REQUESTING PARTY into an unsigned
sidecar, so a sidecar declaring

    {"state": "APPROVED", "decided_by_role": "USER",
     "decided_by": "Self (self-approved)"}

satisfied the gate. D-P17-3 reserves approval gates to the User and states that
"any change to an approved requirement, schema, decision record, or protected
file" is NOT delegated, so tightening this gate is a User decision.

These tests execute the REAL CLI in-process via the same harness the existing
P17 security suite uses. They do not re-implement the gate as a standalone
predicate, so they cannot pass while the real gate behaves differently.

Proposed alongside the gate change. Not yet registered in any runner.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)

from framework.sps2.p17 import state  # noqa: E402
from framework.sps2.p17 import __main__ as cli  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures", "p17")
STUB_AGENT = "stub-agent.py"

# Forms that must be REJECTED even though decided_by_role is USER.
SELF_ATTRIBUTED = [
    "Self (self-approved)",
    "Self-approved",
    "Self",
    "self",
    "user",
    "USER",
    "the user",
    "Assistant",
    "Claude",
    "",
    # Near-miss forms that a lenient predicate would wrongly accept.
    "User ",          # trailing space
    " User",          # leading space
    "\u00a0User",     # non-breaking space
    "User\u200b",     # zero-width space
    "\uff35ser",      # fullwidth U
    "User\n",         # trailing newline
    # Non-string types must not raise.
    0, 1, None, [], {}, ["User"],
]


def cli_run(*argv):
    """Invoke the CLI in-process; return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class GateHarness(unittest.TestCase):
    """Isolated project root per test, mirroring test_p17_security.py."""

    PURPOSE = "test"
    AGENTS = (
        {"agent_id": STUB_AGENT, "probe_method": "VERSION_FLAG",
         "capabilities": ["test-double", "repository-state-reading",
                          "markdown", "json"]},
    )

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p17-gate-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp
        state.ensure_dirs(self.root)
        self.write_allowlist(self.PURPOSE, self.AGENTS)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = FIXTURES + os.pathsep + old_path

        def restore():
            os.environ["PATH"] = old_path
        self.addCleanup(restore)

    def write_allowlist(self, purpose, agents, name="allowlist.json"):
        path = os.path.join(self.root, "framework", "sps2", "p17", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"schema": "sps2.p17-allowlist/v1", "purpose": purpose,
                       "trusted_roots": [FIXTURES], "agents": list(agents)}, fh)
        return path

    def cli(self, *argv):
        return cli_run("--root", self.root, *argv)

    def default_task(self, **overrides):
        task = {
            "goal": "stub-mode:write=output.txt",
            "required_capabilities": ["test-double"],
            "acceptance": {
                "command": [sys.executable, "-c", "print('acceptance ok')"],
                "expected_exit_status": 0,
            },
            "timeout_seconds": 30,
        }
        task.update(overrides)
        return task

    def plan_task(self):
        """Create a task and return its generated id."""
        path = os.path.join(self.root, "task.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.default_task(), fh)
        code, out, err = self.cli("plan", "--task-file", path)
        self.assertEqual(code, 0, "plan failed: %s%s" % (out, err))
        for token in out.split():
            if token.startswith("TASK-P17-"):
                return token
        self.fail("no task id in plan output: %s" % out)

    def write_approval(self, task_id, decided_by, role="USER",
                       status="APPROVED"):
        sidecar = os.path.join(state.task_dir(task_id, self.root),
                               "approval.json")
        with open(sidecar, "w", encoding="utf-8") as fh:
            json.dump({"state": status, "decided_by": decided_by,
                       "decided_by_role": role, "decided_at": state.today(),
                       "basis": "gate attribution test"}, fh)
        return sidecar

    def approve(self, task_id, basis="User approved this test task."):
        """Use the CLI's own approve command so digests are bound correctly."""
        code, out, err = self.cli("approve", "--task-id", task_id,
                                  "--basis", basis)
        self.assertEqual(code, 0, "approve failed: %s%s" % (out, err))
        return task_id

    def tamper_decided_by(self, task_id, decided_by, role=None, status=None):
        """Rewrite ONLY the attribution fields of a properly bound approval.

        This models the real attack: a valid, digest-bound approval whose
        decider is self-asserted rather than the User.
        """
        sidecar = os.path.join(state.task_dir(task_id, self.root),
                               "approval.json")
        with open(sidecar, encoding="utf-8") as fh:
            data = json.load(fh)
        data["decided_by"] = decided_by
        if role is not None:
            data["decided_by_role"] = role
        if status is not None:
            data["state"] = status
        with open(sidecar, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return data

    def run_task(self, task_id):
        return self.cli("run", "--task-id", task_id)

    def artifacts(self, task_id):
        d = state.task_dir(task_id, self.root)
        return [n for n in ("stdout.log", "stderr.log", "evidence")
                if os.path.exists(os.path.join(d, n))]


class TestExecutionGateRequiresExactUser(GateHarness):
    """The gate must require decided_by to be exactly 'User'."""

    def test_self_attributed_user_role_is_rejected(self):
        """decided_by_role=USER must not be sufficient by itself.

        This is the control the suite lacks: existing gate tests vary role or
        state, never decided_by while the role stays USER.
        """
        for who in SELF_ATTRIBUTED:
            with self.subTest(decided_by=who):
                root = tempfile.mkdtemp(prefix="p17-gate-sub-")
                self.addCleanup(shutil.rmtree, root, ignore_errors=True)
                outer, self.root = self.root, root
                try:
                    state.ensure_dirs(self.root)
                    self.write_allowlist(self.PURPOSE, self.AGENTS)
                    task_id = self.plan_task()
                    self.approve(task_id)
                    self.tamper_decided_by(task_id, who)
                    code, out, err = self.run_task(task_id)
                    arts = self.artifacts(task_id)
                finally:
                    self.root = outer
                self.assertNotEqual(
                    code, 0,
                    "decided_by=%r satisfied GATE-P17-3 and was NOT rejected"
                    % who)
                self.assertFalse(
                    arts, "decided_by=%r produced artifacts %s" % (who, arts))

    def test_exact_user_is_accepted(self):
        """A genuine User approval must still reach execution."""
        task_id = self.plan_task()
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, 0, "exact 'User' approval refused: %s%s"
                         % (out, err))

    def test_wrong_role_is_rejected(self):
        """decided_by=User with role AGENT must still be rejected."""
        task_id = self.plan_task()
        self.approve(task_id)
        self.tamper_decided_by(task_id, "User", role="AGENT")
        code, _, _ = self.run_task(task_id)
        self.assertNotEqual(code, 0)

    def test_wrong_state_is_rejected(self):
        """decided_by=User with a non-APPROVED state must be rejected."""
        task_id = self.plan_task()
        self.approve(task_id)
        self.tamper_decided_by(task_id, "User", status="PENDING")
        code, _, _ = self.run_task(task_id)
        self.assertNotEqual(code, 0)

    def test_missing_approval_is_rejected(self):
        """No sidecar at all must be rejected."""
        task_id = self.plan_task()
        code, _, _ = self.run_task(task_id)
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
