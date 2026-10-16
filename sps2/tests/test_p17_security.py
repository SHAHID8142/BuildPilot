#!/usr/bin/env python3
"""SPS 2.0 P17 Slice 1 negative security suite.

Covers the security test matrix of the approved plan (.sps/plan.md, section
13): SEC-P17-01..11 plus the mandated cases (invalid task rejection,
deterministic selection, timeout and process termination, non-zero execution
status, acceptance-command failure, execution/verification separation,
evidence schema validity and digest verification, corrupted or incomplete
evidence, disabled real-agent execution rejection, and fail-closed behaviour
when required authorisation is missing).

REPOSITORY-LOCAL TEST DOUBLES ONLY. No real agent CLI (opencode, claude,
codex, copilot or any other) is invoked by any test in this file. Real-agent
execution is disabled by default and GATE-P17-4 is OPEN.

Every test runs against an isolated temporary project root, so no test writes
into the real repository's project-local state.

Standard library unittest only; no dependency.
"""
import ast
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from sps2.p17 import (  # noqa: E402
    confinement, discovery, execution, intake, plan as plan_mod, record,
    scrub, selection as selection_mod, state, __main__ as cli)

FIXTURES = os.path.join(HERE, "fixtures", "p17")
STUB_AGENT = "stub-agent.py"
STUB_SLOW = "stub-slow.py"

# Executables that would mean a network listener or outbound request.
FORBIDDEN_IMPORTS = ("socket", "http", "urllib", "ftplib", "smtplib",
                      "telnetlib", "asyncio", "ssl", "xmlrpc", "webbrowser")
# The rotation / quota-evasion vocabulary that must not exist anywhere.
FORBIDDEN_VOCABULARY = ("rotate", "rotation", "account_pool", "quota_bypass",
                        "proxy_account", "switch_account", "ban_evad")


