"""Focused tests for the P10 layout registry (REQ-P10-02).

Covers REQ-P10-02 acceptance criteria 1-5 and the eight required test
areas.  Tests exercise real behavior against the P8 ContentType model
and validators; they do not assert on source-file contents.
"""

from __future__ import annotations

import unittest

from domain.cms.model import ContentType
from domain.cms.output_safety import encode_for_html
from domain.cms.validation import validate_content_type
from domain.frontend.layout_registry import (
    FALLBACK,
    FALLBACK_LAYOUT_ID,
    LAYOUT_REGISTRY,
    RESOLVED,
    UNKNOWN_LAYOUT,
    UNRESOLVED_FIELD_SLOT,
    LayoutRegistryError,
    is_registered,
    registered_layout_ids,
    resolve,
    validate_layout_definition,
)

# The Home ContentType contract: heading and body, both required text.
HOME_FIELDS = [
    {"name": "heading", "type": "text", "required": True},
    {"name": "body", "type": "text", "required": True},
]


def _home_content_type() -> ContentType:
    """Build a real P8 ContentType for the Home contract."""
    return ContentType("home", [dict(f) for f in HOME_FIELDS])


class TestRegistryEnumeration(unittest.TestCase):
    """REQ-P10-02 criterion 1: the registry enumerates every layout."""

    def test_home_default_is_the_only_registered_layout(self) -> None:
        self.assertEqual(registered_layout_ids(), ("home-default",))
        self.assertEqual(set(LAYOUT_REGISTRY.keys()), {"home-default"})

    def test_home_default_declares_exactly_heading_and_body(self) -> None:
        definition = LAYOUT_REGISTRY["home-default"]
        self.assertEqual(definition.layout_id, "home-default")
        self.assertEqual(definition.field_slots, ("heading", "body"))

    def test_layout_is_not_registered_merely_by_being_stored(self) -> None:
        # REQ-P10-02 criterion 3: a P8 Section.layout string is data,
        # not proof of registration.  Only explicit membership counts.
        self.assertTrue(is_registered("home-default"))
        self.assertFalse(is_registered("hero"))
        self.assertFalse(is_registered("grid"))
        self.assertFalse(is_registered("does-not-exist"))
        self.assertFalse(is_registered(""))


class TestResolvedLayout(unittest.TestCase):
    """REQ-P10-02 criterion 4: slots resolve against ContentType fields."""

    def test_home_default_resolves_against_home_content_type(self) -> None:
        ct = _home_content_type()
        # The ContentType is a valid P8 ContentType.
        validate_content_type(ct.to_dict())
        resolution = resolve("home-default", ct)
        self.assertTrue(resolution.ok)
        self.assertEqual(resolution.status, RESOLVED)
        self.assertEqual(resolution.layout_id, "home-default")
        self.assertEqual(resolution.field_slots, ("heading", "body"))
        self.assertEqual(resolution.errors, ())

    def test_home_default_resolves_against_content_type_dict(self) -> None:
        resolution = resolve(
            "home-default", {"fields": [dict(f) for f in HOME_FIELDS]}
        )
        self.assertTrue(resolution.ok)
        self.assertEqual(resolution.field_slots, ("heading", "body"))

    def test_resolution_is_deterministic(self) -> None:
        ct = _home_content_type()
        self.assertEqual(resolve("home-default", ct), resolve("home-default", ct))

    def test_resolution_leaves_registry_and_content_type_unchanged(self) -> None:
        # REQ-P10-02 criterion 3: the registry is the single source of
        # meaning and does not mutate P8-stored data.
        ct = _home_content_type()
        before = ct.to_dict()
        resolve("home-default", ct)
        resolve("unknown-layout", ct)
        self.assertEqual(ct.to_dict(), before)
        self.assertEqual(registered_layout_ids(), ("home-default",))


class TestMissingRequiredField(unittest.TestCase):
    """A declared slot absent from the ContentType is rejected (fail closed)."""

    def test_missing_body_field_is_rejected(self) -> None:
        ct = ContentType(
            "home", [{"name": "heading", "type": "text", "required": True}]
        )
        resolution = resolve("home-default", ct)
        self.assertFalse(resolution.ok)
        self.assertEqual(resolution.status, FALLBACK)
        self.assertEqual(resolution.field_slots, ())
        self.assertEqual(len(resolution.errors), 1)
        self.assertEqual(resolution.errors[0].code, UNRESOLVED_FIELD_SLOT)
        self.assertIn("body", resolution.errors[0].message)

    def test_empty_content_type_rejects_all_slots(self) -> None:
        ct = ContentType("home", [])
        resolution = resolve("home-default", ct)
        self.assertFalse(resolution.ok)
        self.assertEqual(resolution.status, FALLBACK)
        self.assertEqual(resolution.field_slots, ())
        self.assertEqual(resolution.errors[0].code, UNRESOLVED_FIELD_SLOT)

    def test_no_content_type_fails_closed(self) -> None:
        resolution = resolve("home-default")
        self.assertFalse(resolution.ok)
        self.assertEqual(resolution.status, FALLBACK)
        self.assertEqual(resolution.field_slots, ())
        self.assertEqual(resolution.errors[0].code, UNRESOLVED_FIELD_SLOT)


