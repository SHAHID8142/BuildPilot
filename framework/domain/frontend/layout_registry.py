"""P10 layout registry (REQ-P10-02).

D-P10-2 ("P8 / P10 Presentation Ownership") assigns P10 ownership of
``framework/domain/frontend/`` and, specifically, "the interpretation and registry
of Section.layout values."  P8 continues to store ``Section.layout`` as
CMS data but defines no presentation meaning for it (REQ-P10-02
criterion 3).  This module is that single source of presentation
meaning: it enumerates every layout identifier the renderer knows how to
render and declares which content field slots each consumes
(REQ-P10-02 criteria 1 and 4).

Fail-closed contract
--------------------
* Only explicitly registered layouts resolve.  Nothing is inferred,
  guessed, or silently substituted.
* A ``Section.layout`` value absent from the registry is NEVER silently
  rendered as ``home-default`` or any other layout.  Resolution returns
  a deterministic fallback (no field slots consumed) plus a recorded
  error naming the unknown identifier (REQ-P10-02 criterion 2).
* Every declared field slot must resolve to a field present in the P8
  ``ContentType`` definition; a slot that does not resolve is rejected
  (REQ-P10-02 criterion 4).
* Errors carry only structural metadata (layout identifiers and
  field-slot names).  They never carry raw CMS content.

Scope boundary
--------------
This module resolves layout identifiers to their declared field slots.
It does NOT render HTML, does NOT consume or store content values, does
NOT publish or authorize publication of any content, and does NOT
bypass the P8 per-sink output-encoding boundary
(``framework.domain.cms.output_safety``).  The renderer that turns a resolution
into a defined fallback document or a rendered slice is a separate,
out-of-scope component (REQ-P10-02 defines the registry; the renderer
is built under the P10 slice contract).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, FrozenSet, Tuple

# Sentinel marking the deterministic unknown-layout fallback.  This is
# NOT a registered, renderable layout: it exists only to make "no
# layout resolved" explicit and distinguishable from any real layout
# identifier.  It is never ``home-default`` and never an arbitrary
# registered layout.
FALLBACK_LAYOUT_ID = "__p10_no_layout__"

# Resolution statuses.
RESOLVED = "resolved"
FALLBACK = "fallback"

# Recorded-error codes.
UNKNOWN_LAYOUT = "P10_UNKNOWN_LAYOUT"
UNRESOLVED_FIELD_SLOT = "P10_UNRESOLVED_FIELD_SLOT"

# layout_id shape, mirroring framework/sps2/schemas/p10-slice.schema.json
# ``layout_id`` (``^[a-z][a-z0-9-]*$``).
_LAYOUT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


class LayoutRegistryError(ValueError):
    """Raised when a layout definition is malformed (fail closed)."""


@dataclass(frozen=True)
class LayoutDefinition:
    """A registered layout and the content field slots it consumes."""

    layout_id: str
    field_slots: Tuple[str, ...]


@dataclass(frozen=True)
class LayoutError:
    """A recorded registry error.  Carries structural metadata only."""

    code: str
    layout_id: str
    message: str


@dataclass(frozen=True)
class LayoutResolution:
    """The deterministic outcome of resolving a layout identifier.

    ``status`` is ``RESOLVED`` when the layout is registered and every
    declared field slot resolves against the supplied ContentType, else
    ``FALLBACK``.  On ``FALLBACK`` the renderer consumes no CMS field
    slots (``field_slots`` is empty), so an unknown or incomplete layout
    can never authorize rendering or publication of content.
    """

    layout_id: str
    status: str
    field_slots: Tuple[str, ...]
    errors: Tuple[LayoutError, ...]

    @property
    def ok(self) -> bool:
        """True only when fully resolved with no recorded errors."""
        return self.status == RESOLVED and not self.errors


def validate_layout_definition(
    layout_id: str, field_slots: Iterable[str]
) -> LayoutDefinition:
    """Validate and build a ``LayoutDefinition``, failing closed.

    A definition is malformed when the ``layout_id`` is not a
    non-empty lowercase identifier, when ``field_slots`` is empty, when
    a slot is not a non-empty string, or when a slot is duplicated.
    Malformed definitions raise ``LayoutRegistryError`` and are never
    registered.
    """
    if not isinstance(layout_id, str) or not _LAYOUT_ID_PATTERN.fullmatch(layout_id):
        raise LayoutRegistryError(
            f"layout_id must match {_LAYOUT_ID_PATTERN.pattern!r}; got {layout_id!r}"
        )
    if isinstance(field_slots, (str, bytes)) or not isinstance(field_slots, Iterable):
        raise LayoutRegistryError(
            "field_slots must be an iterable of field-name strings"
        )
    slots: list[str] = []
    for slot in field_slots:
        if not isinstance(slot, str) or not slot:
            raise LayoutRegistryError(
                f"field slots must be non-empty strings; got {slot!r}"
            )
        if slot in slots:
            raise LayoutRegistryError(
                f"duplicate field slot {slot!r} in layout {layout_id!r}"
            )
        slots.append(slot)
    if not slots:
        raise LayoutRegistryError(
            f"layout {layout_id!r} must declare at least one field slot"
        )
    return LayoutDefinition(layout_id=layout_id, field_slots=tuple(slots))


def _build_registry(
    spec: Mapping[str, Tuple[str, ...]]
) -> dict[str, LayoutDefinition]:
    """Build the registry from an explicit spec, failing closed.

    Every entry is validated through ``validate_layout_definition``; a
    malformed entry raises before it can enter the registry.
    """
    registry: dict[str, LayoutDefinition] = {}
    for layout_id, slots in spec.items():
        definition = validate_layout_definition(layout_id, slots)
        registry[definition.layout_id] = definition
    return registry


# The complete, explicit enumeration of layout identifiers the renderer
# knows how to render (REQ-P10-02 criterion 1).  Adding a layout is an
# explicit act here; nothing is inferred.  ``home-default`` consumes the
# ``heading`` and ``body`` field slots of the Home ContentType.
_LAYOUT_SPEC: Mapping[str, Tuple[str, ...]] = {
    "home-default": ("heading", "body"),
}

# Exposed as an immutable mapping so callers cannot mutate the registry.
LAYOUT_REGISTRY: Mapping[str, LayoutDefinition] = MappingProxyType(
    _build_registry(_LAYOUT_SPEC)
)


def registered_layout_ids() -> Tuple[str, ...]:
    """Return every registered layout identifier (criterion 1)."""
    return tuple(LAYOUT_REGISTRY.keys())


def is_registered(layout_id: Any) -> bool:
    """True only for an explicitly registered layout identifier.

    A layout string merely stored by P8 is NOT proof of registration
    (REQ-P10-02): only membership in this registry counts.
    """
    return isinstance(layout_id, str) and layout_id in LAYOUT_REGISTRY


def _extract_field_names(content_type: Any) -> FrozenSet[str]:
    """Extract the set of field names defined by a P8 ContentType.

    Accepts the P8 ContentType mapping (``{"fields": [{"name": ...},
    ...]}``), a P8 ``ContentType`` model object (``.fields``), or any
    iterable of field-name strings.  Anything else raises ``TypeError``
    so a malformed input fails closed instead of being coerced into a
    false match.
    """
    if isinstance(content_type, Mapping):
        if "fields" not in content_type:
            raise TypeError("ContentType mapping must declare a 'fields' sequence")
        raw: Any = content_type["fields"]
    elif hasattr(content_type, "fields"):
        # P8 ContentType model object (framework.domain.cms.model.ContentType).
        raw = content_type.fields
    else:
        raw = content_type
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Iterable):
        raise TypeError("ContentType fields must be a sequence of field definitions")
    names: set[str] = set()
    for item in raw:
        name = item.get("name") if isinstance(item, Mapping) else item
        if not isinstance(name, str) or not name:
            raise TypeError(
                "ContentType field entries must carry a non-empty 'name'"
            )
        names.add(name)
    return frozenset(names)


def resolve(layout_id: Any, content_type: Any = None) -> LayoutResolution:
    """Resolve a layout identifier against the registry and a ContentType.

    Parameters
    ----------
    layout_id:
        The ``Section.layout`` value stored by P8.  P8 stores it as
        data without presentation meaning; this function is the sole
        source of that meaning.
    content_type:
        The P8 ContentType definition whose fields the layout's slots
        must resolve against.  When ``None``, slot resolution cannot be
        established and the layout fails closed.

    Returns
    -------
    LayoutResolution
        ``RESOLVED`` with the declared field slots when the layout is
        registered and every slot is present in the ContentType;
        otherwise a deterministic ``FALLBACK`` with no field slots and
        a recorded error.  This function never raises for an unknown or
        malformed layout: those cases are recorded, returned fallbacks,
        not exceptions (REQ-P10-02 criterion 5).
    """
    # Unknown layout -> deterministic fallback.  Never a silent
    # substitution of home-default and never an arbitrary layout.
    if not is_registered(layout_id):
        unknown = layout_id if isinstance(layout_id, str) else repr(layout_id)
        error = LayoutError(
            code=UNKNOWN_LAYOUT,
            layout_id=unknown,
            message=(
                f"Unknown layout identifier {unknown!r} is not registered in "
                "the P10 layout registry; no layout was resolved and no CMS "
                "content is consumed. Registering a layout is an explicit act; "
                "it was not inferred, guessed, or substituted with home-default."
            ),
        )
        return LayoutResolution(
            layout_id=FALLBACK_LAYOUT_ID,
            status=FALLBACK,
            field_slots=(),
            errors=(error,),
        )

    definition = LAYOUT_REGISTRY[layout_id]

    # Registered layout: every declared slot must resolve to a field
    # present in the P8 ContentType definition.  Without a ContentType,
    # slot resolution cannot be established -> fail closed.
    if content_type is None:
        error = LayoutError(
            code=UNRESOLVED_FIELD_SLOT,
            layout_id=layout_id,
            message=(
                f"Layout {layout_id!r} is registered but no ContentType was "
                "supplied to validate its field slots; resolution fails closed."
            ),
        )
        return LayoutResolution(
            layout_id=layout_id, status=FALLBACK, field_slots=(), errors=(error,)
        )

    try:
        available = _extract_field_names(content_type)
    except TypeError as exc:
        error = LayoutError(
            code=UNRESOLVED_FIELD_SLOT,
            layout_id=layout_id,
            message=f"Layout {layout_id!r} cannot resolve: {exc}",
        )
        return LayoutResolution(
            layout_id=layout_id, status=FALLBACK, field_slots=(), errors=(error,)
        )

    unresolved = [slot for slot in definition.field_slots if slot not in available]
    if unresolved:
        error = LayoutError(
            code=UNRESOLVED_FIELD_SLOT,
            layout_id=layout_id,
            message=(
                f"Layout {layout_id!r} declares field slots {unresolved!r} "
                "that are not present in the supplied ContentType; resolution "
                "fails closed and no CMS content is consumed."
            ),
        )
        return LayoutResolution(
            layout_id=layout_id, status=FALLBACK, field_slots=(), errors=(error,)
        )

    return LayoutResolution(
        layout_id=layout_id,
        status=RESOLVED,
        field_slots=definition.field_slots,
        errors=(),
    )
