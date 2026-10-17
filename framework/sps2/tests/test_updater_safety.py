"""Regression tests for installer updater safety boundaries."""

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[3]
BOOTSTRAP = REPO / "scripts" / "bootstrap-sps.sh"
GET_SPS = REPO / "get-sps.sh"
BASH_UPDATER = REPO / "scripts" / "sps-update.sh"
PS_BOOTSTRAP = REPO / "get-sps.ps1"
PS_UPDATER = REPO / "scripts" / "update-sps.ps1"
MIRROR_BOOTSTRAP = REPO / "skill" / "sps" / "scripts" / "bootstrap-sps.sh"
MIRROR_BASH_UPDATER = REPO / "skill" / "sps" / "scripts" / "sps-update.sh"
MIRROR_PS_UPDATER = REPO / "skill" / "sps" / "scripts" / "update-sps.ps1"


def _git(*arguments, cwd):
    subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _dirty_repository(root):
    repository = root / "source"
    repository.mkdir()
    _git("-c", "init.defaultBranch=main", "init", cwd=repository)
    (repository / "local-change.txt").write_text("preserve me\n", encoding="utf-8")
    return repository


def _fake_command(directory, name):
    path = directory / name
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class BootstrapAutoUpdateTests(unittest.TestCase):
    def test_bash_bootstrap_does_not_auto_apply_updates(self):
        for path in (BOOTSTRAP, MIRROR_BOOTSTRAP):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("sps-update.sh --yes", source)
                self.assertNotIn("auto-applying", source)

    def test_bash_bootstrap_refuses_symlinked_sps_destination(self):
        with tempfile.TemporaryDirectory(prefix="sps-bootstrap-") as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "profile.md"
            sentinel.write_text("preserve me\n", encoding="utf-8")
            target = root / "target"
            target.mkdir()
            (target / ".sps").symlink_to(outside, target_is_directory=True)
            environment = os.environ.copy()
            environment.update({"HOME": str(root / "home")})
            result = subprocess.run(["bash", str(BOOTSTRAP), "--force", str(target)], env=environment,
                                     capture_output=True, text=True, timeout=15, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlinked SPS destination", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve me\n")

    def test_bash_bootstrap_preflights_template_symlinks_before_writing(self):
        for dangling in (False, True):
            with self.subTest(dangling=dangling), tempfile.TemporaryDirectory(prefix="sps-bootstrap-") as directory:
                root = Path(directory)
                target_dir = root / "target"
                destination = target_dir / ".sps"
                destination.mkdir(parents=True)
                target = root / "outside.txt"
                if not dangling:
                    target.write_text("preserve me\n", encoding="utf-8")
                (destination / "profile.md").symlink_to(target)
                environment = os.environ.copy()
                environment["HOME"] = str(root / "home")
                result = subprocess.run(["bash", str(BOOTSTRAP), "--force", str(target_dir)], env=environment,
                                         capture_output=True, text=True, timeout=15, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("symlinked template destination", result.stderr)
                self.assertTrue((destination / "profile.md").is_symlink())
                self.assertFalse((destination / "handoff.md").exists())
                if not dangling:
                    self.assertEqual(target.read_text(encoding="utf-8"), "preserve me\n")
                else:
                    self.assertFalse(target.exists())


class BashUpdaterSafetyTests(unittest.TestCase):
    def test_bootstrap_refuses_dirty_source_before_updating(self):
        with tempfile.TemporaryDirectory(prefix="sps-updater-") as directory:
            root = Path(directory)
            repository = _dirty_repository(root)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            _fake_command(fake_bin, "node")
            _fake_command(fake_bin, "npx")
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                    "SPS_REPO_DIR": str(repository),
                }
            )
            result = subprocess.run(
                ["bash", str(GET_SPS)],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Local changes present", result.stderr)
            self.assertIn("preserve me", (repository / "local-change.txt").read_text(encoding="utf-8"))

    def test_updater_refuses_dirty_source_before_network_check(self):
        with tempfile.TemporaryDirectory(prefix="sps-updater-") as directory:
            root = Path(directory)
            repository = _dirty_repository(root)
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "SPS_REPO_DIR": str(repository),
                }
            )
            result = subprocess.run(
                ["bash", str(BASH_UPDATER), "--yes"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Local changes present", result.stderr)
            self.assertIn("preserve me", (repository / "local-change.txt").read_text(encoding="utf-8"))

    def test_bootstrap_refuses_non_git_destination(self):
        with tempfile.TemporaryDirectory(prefix="sps-updater-") as directory:
            root = Path(directory)
            destination = root / "destination"
            destination.write_text("preserve me\n", encoding="utf-8")
            fake_bin = root / "bin"
            fake_bin.mkdir()
            _fake_command(fake_bin, "node")
            _fake_command(fake_bin, "npx")
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                    "SPS_REPO_DIR": str(destination),
                }
            )
            result = subprocess.run(
                ["bash", str(GET_SPS)],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a Git worktree", result.stderr)
            self.assertEqual(destination.read_text(encoding="utf-8"), "preserve me\n")

    def test_updater_refuses_non_git_destination_before_network_check(self):
        with tempfile.TemporaryDirectory(prefix="sps-updater-") as directory:
            root = Path(directory)
            destination = root / "destination"
            destination.write_text("preserve me\n", encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "SPS_REPO_DIR": str(destination),
                }
            )
            result = subprocess.run(
                ["bash", str(BASH_UPDATER), "--yes"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a Git worktree", result.stderr)
            self.assertEqual(destination.read_text(encoding="utf-8"), "preserve me\n")

    def test_bash_updaters_do_not_contain_default_destructive_fallbacks(self):
        for path in (GET_SPS, BASH_UPDATER, MIRROR_BASH_UPDATER):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("git reset --hard", source)
                self.assertNotIn('rm -rf "$REPO_DIR"', source)

    def test_bash_updater_checks_source_safety_before_network(self):
        source = BASH_UPDATER.read_text(encoding="utf-8")
        self.assertLess(source.index("Local changes present"), source.index("\nchecker\n"))

    def test_bash_updater_stops_on_source_directory_change_failure(self):
        for path in (BASH_UPDATER, MIRROR_BASH_UPDATER):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertIn('if ! cd "$REPO_DIR"; then', source)
                self.assertIn("Cannot enter the updated source directory", source)


class InlineFallbackRemovalTests(unittest.TestCase):
    """Round 26A: the inline remote-version fallback is gone, fail-closed.

    The former fallback (sps-update.sh :51-66) fetched the remote VERSION
    with no format validation when check-update.sh was absent. It is
    replaced by a fail-closed offline return: no network request, exit 2.
    """

    def test_no_inline_remote_version_fetch_remains(self):
        for path in (BASH_UPDATER, MIRROR_BASH_UPDATER):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("raw.githubusercontent.com", source)
                self.assertNotIn("curl", source)

    def test_missing_hardened_checker_fails_closed_with_exit_2(self):
        # Run the updater from an isolated root so neither candidate
        # check-update.sh exists, with a dead curl stub as a belt-and-
        # braces guarantee that no network request is even attemptable.
        with tempfile.TemporaryDirectory(prefix="sps-updater-") as directory:
            root = Path(directory)
            # Isolated copy of the updater with ROOT pointing at the stub tree.
            script_dir = root / "scripts"
            script_dir.mkdir()
            shutil.copyfile(BASH_UPDATER, script_dir / "sps-update.sh")
            stub_bin = root / "bin"
            stub_bin.mkdir()
            curl = stub_bin / "curl"
            curl.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
            curl.chmod(0o755)
            environment = os.environ.copy()
            environment.update({
                "HOME": str(root / "home"),
                "PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}",
                # SPS_REPO_DIR also lacks check-update.sh: the second
                # candidate must miss too.
                "SPS_REPO_DIR": str(root / "empty-repo"),
            })
            (root / "empty-repo").mkdir()
            result = subprocess.run(
                ["bash", str(script_dir / "sps-update.sh"), "--check"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("check-update.sh not found", result.stderr)
            self.assertNotIn("update available", result.stdout)
            self.assertNotIn("up to date", result.stdout)

    def test_missing_checker_path_makes_no_network_request(self):
        # The offline message must be the checker-unavailable one, not a
        # fetch that happened to fail: assert the dead curl stub was never
        # invoked by leaving a marker file if it runs.
        with tempfile.TemporaryDirectory(prefix="sps-updater-") as directory:
            root = Path(directory)
            script_dir = root / "scripts"
            script_dir.mkdir()
            shutil.copyfile(BASH_UPDATER, script_dir / "sps-update.sh")
            stub_bin = root / "bin"
            stub_bin.mkdir()
            curl = stub_bin / "curl"
            curl.write_text(
                "#!/bin/sh\ntouch %s\nexit 7\n" % (root / "curl-ran"),
                encoding="utf-8")
            curl.chmod(0o755)
            environment = os.environ.copy()
            environment.update({
                "HOME": str(root / "home"),
                "PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}",
                "SPS_REPO_DIR": str(root / "empty-repo"),
            })
            (root / "empty-repo").mkdir()
            result = subprocess.run(
                ["bash", str(script_dir / "sps-update.sh"), "--check"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse((root / "curl-ran").exists(),
                             "curl was invoked from the fallback path")


class PowerShellUpdaterSafetyTests(unittest.TestCase):
    def test_powershell_updaters_do_not_contain_default_destructive_fallbacks(self):
        for path in (PS_BOOTSTRAP, PS_UPDATER, MIRROR_PS_UPDATER):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("git reset --hard", source)
                self.assertNotIn("Remove-Item -Recurse -Force $repoDir", source)

    def test_powershell_updater_checks_source_safety_before_update_network(self):
        for path in (PS_UPDATER, MIRROR_PS_UPDATER):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertLess(
                    source.index("Local changes present"),
                    source.index("Offline - cannot check for updates"),
                )
                self.assertLess(
                    source.index("not a Git worktree"),
                    source.index("Offline - cannot check for updates"),
                )

    def test_powershell_clone_failure_does_not_claim_destination_is_unchanged(self):
        for path in (PS_UPDATER, MIRROR_PS_UPDATER, PS_BOOTSTRAP):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertIn("destination may be partially created", source)
                self.assertNotIn("destination left unchanged", source)

    def test_updater_mirrors_are_byte_identical(self):
        for primary, mirror in (
            (BOOTSTRAP, MIRROR_BOOTSTRAP),
            (BASH_UPDATER, MIRROR_BASH_UPDATER),
            (PS_UPDATER, MIRROR_PS_UPDATER),
            (REPO / "scripts" / "check-update.sh", REPO / "skill" / "sps" / "scripts" / "check-update.sh"),
            (REPO / "scripts" / "check-update.ps1", REPO / "skill" / "sps" / "scripts" / "check-update.ps1"),
        ):
            with self.subTest(primary=primary, mirror=mirror):
                self.assertEqual(primary.read_bytes(), mirror.read_bytes())

    @unittest.skipUnless(shutil.which("pwsh"), "pwsh is unavailable")
    def test_powershell_updater_refuses_dirty_source(self):
        with tempfile.TemporaryDirectory(prefix="sps-updater-") as directory:
            root = Path(directory)
            home = root / "home"
            repository = home / ".sps" / "src" / "Shahid-Personal-SkillSet"
            repository.mkdir(parents=True)
            _git("-c", "init.defaultBranch=main", "init", cwd=repository)
            (repository / "local-change.txt").write_text("preserve me\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = str(home)
            result = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(PS_UPDATER),
                    "-Yes",
                ],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Local changes present", result.stdout)
            self.assertIn(
                "preserve me",
                (repository / "local-change.txt").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
