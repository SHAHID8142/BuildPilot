"""Contract tests for the COPY-GATE copy validator (check_copy.py).

skill/sps/COPY-GATE.md machine-checkable laws, enforced by
framework/sps2/tools/check_copy.py. These tests pin that it:
1. FIRES on EN stock slop phrases (CRITICAL),
2. FIRES on Bangla slop phrases, সাধু forms, word-initial ড়, missing দাঁড়ি,
3. FIRES on negative parallelism (2+), Lorem ipsum, and lexicon density,
4. passes clean human copy (EN + BN) in both modes,
5. advisory mode never exits nonzero; deployment mode exits 1 on CRITICAL,
6. does not self-trip on the BuildPilot repo itself.

Subprocess-driven against a scratch tree — the live repo is never touched.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "check_copy.py"


def _run(*args: str):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


class TestCheckCopy(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.tree = Path(self._temp.name)

    def _write(self, rel: str, text: str) -> Path:
        p = self.tree / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_en_slop_phrase_fails_deployment(self) -> None:
        self._write("index.html", "<h1>In today's fast-paced world, buy things.</h1>")
        r = _run(str(self.tree), "--mode", "deployment")
        self.assertEqual(r.returncode, 1)
        self.assertIn("COPY_EN_SLOP_PHRASE", r.stderr)

    def test_bn_slop_and_sadhu_fail(self) -> None:
        self._write("page.html", "<p>গুরুত্বপূর্ণ ভূমিকা পালন করে।</p>"
                                 "<p>আমরা করিয়াছে এই কাজ।</p>")
        r = _run(str(self.tree), "--mode", "deployment")
        self.assertEqual(r.returncode, 1)
        self.assertIn("COPY_BN_SLOP_PHRASE", r.stderr)
        self.assertIn("COPY_BN_SADHU_WB_FORM", r.stderr)

    def test_bn_initial_rra_fails(self) -> None:
        self._write("page.html", "<p>ড়াক্তার ড়ে শুরু হয় না কোনো শব্দ।</p>")
        r = _run(str(self.tree), "--mode", "deployment")
        self.assertIn("COPY_BN_INITIAL_RRA", r.stderr)

    def test_bn_danda_missing_fails(self) -> None:
        self._write("page.md", "# শিরোনাম\n\nঢাকার তাঁতিদের হাতে বোনা জামদানি একটি ঐতিহ্যবাহী শিল্প এবং এটি প্রজন্মের পর প্রজন্ম ধরে চলে আসছে এই অঞ্চলে.\n")
        r = _run(str(self.tree), "--mode", "deployment")
        self.assertIn("COPY_BN_DANDA", r.stderr)

    def test_negative_parallelism_fires_on_two(self) -> None:
        self._write("page.md",
                    "This is not just a product, but a revolution. "
                    "It is not just a tool, but a transformation. "
                    "Real value for real teams every single day of the year.")
        r = _run(str(self.tree), "--mode", "deployment")
        self.assertIn("COPY_NEGATIVE_PARALLELISM", r.stderr)

    def test_lorem_ipsum_fails(self) -> None:
        self._write("page.md", "Lorem ipsum dolor sit amet, consectetur.")
        r = _run(str(self.tree), "--mode", "deployment")
        self.assertIn("COPY_PLACEHOLDER", r.stderr)

    def test_clean_copy_passes_both_modes(self) -> None:
        self._write("index.md",
                    "# হাতে বোনা জামদানি\n\n"
                    "ঢাকার তাঁতিদের হাতে বোনা খাঁটি জামদানি শাড়ি। প্রতিটি সুতোয় "
                    "প্রজন্মের যত্ন। অর্ডার করুন আজই।\n\n"
                    "## Fast delivery, real warranty\n\n"
                    "Orders ship within 48 hours from Dhaka. Every saree carries "
                    "a 7-day return promise, no questions asked.")
        for mode in ("advisory", "deployment"):
            r = _run(str(self.tree), "--mode", mode)
            self.assertEqual(r.returncode, 0, f"mode={mode}: {r.stderr}")

    def test_advisory_never_fails(self) -> None:
        self._write("index.html", "<h1>In today's fast-paced world, buy things.</h1>")
        r = _run(str(self.tree), "--mode", "advisory")
        self.assertEqual(r.returncode, 0)
        self.assertIn("COPY_EN_SLOP_PHRASE", r.stderr)

    def test_repo_does_not_self_trip(self) -> None:
        r = _run(str(REPO_ROOT), "--mode", "deployment")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
