#!/usr/bin/env python3
"""P7 readiness under the D-P3-D zero-adapter (delete-all) state.

D-P3-D is an APPROVED User decision (decided_by=User, decided_on=2026-10-04)
whose text reads:

    "Delete all adapters means deletion of all per-agent adapter
     entries/directories. The core-owned adapter contract and registry
     remain. An empty adapter registry [] is valid and must be accepted by
     the portability test."

Deleting every per-agent adapter removes the DECLARED `generic` fallback along
with the two real adapters (codex, opencode), because `generic` IS a per-agent
adapter entry. The empty state therefore has no `generic` entry by
construction.

`validate-p7-readiness.py` originally computed

    generic = PT.FALLBACK_ADAPTER_ID in PT.entry_ids(adapters)

and required `generic` for `delivered`. Under an empty registry that expression
is False, so `delivered` became False while the roadmap record still claimed
SATISFIED, emitting RECORD_OVERSTATES_P3 and failing the portability harness in
exactly the state D-P3-D requires to be accepted. The `count_ok` invariant
immediately below already carried the empty-registry exemption; `generic` did
not, which made the exemption only partially applied.

DESIGN NOTE — why these tests RUN THE VALIDATOR instead of re-deriving
`delivered` in Python. An earlier version of this file recomputed the predicate
locally and asserted on that value. It was vacuous: it tested the test's own
copy of the rule, so it passed unchanged against the reverted (defective)
validator, which proves nothing. Every assertion below therefore executes the
real `validate-p7-readiness.py` in a disposable copy of the repository and
inspects its actual verdict text and exit status.

The pair is deliberately two-directional, because a fix that merely silenced
the check would be a weakening rather than a correction:

  1. the empty registry is accepted (the D-P3-D obligation), and
  2. a NON-EMPTY registry that omits the generic fallback is still rejected
     (the control the original expression existed to enforce).

Repository-local, standard library only. Nothing is written into the real
repository: every case runs in a temporary copy of the tree.
"""

import os
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "sps2", "tools")
VALIDATOR_REL = os.path.join("sps2", "tools", "validate-p7-readiness.py")
REGISTRY_REL = os.path.join("sps2", "core", "adapters", "registry.json")


def _copy_tree(dest):
    """Copy the repository the same way the portability harness does.

    `shutil.copytree` (not `git archive`) is required: the validator's own
    gates shell out to git, and a tree without `.git` produces misleading
    failures that have nothing to do with the question under test.
    """
    sys.path.insert(0, TOOLS)
    spec = __import__("importlib.util", fromlist=["util"]).spec_from_file_location(
        "pt_regression", os.path.join(TOOLS, "portability.py"))
    module = __import__("importlib.util", fromlist=["util"]).module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.copy_tree(REPO, dest)


class ZeroAdapterReadinessTest(unittest.TestCase):
    """The shipped validator's real verdict, in both registry states."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="p7-zero-adapter-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run_validator(self, tag, mutate):
        """Copy the repo, apply *mutate* to the registry, run the validator."""
        tree = _copy_tree(os.path.join(self.tmp, tag))
        path = os.path.join(tree, REGISTRY_REL)
        with open(path) as handle:
            data = json.load(handle)
        data["adapters"] = mutate(data.get("adapters") or [])
        with open(path, "w") as handle:
            json.dump(data, handle, indent=2)
        completed = subprocess.run(
            [sys.executable, os.path.join(tree, VALIDATOR_REL)],
            cwd=tree, capture_output=True, text=True, timeout=300)
        return completed.returncode, completed.stdout + completed.stderr

    def test_empty_registry_is_accepted_by_d3d(self):
        """D-P3-D: the delete-all state must be accepted, generic included."""
        rc, output = self._run_validator("empty", lambda _a: [])
        self.assertNotIn(
            "RECORD_OVERSTATES_P3", output,
            "D-P3-D states an empty adapter registry 'is valid and must be "
            "accepted by the portability test', but the validator reported the "
            "roadmap record as overstating P3:\n%s" % output)
        self.assertEqual(
            rc, 0,
            "the zero-adapter state is the D-P3-D obligation and must be "
            "green; validator exited %d:\n%s" % (rc, output))

    def test_non_empty_registry_without_generic_is_still_rejected(self):
        """The control the original expression enforced must survive the fix.

        This is the non-vacuous half of the pair: deleting the `generic`
        requirement outright would satisfy the empty-registry test above while
        silently dropping this rejection.
        """
        rc, output = self._run_validator(
            "no-generic",
            lambda adapters: [a for a in adapters
                              if a.get("agent_id") != "generic"])
        self.assertIn(
            "RECORD_OVERSTATES_P3", output,
            "a registry that ships real adapters but drops the DECLARED "
            "generic fallback must still be rejected as not-delivered:\n%s"
            % output)
        self.assertNotEqual(rc, 0)

    def test_delivered_state_in_the_real_repository_still_holds(self):
        """The shipped registry remains green: no unrelated regression."""
        completed = subprocess.run(
            [sys.executable, VALIDATOR_REL],
            cwd=REPO, capture_output=True, text=True, timeout=300)
        output = completed.stdout + completed.stderr
        self.assertNotIn("RECORD_OVERSTATES_P3", output)
        self.assertEqual(completed.returncode, 0, output)


if __name__ == "__main__":
    unittest.main()
