"""Contract tests for the skill-provenance gate (T-29).

scripts/sps-provenance.sh pins content digests of third-party skills found in
the installer's SYNC_PATHS skills dirs (bundled MANAGED_SKILLS are skipped —
they are governed by the install manifest). These tests pin that:
1. `pin` writes ~/.sps/provenance.json with one record per third-party skill,
2. `check` reports PINNED-OK on unchanged content and exit 0,
3. `check` reports PROVENANCE-DRIFT after a SKILL.md mutation,
4. `check` reports UNPINNED for a skill added after pinning,
5. `--strict` exits 1 on drift (and only on drift),
6. bundled skills (sps / sps-cms / sps-seo) are never pinned.

Subprocess-driven against a scratch HOME with fake skills dirs — the live
~/.claude/skills and ~/.sps/provenance.json are never touched.
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "sps-provenance.sh"

MANAGED = ("sps", "sps-cms", "sps-seo")


def _run(home: Path, *args: str):
    env = dict(os.environ, HOME=str(home))
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True, text=True, env=env, cwd=str(REPO_ROOT),
    )


def _mk_skill(dirs_root: Path, name: str, body: str = "hello") -> Path:
    d = dirs_root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"# {name}\n{body}\n", encoding="utf-8")
    (d / "extra.txt").write_text("support file\n", encoding="utf-8")
    return d


class TestProvenance(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.home = Path(self._temp.name) / "home"
        self.home.mkdir()
        # Fake install.sh so the script parses MANAGED_SKILLS/SYNC_PATHS from
        # a controlled tree instead of the real installer.
        self.repo_shim = Path(self._temp.name) / "shim"
        (self.repo_shim / "scripts").mkdir(parents=True)
        (self.repo_shim / "install.sh").write_text(
            'MANAGED_SKILLS=("sps" "sps-cms" "sps-seo")\n'
            "SYNC_PATHS=(\n"
            f'  "{self.home}/.claude/skills"\n'
            f'  "{self.home}/.cursor/skills"\n'
            ")\n",
            encoding="utf-8",
        )
        # Copy the real script into the shim so its install.sh lookup finds
        # the fake one (lookup walks up from the script's own location).
        self.script = self.repo_shim / "scripts" / "sps-provenance.sh"
        self.script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
        self.claude_skills = self.home / ".claude" / "skills"
        self.cursor_skills = self.home / ".cursor" / "skills"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _run_shim(self, *args: str):
        env = dict(os.environ, HOME=str(self.home))
        return subprocess.run(
            ["bash", str(self.script), *args],
            capture_output=True, text=True, env=env, cwd=str(REPO_ROOT),
        )

    def test_pin_writes_json_and_check_reports_pinned_ok(self) -> None:
        _mk_skill(self.claude_skills, "cool-skill")
        _mk_skill(self.cursor_skills, "other-skill")
        proc = self._run_shim("pin")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        store = json.loads((self.home / ".sps" / "provenance.json").read_text())
        self.assertIn("cool-skill", store)
        self.assertIn("other-skill", store)
        self.assertIn("digest", store["cool-skill"])
        self.assertIn("pinned_at", store["cool-skill"])
        proc = self._run_shim("check")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("PINNED-OK: cool-skill", proc.stdout)
        self.assertIn("0 drifted, 0 unpinned", proc.stdout)

    def test_bundled_managed_skills_are_skipped(self) -> None:
        for name in MANAGED:
            _mk_skill(self.claude_skills, name)
        _mk_skill(self.claude_skills, "third-party")
        proc = self._run_shim("pin")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        store = json.loads((self.home / ".sps" / "provenance.json").read_text())
        self.assertEqual(list(store), ["third-party"])
        for name in MANAGED:
            self.assertNotIn(name, store)

    def test_mutated_skill_md_reports_drift(self) -> None:
        d = _mk_skill(self.claude_skills, "cool-skill")
        self._run_shim("pin")
        (d / "SKILL.md").write_text("# cool-skill\ntampered\n", encoding="utf-8")
        proc = self._run_shim("check")
        self.assertEqual(proc.returncode, 0)  # report-only by default
        self.assertIn("PROVENANCE-DRIFT: cool-skill", proc.stdout)

    def test_mutated_support_file_reports_drift(self) -> None:
        d = _mk_skill(self.claude_skills, "cool-skill")
        self._run_shim("pin")
        (d / "extra.txt").write_text("changed\n", encoding="utf-8")
        proc = self._run_shim("check")
        self.assertIn("PROVENANCE-DRIFT: cool-skill", proc.stdout)

    def test_new_skill_after_pin_reports_unpinned(self) -> None:
        _mk_skill(self.claude_skills, "cool-skill")
        self._run_shim("pin")
        _mk_skill(self.claude_skills, "late-arrival")
        proc = self._run_shim("check")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("UNPINNED: late-arrival", proc.stdout)
        self.assertIn("PINNED-OK: cool-skill", proc.stdout)

    def test_strict_exits_1_on_drift_only(self) -> None:
        d = _mk_skill(self.claude_skills, "cool-skill")
        self._run_shim("pin")
        _mk_skill(self.claude_skills, "late-arrival")  # UNPINNED, not drift
        (d / "SKILL.md").write_text("# cool-skill\ntampered\n", encoding="utf-8")
        proc = self._run_shim("check", "--strict")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROVENANCE-DRIFT: cool-skill", proc.stdout)
        # Unpinned alone must NOT trip --strict (onboarding state, not tampering).
        (d / "SKILL.md").write_text("# cool-skill\nhello\n", encoding="utf-8")  # restore original
        proc = self._run_shim("check", "--strict")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("UNPINNED: late-arrival", proc.stdout)

    def test_no_skills_dirs_notes_and_exits_0(self) -> None:
        proc = self._run_shim("check")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("no skills directories found", proc.stdout)
        proc = self._run_shim("pin")
        self.assertEqual(proc.returncode, 0)

    def test_no_provenance_json_all_skills_unpinned(self) -> None:
        _mk_skill(self.claude_skills, "cool-skill")
        proc = self._run_shim("check")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("UNPINNED: cool-skill", proc.stdout)
        self.assertNotIn("PINNED-OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
