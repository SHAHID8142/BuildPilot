#!/usr/bin/env python3
"""SPS 2.0 P17 Slice 1 end-to-end demonstration.

Drives the complete Task Runner lifecycle - intake, ordered plan, runtime
discovery, deterministic selection, bounded test-double execution, independent
objective verification, status and evidence with integrity digests.

TEST ISOLATION: the lifecycle runs against a dedicated TEMPORARY project root
that is removed on completion. Every task record, plan, transcript, evidence
record, usage-log entry and enablement state the suite produces stays inside
that temporary root. The suite reads the implementation, schema and test
doubles from the repository, and must never write to real repository state.

REPOSITORY-LOCAL TEST DOUBLES ONLY. No real agent CLI is invoked. Real-agent
execution is disabled by default and GATE-P17-4 is OPEN; this demonstration
proves the PIPELINE, not real-agent isolation, and it never claims to.

Conformance is checked twice: structurally at runtime by the implementation's
own self-check, and against the approved Draft 2020-12 schema with the ambient
ajv when it is available (skipped with a stated reason when it is not).

Standard library unittest only; no dependency.
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

from sps2.p17 import record, state, __main__ as cli  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures", "p17")
TEST_ALLOWLIST = os.path.join(FIXTURES, "test-allowlist.json")
SCHEMA = os.path.join(REPO, "sps2", "schemas", "p17-task-record.schema.json")
# The ajv tool location is opt-in and supplied by the operator. It is NOT
# hardcoded here: the project-local boundary rule (isolation validator) forbids
# machine-global path literals inside sps2/. When it is not supplied the full
# schema validation SKIPs with a stated reason, per GOVERNANCE.md section 4.
AJV_ROOT = os.environ.get("P17_AJV_ROOT")


def cli_run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestSlice1EndToEnd(unittest.TestCase):
    """One full lifecycle, asserted at every stage, in an isolated root."""

    def repo_state_signature(self):
        """Signature of the REAL repository's P17 state (read-only).

        Used only to prove the suite leaves real repository state untouched.
        """
        tasks = state.tasks_root(REPO)
        evidence = state.evidence_root(REPO)
        usage = os.path.join(REPO, ".sps", "tasks", "p17", "usage.log")
        return (
            sorted(os.listdir(tasks)) if os.path.isdir(tasks) else [],
            sorted(os.listdir(evidence)) if os.path.isdir(evidence) else [],
            os.path.getsize(usage) if os.path.exists(usage) else None,
        )

    def _assert_repo_untouched(self):
        after = self.repo_state_signature()
        if after != self.repo_before:
            self.fail("TEST ISOLATION VIOLATION: the suite modified real "
                      "repository P17 state (%r -> %r)"
                      % (self.repo_before, after))

    def setUp(self):
        # Registered FIRST so it runs LAST, after every other cleanup.
        self.repo_before = self.repo_state_signature()
        self.addCleanup(self._assert_repo_untouched)
        # TEST ISOLATION. Every artefact this suite produces - task records,
        # plans, transcripts, verification evidence, usage-log entries and the
        # real-agent enablement state - is written inside a dedicated temporary
        # root and removed afterwards. The suite reads from the repository
        # (implementation, schema, test doubles) but must never write to it.
        self.root = tempfile.mkdtemp(prefix="p17-e2e-root-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        state.ensure_dirs(self.root)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = FIXTURES + os.pathsep + old_path

        def restore():
            os.environ["PATH"] = old_path
        self.addCleanup(restore)
        task_dir = tempfile.mkdtemp(prefix="p17-e2e-")
        self.addCleanup(shutil.rmtree, task_dir, ignore_errors=True)
        self.task_file = os.path.join(task_dir, "task.json")
        payload = {
            "goal": "stub-mode:write=demonstration-output.txt",
            "required_capabilities": ["test-double"],
            "acceptance": {
                "command": [sys.executable, "-c",
                            "print('acceptance: objective command satisfied')"],
                "expected_exit_status": 0,
            },
            "timeout_seconds": 60,
        }
        with open(self.task_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        self.task_id = None

    def test_full_lifecycle_produces_verified_record_and_evidence(self):
        # 1. plan
        code, out, err = cli_run("--root", self.root, "plan",
                                 "--task-file", self.task_file,
                                 "--allowlist", TEST_ALLOWLIST)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertIn("AWAITING_USER_APPROVAL", out)
        for token in out.split():
            if token.startswith("TASK-P17-"):
                self.task_id = token
        self.assertIsNotNone(self.task_id, out)

        # 2. the record is schema-shaped and awaiting approval
        doc = record.load(self.task_id, self.root)
        self.assertEqual(record.violations(doc), [])
        self.assertIsNone(doc.get("execution"))
        self.assertIsNone(doc.get("verification"))
        self.assertIsNone(doc.get("approval"))
        self.assertEqual(doc["status"], "AWAITING_USER_APPROVAL")
        self.assertEqual(doc["agent_selection"]["selected_agent"],
                         "stub-agent.py")
        self.assertEqual(len(doc["agent_selection"]["selection_fingerprint"]),
                         64)

        # 3. run without approval must be refused (fail closed)
        code, out, err = cli_run("--root", self.root, "run",
                                 "--task-id", self.task_id,
                                 "--allowlist", TEST_ALLOWLIST)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("no recorded User approval", err)

        # 4. explicit approval
        code, out, err = cli_run(
            "--root", self.root, "approve", "--task-id", self.task_id,
            "--basis", "Slice 1 end-to-end demonstration: the User-approved "
                       "test-double task may execute.")
        self.assertEqual(code, cli.EXIT_OK, out + err)

        # 5. run
        code, out, err = cli_run("--root", self.root, "run",
                                 "--task-id", self.task_id,
                                 "--allowlist", TEST_ALLOWLIST)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertIn("COMPLETED exit_status=0", out)
        self.assertIn("acceptance PASS", out)

        # 6. the recorded outcome is genuinely complete
        doc = record.load(self.task_id, self.root)
        self.assertEqual(record.violations(doc), [])
        self.assertEqual(doc["status"], "VERIFIED")
        self.assertEqual(doc["execution"]["outcome"], "COMPLETED")
        self.assertEqual(doc["execution"]["exit_status"], 0)
        self.assertEqual(doc["execution"]["environment_policy"],
                         "EXPLICIT_ALLOWLIST")
        self.assertEqual(doc["verification"]["result"], "PASS")
        self.assertEqual(doc["verification"]["verifier"], "OBJECTIVE_COMMAND")
        self.assertEqual(doc["approval"]["decided_by_role"], "USER")
        self.assertEqual(doc["approval"]["state"], "APPROVED")
        for key in ("plan_sha256", "stdout_sha256", "stderr_sha256",
                    "evidence_sha256"):
            self.assertEqual(len(doc["digests"][key]), 64, key)

        # 7. evidence record written with the governance fields
        evidence_id = doc["verification"]["evidence_ref"]
        evidence_path = os.path.join(state.evidence_root(self.root),
                                     "%s.json" % evidence_id)
        self.assertTrue(os.path.exists(evidence_path), evidence_path)
        evidence = state.read_json(evidence_path)
        self.assertEqual(evidence["task"], self.task_id)
        self.assertEqual(evidence["result"], "PASS")
        self.assertIn("does not establish real-agent isolation", evidence["note"])

        # 8. the double actually worked in its own workspace
        workspace = os.path.join(state.task_dir(self.task_id, self.root),
                                 "workspace")
        self.assertTrue(os.path.exists(os.path.join(
            workspace, "demonstration-output.txt")))

        # 9. integrity verification is clean, and the CLI agrees
        code, out, err = cli_run("--root", self.root, "verify",
                                 "--task-id", self.task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertIn("no findings", out)

        code, out, err = cli_run("--root", self.root, "status",
                                 "--task-id", self.task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertIn("VERIFIED", out)
        self.assertIn("real-agent execution is disabled", out)

        # 10. real-agent execution is still disabled after a successful run
        enablement = state.real_agent_enablement(self.root)
        self.assertFalse(enablement["enabled"])
        self.assertEqual(enablement["gate"], "GATE-P17-4")

    def test_generated_record_conforms_to_the_approved_schema(self):
        """Full Draft 2020-12 validation with the ambient ajv, or SKIP."""
        if not AJV_ROOT:
            self.skipTest(
                "P17_AJV_ROOT is not set, so the ambient ajv cannot be located. "
                "This machine-global path is deliberately not hardcoded: the "
                "project-local boundary rule forbids it inside sps2/. The "
                "runtime structural self-check (record.violations) still ran in "
                "test_full_lifecycle_produces_verified_record_and_evidence.")
        ajv = os.path.join(AJV_ROOT, "ajv", "dist", "2020.js")
        ajv_formats = os.path.join(AJV_ROOT, "ajv-formats", "dist", "index.js")
        if not (os.path.exists(ajv) and os.path.exists(ajv_formats)):
            self.skipTest("ajv not found under P17_AJV_ROOT=%s" % AJV_ROOT)
        if shutil.which("node") is None:
            self.skipTest("node is not available; full schema validation cannot "
                          "run here. The runtime structural self-check still "
                          "ran in test_full_lifecycle.")
        code, out, err = cli_run("--root", self.root, "plan",
                                 "--task-file", self.task_file,
                                 "--allowlist", TEST_ALLOWLIST)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        task_id = [t for t in out.split() if t.startswith("TASK-P17-")][0]
        cli_run("--root", self.root, "approve", "--task-id", task_id,
                "--basis", "Schema conformance demonstration (User-approved "
                           "test-double task).")
        code, out, err = cli_run("--root", self.root, "run", "--task-id",
                                 task_id, "--allowlist", TEST_ALLOWLIST)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        record_path = os.path.join(state.task_dir(task_id, self.root),
                                   "record.json")

        script = (
            "import Ajv2020 from '%s';"
            "import addFormats from '%s';"
            "import {readFileSync} from 'node:fs';"
            "const ajv=new Ajv2020({strict:true,allErrors:true});"
            "addFormats(ajv);"
            "const validate=ajv.compile(JSON.parse(readFileSync('%s','utf8')));"
            "const doc=JSON.parse(readFileSync('%s','utf8'));"
            "if(validate(doc)){console.log('CONFORMS');process.exit(0);}"
            "console.log('VIOLATIONS '+ajv.errorsText(validate.errors));"
            "process.exit(1);" % (ajv, ajv_formats, SCHEMA, record_path))
        result = subprocess.run(["node", "--input-type=module", "-e", script],
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0,
                         "schema validation failed: %s%s"
                         % (result.stdout, result.stderr))
        self.assertIn("CONFORMS", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
