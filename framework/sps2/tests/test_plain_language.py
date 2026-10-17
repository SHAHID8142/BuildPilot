"""Contract tests for plain-language mode (T-35).

When a project sets `language: plain` in .sps/agent.md, gate messages are
shown from the plain templates in framework/sps2/templates/plain-gates/.
These tests pin:

1. is_plain is False when .sps/agent.md does not exist (default is inert),
2. is_plain is False for `language: technical` (any other value means default),
3. is_plain is True for `language: plain` (spacing/comment tolerant),
4. render substitutes {placeholders} from fields,
5. an unknown gate fails closed: PLAIN_GATE_MISSING on stderr, exit 1,
6. a missing field renders `<fill in: name>` instead of crashing,
7. all 5 gate templates exist and each starts its body with a
   "What you're deciding:" line (pins the user-facing contract).

The live tree is never touched — every filesystem test runs in a temp dir.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "plain_language.py"
TEMPLATE_DIR = REPO_ROOT / "framework" / "sps2" / "templates" / "plain-gates"

sys.path.insert(0, str(REPO_ROOT / "framework" / "sps2" / "tools"))
import plain_language  # noqa: E402

GATES = ("kickoff", "g1", "g2", "approval-packet", "handoff")


def _run_cli(*argv: str):
    proc = subprocess.run(
        [sys.executable, str(TOOL), *argv],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return proc.returncode, proc.stdout, proc.stderr


class PlainLanguageTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.project = Path(self._temp.name) / "proj"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def write_agent_md(self, text: str) -> None:
        sps = self.project / ".sps"
        sps.mkdir(parents=True, exist_ok=True)
        (sps / "agent.md").write_text(text, encoding="utf-8")


class TestIsPlain(PlainLanguageTestBase):
    def test_no_agent_md_is_false(self):
        # (a) no .sps/agent.md at all -> not plain, default behavior
        self.project.mkdir(parents=True)
        self.assertFalse(plain_language.is_plain(self.project))

    def test_technical_is_false(self):
        # (b) `language: technical` must NOT match
        self.write_agent_md("# Agent\n\nlanguage: technical\n")
        self.assertFalse(plain_language.is_plain(self.project))

    def test_plain_is_true(self):
        # (c) `language: plain` -> plain mode on
        self.write_agent_md("# Agent\n\nlanguage: plain\n")
        self.assertTrue(plain_language.is_plain(self.project))

    def test_plain_with_spacing_and_comment_is_true(self):
        self.write_agent_md("language:   plain   # client is non-technical\n")
        self.assertTrue(plain_language.is_plain(self.project))

    def test_other_value_is_false(self):
        self.write_agent_md("language: plain-text\n")
        self.assertFalse(plain_language.is_plain(self.project))

    def test_language_mention_in_prose_is_false(self):
        # only a real `language: plain` setting line counts, not prose
        self.write_agent_md("we once wrote language: plain in a doc\n")
        self.assertFalse(plain_language.is_plain(self.project))


class TestRender(PlainLanguageTestBase):
    def test_render_substitutes_fields(self):
        # (d) {placeholders} filled from fields
        self.write_agent_md("language: plain\n")
        out = plain_language.render(
            self.project, "g1",
            project="Acme Ceramics", summary="A 5-page shop",
            options="- yes\n- no",
        )
        self.assertIn("Acme Ceramics", out)
        self.assertIn("A 5-page shop", out)
        self.assertNotIn("{project}", out)
        self.assertNotIn("{summary}", out)

    def test_unknown_gate_errors_exit_1(self):
        # (e) unknown gate -> PLAIN_GATE_MISSING on stderr, exit 1
        self.write_agent_md("language: plain\n")
        with self.assertRaises(SystemExit) as ctx:
            plain_language.render(self.project, "quarterly-review")
        self.assertEqual(ctx.exception.code, 1)

    def test_unknown_gate_cli_exit_1_with_plain_gate_missing(self):
        self.write_agent_md("language: plain\n")
        code, out, err = _run_cli("render", str(self.project), "quarterly-review")
        self.assertEqual(code, 1)
        self.assertIn("PLAIN_GATE_MISSING", err)

    def test_missing_field_renders_fallback(self):
        # (f) missing field -> <fill in: name>, no crash
        self.write_agent_md("language: plain\n")
        out = plain_language.render(self.project, "g1", project="Acme")
        self.assertIn("<fill in: summary>", out)
        self.assertIn("<fill in: options>", out)
        self.assertIn("Acme", out)

    def test_empty_field_renders_fallback(self):
        self.write_agent_md("language: plain\n")
        out = plain_language.render(self.project, "g1", project="", summary="s")
        self.assertIn("<fill in: project>", out)

    def test_render_cli_roundtrip(self):
        self.write_agent_md("language: plain\n")
        code, out, err = _run_cli(
            "render", str(self.project), "g1",
            "--field", "project=Acme",
            "--field", "summary=short plan",
            "--field", "options=- yes",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("**What you're deciding:**", out)
        self.assertIn("Acme", out)
        self.assertIn("short plan", out)

    def test_is_plain_cli_exit_0(self):
        code, out, _ = _run_cli("is-plain", str(self.project))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "false")
        self.write_agent_md("language: plain\n")
        code, out, _ = _run_cli("is-plain", str(self.project))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "true")


class TestTemplatesPinned(unittest.TestCase):
    # (g) all 5 templates exist and carry the "What you're deciding:" line
    def test_all_five_templates_exist(self):
        for gate in GATES:
            with self.subTest(gate=gate):
                self.assertTrue(
                    (TEMPLATE_DIR / f"{gate}.md").is_file(),
                    f"missing plain template for gate '{gate}'")

    def test_each_template_has_deciding_line(self):
        for gate in GATES:
            with self.subTest(gate=gate):
                text = (TEMPLATE_DIR / f"{gate}.md").read_text(encoding="utf-8")
                self.assertIn("**What you're deciding:**", text)

    def test_deciding_line_is_first_line(self):
        for gate in GATES:
            with self.subTest(gate=gate):
                first = (TEMPLATE_DIR / f"{gate}.md").read_text(
                    encoding="utf-8").splitlines()[0]
                self.assertTrue(first.startswith("**What you're deciding:**"),
                                f"{gate}.md must open with the deciding line")

    def test_templates_within_40_lines(self):
        for gate in GATES:
            with self.subTest(gate=gate):
                n = len((TEMPLATE_DIR / f"{gate}.md").read_text(
                    encoding="utf-8").splitlines())
                self.assertLessEqual(n, 40, f"{gate}.md is {n} lines (max 40)")


if __name__ == "__main__":
    unittest.main()
