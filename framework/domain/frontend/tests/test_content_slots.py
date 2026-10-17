"""Focused tests for the P10 Home content-slot value adapter.

Covers the user-authorized mapping (home-default: heading -> Content.title,
body -> Content.body), fail-closed behavior on every structural mismatch, the
P8 output-safety boundary, and the draft-vs-published rule.

Tests exercise actual adapter behavior against the real P8 model, the real
output-safety functions, and the real persisted Home records where relevant.
"""

from __future__ import annotations

import unittest

from framework.domain.cms.model import ContentType
from framework.domain.cms.output_safety import encode_for_html
from framework.domain.frontend.content_slots import (
    CONTENT_TYPE_MISMATCH,
    FALLBACK,
    INVALID_VALUE,
    MALFORMED_CONTENT,
    MISSING_VALUE,
    RESOLVED,
    SUPPORTED_LAYOUT_ID,
    UNKNOWN_LAYOUT,
    UNSUPPORTED_SLOT,
    resolve_content_slots,
    satisfies_published_only,
    supported_slots,
)

HOME_CT_ID = "c64e3d79694e49eebd6c09ee58a53c87"

# A representative P8 Content record with the fixed title/body properties.
def _content(**overrides):
    data = {
        "id": "content-1",
        "type_id": HOME_CT_ID,
        "title": "Welcome heading",
        "body": "Welcome body text",
        "status": "published",
        "author_id": "author-1",
        "created_at": "2026-10-13T00:00:00+00:00",
        "updated_at": "2026-10-13T00:00:00+00:00",
        "published_at": "2026-10-13T00:01:00+00:00",
    }
    data.update(overrides)
    return data


def _home_content_type() -> dict:
    """Return the approved Home ContentType definition (id + name + fields).

    The authorized mapping requires the Home ContentType identity, so this
    fixture uses the persisted Home ContentType id and the ``home`` name
    with the heading/body text fields.
    """
    return {
        "id": HOME_CT_ID,
        "name": "home",
        "fields": [
            {"name": "heading", "type": "text", "required": True},
            {"name": "body", "type": "text", "required": True},
        ],
        "created_at": "2026-10-13T00:00:00+00:00",
        "updated_at": "2026-10-13T00:00:00+00:00",
    }


class TestAuthorizedMapping(unittest.TestCase):
    """The authorized home-default slot -> P8 property mapping."""

    def test_supported_layout_and_slots(self) -> None:
        self.assertEqual(SUPPORTED_LAYOUT_ID, "home-default")
        self.assertEqual(supported_slots("home-default"), ("heading", "body"))
        # No other layout is bound by this adapter.
        self.assertEqual(supported_slots("some-other-layout"), ())

    def test_heading_resolves_from_content_title(self) -> None:
        res = resolve_content_slots(
            "home-default", _content(), content_type_id=HOME_CT_ID
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.status, RESOLVED)
        self.assertEqual(res.values["heading"], encode_for_html("Welcome heading"))
        self.assertEqual(res.errors, ())

    def test_body_resolves_from_content_body(self) -> None:
        res = resolve_content_slots(
            "home-default", _content(), content_type_id=HOME_CT_ID
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.values["body"], encode_for_html("Welcome body text"))

    def test_both_slots_resolve_together(self) -> None:
        res = resolve_content_slots(
            "home-default",
            _content(),
            content_type_id=HOME_CT_ID,
            content_type=_home_content_type(),
        )
        self.assertTrue(res.ok)
        self.assertEqual(set(res.values.keys()), {"heading", "body"})

    def test_content_type_identity_must_be_home(self) -> None:
        # Approved Home ContentType accepted.
        ok = resolve_content_slots(
            "home-default",
            _content(),
            content_type_id=HOME_CT_ID,
            content_type=_home_content_type(),
        )
        self.assertTrue(ok.ok)


