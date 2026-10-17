"""P10 Home layout content-slot value adapter.

This module binds the ``home-default`` layout's declared field slots to
their ACTUAL values on a persisted P8 Content record. The layout registry
(``framework.domain.frontend.layout_registry``) is deliberately DEFINITIONS-ONLY: it
verifies that a registered layout's slots appear in a P8 ContentType
definition. It never supplies values. This module supplies the values for
one authorized, explicit case only:

    layout_id "home-default" (and no other):
        slot "heading" -> P8 Content.title
        slot "body"   -> P8 Content.body

Scope and ownership
-------------------
P8 owns CMS/content semantics; P10 owns presentation and the interpretation
of ``Section.layout`` values (D-P10-2). This adapter is P10-owned and lives
under ``framework/domain/``. It does not reimplement, duplicate, or alter any P8
content semantics; it reads the existing fixed P8 ``Content`` properties
that the model already exposes.

This mapping is deliberately NOT a general framework. It does NOT infer
property names dynamically, does NOT assume arbitrary ContentType fields map
to identically- or similarly-named P8 Content properties, and does NOT apply
to any layout other than ``home-default``. An unmapped layout or slot fails
closed; nothing is guessed.

Output safety
-------------
Values are produced through the APPROVED P8 output-safety boundary. The P8
model stores PLAIN TEXT only; every value returned here is passed through
``framework.domain.cms.output_safety.encode_for_html`` exactly once, so a caller can
place the result directly in an HTML sink. The adapter never interpolates a
raw CMS value into HTML and never leaks raw CMS values in errors.

Publication status
------------------
This adapter does NOT enforce publication. It resolves structural values and
reports the record's own ``status`` so a caller can apply a publication rule.
Treating a ``draft`` as satisfying a published-only reference is explicitly
NOT something this adapter does. Publication enforcement belongs to the
runtime validation gate (REQ-P10-09), which does not exist; this adapter
does not implement or claim REQ-P10-09.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from framework.domain.cms.output_safety import encode_for_html, validate_plain_text

# The single layout this adapter is authorized to bind.
SUPPORTED_LAYOUT_ID = "home-default"

# The authorized, explicit slot -> P8 Content property mapping for
# ``home-default`` ONLY. This is a frozen, auditable declaration of one
# user-approved decision; it is not inferred and not generalized.
_HOME_SLOT_SOURCE: Mapping[str, str] = {
    "heading": "title",
    "body": "body",
}

# Recorded-error codes.
UNKNOWN_LAYOUT = "P10_CONTENT_SLOT_UNKNOWN_LAYOUT"
UNSUPPORTED_SLOT = "P10_CONTENT_SLOT_UNSUPPORTED_SLOT"
CONTENT_TYPE_MISMATCH = "P10_CONTENT_SLOT_CONTENT_TYPE_MISMATCH"
MALFORMED_CONTENT = "P10_CONTENT_SLOT_MALFORMED_CONTENT"
MISSING_VALUE = "P10_CONTENT_SLOT_MISSING_VALUE"
INVALID_VALUE = "P10_CONTENT_SLOT_INVALID_VALUE"


@dataclass(frozen=True)
class SlotResolutionError:
    """A recorded adapter error. Identifies structural problems only.

    Carries a code, a slot name, and a P8 property identifier. It never
    carries a raw CMS content value.
    """

    code: str
    slot: str | None
    message: str


@dataclass(frozen=True)
class SlotResolution:
    """Deterministic, fail-closed outcome of resolving slots to values.

    ``status`` is ``RESOLVED`` only when every requested slot was authorized,
    present as the correct type, and non-empty. Otherwise it is ``FALLBACK``
    with ``values`` empty and one or more recorded errors. A fallback is
    never permission to render or publish.
    """

    layout_id: str
    status: str
    values: Mapping[str, str]
    errors: Tuple[SlotResolutionError, ...]
    content_status: str | None

    @property
    def ok(self) -> bool:
        """True only when fully resolved with no recorded errors."""
        return self.status == RESOLVED and not self.errors


RESOLVED = "resolved"
FALLBACK = "fallback"


def supported_slots(layout_id: str) -> Tuple[str, ...]:
    """Return the authorized slots for ``home-default``; empty otherwise."""
    if layout_id != SUPPORTED_LAYOUT_ID:
        return ()
    return tuple(_HOME_SLOT_SOURCE.keys())


def _resolve_one(
    content: Mapping[str, Any], slot: str
) -> tuple[str | None, SlotResolutionError | None]:
    prop = _HOME_SLOT_SOURCE.get(slot)
    if prop is None:
        return None, SlotResolutionError(
            code=UNSUPPORTED_SLOT,
            slot=slot,
            message=(
                f"Slot {slot!r} is not part of the authorized "
                f"{SUPPORTED_LAYOUT_ID} mapping; resolution fails closed."
            ),
        )
    if prop not in content:
        return None, SlotResolutionError(
            code=MALFORMED_CONTENT,
            slot=slot,
            message=(
                f"Content record does not expose the P8 property {prop!r} "
                f"required by slot {slot!r}; resolution fails closed."
            ),
        )
    raw = content[prop]
    if not isinstance(raw, str):
        return None, SlotResolutionError(
            code=INVALID_VALUE,
            slot=slot,
            message=(
                f"P8 property {prop!r} for slot {slot!r} must be a string; "
                "resolution fails closed."
            ),
        )
    # Content is PLAIN TEXT only; enforce that contract before encoding.
    try:
        plain = validate_plain_text(raw)
    except ValueError:
        return None, SlotResolutionError(
            code=INVALID_VALUE,
            slot=slot,
            message=(
                f"P8 property {prop!r} for slot {slot!r} is not plain text; "
                "resolution fails closed."
            ),
        )
    if plain == "":
        return None, SlotResolutionError(
            code=MISSING_VALUE,
            slot=slot,
            message=(
                f"P8 property {prop!r} for slot {slot!r} is empty; "
                "resolution fails closed."
            ),
        )
    # Single, approved encoding at the sink boundary. Plain text in,
    # HTML-safe out. Never raw.
    return encode_for_html(plain), None


def resolve_content_slots(
    layout_id: Any,
    content: Any,
    *,
    content_type_id: Any = None,
    content_type: Any = None,
    slots: Tuple[str, ...] | None = None,
) -> SlotResolution:
    """Resolve a Home layout's slots to actual values on a P8 Content record.

    Args:
        layout_id: The layout to resolve. Only ``home-default`` is supported;
            anything else fails closed.
        content: The persisted P8 Content record (mapping) whose fixed
            ``title``/``body`` properties supply the slot values.
        content_type_id: The approved Home ContentType ID the record's
            ``type_id`` must equal. When ``None``, the type check is skipped
            (the caller may rely on the registry's definition check instead).
        content_type: The approved Home ContentType definition. When
            provided, its ``id`` is additionally required to equal the
            record's ``type_id`` and its name to be ``home``, so a mismatched
            ContentType fails closed.
        slots: Optional explicit slots to resolve. Defaults to the authorized
            ``home-default`` slots. An unsupported slot fails closed.

    Returns:
        SlotResolution: ``RESOLVED`` with HTML-safe values when every slot is
        authorized, well-typed, and non-empty; otherwise a deterministic
        ``FALLBACK`` with no values and recorded structural errors.
    """
    # Unknown layout -> deterministic fallback, never a guessed mapping.
    if layout_id != SUPPORTED_LAYOUT_ID:
        return SlotResolution(
            layout_id=layout_id if isinstance(layout_id, str) else repr(layout_id),
            status=FALLBACK,
            values={},
            errors=(
                SlotResolutionError(
                    code=UNKNOWN_LAYOUT,
                    slot=None,
                    message=(
                        f"Layout {layout_id!r} is not bound by the Home content "
                        "slot adapter; no values were resolved. Only "
                        f"{SUPPORTED_LAYOUT_ID!r} is authorized."
                    ),
                ),
            ),
            content_status=None,
        )

    # Malformed content record -> fail closed before any access.
    if not isinstance(content, Mapping):
        return SlotResolution(
            layout_id=SUPPORTED_LAYOUT_ID,
            status=FALLBACK,
            values={},
            errors=(
                SlotResolutionError(
                    code=MALFORMED_CONTENT,
                    slot=None,
                    message="Content record must be a mapping; resolution fails closed.",
                ),
            ),
            content_status=None,
        )

    # The record must reference the approved Home ContentType through type_id.
    if content_type_id is not None:
        if content.get("type_id") != content_type_id:
            return SlotResolution(
                layout_id=SUPPORTED_LAYOUT_ID,
                status=FALLBACK,
                values={},
                errors=(
                    SlotResolutionError(
                        code=CONTENT_TYPE_MISMATCH,
                        slot=None,
                        message=(
                            "Content record type_id does not match the approved "
                            "Home ContentType id; resolution fails closed."
                        ),
                    ),
                ),
                content_status=None,
            )

    # When the ContentType definition is supplied, verify its identity too.
    if content_type is not None:
        ct_id = content_type.get("id") if isinstance(content_type, Mapping) else None
        ct_name = (
            content_type.get("name") if isinstance(content_type, Mapping) else None
        )
        if ct_id != content.get("type_id") or ct_name != "home":
            return SlotResolution(
                layout_id=SUPPORTED_LAYOUT_ID,
                status=FALLBACK,
                values={},
                errors=(
                    SlotResolutionError(
                        code=CONTENT_TYPE_MISMATCH,
                        slot=None,
                        message=(
                            "Supplied ContentType is not the approved Home "
                            "ContentType (id/name mismatch with the record); "
                            "resolution fails closed."
                        ),
                    ),
                ),
                content_status=None,
            )

    requested = tuple(slots) if slots is not None else supported_slots(layout_id)

    values: dict[str, str] = {}
    errors: list[SlotResolutionError] = []
    for slot in requested:
        value, err = _resolve_one(content, slot)
        if err is not None:
            errors.append(err)
        else:
            values[slot] = value  # type: ignore[assignment]

    # Any error -> fail closed: no partial values are returned.
    if errors:
        return SlotResolution(
            layout_id=SUPPORTED_LAYOUT_ID,
            status=FALLBACK,
            values={},
            errors=tuple(errors),
            content_status=content.get("status") if isinstance(content.get("status"), str) else None,
        )

    return SlotResolution(
        layout_id=SUPPORTED_LAYOUT_ID,
        status=RESOLVED,
        values=values,
        errors=(),
        content_status=content.get("status") if isinstance(content.get("status"), str) else None,
    )


def satisfies_published_only(resolution: SlotResolution, required_status: str = "published") -> bool:
    """True only when the record's own status equals the required status.

    This mirrors the single permitted ``required_status`` value from
    ``framework.sps2.p10-slice/v1``. A ``draft`` record does NOT satisfy a published-only
    reference. This is a local status check, not the REQ-P10-09 runtime gate.
    """
    if not resolution.ok:
        return False
    return resolution.content_status == required_status