class TestUnknownLayoutFallback(unittest.TestCase):
    """REQ-P10-02 criteria 2 and 5: unknown layout -> fallback + error."""

    def test_unknown_layout_returns_fallback_not_exception(self) -> None:
        # Criterion 5: the unknown-layout case yields a defined fallback
        # and a recorded error, NOT an exception and NOT an arbitrary
        # render.
        resolution = resolve("a-layout-that-was-never-registered")
        self.assertIsInstance(resolution, object)
        self.assertEqual(resolution.status, FALLBACK)
        self.assertEqual(resolution.layout_id, FALLBACK_LAYOUT_ID)
        self.assertEqual(resolution.field_slots, ())
        self.assertEqual(len(resolution.errors), 1)
        self.assertEqual(resolution.errors[0].code, UNKNOWN_LAYOUT)

    def test_unknown_layout_error_records_the_unknown_identifier(self) -> None:
        unknown = "totally-unknown-layout"
        resolution = resolve(unknown)
        self.assertEqual(resolution.errors[0].layout_id, unknown)
        self.assertIn(unknown, resolution.errors[0].message)

    def test_unknown_layout_is_never_silently_mapped_to_home_default(self) -> None:
        # Criterion 2: never silently rendered as home-default or a guess.
        for unknown in ("hero", "grid", "list", "single", "custom", "home", ""):
            resolution = resolve(unknown)
            self.assertEqual(resolution.status, FALLBACK)
            self.assertNotEqual(resolution.layout_id, "home-default")
            self.assertNotEqual(resolution.layout_id, unknown)
            self.assertEqual(resolution.field_slots, ())

    def test_fallback_is_distinct_from_every_registered_layout(self) -> None:
        self.assertNotIn(FALLBACK_LAYOUT_ID, LAYOUT_REGISTRY)
        self.assertNotEqual(FALLBACK_LAYOUT_ID, "home-default")

    def test_non_string_layout_fails_closed(self) -> None:
        for bad in (None, 123, ["home-default"], {"layout": "home-default"}):
            resolution = resolve(bad)
            self.assertEqual(resolution.status, FALLBACK)
            self.assertEqual(resolution.field_slots, ())
            self.assertEqual(resolution.errors[0].code, UNKNOWN_LAYOUT)


class TestMalformedDefinitionsFailClosed(unittest.TestCase):
    """Invalid or malformed layout definitions fail closed."""

    def test_invalid_layout_id_rejected(self) -> None:
        for bad_id in ("", "Bad_Id", "1starts-with-digit", "has space", "UPPER"):
            with self.assertRaises(LayoutRegistryError):
                validate_layout_definition(bad_id, ["heading"])

    def test_empty_field_slots_rejected(self) -> None:
        with self.assertRaises(LayoutRegistryError):
            validate_layout_definition("some-layout", [])

    def test_non_string_field_slot_rejected(self) -> None:
        with self.assertRaises(LayoutRegistryError):
            validate_layout_definition("some-layout", ["heading", 123])
        with self.assertRaises(LayoutRegistryError):
            validate_layout_definition("some-layout", [None])

    def test_duplicate_field_slot_rejected(self) -> None:
        with self.assertRaises(LayoutRegistryError):
            validate_layout_definition("some-layout", ["heading", "heading"])

    def test_field_slots_as_bare_string_rejected(self) -> None:
        with self.assertRaises(LayoutRegistryError):
            validate_layout_definition("some-layout", "heading")


class TestOutputSafetyBoundary(unittest.TestCase):
    """Errors never expose raw CMS content; output safety remains intact."""

    def test_errors_do_not_expose_raw_cms_content(self) -> None:
        # A sensitive content value present in the system must never
        # appear in any registry error: resolve() only ever sees
        # structural metadata (layout identifiers and field-slot names),
        # never content values.
        sensitive = "<script>alert('secret-home-copy')</script>"
        incomplete = ContentType(
            "home", [{"name": "heading", "type": "text", "required": True}]
        )
        resolutions = (
            resolve("not-a-registered-layout"),
            resolve("home-default", incomplete),
        )
        for resolution in resolutions:
            for error in resolution.errors:
                self.assertNotIn(sensitive, error.message)
                self.assertNotIn("secret-home-copy", error.message)
                self.assertNotIn("<script>", error.message)
                self.assertNotIn("alert(", error.message)

    def test_p8_output_safety_behavior_remains_intact(self) -> None:
        # REQ-P10-02 does not alter the P8 per-sink output-encoding
        # boundary.
        payload = "<script>alert('xss')</script>"
        encoded = encode_for_html(payload)
        self.assertNotIn("<script>", encoded)
        self.assertIn("&lt;script&gt;", encoded)

    def test_raw_content_text_is_not_treated_as_a_content_type(self) -> None:
        # Passing raw content where a ContentType definition belongs fails
        # closed: the registry consumes field names, never content values.
        raw = "<script>raw home body copy</script>"
        resolution = resolve("home-default", raw)
        self.assertEqual(resolution.status, FALLBACK)
        self.assertEqual(resolution.field_slots, ())
        self.assertEqual(resolution.errors[0].code, UNRESOLVED_FIELD_SLOT)
        self.assertNotIn("raw home body copy", resolution.errors[0].message)
        self.assertNotIn("<script>", resolution.errors[0].message)

    def test_field_slots_are_names_not_values(self) -> None:
        ct = _home_content_type()
        resolution = resolve("home-default", ct)
        self.assertEqual(resolution.field_slots, ("heading", "body"))
        self.assertTrue(all(isinstance(slot, str) for slot in resolution.field_slots))


if __name__ == "__main__":
    unittest.main()
