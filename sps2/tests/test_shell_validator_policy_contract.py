#!/usr/bin/env python3
"""Guards for the shell validators that consume the canonical attribution policy.

These tests exist because of a defect class a Python-only suite cannot see. A
migrated `.sh` validator can be syntactically valid and still be inert,
inverted, or a silent no-op. Every defect found in review during SPEC-2 fitted
one of five shapes, and each shape has a static guard below:

  1. `bash -n` never run -> an unbalanced `if` kills the whole validator.
  2. Heredoc body indented -> python exits 1 on IndentationError, which a
     branch reading non-zero as "agent found" turns into a false positive.
  3. A policy lookup branched as though non-zero meant "found" -> an unavailable
     policy silently becomes an approval PASS.
  4. `rx = matcher.pattern` -> `rx.search` raises AttributeError, which reads as
     a hit that does not exist.
  5. An unguarded policy import in a CAPTURED-output block -> the captured
     string is empty, every `[ -n "$out" ]` guard is false, and the control
     records neither pass nor fail.

These are static guards: cheap, and they run without executing a validator.
The behavioural proof - injecting an agent approval, then deleting the policy -
is recorded in the SPEC-2 report, because running the full validators inside a
unit test is slow and each spawns many child processes.
"""
import os
import re
import subprocess
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MIGRATED_SHELL = [
    "sps2/tools/validate-p3.sh",
    "sps2/tools/validate-p4.sh",
    ".sps/tools/validate-capability.sh",
    ".sps/tools/validate-control.sh",
    ".sps/tools/validate-governance.sh",
]

# Validators that define agent_flagged_* helpers whose exit status carries the
# verdict, and therefore MUST branch on that status rather than output emptiness.
# Not used for assertion; retained as documentation of which validators own a
# named agent_verdict helper.
VERDICT_SHELL = [
    ".sps/tools/validate-governance.sh",
]


def _read(rel):
    with open(os.path.join(REPO, rel), "r", encoding="utf-8") as fh:
        return fh.read()


