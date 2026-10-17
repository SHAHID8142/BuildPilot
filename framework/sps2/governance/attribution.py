#!/usr/bin/env python3
"""SPS 2.0 P5 approval-attribution governance control.

This module lives in governance/, not core/, for a specific architectural
reason: the core must be agent-neutral and must never reference or branch on a
specific agent. Detecting an agent-attributed approval necessarily requires
knowing what agent names look like, so that knowledge is confined here, behind
the core/governance boundary, and the core receives it as an injected
predicate rather than hard-coding it.

Core therefore never names an agent, and the control still holds.
"""
import json
import os
import re

POLICY_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           "attribution_policy.json")

# Admissible shape of ONE token.
#
# re.escape() neutralises regex metacharacters, so a well-typed but degenerate
# token list ("(", "[", "*", "\", "a b", "   ") still compiles rather than
# failing at re.compile() time. Such a pattern simply matches nothing, so the
# compiled matcher silently stops detecting anything and every consumer emits 0
# bytes, which the shell harness scores as a clean PASS. The loader validates
# TYPE today; this pattern is the SEMANTIC check that the type guard alone
# cannot express.
#
#   - ASCII lowercase alphanumerics and interior hyphens only. No whitespace,
#     no punctuation, no regex metacharacter, so re.escape() is a no-op and the
#     compiled alternation is exactly the approved \b(...)\b form. Every one of
#     the ratified 17 tokens satisfies this unchanged.
#   - Must begin and end with an alphanumeric, so '', '(', '-', '--' and '-a'
#     are rejected. A token can never start with the hyphen that separates
#     compound names, which keeps \b semantics meaningful.
#   - No underscore: \b does not fire between a word character and '_', so such
#     a token could never match under the approved word-boundary semantics.
#   - No '^' or '$' anchor: an anchor inside the alternation either makes the
#     pattern unmatchable or unanchors the intended word boundary.
#   - Lowercase only, because the matcher is compiled with re.I: an uppercase
#     spelling would be a behavioural duplicate of its lowercase form and would
#     signal an un-reviewed edit. The canonical set is entirely lowercase.
TOKEN_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\Z")


def load_agent_tokens(path=POLICY_PATH):
    """The agent-name token set, loaded from the authoritative policy file.

    framework/sps2/governance/attribution_policy.json is the single source of truth for
    these tokens. Consumers MUST import them from here (or call this) rather
    than hardcoding a list of their own; a hardcoded duplicate is a divergence
    bug. Matching semantics live in this module, not in the data file. A
    missing or malformed policy file raises rather than silently degrading to
    an empty vocabulary, which would let every approver identity through.
    """
    with open(path, "r", encoding="utf-8") as handle:
        policy = json.load(handle)
    if not isinstance(policy, dict):
        # Valid JSON of the wrong top-level type (a list, string, number,
        # boolean or null) must fail as a controlled ValueError. Calling
        # .get() on it raises AttributeError instead, which is NOT part of
        # this module's documented failure surface: it escapes the consumer
        # guards in check_sps2.py / check_p2.py, which then print nothing to
        # stdout, and an empty stdout is scored as a clean PASS by
        # assert_clean in validate-sps2.sh. Fail closed with a type that the
        # guards already handle.
        raise ValueError("attribution policy must be a JSON object, got %s: %r"
                         % (type(policy).__name__, path))
    tokens = policy.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise ValueError("attribution policy defines no tokens: %r" % (path,))
    if not all(isinstance(t, str) and t for t in tokens):
        raise ValueError("attribution policy has a non-string token: %r" % (tokens,))
    # SEMANTIC validation. Type-correctness is not enough: a well-typed but
    # degenerate list is accepted by the checks above, re.escape() keeps it
    # compiling, and the resulting matcher detects nothing. Every consumer then
    # prints nothing to stdout, and the stdout-based shell harness scores an
    # empty stdout as a clean PASS. Reject such a policy loudly, with the same
    # ValueError the consumer guards in check_sps2.py / check_p2.py already
    # report as a visible "ERR attribution policy unavailable: ..." line at
    # exit 0, so a silently disabled control cannot be mistaken for a clean one.
    #
    # A duplicate token is rejected as well, although under \b(...)\b it does
    # not by itself change behaviour: a duplicate means the file was edited
    # without review, and DEC-0025's own instruction was "Do not introduce
    # duplicate tokens". Catching it here keeps that requirement enforceable.
    seen = set()
    duplicates = []
    for token in tokens:
        if not TOKEN_PATTERN.match(token):
            raise ValueError(
                "attribution policy has a malformed token %r: tokens must be "
                "lowercase ASCII alphanumerics with interior hyphens only "
                "(no whitespace, punctuation, regex metacharacters, "
                "underscores, anchors or leading/trailing hyphens): %r"
                % (token, path))
        if token in seen and token not in duplicates:
            duplicates.append(token)
        seen.add(token)
    if duplicates:
        raise ValueError(
            "attribution policy has duplicate token(s) %r: a duplicate is an "
            "unreviewed edit and a token may be listed only once: %r"
            % (sorted(duplicates), path))
    return tuple(tokens)

