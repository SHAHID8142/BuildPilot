"""Contract tests for the .sps/ backup + restore tool (scripts/sps-backup.sh).

T-24: sps-backup.sh snapshots a project's .sps/ directory into a rolling
window of timestamped tar.gz archives, and restores one back with an
explicit --yes gate. These tests pin:

1. snapshot creates a timestamped archive under .sps/backups/,
2. retention keeps the last 10 snapshots and prunes older ones (PRUNED: line),
3. restore WITHOUT --yes refuses and changes nothing,
4. restore WITH --yes replaces .sps/ and leaves the pre-restore copy
   (.sps.pre-restore-<ts>) as the user's safety net,
5. list shows the snapshot entries.

Runs the script as a subprocess against a scratch project directory — the
live tree is never touched.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "scripts" / "sps-backup.sh"


def _run(args, project_root):
    env = dict(os.environ)
    return subprocess.run(
        ["bash", str(TOOL), *args],
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )


def _make_project(tmp):
    """Scratch git project with a populated .sps/ (git root needed by the tool)."""
    root = Path(tmp) / "proj"
    (root / ".sps").mkdir(parents=True)
    for i in range(3):
        (root / ".sps" / f"file{i}.md").write_text(f"content {i}\n", encoding="utf-8")
    (root / ".sps" / "law-rejections-20260101.jsonl").write_text(
        '{"archived": true}\n", encoding="utf-8"'
    )
    (root / ".sps" / "quarantine").mkdir()
    (root / ".sps" / "quarantine" / "junk.txt").write_text("junk\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    return root


def _snapshot_count(root):
    return len(list((root / ".sps" / "backups").glob("sps-*.tar.gz")))


class TestSpsBackup(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.root = _make_project(self._temp.name)

    def tearDown(self):
        self._temp.cleanup()

    def test_snapshot_creates_archive(self):
        p = _run(["snapshot"], self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("SNAPSHOT:", p.stdout)
        self.assertEqual(_snapshot_count(self.root), 1)
        # Exclusions: quarantine and law-rejection ARCHIVES are not in the tarball
        listing = subprocess.run(
            ["tar", "-tzf", str(next((self.root / ".sps" / "backups").glob("sps-*.tar.gz")))],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertNotIn("quarantine", listing)
        self.assertNotIn("law-rejections-20260101.jsonl", listing)
        self.assertIn("file0.md", listing)

    def test_missing_sps_is_graceful(self):
        empty = Path(self._temp.name) / "empty"
        empty.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=empty, check=True)
        p = _run(["snapshot"], empty)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("nothing to snapshot", p.stdout)

    def test_retention_keeps_10_prunes_older(self):
        for _ in range(11):
            p = _run(["snapshot"], self.root)
            self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(_snapshot_count(self.root), 10)
        self.assertIn("PRUNED:", p.stdout)

    def test_restore_without_yes_refuses(self):
        _run(["snapshot"], self.root)
        snap = sorted((self.root / ".sps" / "backups").glob("sps-*.tar.gz"))[0]
        (self.root / ".sps" / "mutated.txt").write_text("changed\n", encoding="utf-8")
        p = _run(["restore", str(snap)], self.root)
        self.assertNotEqual(p.returncode, 0, "restore must refuse without --yes")
        self.assertIn("--yes", p.stdout)
        self.assertIn("preview only", p.stdout)
        # nothing changed
        self.assertTrue((self.root / ".sps" / "mutated.txt").exists())
        self.assertFalse(list(self.root.glob(".sps.pre-restore-*")))

    def test_restore_with_yes_replaces_and_keeps_safety_net(self):
        _run(["snapshot"], self.root)
        snap = sorted((self.root / ".sps" / "backups").glob("sps-*.tar.gz"))[0]
        (self.root / ".sps" / "mutated.txt").write_text("changed\n", encoding="utf-8")
        (self.root / ".sps" / "file0.md").write_text("MUTATED\n", encoding="utf-8")
        p = _run(["restore", str(snap), "--yes"], self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("RESTORED:", p.stdout)
        self.assertIn("MOVED ASIDE:", p.stdout)
        # content matches the snapshot (mutated.txt gone, file0.md original)
        self.assertFalse((self.root / ".sps" / "mutated.txt").exists())
        self.assertEqual((self.root / ".sps" / "file0.md").read_text(), "content 0\n")
        # safety net exists and still holds the mutated state
        pres = list(self.root.glob(".sps.pre-restore-*"))
        self.assertEqual(len(pres), 1)
        self.assertTrue((pres[0] / "mutated.txt").exists())
        self.assertEqual((pres[0] / "file0.md").read_text(), "MUTATED\n")

    def test_list_shows_entries(self):
        _run(["snapshot"], self.root)
        p = _run(["list"], self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("sps-", p.stdout)
        self.assertIn("age", p.stdout)

    def test_list_empty_is_graceful(self):
        p = _run(["list"], self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("no snapshots", p.stdout)


if __name__ == "__main__":
    unittest.main()
