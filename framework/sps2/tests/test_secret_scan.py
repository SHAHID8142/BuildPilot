"""Contract tests for the T-25 secret-scan gate (scripts/secret-scan.sh).

Follows the subprocess-driven, scratch-copy conventions of
test_generated_tests.py: the live tree is never modified — each test copies
the scan script into a temp git repo and runs it there.

Pins:
1. a clean scratch repo -> exit 0,
2. a planted sk_live_ key -> exit 1 with the value MASKED in output,
3. an allowlisted hit -> exit 0,
4. a binary file containing fake key bytes -> skipped (exit 0),
5. exit 2 outside a git repository.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN = REPO_ROOT / "scripts" / "secret-scan.sh"

FAKE_KEY = "sk_live_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"  # synthetic, 30-char tail
ALLOWLIST_HIT = "glpat-AbCdEfGhIjKlMnOpQrSt"  # same shape as repo fixtures


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env={
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
            "HOME": str(repo),
            "PATH": "/usr/bin:/bin",
        },
    )


def _scratch_repo() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="sps-secret-scan-test-"))
    _git(tmp, "init", "-q")
    _git(tmp, "config", "user.email", "t@example.com")
    _git(tmp, "config", "user.name", "t")
    (tmp / "README.md").write_text("# scratch\n", encoding="utf-8")
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "-qm", "init")
    return tmp


def _run_scan(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCAN)],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=60,
    )


class TestSecretScan(unittest.TestCase):
    """secret-scan.sh contract: clean=0, hit=1 masked, allowlist=0, binary skip."""

    def test_clean_repo_exits_zero(self) -> None:
        repo = _scratch_repo()
        try:
            proc = _run_scan(repo)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("clean", proc.stdout)
        finally:
            subprocess.run(["rm", "-rf", str(repo)], check=True)

    def test_planted_key_exits_one_with_masked_output(self) -> None:
        repo = _scratch_repo()
        try:
            (repo / "config.txt").write_text(
                f"token = {FAKE_KEY}\n", encoding="utf-8"
            )
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "plant")
            proc = _run_scan(repo)
            self.assertEqual(proc.returncode, 1, proc.stdout)
            self.assertIn("config.txt", proc.stdout)
            self.assertIn("SECRET HIT", proc.stdout)
            # The full secret must never be printed — only first 6 chars + ***.
            self.assertNotIn(FAKE_KEY, proc.stdout)
            self.assertIn("***", proc.stdout)
        finally:
            subprocess.run(["rm", "-rf", str(repo)], check=True)

    def test_allowlisted_line_exits_zero(self) -> None:
        repo = _scratch_repo()
        try:
            (repo / "fixture.md").write_text(
                f"synthetic: {ALLOWLIST_HIT}\n", encoding="utf-8"
            )
            (repo / ".secrets-allowlist").write_text(
                "# comment line\n\n"
                f"{ALLOWLIST_HIT}\n",
                encoding="utf-8",
            )
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "allowlisted fixture")
            proc = _run_scan(repo)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        finally:
            subprocess.run(["rm", "-rf", str(repo)], check=True)

    def test_binary_file_with_key_bytes_is_skipped(self) -> None:
        repo = _scratch_repo()
        try:
            (repo / "blob.bin").write_bytes(
                b"\x00\x01\x02\xff" + FAKE_KEY.encode() + b"\xfe\xfd"
            )
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "binary")
            proc = _run_scan(repo)
            self.assertEqual(
                proc.returncode, 0, "binary file must be skipped: " + proc.stdout
            )
        finally:
            subprocess.run(["rm", "-rf", str(repo)], check=True)

    def test_exits_two_outside_git_repo(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sps-nogit-") as tmp:
            proc = subprocess.run(
                ["bash", str(SCAN)],
                capture_output=True,
                text=True,
                cwd=tmp,
                timeout=60,
                env={
                    "PATH": "/usr/bin:/bin",
                    "HOME": tmp,
                    "GIT_CEILING_DIRECTORIES": tmp,
                },
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)

    def test_real_repo_scans_clean_or_allowlisted(self) -> None:
        """The live tree must pass the gate (clean or allowlisted hits only)."""
        proc = subprocess.run(
            ["bash", str(SCAN)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=120,
        )
        self.assertEqual(
            proc.returncode, 0, "real repo has unallowed secret-shaped hits:\n" + proc.stdout
        )


if __name__ == "__main__":
    unittest.main()