class TestFailClosed(unittest.TestCase):
    """Structural mismatches must fail closed, never guess or fall back."""

    def test_unknown_layout_fails_closed(self) -> None:
        res = resolve_content_slots("not-home-default", _content())
        self.assertFalse(res.ok)
        self.assertEqual(res.status, FALLBACK)
        self.assertEqual(res.values, {})
        self.assertEqual([e.code for e in res.errors], [UNKNOWN_LAYOUT])

    def test_unknown_slot_fails_closed(self) -> None:
        res = resolve_content_slots(
            "home-default", _content(), content_type_id=HOME_CT_ID,
            slots=("heading", "subtitle"),
        )
        self.assertFalse(res.ok)
        self.assertEqual(res.values, {})
        self.assertIn(UNSUPPORTED_SLOT, [e.code for e in res.errors])

    def test_different_content_type_id_fails_closed(self) -> None:
        res = resolve_content_slots(
            "home-default", _content(), content_type_id="some-other-ct-id"
        )
        self.assertFalse(res.ok)
        self.assertEqual(res.values, {})
        self.assertEqual([e.code for e in res.errors], [CONTENT_TYPE_MISMATCH])

    def test_content_type_id_mismatch_fails_closed(self) -> None:
        res = resolve_content_slots(
            "home-default",
            _content(type_id="mismatched-id"),
            content_type_id=HOME_CT_ID,
        )
        self.assertFalse(res.ok)
        self.assertEqual([e.code for e in res.errors], [CONTENT_TYPE_MISMATCH])

    def test_wrong_content_type_definition_fails_closed(self) -> None:
        # A different ContentType definition (name != home) fails closed.
        other_ct = ContentType("other", [{"name": "heading", "type": "text", "required": True}])
        res = resolve_content_slots(
            "home-default",
            _content(),
            content_type_id=HOME_CT_ID,
            content_type=other_ct.to_dict(),
        )
        self.assertFalse(res.ok)
        self.assertEqual([e.code for e in res.errors], [CONTENT_TYPE_MISMATCH])

    def test_missing_title_fails_closed(self) -> None:
        record = _content()
        del record["title"]
        res = resolve_content_slots("home-default", record, content_type_id=HOME_CT_ID)
        self.assertFalse(res.ok)
        self.assertEqual(res.values, {})
        self.assertIn(MALFORMED_CONTENT, [e.code for e in res.errors])

    def test_missing_body_fails_closed(self) -> None:
        record = _content()
        del record["body"]
        res = resolve_content_slots("home-default", record, content_type_id=HOME_CT_ID)
        self.assertFalse(res.ok)
        self.assertIn(MALFORMED_CONTENT, [e.code for e in res.errors])

    def test_empty_required_values_fail_closed(self) -> None:
        res = resolve_content_slots(
            "home-default", _content(title="", body=""), content_type_id=HOME_CT_ID
        )
        self.assertFalse(res.ok)
        self.assertEqual(res.values, {})
        codes = [e.code for e in res.errors]
        self.assertEqual(codes, [MISSING_VALUE, MISSING_VALUE])

    def test_empty_title_fails_closed(self) -> None:
        res = resolve_content_slots("home-default", _content(title=""), content_type_id=HOME_CT_ID)
        self.assertFalse(res.ok)
        self.assertEqual([e.code for e in res.errors], [MISSING_VALUE])

    def test_invalid_value_type_fails_closed(self) -> None:
        res = resolve_content_slots(
            "home-default", _content(body=123), content_type_id=HOME_CT_ID
        )
        self.assertFalse(res.ok)
        self.assertIn(INVALID_VALUE, [e.code for e in res.errors])

    def test_malformed_content_object_fails_closed(self) -> None:
        for bad in ("not-a-mapping", None, 42, ["list"]):
            res = resolve_content_slots("home-default", bad, content_type_id=HOME_CT_ID)
            self.assertFalse(res.ok)
            self.assertEqual(res.values, {})
            self.assertEqual([e.code for e in res.errors], [MALFORMED_CONTENT])


