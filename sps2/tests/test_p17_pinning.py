#!/usr/bin/env python3
"""P17 executable-pinning suite (fail-closed resolution).

An allowlisted NAME is never resolved against the ambient PATH: PATH
order is attacker-influenceable and a same-named executable placed
earlier in PATH would otherwise shadow the approved one. Each entry is
resolved either by an explicit absolute `pinned_path` or by a name
lookup confined to the allowlist's configured `trusted_roots`. Missing
configuration, a pin that is missing/not a file/not executable, or a
resolution that escapes the trusted roots all fail closed. The resolved
executable's SHA-256 is recorded at discovery and re-verified
immediately before spawning, which detects substitution between those
two moments.

REPOSITORY-LOCAL TEST DOUBLES ONLY. No real agent CLI is invoked by
any test in this file. Real-agent execution is disabled by default and
GATE-P17-4 is OPEN.

Every test runs against isolated temporary roots, so no test writes
into the real repository's project-local P17 state.

Standard library unittest only; no dependency.
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
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from sps2.p17 import (  # noqa: E402
    discovery, record, state, __main__ as cli)

FIXTURES = os.path.join(HERE, "fixtures", "p17")
STUB_AGENT = "stub-agent.py"


def cli_run(*argv):
    """Invoke the CLI in-process; return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def make_executable(directory, name, marker, executable=True):
    """Write a harmless repository-local test double and make it
    executable. It answers --version with `marker` and otherwise echoes
    it. It is NOT an agent and performs no real work."""
    path = os.path.join(directory, name)
    body = (
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "VERSION = %r\n"
        "if '--version' in sys.argv:\n"
        "    print(VERSION)\n"
        "else:\n"
        "    print('double %s ran')\n"
        "sys.exit(0)\n" % (marker, marker)
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    if executable:
        os.chmod(path, 0o755)
    return path


class PinningTestCase(unittest.TestCase):
    """Isolated project root and stub directories per test."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p17-pin-")
        self.root = os.path.join(self.tmp, "project")
        os.makedirs(self.root)
        self.stubs = os.path.join(self.tmp, "stubs")
        os.makedirs(self.stubs)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def allowlist_file(self, purpose="test", agents=None,
                       trusted_roots=None, name="allowlist.json"):
        path = os.path.join(self.root, "sps2", "p17", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {"schema": "sps2.p17-allowlist/v1",
                   "purpose": purpose}
        if trusted_roots is not None:
            payload["trusted_roots"] = trusted_roots
        if agents is not None:
            payload["agents"] = agents
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return path

    def agent(self, agent_id, capabilities=("test-double",),
              pinned_path=None):
        entry = {"agent_id": agent_id, "probe_method": "VERSION_FLAG",
                 "capabilities": list(capabilities)}
        if pinned_path is not None:
            entry["pinned_path"] = pinned_path
        return entry

    def discover(self, allowlist, allowlist_file):
        return discovery.discover(allowlist, cwd=self.root,
                                  root=self.root,
                                  allowlist_file=allowlist_file)


# ---------------------------------------------------------------------------
# Duplicate executable names in separate trusted roots
# ---------------------------------------------------------------------------
class TestDuplicateNamesInSeparateRoots(PinningTestCase):
    """The same name in two trusted roots resolves by root order."""

    def test_first_trusted_root_wins_and_digest_matches_it(self):
        dir_a = os.path.join(self.tmp, "rootA")
        dir_b = os.path.join(self.tmp, "rootB")
        os.makedirs(dir_a)
        os.makedirs(dir_b)
        twin_a = make_executable(dir_a, "twin.py", "FROM-ROOT-A")
        twin_b = make_executable(dir_b, "twin.py", "FROM-ROOT-B")

        entry = self.agent("twin.py")
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [dir_a, dir_b], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[dir_a, dir_b])

        resolved, mode, roots = discovery.resolve_entry(
            entry, allowlist, path)
        self.assertEqual(os.path.realpath(resolved),
                         os.path.realpath(twin_a))
        self.assertEqual(mode, discovery.RESOLUTION_TRUSTED_ROOT)
        self.assertNotEqual(os.path.realpath(resolved),
                            os.path.realpath(twin_b))
        self.assertEqual(discovery.executable_digest(resolved),
                         discovery.executable_digest(twin_a))

    def test_reversing_trusted_root_order_selects_the_other_file(self):
        dir_a = os.path.join(self.tmp, "rootA")
        dir_b = os.path.join(self.tmp, "rootB")
        os.makedirs(dir_a)
        os.makedirs(dir_b)
        twin_a = make_executable(dir_a, "twin.py", "FROM-ROOT-A")
        twin_b = make_executable(dir_b, "twin.py", "FROM-ROOT-B")

        entry = self.agent("twin.py")
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [dir_b, dir_a], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[dir_b, dir_a])

        resolved, _, _ = discovery.resolve_entry(entry, allowlist, path)
        self.assertEqual(os.path.realpath(resolved),
                         os.path.realpath(twin_b))
        self.assertNotEqual(os.path.realpath(resolved),
                            os.path.realpath(twin_a))


# ---------------------------------------------------------------------------
# Ambient PATH order cannot shadow an approved executable
# ---------------------------------------------------------------------------
class TestAmbientPathOrderIsIrrelevant(PinningTestCase):
    """A hostile same-named executable earlier on PATH is never chosen."""

    def test_hostile_earlier_path_entry_is_not_selected(self):
        hostile_dir = os.path.join(self.tmp, "hostile")
        os.makedirs(hostile_dir)
        hostile = make_executable(hostile_dir, STUB_AGENT,
                                  "HOSTILE-SHADOW")
        # The hostile copy is placed FIRST on the ambient PATH.
        previous = os.environ.get("PATH", "")
        os.environ["PATH"] = hostile_dir + os.pathsep + previous
        self.addCleanup(setattr, os.environ, "PATH", previous)

        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [FIXTURES], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[FIXTURES])

        resolved, mode, _ = discovery.resolve_entry(
            entry, allowlist, path)
        # Resolution is confined to the trusted root, so the approved
        # fixture wins even though the hostile copy is earlier on PATH.
        self.assertEqual(os.path.realpath(resolved),
                         os.path.realpath(
                             os.path.join(FIXTURES, STUB_AGENT)))
        self.assertNotEqual(os.path.realpath(resolved),
                            os.path.realpath(hostile))
        self.assertEqual(mode, discovery.RESOLUTION_TRUSTED_ROOT)
        self.assertNotEqual(discovery.executable_digest(resolved),
                            discovery.executable_digest(hostile))

    def test_unpinned_name_absent_from_trusted_roots_is_unavailable(self):
        # A name that exists only on the ambient PATH, in no trusted
        # root, must never be resolved by falling back to PATH.
        only_on_path = os.path.join(self.tmp, "onlyonpath")
        os.makedirs(only_on_path)
        make_executable(only_on_path, "path-only.py", "PATH-ONLY")
        previous = os.environ.get("PATH", "")
        os.environ["PATH"] = only_on_path + os.pathsep + previous
        self.addCleanup(setattr, os.environ, "PATH", previous)

        entry = self.agent("path-only.py")
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [FIXTURES], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[FIXTURES])

        with self.assertRaises(discovery.DiscoveryError):
            discovery.resolve_entry(entry, allowlist, path)

        snapshot = self.discover(allowlist, path)
        record = snapshot["agents"][0]
        self.assertFalse(record["available"])
        self.assertIn("resolution refused", record["note"] or "")
        self.assertIn("ambient PATH", record["note"])


# ---------------------------------------------------------------------------
# Unauthorized executable rejection
# ---------------------------------------------------------------------------
class TestUnauthorizedExecutableRejection(PinningTestCase):
    """An executable outside the allowlist can never be selected."""

    def test_rogue_in_trusted_root_is_not_in_allowlist_so_never_selected(self):
        rogue_dir = os.path.join(self.tmp, "rogue-root")
        os.makedirs(rogue_dir)
        rogue = make_executable(rogue_dir, "rogue.py", "ROGUE")
        make_executable(rogue_dir, STUB_AGENT, "APPROVED")

        # Only stub-agent.py is allowlisted; rogue.py is present in the
        # trusted root but is not an allowlist entry, so selection can
        # never return it.
        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [rogue_dir], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[rogue_dir])
        snapshot = self.discover(allowlist, path)
        self.assertEqual(snapshot["available_count"], 1)
        self.assertEqual(os.path.realpath(
            snapshot["agents"][0]["resolved_path"]),
            os.path.realpath(os.path.join(rogue_dir, STUB_AGENT)))
        self.assertNotEqual(os.path.realpath(
            snapshot["agents"][0]["resolved_path"]),
            os.path.realpath(rogue))

    def test_capability_gate_still_applies_within_trusted_roots(self):
        rogue_dir = os.path.join(self.tmp, "rogue-root")
        os.makedirs(rogue_dir)
        make_executable(rogue_dir, "rogue.py", "ROGUE")
        entry = self.agent("rogue.py", capabilities=("never-declared",))
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [rogue_dir], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[rogue_dir])
        snapshot = self.discover(allowlist, path)
        # Resolved inside the trusted root but excluded by selection for
        # missing capabilities.
        self.assertTrue(snapshot["agents"][0]["available"])
        from sps2.p17 import selection as selection_mod
        chosen, _, excluded = selection_mod.select(
            allowlist, snapshot, ["test-double"])
        self.assertIsNone(chosen)
        self.assertIn("missing required capabilities",
                      excluded[0]["reason"])


# ---------------------------------------------------------------------------
# Missing or invalid pinned-path configuration
# ---------------------------------------------------------------------------
class TestMissingConfigurationFailsClosed(PinningTestCase):
    """No trusted_roots and no pin => fail closed, nothing executes."""

    def test_no_trusted_roots_is_refused_at_resolution(self):
        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "agents": [entry]}
        path = self.allowlist_file(agents=[entry])
        with self.assertRaises(discovery.DiscoveryError):
            discovery.resolve_entry(entry, allowlist, path)

    def test_no_trusted_roots_records_unavailable_and_blocks_the_run(self):
        entry = self.agent(STUB_AGENT)
        path = self.allowlist_file(agents=[entry])
        with open(path, encoding="utf-8") as handle:
            allowlist = json.load(handle)
        snapshot = self.discover(allowlist, path)
        probe = snapshot["agents"][0]
        self.assertFalse(probe["available"])
        self.assertIsNone(probe["resolved_path"])
        self.assertIn("resolution refused", probe["note"] or "")

        # End to end: the run must BLOCK, spawn nothing, and record why.
        # The plan/approve phases use a VALID allowlist (plan also
        # discovers, so it needs one); only the run uses the broken one.
        valid = self.allowlist_file(agents=[self.agent(STUB_AGENT)],
                                    trusted_roots=[FIXTURES],
                                    name="valid.json")
        broken = self.allowlist_file(agents=[self.agent(STUB_AGENT)],
                                     name="broken.json")
        task = {
            "goal": "stub-mode:write=output.txt",
            "required_capabilities": ["test-double"],
            "acceptance": {
                "command": [sys.executable, "-c", "print('acceptance ok')"],
                "expected_exit_status": 0,
            },
            "timeout_seconds": 30,
        }
        task_path = os.path.join(self.tmp, "task.json")
        with open(task_path, "w", encoding="utf-8") as handle:
            json.dump(task, handle)
        code, out, err = cli_run("--root", self.root, "plan",
                                 "--task-file", task_path,
                                 "--allowlist", valid)
        self.assertEqual(code, 0, err)
        task_id = next(t for t in out.split()
                       if t.startswith("TASK-P17-"))
        code, out, err = cli_run("--root", self.root, "approve",
                                 "--task-id", task_id,
                                 "--basis", "test approval")
        self.assertEqual(code, 0, err)
        code, out, err = cli_run("--root", self.root, "run",
                                 "--task-id", task_id,
                                 "--allowlist", broken)
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertIn("no eligible agent", err)
        self.assertIn("resolution refused", err)
        doc = record.load(task_id, self.root)
        self.assertEqual(doc["status"], "BLOCKED")


class TestInvalidConfigurationFailsClosed(PinningTestCase):
    """A malformed declaration is operator error and fails closed."""

    def test_trusted_roots_not_a_list(self):
        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": "/not/a/list", "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots="/not/a/list")
        with self.assertRaises(discovery.DiscoveryError):
            self.discover(allowlist, path)

    def test_trusted_roots_empty_list(self):
        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [], "agents": [entry]}
        path = self.allowlist_file(agents=[entry], trusted_roots=[])
        with self.assertRaises(discovery.DiscoveryError):
            self.discover(allowlist, path)

    def test_trusted_root_is_not_a_directory(self):
        not_a_dir = os.path.join(self.tmp, "plain-file")
        with open(not_a_dir, "w", encoding="utf-8") as handle:
            handle.write("x")
        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [not_a_dir], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[not_a_dir])
        with self.assertRaises(discovery.DiscoveryError):
            self.discover(allowlist, path)

    def test_pinned_path_does_not_exist(self):
        entry = self.agent(STUB_AGENT,
                           pinned_path=os.path.join(self.tmp, "missing.py"))
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [self.stubs], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[self.stubs])
        with self.assertRaises(discovery.DiscoveryError):
            discovery.resolve_entry(entry, allowlist, path)

    def test_pinned_path_is_a_directory(self):
        entry = self.agent(STUB_AGENT, pinned_path=self.stubs)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [self.stubs], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[self.stubs])
        with self.assertRaises(discovery.DiscoveryError):
            discovery.resolve_entry(entry, allowlist, path)

    def test_pinned_path_not_executable(self):
        stub = make_executable(self.stubs, STUB_AGENT, "NOT-EXEC",
                               executable=False)
        entry = self.agent(STUB_AGENT, pinned_path=stub)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [self.stubs], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[self.stubs])
        with self.assertRaises(discovery.DiscoveryError):
            discovery.resolve_entry(entry, allowlist, path)

    def test_pinned_path_outside_trusted_roots(self):
        elsewhere = os.path.join(self.tmp, "elsewhere")
        os.makedirs(elsewhere)
        stub = make_executable(elsewhere, STUB_AGENT, "ELSEWHERE")
        entry = self.agent(STUB_AGENT, pinned_path=stub)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [self.stubs], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[self.stubs])
        with self.assertRaises(discovery.DiscoveryError):
            discovery.resolve_entry(entry, allowlist, path)

    def test_pinned_path_inside_trusted_root_resolves(self):
        stub = make_executable(self.stubs, STUB_AGENT, "PINNED-OK")
        entry = self.agent(STUB_AGENT, pinned_path=stub)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [self.stubs], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[self.stubs])
        resolved, mode, _ = discovery.resolve_entry(
            entry, allowlist, path)
        self.assertEqual(resolved, os.path.realpath(stub))
        self.assertEqual(mode, discovery.RESOLUTION_PINNED)
        self.assertEqual(discovery.executable_digest(resolved),
                         discovery.executable_digest(stub))


# ---------------------------------------------------------------------------
# Executable substitution detection
# ---------------------------------------------------------------------------
class TestExecutableSubstitution(PinningTestCase):
    """A changed executable is detected before it is spawned."""

    def test_verify_unchanged_detects_a_swapped_binary(self):
        stub = make_executable(self.stubs, STUB_AGENT, "ORIGINAL")
        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1", "purpose": "test",
                     "trusted_roots": [self.stubs], "agents": [entry]}
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[self.stubs])
        resolved, _, _ = discovery.resolve_entry(entry, allowlist, path)
        expected = discovery.executable_digest(resolved)
        # Unchanged: verification succeeds and returns the digest.
        self.assertEqual(discovery.verify_unchanged(
            resolved, expected, STUB_AGENT), expected)

        # Substitute the binary after discovery.
        make_executable(self.stubs, STUB_AGENT, "SUBSTITUTED")
        with self.assertRaises(discovery.DiscoveryError) as ctx:
            discovery.verify_unchanged(resolved, expected, STUB_AGENT)
        self.assertIn("substituted", str(ctx.exception))

    def test_verify_unchanged_refuses_an_unreadable_digest(self):
        stub = make_executable(self.stubs, STUB_AGENT, "ORIGINAL")
        with self.assertRaises(discovery.DiscoveryError) as ctx:
            discovery.verify_unchanged(stub, None, STUB_AGENT)
        self.assertIn("no recorded executable digest", str(ctx.exception))

    def test_verify_unchanged_refuses_an_unreadable_file(self):
        missing = os.path.join(self.stubs, "gone.py")
        with self.assertRaises(discovery.DiscoveryError) as ctx:
            discovery.verify_unchanged(missing, "0" * 64, "gone.py")
        self.assertIn("cannot be read", str(ctx.exception))


# ---------------------------------------------------------------------------
# Production refusal and disabled real-agent execution
# ---------------------------------------------------------------------------
class TestProductionRefusalAndEnablement(PinningTestCase):
    """A production allowlist is refused before any probe or spawn."""

    def test_production_allowlist_is_refused_before_probing(self):
        entry = self.agent(STUB_AGENT)
        allowlist = {"schema": "sps2.p17-allowlist/v1",
                     "purpose": "production",
                     "trusted_roots": [FIXTURES], "agents": [entry]}
        path = self.allowlist_file(purpose="production", agents=[entry],
                                   trusted_roots=[FIXTURES])
        with self.assertRaises(discovery.DiscoveryError) as ctx:
            self.discover(allowlist, path)
        self.assertIn("real-agent execution is disabled", str(ctx.exception))
        self.assertIn("GATE-P17-4", str(ctx.exception))

    def test_real_agent_execution_remains_disabled(self):
        enablement = state.real_agent_enablement(self.root)
        self.assertFalse(enablement.get("enabled"))
        self.assertEqual(enablement.get("gate"), "GATE-P17-4")
        self.assertIsNone(enablement.get("decision_ref"))

    def test_production_allowlist_run_is_refused(self):
        # Plan/approve with a valid TEST allowlist (plan also
        # discovers); the run uses the PRODUCTION allowlist, which
        # must be refused before any probe or spawn.
        valid = self.allowlist_file(agents=[self.agent(STUB_AGENT)],
                                    trusted_roots=[FIXTURES],
                                    name="valid.json")
        production = self.allowlist_file(purpose="production",
                                          agents=[self.agent(STUB_AGENT)],
                                          trusted_roots=[FIXTURES],
                                          name="production.json")
        task = {
            "goal": "stub-mode:write=output.txt",
            "required_capabilities": ["test-double"],
            "acceptance": {
                "command": [sys.executable, "-c", "print('acceptance ok')"],
                "expected_exit_status": 0,
            },
            "timeout_seconds": 30,
        }
        task_path = os.path.join(self.tmp, "task.json")
        with open(task_path, "w", encoding="utf-8") as handle:
            json.dump(task, handle)
        code, out, err = cli_run("--root", self.root, "plan",
                                 "--task-file", task_path,
                                 "--allowlist", valid)
        self.assertEqual(code, 0, err)
        task_id = next(t for t in out.split()
                       if t.startswith("TASK-P17-"))
        code, out, err = cli_run("--root", self.root, "approve",
                                 "--task-id", task_id,
                                 "--basis", "test approval")
        self.assertEqual(code, 0, err)
        code, out, err = cli_run("--root", self.root, "run",
                                 "--task-id", task_id,
                                 "--allowlist", production)
        self.assertEqual(code, cli.EXIT_REJECTED)
        self.assertIn("real-agent execution is disabled", err)


# ---------------------------------------------------------------------------
# Successful execution of an approved harmless test double
# ---------------------------------------------------------------------------
class TestSuccessfulExecutionOfApprovedStub(PinningTestCase):
    """A pinned, allowlisted test double executes and verifies."""

    def test_approved_stub_runs_to_verified(self):
        entry = self.agent(STUB_AGENT)
        path = self.allowlist_file(agents=[entry],
                                   trusted_roots=[FIXTURES])
        task = {
            "goal": "stub-mode:write=output.txt",
            "required_capabilities": ["test-double"],
            "acceptance": {
                "command": [sys.executable, "-c", "print('acceptance ok')"],
                "expected_exit_status": 0,
            },
            "timeout_seconds": 30,
        }
        task_path = os.path.join(self.tmp, "task.json")
        with open(task_path, "w", encoding="utf-8") as handle:
            json.dump(task, handle)
        code, out, err = cli_run("--root", self.root, "plan",
                                 "--task-file", task_path,
                                 "--allowlist", path)
        self.assertEqual(code, 0, err)
        task_id = next(t for t in out.split()
                       if t.startswith("TASK-P17-"))
        code, out, err = cli_run("--root", self.root, "approve",
                                 "--task-id", task_id,
                                 "--basis", "test approval")
        self.assertEqual(code, 0, err)
        code, out, err = cli_run("--root", self.root, "run",
                                 "--task-id", task_id,
                                 "--allowlist", path)
        self.assertEqual(code, 0, "run failed: %s%s" % (out, err))

        doc = record.load(task_id, self.root)
        self.assertEqual(doc["status"], "VERIFIED")
        self.assertEqual(doc["execution"]["outcome"], "COMPLETED")
        self.assertEqual(doc["execution"]["exit_status"], 0)
        # The resolved executable is the approved fixture, and the
        # resolution mode records that the ambient PATH was bypassed.
        self.assertEqual(doc["agent_selection"]["selected_agent"],
                         STUB_AGENT)
        usage_path = os.path.join(state.tasks_root(self.root),
                                    "usage.log")
        with open(usage_path, encoding="utf-8") as handle:
            usage = [json.loads(line) for line
                       in handle if line.strip()]
        self.assertTrue(usage)
        self.assertEqual(usage[-1]["resolution_mode"],
                         discovery.RESOLUTION_TRUSTED_ROOT)
        self.assertEqual(usage[-1]["executable_sha256"],
                         discovery.executable_digest(
                             os.path.join(FIXTURES, STUB_AGENT)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
