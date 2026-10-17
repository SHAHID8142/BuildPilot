"""Contract tests for T-32 hook-enforced laws (scripts/sps-hooks.sh +
scripts/sps-hook-gate.sh).

Follows the subprocess-driven, scratch-copy conventions of test_secret_scan.py
and test_law_checker.py: the live tree is never modified — install/remove run
in a temp scratch copy of the repo, and the hook gate runs against a shallow
repo copy with constructed payloads.

Pins:
1. install without --yes is refused (exit != 0) and writes no settings,
2. install --yes writes .claude/settings.json with PreToolUse/PostToolUse
   hook entries (and merges into an existing settings file),
3. double install without --force is refused,
4. remove strips its own entries but preserves an unrelated pre-existing key,
5. the hook gate passes a normal write (exit 0, no block),
6. the hook gate BLOCKS an over-budget .sps/task-queue.md write (exit 2),
7. missing python3 falls open (exit 0) via the SPS_PYTHON override.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS = REPO_ROOT / "scripts" / "sps-hooks.sh"
GATE = REPO_ROOT / "scripts" / "sps-hook-gate.sh"

ENV_BASE = {
    "PATH": "/usr/bin:/bin",
    "HOME": "/tmp",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def _run_hooks(repo: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(HOOKS), *args],
        capture_output=True,
        text=True,
        cwd=repo,
        input=stdin,
        timeout=60,
        env={**ENV_BASE, "SPS_TEST_HOOKS": "1"},
    )


def _scratch_repo() -> Path:
    """Shallow repo copy (no .git/node_modules/__pycache__/.tmp-smoke-sps),
    same ignore set as test_law_checker.py, plus a git init so the scripts'
    root resolution works."""
    tmp = Path(tempfile.mkdtemp(prefix="sps-hooks-test-")) / "repo"
    shutil.copytree(
        REPO_ROOT,
        tmp,
        ignore=shutil.ignore_patterns(
            ".git", "node_modules", "__pycache__", ".tmp-smoke-sps"
        ),
    )
    subprocess.run(
        ["git", "init", "-q"],
        cwd=tmp,
        capture_output=True,
        env={**ENV_BASE},
        check=True,
    )
    # The live tree carries .claude/settings.json; tests must start from a
    # clean slate so "install writes settings" / "refusal writes nothing"
    # assertions are meaningful.
    shutil.rmtree(tmp / ".claude", ignore_errors=True)
    return tmp


def _run_gate(payload: dict, repo: Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = {**ENV_BASE, "SPS_TEST_HOOKS": "1"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(repo / "scripts" / "sps-hook-gate.sh"), "pre"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=60,
        env=env,
    )


def _cleanup(tmp: Path) -> None:
    shutil.rmtree(tmp.parent if tmp.parent.name.startswith("sps-hooks-test-") else tmp,
                  ignore_errors=True)


class TestHooksInstallConsentGate(unittest.TestCase):
    """Consent gate: no --yes means no install and no settings written."""

    def test_install_without_yes_refused_and_writes_nothing(self) -> None:
        tmp = _scratch_repo()
        try:
            self.assertFalse((tmp / ".claude" / "settings.json").exists())
            # EOF stdin must NOT count as consent.
            proc = _run_hooks(tmp, "install", stdin=None)
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("REFUSED", proc.stderr)
            self.assertFalse(
                (tmp / ".claude" / "settings.json").exists(),
                "no settings file may be written without --yes",
            )
        finally:
            _cleanup(tmp)

    def test_install_with_yes_writes_hook_entries(self) -> None:
        tmp = _scratch_repo()
        try:
            proc = _run_hooks(tmp, "install", "--yes")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            settings = json.loads(
                (tmp / ".claude" / "settings.json").read_text(encoding="utf-8")
            )
            for event in ("PreToolUse", "PostToolUse"):
                entries = settings["hooks"][event]
                self.assertTrue(
                    any(
                        h.get("_spsHook") == "sps-law-gate"
                        and "sps-hook-gate.sh" in h.get("command", "")
                        for e in entries
                        for h in e.get("hooks", [])
                    ),
                    f"{event} must carry a marked sps-hook-gate entry",
                )
            self.assertIn("OUTSIDE model context", proc.stdout)
        finally:
            _cleanup(tmp)

    def test_double_install_without_force_refused(self) -> None:
        tmp = _scratch_repo()
        try:
            self.assertEqual(_run_hooks(tmp, "install", "--yes").returncode, 0)
            proc = _run_hooks(tmp, "install", "--yes")
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("already installed", proc.stdout + proc.stderr)
            # --force re-installs without duplicating entries.
            proc2 = _run_hooks(tmp, "install", "--yes", "--force")
            self.assertEqual(proc2.returncode, 0, proc2.stdout + proc2.stderr)
            settings = json.loads(
                (tmp / ".claude" / "settings.json").read_text(encoding="utf-8")
            )
            for event in ("PreToolUse", "PostToolUse"):
                marked = [
                    h
                    for e in settings["hooks"][event]
                    for h in e.get("hooks", [])
                    if h.get("_spsHook") == "sps-law-gate"
                ]
                self.assertEqual(len(marked), 1, f"{event} must not duplicate entries")
        finally:
            _cleanup(tmp)

    def test_install_merges_into_existing_settings(self) -> None:
        tmp = _scratch_repo()
        try:
            cl = tmp / ".claude"
            cl.mkdir()
            (cl / "settings.json").write_text(
                json.dumps({"enabledPlugins": {"x": True}, "hooks": {}}),
                encoding="utf-8",
            )
            proc = _run_hooks(tmp, "install", "--yes")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            settings = json.loads(
                (cl / "settings.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                settings.get("enabledPlugins"), {"x": True},
                "pre-existing keys must survive the merge",
            )
            self.assertIn("PreToolUse", settings["hooks"])
        finally:
            _cleanup(tmp)


class TestHooksRemove(unittest.TestCase):
    def test_remove_strips_own_entries_and_preserves_unrelated_key(self) -> None:
        tmp = _scratch_repo()
        try:
            cl = tmp / ".claude"
            cl.mkdir()
            (cl / "settings.json").write_text(
                json.dumps({"enabledPlugins": {}, "customKey": "keep-me"}),
                encoding="utf-8",
            )
            self.assertEqual(_run_hooks(tmp, "install", "--yes").returncode, 0)
            proc = _run_hooks(tmp, "remove")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            settings = json.loads(
                (cl / "settings.json").read_text(encoding="utf-8")
            )
            self.assertEqual(settings.get("customKey"), "keep-me")
            self.assertEqual(
                settings.get("enabledPlugins"), {},
                "unrelated keys must be preserved by remove",
            )
            for event in ("PreToolUse", "PostToolUse"):
                marked = [
                    h
                    for e in settings.get("hooks", {}).get(event, [])
                    for h in e.get("hooks", [])
                    if h.get("_spsHook") == "sps-law-gate"
                ]
                self.assertEqual(marked, [], f"{event} entries must be stripped")
            # status reports not installed, exit 0.
            st = _run_hooks(tmp, "status")
            self.assertEqual(st.returncode, 0)
            self.assertIn("not installed", st.stdout)
        finally:
            _cleanup(tmp)


class TestHookGate(unittest.TestCase):
    """The gate script itself: pass normal writes, block over-budget .sps/."""

    def test_normal_write_passes(self) -> None:
        tmp = _scratch_repo()
        try:
            payload = {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(tmp / "framework" / "domain" / "app.py"),
                    "content": "import os\nPORT = os.environ.get('PORT')\n",
                },
            }
            proc = _run_gate(payload, tmp)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("permissionDecision", proc.stdout)
        finally:
            _cleanup(tmp)

    def test_over_budget_task_queue_write_blocked(self) -> None:
        tmp = _scratch_repo()
        try:
            # task-queue.md budget is 80 lines / 6144 bytes (check_laws.py).
            payload = {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(tmp / ".sps" / "task-queue.md"),
                    "content": "\n".join(f"- task {i}" for i in range(120)),
                },
            }
            proc = _run_gate(payload, tmp)
            self.assertEqual(
                proc.returncode, 2,
                f"over-budget .sps/ write must block (exit 2): {proc.stdout}",
            )
            self.assertIn("deny", proc.stdout)
            self.assertIn("context-budget", proc.stdout + proc.stderr)
        finally:
            _cleanup(tmp)

    def test_within_budget_sps_write_passes(self) -> None:
        tmp = _scratch_repo()
        try:
            payload = {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(tmp / ".sps" / "task-queue.md"),
                    "content": "\n".join(f"- task {i}" for i in range(10)),
                },
            }
            proc = _run_gate(payload, tmp)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        finally:
            _cleanup(tmp)

    def test_missing_python3_falls_open(self) -> None:
        tmp = _scratch_repo()
        try:
            payload = {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(tmp / ".sps" / "task-queue.md"),
                    "content": "\n".join(f"- task {i}" for i in range(120)),
                },
            }
            # SPS_PYTHON override pointing at a nonexistent interpreter must
            # make the gate exit 0 (never block a write because of a missing
            # python3) — the same path a python3-less machine takes.
            proc = _run_gate(
                payload, tmp,
                extra_env={"SPS_PYTHON": "sps-no-such-python3"},
            )
            self.assertEqual(
                proc.returncode, 0,
                "missing python3 must fall open (exit 0), never block",
            )
        finally:
            _cleanup(tmp)

    def test_malformed_payload_falls_open(self) -> None:
        tmp = _scratch_repo()
        try:
            proc = subprocess.run(
                ["bash", str(tmp / "scripts" / "sps-hook-gate.sh"), "pre"],
                input="not json at all {",
                capture_output=True,
                text=True,
                cwd=tmp,
                timeout=60,
                env={**ENV_BASE, "SPS_TEST_HOOKS": "1"},
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        finally:
            _cleanup(tmp)


class TestMirrorLaw(unittest.TestCase):
    """skill/sps/scripts mirrors must be byte-identical to scripts/."""

    def test_mirrors_byte_identical(self) -> None:
        for name in ("sps-hooks.sh", "sps-hook-gate.sh"):
            a = (REPO_ROOT / "scripts" / name).read_bytes()
            b = (REPO_ROOT / "skill" / "sps" / "scripts" / name).read_bytes()
            self.assertEqual(a, b, f"mirror drifted: {name}")

    def test_real_repo_status_reports_not_installed(self) -> None:
        """Report-only sanity on the live tree (never installs there)."""
        proc = subprocess.run(
            ["bash", str(HOOKS), "status"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=60,
            env={**ENV_BASE},
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