# Heuristic denylist of names that INDICATE the decision was made by an
# automated agent rather than by an identifiable human User.
#
# SCOPE. A match is evidence that an approval is agent-attributed. Nothing
# further follows from a match, and nothing at all follows from a NON-match:
#
#   - The TOKEN SET is the single source of truth, in
#     framework/sps2/governance/attribution_policy.json, which this module is the sole
#     consumer of. That is a statement about this file's placement, NOT a
#     claim that it authoritatively classifies any identity: no requirement,
#     schema or decision record enumerates agent identities, and the file is
#     a heuristic vocabulary, not a registry.
#   - A non-match does NOT show that decided_by is a real, authorized User.
#     It is self-asserted free text: the schemas constrain it only to a
#     string (p10-slice adds no length or pattern at all), never to an
#     identity.
#   - String matching cannot establish identity or trusted provenance; the
#     repository defines no identity provider, account registry or signature
#     against which decided_by could be checked.
#   - It is NOT exhaustive. Unicode confusables (cross-script homoglyphs),
#     interior separators and invisible characters defeat it; \b does not
#     fire across "_" or a digit.
#   - Being a denylist, it can also reject a legitimate identity that merely
#     contains a listed word.
#   - It deliberately does NOT match "self", "script" or "autonomous"; each is
#     an ordinary English word that can denote a human name. Legacy validators
#     that listed them are migrated to this behaviour under SPEC-2.
#
# The authoritative obligations are separate and unchanged: rejecting missing,
# null, fabricated or agent-attributed approval (REQ-P10-09 c.6), and the
# schema-enforced decided_by_role == "USER" marker. This heuristic neither
# replaces them nor evidences that they were satisfied.
AGENTISH = re.compile(
    r"\b(%s)\b" % "|".join(re.escape(t) for t in load_agent_tokens()), re.I)


def approval_is_user_attributable(approval):
    """True only for an APPROVED decision naming an identifiable User.

    Requires an APPROVED state, a non-empty decider that is not an agent name,
    and a decision date. Any missing element is not an approval.

    The date is accepted under either established field name. Capability and
    requirement records use `decided_on`; the decision records DEC-0011 to
    DEC-0015 use `decided_at`. Both are accepted so that attribution is judged
    on WHO and WHEN, not on a spelling difference. A missing date under either
    name is still rejected, and an agent decider is still rejected.
    """
    a = approval or {}
    if a.get("state") != "APPROVED":
        return False
    who = (a.get("decided_by") or "").strip()
    if not who or AGENTISH.search(who):
        return False
    return bool((a.get("decided_on") or a.get("decided_at") or "").strip())


def reason_not_attributable(approval):
    """Explain why an approval is not valid. Empty string means valid."""
    a = approval or {}
    if a.get("state") != "APPROVED":
        return "approval state is %r, not APPROVED" % (a.get("state"),)
    who = (a.get("decided_by") or "").strip()
    if not who:
        return "APPROVED without decided_by"
    if AGENTISH.search(who):
        return "APPROVED by an agent, not a user: %r" % who
    if not (a.get("decided_on") or a.get("decided_at") or "").strip():
        return "APPROVED without decided_on or decided_at"
    return ""