def _heredoc_bodies(text):
    """Yield (terminator, body_lines) for every quoted heredoc."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.search(r"<<-?'([A-Z_][A-Z0-9_]*)'", lines[i])
        if not m:
            i += 1
            continue
        term = m.group(1)
        start = i + 1
        j = start
        while j < len(lines) and lines[j].strip() != term:
            j += 1
        yield term, lines, start, j
        i = j + 1


class TestShellValidatorsParse(unittest.TestCase):
    def test_every_migrated_validator_parses(self):
        for rel in MIGRATED_SHELL:
            with self.subTest(validator=rel):
                proc = subprocess.run(["bash", "-n", os.path.join(REPO, rel)],
                                      capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0,
                                 "%s does not parse:\n%s" % (rel, proc.stderr))

    def test_python_heredoc_bodies_start_at_column_zero(self):
        """A heredoc body is passed verbatim to python.

        If its first line is indented, python raises IndentationError and exits
        non-zero. In a validator that reads non-zero as "agent attributed", that
        is a false positive on every run - observed in review.
        """
        for rel in MIGRATED_SHELL:
            for term, lines, start, end in _heredoc_bodies(_read(rel)):
                if start >= end:
                    continue
                body = lines[start:end]
                # only care about bodies that are python (they contain imports)
                if not any(l.strip().startswith(("import ", "from ")) for l in body):
                    continue
                with self.subTest(validator=rel, heredoc=term):
                    self.assertFalse(
                        body[0].startswith((" ", "\t")),
                        "%s: %s heredoc body starts indented (%r); python will "
                        "raise IndentationError and exit non-zero"
                        % (rel, term, body[0][:40]))


class TestPolicyLookupsFailClosed(unittest.TestCase):
    def test_captured_policy_lookups_are_guarded(self):
        """An unguarded import in a CAPTURED-output block is a silent no-op.

        A block that redirects to a file and then tests `[ -s file ]` is already
        fail-closed: the traceback lands in the file and is reported. But with
        `X="$(python3 ...)"` a failed import yields X="", every `[ -n "$X" ]`
        guard is false, and the control records nothing at all.
        """
        for rel in MIGRATED_SHELL:
            lines = _read(rel).splitlines()
            for i, line in enumerate(lines):
                if '="$(python3' not in line:
                    continue
                # The command substitution may close on the opening line
                # itself, e.g. OUT="$(python3 "$CHECK" gate ...)".
                if line.rstrip().endswith(')"'):
                    close = i
                else:
                    close = next((k for k in range(i + 1, min(i + 400, len(lines)))
                                  if lines[k].rstrip().endswith(')"')), None)
                if close is None:
                    continue
                if "import attribution" not in "\n".join(lines[i:close]):
                    continue
                imports = [k for k in range(i, close)
                           if "import attribution" in lines[k]]
                guarded = all(
                    any("try:" in lines[m] for m in range(max(i, k - 6), k))
                    for k in imports)
                with self.subTest(validator=rel, line=i + 1):
                    self.assertTrue(
                        guarded,
                        "%s:%d captures the output of a python block that "
                        "imports the policy with no try/except guard. If the "
                        "policy is unavailable the captured string is empty and "
                        "the control records neither pass nor fail."
                        % (rel, i + 1))

    def test_no_verdict_helper_is_branched_on_output_emptiness(self):
        """The inverted shape: `if VAR="$(helper)"; then fail; else pass`.

        The helpers exit 1 when an agent name is found. Branching on output
        emptiness therefore means exit 0 (clean) takes the `else` branch and
        reports pass, while a helper that could not run at all - exit 2 - takes
        the same `else` branch. An unavailable policy then reads as clean.
        """
        inverted = re.compile(r'if\s+\w+="\$\(\s*agent_flagged_\w+\)')
        for rel in MIGRATED_SHELL:
            with self.subTest(validator=rel):
                self.assertIsNone(
                    inverted.search(_read(rel)),
                    "%s branches an agent-verdict helper on output emptiness; "
                    "use a captured exit status so 'could not run' can fail"
                    % rel)

    def test_each_agent_flagged_call_captures_its_exit_status(self):
        """Per call, not per file.

        A file that branches correctly on one control still fails if a second
        control reverts to reading output emptiness. Checking per file would
        let the correct control mask the broken one - which is how this
        inversion survived one round of review.
        """
        for rel in MIGRATED_SHELL:
            lines = _read(rel).splitlines()
            calls = [k for k, l in enumerate(lines)
                     if re.search(r'=\"\$\(agent_flagged_\w+\)"', l)]
            for k in calls:
                nxt = next((m for m in range(k + 1, min(k + 4, len(lines)))
                            if lines[m].strip()), None)
                with self.subTest(validator=rel, line=k + 1):
                    self.assertIsNotNone(nxt, "%s:%d helper call has no branch"
                                         % (rel, k + 1))
                    # the capture may sit on the call line itself or the next
                    captures = (re.search(r"_rc\w*=\$\?", lines[k])
                                or (nxt is not None
                                    and re.search(r"_rc\w*=\$\?", lines[nxt])))
                    self.assertIsNotNone(
                        captures,
                        "%s:%d calls a verdict helper without capturing its "
                        "exit status on that line or the next; a failure and "
                        "a clean result would collapse into one branch"
                        % (rel, k + 1))

    def test_no_validator_searches_the_pattern_string(self):
        """`matcher.pattern` is a str; `str.search` raises AttributeError."""
        pattern = re.compile(
            r"(\w+)\s*=\s*(?:ATTR|_ATTR|ATTRRIBUTION|_ATTRIBUTION)\.AGENTISH\.pattern")
        for rel in MIGRATED_SHELL:
            with self.subTest(validator=rel):
                found = pattern.findall(_read(rel))
                self.assertEqual(
                    found, [],
                    "%s assigns %s from AGENTISH.pattern; use the compiled "
                    "matcher or the module" % (rel, found))


class TestPolicyIsTheOnlySourceForShell(unittest.TestCase):
    def test_no_shell_validator_hardcodes_a_token_alternation(self):
        alternation = re.compile(r"agent\|ai\|assistant")
        for rel in MIGRATED_SHELL:
            with self.subTest(validator=rel):
                self.assertIsNone(
                    alternation.search(_read(rel)),
                    "%s still hardcodes an agent-token alternation" % rel)


if __name__ == "__main__":
    unittest.main()