def cli_run(*argv):
    """Invoke the CLI in-process; return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class P17TestCase(unittest.TestCase):
    """Isolated project root per test, with a test-purpose allowlist."""

    PURPOSE = "test"
    AGENTS = (
        {"agent_id": STUB_AGENT, "probe_method": "VERSION_FLAG",
         "capabilities": ["test-double", "repository-state-reading",
                          "markdown", "json"]},
        {"agent_id": STUB_SLOW, "probe_method": "VERSION_FLAG",
         "capabilities": ["slow-test-double"]},
    )

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p17-sec-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp
        state.ensure_dirs(self.root)
        self.allowlist = self.write_allowlist(self.PURPOSE, self.AGENTS)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = FIXTURES + os.pathsep + old_path

        def restore():
            os.environ["PATH"] = old_path
        self.addCleanup(restore)

    def write_allowlist(self, purpose, agents, name="allowlist.json"):
        path = os.path.join(self.root, "sps2", "p17", name)
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        payload = {"schema": "sps2.p17-allowlist/v1", "purpose": purpose,
                   "trusted_roots": [FIXTURES],
                   "agents": list(agents)}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return path

    def task_file(self, payload, name="task.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as handle:
            if isinstance(payload, str):
                handle.write(payload)
            else:
                json.dump(payload, handle, indent=2)
        return path

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

    def cli(self, *argv):
        return cli_run("--root", self.root, *argv)

    def plan_task(self, payload=None, name="task.json"):
        path = self.task_file(payload if payload is not None
                              else self.default_task(), name)
        code, out, err = self.cli("plan", "--task-file", path)
        self.assertEqual(code, 0, "plan failed: %s%s" % (out, err))
        for token in out.split():
            if token.startswith("TASK-P17-"):
                return token
        self.fail("no task id in plan output: %s" % out)

    def approve(self, task_id, basis="User approved this test task explicitly."):
        code, out, err = self.cli("approve", "--task-id", task_id,
                                  "--basis", basis)
        self.assertEqual(code, 0, "approve failed: %s%s" % (out, err))
        return task_id

    def run_task(self, task_id, *extra):
        return self.cli("run", "--task-id", task_id, *extra)

    def record_of(self, task_id):
        return record.load(task_id, self.root)


# ---------------------------------------------------------------------------
# SEC-P17-01  local-only execution
# ---------------------------------------------------------------------------
class TestLocalOnly(P17TestCase):
    """SEC-P17-01: no network capability and no deployment path exists."""

    def modules(self):
        directory = os.path.join(REPO, "sps2", "p17")
        return [os.path.join(directory, name)
                for name in sorted(os.listdir(directory))
                if name.endswith(".py")]

    def test_no_network_or_deployment_imports(self):
        offenders = []
        for path in self.modules():
            with open(path, "r", encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for name in names:
                    if name in FORBIDDEN_IMPORTS:
                        offenders.append("%s imports %s" % (path, name))
        self.assertEqual(offenders, [],
                         "network/deployment imports present: %s" % offenders)

    def test_no_listener_or_publish_entry_point(self):
        offenders = []
        for path in self.modules():
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            for needle in ("socketserver", "http.server", "uvicorn",
                           "flask", "django", "listen(", "bind(",
                           "deploy(", "publish("):
                if needle in text:
                    offenders.append("%s references %r" % (path, needle))
        self.assertEqual(offenders, [], offenders)

    def test_cli_exposes_no_server_or_deploy_command(self):
        parser = cli.build_parser()
        subcommands = set()
        for action in parser._actions:
            if hasattr(action, "choices") and action.choices:
                subcommands |= set(action.choices.keys())
        self.assertEqual(subcommands, {"plan", "approve", "run", "verify",
                                       "status", "discover"})


# ---------------------------------------------------------------------------
# SEC-P17-02  authorised executables
# ---------------------------------------------------------------------------
class TestAuthorisedExecutables(P17TestCase):
    """SEC-P17-02: only allowlisted executables, availability never assumed."""

    def test_documented_but_absent_tool_is_reported_unavailable(self):
        absent = {"agent_id": "definitely-not-installed-p17-xyz",
                  "probe_method": "VERSION_FLAG",
                  "capabilities": ["test-double"]}
        self.write_allowlist("test", (absent,) + self.AGENTS)
        allowlist = discovery.load_allowlist(self.root)
        snapshot = discovery.discover(allowlist, cwd=self.root, root=self.root)
        probed = {a["agent_id"]: a for a in snapshot["agents"]}
        self.assertFalse(probed["definitely-not-installed-p17-xyz"]["available"])
        self.assertIn("PATH", probed["definitely-not-installed-p17-xyz"]["note"])

    def test_absent_only_allowlist_blocks_selection_fail_closed(self):
        absent = {"agent_id": "definitely-not-installed-p17-xyz",
                  "probe_method": "VERSION_FLAG",
                  "capabilities": ["test-double"]}
        self.write_allowlist("test", (absent,))
        path = self.task_file(self.default_task())
        code, out, err = self.cli("plan", "--task-file", path)
        # Fail closed at intake-to-plan: nothing can be planned for execution
        # when no allowlisted executable is available at runtime.
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("no available agent", err.lower())
        self.assertEqual(
            [d for d in os.listdir(state.tasks_root(self.root))
             if d.startswith("TASK-P17-")], [])

    def test_run_time_selection_failure_records_blocked(self):
        # Plan while the double IS available, then remove it from the
        # allowlist before the run: the run must fail closed and record
        # BLOCKED, not silently proceed.
        task_id = self.plan_task()
        self.approve(task_id)
        absent = {"agent_id": "definitely-not-installed-p17-xyz",
                  "probe_method": "VERSION_FLAG",
                  "capabilities": ["test-double"]}
        self.write_allowlist("test", (absent,))
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("no eligible agent", err.lower())
        doc = self.record_of(task_id)
        self.assertEqual(doc["status"], "BLOCKED")
        # No execution block at all: nothing ran, so nothing is recorded as run.
        self.assertIsNone(doc.get("execution"))
        self.assertIsNone(doc["agent_selection"]["selected_agent"])

    def test_executable_outside_the_allowlist_can_never_be_selected(self):
        # A capable executable exists on PATH but is not in the allowlist, and
        # no allowlisted agent declares the required capability.
        shutil.copy(os.path.join(FIXTURES, STUB_AGENT),
                    os.path.join(self.tmp, "unlisted-agent.py"))
        os.chmod(os.path.join(self.tmp, "unlisted-agent.py"), 0o755)
        os.environ["PATH"] = self.tmp + os.pathsep + os.environ["PATH"]
        task = self.default_task()
        task["required_capabilities"] = ["never-declared-capability"]
        path = self.task_file(task)
        code, out, err = self.cli("plan", "--task-file", path)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("no available agent", err.lower())
        self.assertNotIn("unlisted-agent", out + err)

    def test_probe_command_is_restricted_to_a_version_or_help_flag(self):
        bad = {"agent_id": STUB_AGENT, "probe_method": "RUNTIME_PROBE",
               "capabilities": ["test-double"]}
        self.write_allowlist("test", (bad,))
        allowlist = discovery.load_allowlist(self.root)
        with self.assertRaises(discovery.DiscoveryError):
            discovery.discover(allowlist, cwd=self.root, root=self.root)

    def test_probe_argv_cannot_smuggle_extra_arguments(self):
        bad = {"agent_id": STUB_AGENT, "probe_method": "VERSION_FLAG",
               "probe_argv": ["--version", "--dangerous-flag"],
               "capabilities": ["test-double"]}
        self.write_allowlist("test", (bad,))
        allowlist = discovery.load_allowlist(self.root)
        with self.assertRaises(discovery.DiscoveryError):
            discovery.discover(allowlist, cwd=self.root, root=self.root)


# ---------------------------------------------------------------------------
# SEC-P17-03  provider compliance
# ---------------------------------------------------------------------------
class TestProviderCompliance(P17TestCase):
    """SEC-P17-03: no account rotation and no quota-circumvention mechanism."""

    def test_no_rotation_or_evasion_vocabulary_in_the_implementation(self):
        directory = os.path.join(REPO, "sps2", "p17")
        offenders = []
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(directory, name)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read().lower()
            for needle in FORBIDDEN_VOCABULARY:
                if needle in text:
                    offenders.append("%s mentions %r" % (name, needle))
        self.assertEqual(offenders, [],
                         "provider-circumvention vocabulary present: %s"
                         % offenders)

    def test_allowlist_schema_has_no_account_or_credential_fields(self):
        allowlist = discovery.load_allowlist(self.root)
        for entry in allowlist["agents"]:
            for forbidden in ("account", "accounts", "credential",
                              "credentials", "token", "api_key", "password",
                              "proxy"):
                self.assertNotIn(forbidden, entry,
                                 "allowlist entry carries %r" % forbidden)

    def test_a_simulated_provider_limit_is_recorded_not_evaded(self):
        task = self.default_task(
            goal="stub-mode:exit=9",
            acceptance={"command": [sys.executable, "-c", "raise SystemExit(0)"],
                        "expected_exit_status": 0})
        task_id = self.plan_task(task)
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        # The double exits 9: recorded verbatim as a failure, never retried into
        # a pass, and no second agent is tried.
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        doc = self.record_of(task_id)
        self.assertEqual(doc["execution"]["exit_status"], 9)
        self.assertEqual(doc["execution"]["outcome"], "FAILED")
        self.assertEqual(doc["status"], "FAILED")


# ---------------------------------------------------------------------------
# SEC-P17-04  process control
# ---------------------------------------------------------------------------
class TestProcessControl(P17TestCase):
    """SEC-P17-04: bounded timeout and real process-tree termination."""

    def test_timeout_terminates_the_process_tree(self):
        task = self.default_task(
            goal="stub-mode:sleep=300",
            required_capabilities=["slow-test-double"],
            timeout_seconds=2)
        task_id = self.plan_task(task)
        self.approve(task_id)
        started = time.time()
        code, out, err = self.run_task(task_id)
        elapsed = time.time() - started
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        doc = self.record_of(task_id)
        self.assertEqual(doc["execution"]["outcome"], "TIMEOUT")
        self.assertIsNone(doc["execution"]["exit_status"])
        self.assertIn("TIMEOUT", out)
        self.assertLess(elapsed, 60,
                        "bounded timeout did not bound the execution")
        # The grandchild the double spawned must not survive: the whole
        # process group is signalled, not just the direct child.
        transcript = ""
        with open(os.path.join(state.task_dir(task_id, self.root),
                               "stdout.log"), encoding="utf-8") as handle:
            transcript = handle.read()
        for line in transcript.splitlines():
            if "grandchild pid" in line:
                pid = int(line.rsplit(" ", 1)[1])
                time.sleep(0.5)
                with self.assertRaises(OSError):
                    os.kill(pid, 0)
                break
        else:
            self.fail("grandchild pid was never reported: %r" % transcript)

    def test_non_zero_exit_status_is_recorded_verbatim(self):
        task = self.default_task(goal="stub-mode:exit=3")
        task_id = self.plan_task(task)
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        doc = self.record_of(task_id)
        self.assertEqual(doc["execution"]["exit_status"], 3)
        self.assertNotEqual(doc["status"], "VERIFIED")

    def test_stdout_and_stderr_are_captured_with_digests(self):
        task_id = self.plan_task()
        self.approve(task_id)
        self.run_task(task_id)
        doc = self.record_of(task_id)
        task_dir = state.task_dir(task_id, self.root)
        for ref, key in (("stdout.log", "stdout_sha256"),
                         ("stderr.log", "stderr_sha256")):
            path = os.path.join(task_dir, ref)
            self.assertTrue(os.path.exists(path), "%s missing" % ref)
            self.assertEqual(doc["execution"]["stdout_ref"], "stdout.log")
            self.assertEqual(doc["execution"]["stderr_ref"], "stderr.log")
            self.assertEqual(len(doc["digests"][key]), 64)
        self.assertIn("stub-agent", open(os.path.join(task_dir, "stdout.log"),
                                         encoding="utf-8").read())

    def test_shell_strings_are_never_executed(self):
        with self.assertRaises(execution.ExecutionError):
            execution.run_once("echo hi; rm -rf /", cwd=self.tmp,
                               timeout_seconds=5)
        with self.assertRaises(execution.ExecutionError):
            execution.run_once([], cwd=self.tmp, timeout_seconds=5)


# ---------------------------------------------------------------------------
# SEC-P17-05  directory confinement (preventive vs detective)
# ---------------------------------------------------------------------------
class TestConfinement(P17TestCase):
    """SEC-P17-05: the boundary does NOT claim to be complete confinement."""

    def test_traversal_in_the_acceptance_command_is_rejected_at_intake(self):
        task = self.default_task()
        task["acceptance"]["command"] = [sys.executable, "../../etc/hosts"]
        path = self.task_file(task)
        code, out, err = self.cli("plan", "--task-file", path)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("rejected", err.lower())
        self.assertEqual(
            [d for d in os.listdir(state.tasks_root(self.root))
             if d.startswith("TASK-P17-")], [])

    def test_symlink_pointing_outside_the_boundary_is_rejected(self):
        # The symlink target is a real directory OUTSIDE the project boundary
        # but is computed, never a machine-global path literal (the isolation
        # validator forbids those inside sps2/).
        outside = tempfile.mkdtemp(prefix="p17-outside-")
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        target_file = os.path.join(outside, "target.txt")
        with open(target_file, "w", encoding="utf-8") as handle:
            handle.write("outside\n")
        link_path = os.path.join(self.tmp, "escape-link")
        os.symlink(outside, link_path)
        task = self.default_task()
        task["acceptance"]["command"] = [sys.executable,
                                         os.path.join(link_path, "target.txt")]
        path = self.task_file(task)
        code, out, err = self.cli("plan", "--task-file", path)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("outside the project boundary", err)

    def test_argv_path_escape_is_rejected_before_any_spawn(self):
        with self.assertRaises(confinement.ConfinementViolation) as caught:
            confinement.check_argv_paths(["/bin/echo", "../../escape"],
                                         self.root, base=self.tmp)
        self.assertEqual(caught.exception.kind, "PATH_ESCAPE_REJECTED")

    def test_writes_inside_the_boundary_are_detected_after_the_fact(self):
        target = os.path.join(self.root, "written-outside-workspace.txt")
        task = self.default_task(goal="stub-mode:escape-internal=%s" % target)
        task_id = self.plan_task(task)
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        # DETECTION, not prevention: the write happened and is reported.
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        self.assertTrue(os.path.exists(target),
                        "the double really did write (detection, not blocking)")
        self.assertIn("DETECTED", out)
        self.assertIn("detection, not prevention", out)
        self.assertEqual(self.record_of(task_id)["status"], "FAILED")

    def test_out_of_boundary_write_is_detected_when_watched(self):
        watch = tempfile.mkdtemp(prefix="p17-watch-")
        self.addCleanup(shutil.rmtree, watch, ignore_errors=True)
        target = os.path.join(watch, "outside-the-boundary.txt")
        task = self.default_task(goal="stub-mode:escape-internal=%s" % target)
        task_id = self.plan_task(task)
        self.approve(task_id)
        code, out, err = self.run_task(task_id, "--watch-path", watch)
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        self.assertIn("outside-the-boundary.txt", out)

    def test_workspace_writes_are_not_violations(self):
        task_id = self.plan_task()
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertNotIn("DETECTED", out)
        workspace = confinement.workspace_for(task_id, self.root)
        self.assertTrue(os.path.exists(os.path.join(workspace, "output.txt")))

    def test_cwd_is_documented_as_not_a_boundary(self):
        with open(os.path.join(REPO, "sps2", "p17", "confinement.py"),
                  encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("is NOT a security boundary", text)
        self.assertIn("Detection is not prevention", text)


# ---------------------------------------------------------------------------
# SEC-P17-06  credentials
# ---------------------------------------------------------------------------
class TestCredentials(P17TestCase):
    """SEC-P17-06: no secret ever reaches a stored artefact."""

    @staticmethod
    def _restore_env_var(name, previous, absent):
        """Undo a temporary os.environ mutation, including after a failure.

        Registered via addCleanup so it runs whether the test passes, fails or
        raises. A variable that did not exist before is REMOVED rather than set
        to an empty string, so the environment is restored exactly.
        """
        if previous is absent:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous

    def test_credential_like_task_input_is_rejected_not_stored(self):
        task = self.default_task(
            goal="deploy with api key sk-test-FAKEfakeFAKEfakeFAKE1234567890")
        path = self.task_file(task)
        code, out, err = self.cli("plan", "--task-file", path)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("credential-like", err)
        self.assertEqual(
            [d for d in os.listdir(state.tasks_root(self.root))
             if d.startswith("TASK-P17-")], [])

    def test_secrets_emitted_by_the_double_are_scrubbed_in_transcripts(self):
        task_id = self.plan_task(self.default_task(goal="stub-mode:secret=1"))
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        for name in ("stdout.log", "stderr.log"):
            with open(os.path.join(state.task_dir(task_id, self.root), name),
                      encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("[REDACTED]", text, "%s was not scrubbed" % name)
            self.assertNotIn("sk-test-FAKE", text)
            self.assertNotIn("ghp_FAKE", text)

    def test_scrub_covers_the_recorded_shapes(self):
        cases = {
            "sk-ant-abcdefghijklmnop": "provider-token",
            "ghp_abcdefghijklmnopqrstuvwx": "provider-token",
            "AKIAIOSFODNN7EXAMPLE": "provider-token",
            "Authorization: Bearer abcdefghijklmnopqrst": "bearer-token",
            "password: hunter2hunter2": "assignment",
            "https://user:sekritvalue@example.com/x": "url-credentials",
        }
        for text, expected in cases.items():
            cleaned, removed = scrub.scrub(text)
            self.assertIn(expected, removed, text)
            self.assertIn("[REDACTED]", cleaned, text)

    def test_digests_are_not_mistaken_for_secrets(self):
        digest = "a" * 64
        cleaned, removed = scrub.scrub("plan_sha256=%s" % digest)
        self.assertEqual(removed, [])
        self.assertIn(digest, cleaned)

    def test_scrub_covers_round21_evasion_shapes(self):
        """Round 21A (T-07): the five demonstrated evasion shapes are caught.

        All values are synthetic fixtures, not real credentials.
        """
        cases = {
            # AWS session (temporary) token — sibling of the covered AKIA.
            "ASIAABCDEFGHIJKLMNOP": "provider-token",
            # Slack app-level token — sibling of the covered xox[baprs]-.
            "xapp-1-A0123456789-0123456789": "provider-token",
            # GitLab personal access token.
            "glpat-AbCdEfGhIjKlMnOpQrSt": "provider-token",
            # PEM private-key block without interior spaces.
            "-----BEGINRSAPRIVATEKEY-----MIIEabc-----ENDRSAPRIVATEKEY-----":
                "private-key-block",
            # base64-encoded "password: ..." prefix hedge.
            "cGFzc3dvcmQ6IGh1bnRlcjI=": "base64-credential",
            # base64-encoded "user: ..." prefix hedge.
            "dXNlcjogaHVudGVyMg==": "base64-credential",
            # base64-encoded "auth: ..." prefix hedge.
            "YXV0aDogaHVudGVyMg==": "base64-credential",
        }
        for text, expected in cases.items():
            cleaned, removed = scrub.scrub(text)
            self.assertIn(expected, removed, text)
            self.assertIn("[REDACTED]", cleaned, text)

    def test_scrub_negative_controls_are_not_over_redacted(self):
        """Round 21A (T-07): near-miss shapes must survive untouched.

        Guards the new patterns against excessive redaction: short IDs,
        prefix-only strings, colon-less base64, and empty PEM blocks are
        not secrets.
        """
        negatives = [
            "ASIA1234",                      # below the 16-char body bound
            "AKIA1234",                      # below the 16-char body bound
            "glpat-",                        # prefix alone
            "glpat-short1",                  # below the 16-char body bound
            "xapp-1-short",                  # below the 10-char body bound
            "cGFzc3dvcmRz",                  # base64("passwords"): no colon
            "YXV0aDo",                       # b64 prefix alone, no body
            "dXNlcjo",                       # b64 prefix alone, no body
            "-----BEGIN CERTIFICATE-----",   # BEGIN without the full block
            "Bearer abc12345",               # below the 16-char bearer bound
            "deadbeef" * 8,                  # 64-hex digest, not a secret
        ]
        for text in negatives:
            cleaned, removed = scrub.scrub(text)
            self.assertEqual(removed, [], text)
            self.assertEqual(cleaned, text, text)

    def test_space_free_pem_block_still_requires_full_block(self):
        """The relaxed private-key pattern still needs BEGIN and END."""
        text = "-----BEGINRSAPRIVATEKEY-----MIIEabc"  # no END marker
        cleaned, removed = scrub.scrub(text)
        self.assertEqual(removed, [], text)
        self.assertEqual(cleaned, text, text)

    def test_environment_is_explicit_and_minimal(self):
        _sentinel = "P17_FAKE_PARENT_SECRET"
        _absent = object()
        _previous = os.environ.get(_sentinel, _absent)
        self.addCleanup(self._restore_env_var, _sentinel, _previous, _absent)
        os.environ[_sentinel] = "must-not-be-inherited"
        env = execution.build_environment("/tmp/workspace")
        self.assertNotIn("P17_FAKE_PARENT_SECRET", env)
        self.assertIn("P17_WORKSPACE", env)
        self.assertEqual(set(env) & {"HOME", "AWS_SECRET_ACCESS_KEY",
                                      "OPENAI_API_KEY", "ANTHROPIC_API_KEY"},
                         set())
        self.assertIn("PATH", env)
        self.assertTrue(env["PATH"].split(os.pathsep))

    def test_persisting_a_secret_fails_closed(self):
        with self.assertRaises(scrub.SecretLeak):
            scrub.assert_clean({"goal": "api key sk-test-FAKE1234567890abc"},
                               "unit")

    def test_environment_restoration_helper_restores_both_states(self):
        """The cleanup removes a newly added var and restores a prior value.

        This pins the restore semantics directly, so the guard cannot silently
        degrade into an empty-string assignment.
        """
        name = "P17_RESTORE_PROBE"
        absent = object()
        os.environ.pop(name, None)

        # Newly-added variable is removed, not blanked.
        os.environ[name] = "temp"
        self._restore_env_var(name, absent, absent)
        self.assertNotIn(name, os.environ)

        # Pre-existing variable is restored to its exact previous value.
        os.environ[name] = "original"
        self._restore_env_var(name, "original", absent)
        self.assertEqual(os.environ[name], "original")
        os.environ.pop(name, None)

    def test_sentinel_secret_does_not_survive_the_test(self):
        """Negative control for the leak: the sentinel must be absent here.

        test_environment_is_explicit_and_minimal sets P17_FAKE_PARENT_SECRET.
        unittest runs methods in sorted order, so that test executes before this
        one; if its cleanup regressed, the variable would still be present.
        """
        self.assertNotIn("P17_FAKE_PARENT_SECRET", os.environ)


# ---------------------------------------------------------------------------
# SEC-P17-07  independent verification
# ---------------------------------------------------------------------------
class TestIndependentVerification(P17TestCase):
    """SEC-P17-07: a zero agent exit is never proof of passing."""

    def test_agent_exit_zero_with_failing_acceptance_is_failed(self):
        task = self.default_task(
            acceptance={"command": [sys.executable, "-c",
                                   "raise SystemExit(1)"],
                        "expected_exit_status": 0})
        task_id = self.plan_task(task)
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        doc = self.record_of(task_id)
        self.assertEqual(doc["execution"]["exit_status"], 0)
        self.assertEqual(doc["verification"]["result"], "FAIL")
        self.assertEqual(doc["status"], "FAILED")

    def test_acceptance_command_may_not_be_an_allowlisted_agent(self):
        task = self.default_task(
            acceptance={"command": [STUB_AGENT, "--version"],
                        "expected_exit_status": 0})
        path = self.task_file(task)
        code, out, err = self.cli("plan", "--task-file", path)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("may not be the agent being verified", err)

    def test_execution_and_verification_results_are_separate_fields(self):
        task_id = self.plan_task()
        self.approve(task_id)
        self.run_task(task_id)
        doc = self.record_of(task_id)
        self.assertIn("execution", doc)
        self.assertIn("verification", doc)
        self.assertNotIn("exit_status", doc["verification"])
        self.assertNotIn("result", doc["execution"])
        self.assertIn("structurally separate", doc["verification"]
                      ["independence_statement"])
        self.assertEqual(doc["verification"]["verifier"], "OBJECTIVE_COMMAND")

    def test_unexpected_acceptance_exit_is_reported_as_failure(self):
        task = self.default_task(
            acceptance={"command": [sys.executable, "-c",
                                   "raise SystemExit(7)"],
                        "expected_exit_status": 0})
        task_id = self.plan_task(task)
        self.approve(task_id)
        self.run_task(task_id)
        doc = self.record_of(task_id)
        self.assertEqual(doc["verification"]["result"], "FAIL")


# ---------------------------------------------------------------------------
# SEC-P17-08 / SEC-P17-10  fail-closed and no premature autonomy
# ---------------------------------------------------------------------------
class TestFailClosed(P17TestCase):
    """SEC-P17-08, SEC-P17-10: explicit, auditable, non-zero outcomes."""

    def test_invalid_task_input_is_rejected(self):
        cases = [
            ("not json at all", "not valid JSON"),
            ({}, "goal is missing"),
            (self.default_task(goal="   "), "goal is missing or blank"),
            (self.default_task(unexpected_field="x"), "unknown task field"),
            (self.default_task(required_capabilities="text"), "must be a list"),
            (self.default_task(required_capabilities=["a", "a"]), "duplicate"),
            (self.default_task(acceptance={"command": []}), "non-empty argv"),
            (self.default_task(acceptance={"command": "echo hi"}), "argv array"),
            (self.default_task(acceptance={"command": ["echo hi; ls"]}),
             "shell metacharacters"),
            (self.default_task(timeout_seconds=0), ">= 1"),
            (self.default_task(timeout_seconds="30"), "integer"),
        ]
        for payload, expected in cases:
            with self.subTest(expected=expected):
                path = self.task_file(payload, name="bad.json")
                code, out, err = self.cli("plan", "--task-file", path)
                self.assertEqual(code, cli.EXIT_REJECTED, out + err)
                self.assertIn(expected, err)

    def test_missing_authorisation_blocks_execution(self):
        task_id = self.plan_task()
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("no recorded User approval", err)
        # Nothing may have been spawned or written.
        task_dir = state.task_dir(task_id, self.root)
        self.assertFalse(os.path.exists(os.path.join(task_dir, "stdout.log")))
        self.assertFalse(os.path.exists(os.path.join(task_dir, "stderr.log")))
        self.assertEqual(self.record_of(task_id)["status"],
                         "AWAITING_USER_APPROVAL")

    def test_approval_may_not_be_attributed_to_an_agent(self):
        task_id = self.plan_task()
        sidecar = os.path.join(state.task_dir(task_id, self.root),
                               "approval.json")
        state.write_json(sidecar, {"decided_by": "implementation agent",
                                   "decided_by_role": "AGENT",
                                   "decided_at": state.today(),
                                   "basis": "self approved", "state": "APPROVED"})
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertFalse(os.path.exists(os.path.join(
            state.task_dir(task_id, self.root), "stdout.log")))

    def test_rejection_is_recorded_and_stops_execution(self):
        task_id = self.plan_task()
        code, out, err = self.cli("approve", "--task-id", task_id, "--reject",
                                  "--basis", "User rejects this task.")
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertEqual(self.record_of(task_id)["status"], "REJECTED")
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_REJECTED)

    def test_approval_requires_an_explicit_basis(self):
        task_id = self.plan_task()
        code, out, err = self.cli("approve", "--task-id", task_id,
                                  "--basis", "   ")
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("basis is required", err)

    def test_real_agent_execution_is_disabled_by_default(self):
        production = {"agent_id": "opencode", "probe_method": "VERSION_FLAG",
                      "capabilities": ["test-double"]}
        self.write_allowlist("production", (production,))
        code, out, err = self.cli("discover")
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        self.assertIn("GATE-P17-4", err)
        self.assertIn("No agent was probed", err)

    def test_enablement_state_is_created_disabled(self):
        path = state.enablement_path(self.root)
        data = state.real_agent_enablement(self.root)
        self.assertFalse(data["enabled"])
        self.assertEqual(data["gate"], "GATE-P17-4")
        self.assertIsNone(data["decision_ref"])
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as handle:
            self.assertFalse(json.load(handle)["enabled"])

    def test_enablement_without_a_decision_reference_fails_closed(self):
        state.write_json(state.enablement_path(self.root),
                         {"enabled": True, "decision_ref": None})
        self.assertFalse(state.real_agent_enablement(self.root)["enabled"])

    def test_production_allowlist_is_refused_before_any_probe(self):
        production = {"agent_id": STUB_AGENT, "probe_method": "VERSION_FLAG",
                      "capabilities": ["test-double"]}
        self.write_allowlist("production", (production,))
        allowlist = discovery.load_allowlist(self.root)
        with self.assertRaises(discovery.DiscoveryError) as caught:
            discovery.assert_probe_allowed(
                allowlist, state.real_agent_enablement(self.root))
        self.assertIn("GATE-P17-4", str(caught.exception))

    def test_unknown_task_id_is_rejected(self):
        code, out, err = self.cli("run", "--task-id", "TASK-P17-9999")
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)
        code, out, err = self.cli("status", "--task-id", "TASK-P17-9999")
        self.assertEqual(code, cli.EXIT_REJECTED, out + err)


# ---------------------------------------------------------------------------
# SEC-P17-09  no dependency installation
# ---------------------------------------------------------------------------
class TestNoDependencies(P17TestCase):
    """SEC-P17-09: standard library and intra-repository imports only."""

    def test_imports_are_stdlib_or_intra_repository(self):
        allowed = set(getattr(sys, "stdlib_module_names", ()))
        directory = os.path.join(REPO, "sps2", "p17")
        offenders = []
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(directory, name)
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:      # relative import inside sps2.p17
                        continue
                    roots = [(node.module or "").split(".")[0]]
                else:
                    continue
                for root in roots:
                    if root == "sps2" or root in allowed:
                        continue
                    offenders.append("%s imports %s" % (name, root))
        self.assertEqual(offenders, [], offenders)

    def test_test_doubles_import_only_the_standard_library(self):
        for name in (STUB_AGENT, STUB_SLOW):
            path = os.path.join(FIXTURES, name)
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            allowed = set(getattr(sys, "stdlib_module_names", ()))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertIn(alias.name.split(".")[0], allowed)
                elif isinstance(node, ast.ImportFrom) and not node.level:
                    self.assertIn((node.module or "").split(".")[0], allowed)

    def test_no_package_manager_invocation_anywhere(self):
        directory = os.path.join(REPO, "sps2", "p17")
        offenders = []
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(directory, name), encoding="utf-8") as fh:
                text = fh.read()
            for needle in ("pip install", "pip3 install", "npm install",
                           "uv pip", "brew install", "requirements.txt"):
                if needle in text:
                    offenders.append("%s references %r" % (name, needle))
        self.assertEqual(offenders, [], offenders)


# ---------------------------------------------------------------------------
# SEC-P17-11  evidence integrity
# ---------------------------------------------------------------------------
class TestEvidenceIntegrity(P17TestCase):
    """SEC-P17-11: digests, completeness, and corruption detection."""

    def verified_task(self):
        task_id = self.plan_task()
        self.approve(task_id)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        return task_id

    def test_intact_record_verifies_clean(self):
        task_id = self.verified_task()
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertIn("no findings", out)
        self.assertIn("not that they are the right bytes", out)

    def test_tampered_transcript_is_detected(self):
        task_id = self.verified_task()
        path = os.path.join(state.task_dir(task_id, self.root), "stdout.log")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("tampered\n")
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        self.assertIn("INTEGRITY_MISMATCH", err)
        self.assertIn("stdout.log", err)

    def test_missing_transcript_is_detected(self):
        task_id = self.verified_task()
        os.remove(os.path.join(state.task_dir(task_id, self.root),
                               "stdout.log"))
        code, out, err = self.cli("verify", "--task-id", task_id)
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        self.assertIn("MISSING_ARTEFACT", err)

    def test_incomplete_record_is_detected(self):
        task_id = self.verified_task()
        path = os.path.join(state.task_dir(task_id, self.root), "record.json")
        doc = state.read_json(path)
        del doc["digests"]
        state.write_json(path, doc)
        report = record.verify_integrity(task_id, self.root)
        kinds = {f["kind"] for f in report["findings"]}
        self.assertIn("INCOMPLETE_RECORD", kinds)

    def test_structural_self_check_rejects_a_forged_verified_record(self):
        task_id = self.verified_task()
        doc = self.record_of(task_id)
        # Forge the worst case: VERIFIED with a FAIL verification.
        doc["verification"]["result"] = "FAIL"
        with self.assertRaises(record.RecordInvalid):
            record.write(task_id, doc, self.root)

    def test_record_may_not_carry_unknown_properties(self):
        task_id = self.verified_task()
        doc = self.record_of(task_id)
        doc["sneaky"] = "value"
        with self.assertRaises(record.RecordInvalid):
            record.write(task_id, doc, self.root)

    def test_evidence_record_carries_the_governance_fields(self):
        task_id = self.verified_task()
        evidence_dir = state.evidence_root(self.root)
        files = [f for f in os.listdir(evidence_dir) if f.endswith(".json")]
        self.assertTrue(files, "no evidence record was written")
        payload = state.read_json(os.path.join(evidence_dir, sorted(files)[0]))
        for field in ("id", "task", "command", "expected", "actual", "result",
                      "timestamp", "file", "test", "commit"):
            self.assertIn(field, payload)
        self.assertEqual(payload["task"], task_id)
        self.assertIn(payload["result"], ("PASS", "FAIL", "SKIP", "BLOCKED"))

    def test_evidence_digest_is_recorded_in_the_task_record(self):
        task_id = self.verified_task()
        digest = self.record_of(task_id)["digests"]["evidence_sha256"]
        self.assertIsNotNone(digest)
        self.assertEqual(len(digest), 64)
        path = os.path.join(state.task_dir(task_id, self.root), "evidence",
                            "verification-output.json")
        import hashlib
        with open(path, "rb") as handle:
            self.assertEqual(hashlib.sha256(handle.read()).hexdigest(), digest)


# ---------------------------------------------------------------------------
# determinism and recovery
# ---------------------------------------------------------------------------
class TestDeterminismAndRecovery(P17TestCase):
    """REQ-P17-04 determinism, REQ-P17-11 bounded retry and recovery."""

    def test_selection_is_deterministic_across_100_runs(self):
        allowlist = discovery.load_allowlist(self.root)
        snapshot = discovery.discover(allowlist, cwd=self.root, root=self.root)
        fingerprints = set()
        agents = set()
        for _ in range(100):
            selection, _ordered, _excluded = selection_mod.select(
                allowlist, snapshot, ["test-double"])
            self.assertIsNotNone(selection)
            fingerprints.add(selection["selection_fingerprint"])
            agents.add(selection["selected_agent"])
        self.assertEqual(len(fingerprints), 1,
                         "selection fingerprint was not stable")
        self.assertEqual(agents, {STUB_AGENT})
        self.assertEqual(len(next(iter(fingerprints))), 64)

    def test_selection_is_impossible_when_capabilities_are_unmet(self):
        allowlist = discovery.load_allowlist(self.root)
        snapshot = discovery.discover(allowlist, cwd=self.root, root=self.root)
        selection, ordered, excluded = selection_mod.select(
            allowlist, snapshot, ["nonexistent-capability"])
        self.assertIsNone(selection)
        self.assertEqual(ordered, [])
        self.assertTrue(any("missing required capabilities" in e["reason"]
                            for e in excluded))

    def test_retry_bound_is_enforced_and_recorded(self):
        task_id = self.plan_task()
        self.approve(task_id)
        state.record_attempt(task_id, {"attempt": 1, "at": state.now()},
                             self.root)
        state.record_attempt(task_id, {"attempt": 2, "at": state.now()},
                             self.root)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_TASK_FAILED, out + err)
        self.assertIn("retry bound exhausted", err)
        doc = self.record_of(task_id)
        self.assertEqual(doc["status"], "FAILED")
        self.assertEqual(doc["execution"]["outcome"], "KILLED")
        self.assertFalse(os.path.exists(os.path.join(
            state.task_dir(task_id, self.root), "stdout.log")))

    def test_retry_within_bound_proceeds_and_can_verify(self):
        task_id = self.plan_task()
        self.approve(task_id)
        state.record_attempt(task_id, {"attempt": 1, "at": state.now()},
                             self.root)
        code, out, err = self.run_task(task_id)
        self.assertEqual(code, cli.EXIT_OK, out + err)
        self.assertEqual(self.record_of(task_id)["status"], "VERIFIED")

    def test_plan_digest_is_reproducible(self):
        first = plan_mod.build("goal", ["a"], ["true"])
        second = plan_mod.build("goal", ["a"], ["true"])
        first.pop("created_at")
        second.pop("created_at")
        self.assertEqual(plan_mod.plan_digest(first),
                         plan_mod.plan_digest(second))

    def test_plan_with_no_steps_is_refused(self):
        with self.assertRaises(plan_mod.PlanError):
            plan_mod.persist("TASK-P17-0001", {"steps": []}, self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