class TestErrorHygiene(unittest.TestCase):
    """Errors must never leak raw CMS values."""

    def test_errors_do_not_expose_raw_values(self) -> None:
        secret = "<script>alert('secret')</script>"
        record = _content(title=secret, body=secret, type_id="mismatched")
        res = resolve_content_slots("home-default", record, content_type_id=HOME_CT_ID)
        self.assertFalse(res.ok)
        for err in res.errors:
            self.assertNotIn(secret, err.message)
            self.assertNotIn("alert(", err.message)
            self.assertNotIn("<script>", err.message)

    def test_errors_do_not_expose_values_on_empty_or_invalid(self) -> None:
        res = resolve_content_slots(
            "home-default", _content(title="", body=object()), content_type_id=HOME_CT_ID
        )
        self.assertFalse(res.ok)
        for err in res.errors:
            self.assertNotIn("object", err.message)


class TestOutputSafetyBoundary(unittest.TestCase):
    """Values pass through the approved P8 output-safety boundary."""

    def test_values_are_encoded_exactly_once(self) -> None:
        payload = "<script>alert('xss')</script>"
        res = resolve_content_slots(
            "home-default", _content(title=payload, body=payload), content_type_id=HOME_CT_ID
        )
        self.assertTrue(res.ok)
        for value in res.values.values():
            # No raw tag survives, and it is encoded exactly once (single
            # pass => "&lt;script&gt;", not double-encoded "&amp;lt;").
            self.assertNotIn("<script>", value)
            self.assertIn("&lt;script&gt;", value)
            self.assertNotIn("&amp;lt;", value)

    def test_no_double_encoding_of_body(self) -> None:
        text = "Plain & simple <text>"
        res = resolve_content_slots(
            "home-default", _content(body=text), content_type_id=HOME_CT_ID
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.values["body"], encode_for_html(text))

    def test_title_and_body_both_encoded_at_sink(self) -> None:
        res = resolve_content_slots(
            "home-default",
            _content(title="a & b", body="c < d"),
            content_type_id=HOME_CT_ID,
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.values["heading"], "a &amp; b")
        self.assertEqual(res.values["body"], "c &lt; d")


class TestPublicationRule(unittest.TestCase):
    """A draft must not satisfy a published-only reference."""

    def test_draft_does_not_satisfy_published_only(self) -> None:
        draft = _content(status="draft", published_at=None)
        res = resolve_content_slots("home-default", draft, content_type_id=HOME_CT_ID)
        self.assertTrue(res.ok)  # structural values resolve
        self.assertEqual(res.content_status, "draft")
        self.assertFalse(satisfies_published_only(res))

    def test_published_satisfies_published_only(self) -> None:
        pub = _content(status="published", published_at="2026-10-13T00:01:00+00:00")
        res = resolve_content_slots("home-default", pub, content_type_id=HOME_CT_ID)
        self.assertTrue(res.ok)
        self.assertEqual(res.content_status, "published")
        self.assertTrue(satisfies_published_only(res))

    def test_unresolved_never_satisfies_published_only(self) -> None:
        res = resolve_content_slots("not-home-default", _content())
        self.assertFalse(satisfies_published_only(res))


class TestPersistedHomeRecord(unittest.TestCase):
    """The real persisted Home record: published by user ratification
    (P10 completion, commit 1279cd6), structurally valid, published-only."""

    def test_persisted_home_content_is_published(self) -> None:
        import json
        import os

        data_dir = os.path.join("framework", "domain", "cms", "data")
        ctypes = json.load(open(os.path.join(data_dir, "content_types.json")))
        contents = json.load(open(os.path.join(data_dir, "content.json")))
        home_ct = next(c for c in ctypes if c["name"] == "home")
        home_content = next(c for c in contents if c["type_id"] == home_ct["id"])
        # The persisted Home Content is published (user-ratified 2026-10-17).
        self.assertEqual(home_content["status"], "published")
        self.assertTrue(home_content["published_at"])
        # And it resolves structurally and satisfies published-only.
        res = resolve_content_slots(
            "home-default", home_content, content_type_id=home_ct["id"]
        )
        self.assertTrue(res.ok)
        self.assertTrue(satisfies_published_only(res))


if __name__ == "__main__":
    unittest.main()