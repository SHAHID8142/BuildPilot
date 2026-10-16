"""P10 Home slice renderer and static build path (REQ-P10-09 stage-3 build).

Scope
-----
This module implements the MINIMUM real renderer/static-build path required
to evaluate ``sps2/project/SLICE-P10-01.json`` against actual CMS inputs,
under the Round 13 implementation authorization. It is deliberately narrow:

- ONE layout (``home-default``), ONE route (``/``), ONE content reference.
- In-process, stdlib-only, zero network: no socket, no server, no subprocess,
  no deployment (DEC-7101: pure in-process, LOCAL_NON_NETWORK_EXPOSED).
- No state-changing backend operations (DEC-7108: the slice declares none and
  this module adds none; the only writes are the declared build directory).

Output safety
-------------
Every CMS value reaches an HTML sink through the APPROVED P8 per-sink encoder
(``domain.cms.output_safety.encode_for_html``), invoked exactly once per
value by the authorized slot adapter (``domain.frontend.content_slots``).
This module never interpolates a raw CMS value into HTML and never handles
raw values itself: it consumes only the adapter's already-encoded output.

SEO boundary
------------
SEO is OWNED BY P9 (DEC-7109). This module does not reimplement any SEO
logic: metadata comes from ``domain.seo.metadata`` (which marks draft content
noindex/nofollow per Threat Model 5.9), robots.txt from ``generate_robots_txt``,
and sitemap.xml from ``generate_sitemap_from_cms_items`` (which strictly
excludes unpublished items). The emitted artifact set is exactly the
``p10_to_p9_contract`` shape: HTML discoverable by the audit's ``**/*.html``
scan, plus robots.txt and sitemap.xml at the build root.

Publication boundary
--------------------
This module does NOT publish content and does NOT promote a draft. With the
default ``draft_policy="fail"`` a draft record ABORTS the build (harness
contract stage 3: "abort; report the failing build stage"). The explicit
``draft_policy="noindex_preview"`` mode exists for deterministic error-state
and harness coverage only: it renders the draft with P9's automatic
noindex/nofollow directives and the record remains excluded from the
sitemap. It is a local preview artifact, never a published route, and it
never mutates CMS state.

Determinism
-----------
Identical CMS state yields byte-identical output: no timestamps, no locale
text, and no randomness enter the emitted bytes. The sitemap urlset carries
no generation timestamp, and robots.txt is generated deterministically by the
P9 engine.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, List, Mapping, Sequence

from domain.cms.output_safety import encode_for_html  # noqa: F401  (sink contract documentation)
from domain.frontend.content_slots import (
    SUPPORTED_LAYOUT_ID,
    resolve_content_slots,
)
from domain.seo.indexing import (
    generate_robots_txt,
    generate_sitemap_from_cms_items,
    generate_sitemap_xml,
)
from domain.seo.metadata import (
    generate_metadata_from_content,
    render_html_meta_tags,
)
from domain.seo.model import RobotsConfig, RobotsGroup

__all__ = [
    "HomeBuildError",
    "BuildResult",
    "find_content_record",
    "render_home_document",
    "build_home_slice",
    "validate_home_document",
    "ReparseFinding",
]

# The single authorized route for the initial slice (DEC-7105).
SUPPORTED_ROUTE = "/"

# The canonical domain used for metadata and sitemap URLs. This is the P9
# audit's own default (domain/seo/audit.py audit_directory), adopted here so
# the audit parses exactly the URLs the renderer emitted. It is a build
# parameter inherited from P9, not an invented deployment claim.
DEFAULT_CANONICAL_DOMAIN = "https://example.com"

# Draft-handling policies.
DRAFT_POLICY_FAIL = "fail"                    # default: abort the build
DRAFT_POLICY_NOINDEX_PREVIEW = "noindex_preview"  # deterministic error-state preview


class HomeBuildError(Exception):
    """A fail-closed build abort. Names the failing harness stage.

    The message never carries raw CMS content values.
    """


@dataclass(frozen=True)
class BuildResult:
    """Outcome of one successful build. Records facts, never approvals."""

    build_dir: str
    files: tuple[str, ...]
    route: str
    layout_id: str
    content_id: str
    content_status: str
    draft_preview: bool
    sitemap_url_count: int


@dataclass(frozen=True)
class ReparseFinding:
    """One structural finding from reparse validation."""

    code: str
    detail: str


def find_content_record(
    content_records: Sequence[Any], content_id: str
) -> Mapping[str, Any]:
    """Locate the referenced Content record by id; fail closed on ambiguity.

    Identity is resolved by unique id, never by array position: a duplicate
    id is an integrity failure, not a last-writer-wins lookup.
    """
    if not isinstance(content_id, str) or not content_id:
        raise HomeBuildError("stage 3 (build): slice declares no usable content_id")
    matches: List[Mapping[str, Any]] = []
    for record in content_records:
        if isinstance(record, Mapping) and record.get("id") == content_id:
            matches.append(record)
    if not matches:
        raise HomeBuildError(
            f"stage 3 (build): referenced content id not found in CMS records"
        )
    if len(matches) > 1:
        raise HomeBuildError(
            "stage 3 (build): duplicate content id in CMS records; "
            "identity must be unique"
        )
    return matches[0]


def _enforce_publication(status: Any, content_id: str, draft_policy: str) -> bool:
    """Apply the publication boundary. Returns draft_preview flag.

    A draft never silently becomes a published route. The default policy
    aborts; the explicit preview policy renders a noindex error-state.
    """
    if not isinstance(status, str) or not status:
        raise HomeBuildError(
            f"stage 3 (build): content {content_id!r} carries no usable status"
        )
    if status == "published":
        return False
    if draft_policy == DRAFT_POLICY_FAIL:
        raise HomeBuildError(
            f"stage 3 (build): content {content_id!r} is status {status!r}, "
            "not 'published'; the default draft policy aborts the build and "
            "no published route is produced"
        )
    if draft_policy == DRAFT_POLICY_NOINDEX_PREVIEW:
        return True
    raise HomeBuildError(
        f"stage 3 (build): unknown draft_policy {draft_policy!r}"
    )


def render_home_document(
    slice_doc: Mapping[str, Any],
    content_records: Sequence[Any],
    content_types: Sequence[Any],
    *,
    canonical_domain: str = DEFAULT_CANONICAL_DOMAIN,
    draft_policy: str = DRAFT_POLICY_FAIL,
) -> str:
    """Render the Home slice's single HTML document. Pure; no I/O.

    Fails closed on: unknown layout, unknown route, missing/ambiguous content,
    ContentType mismatch, missing or empty required fields, and draft content
    under the default draft policy. Every CMS value is HTML-encoded exactly
    once at the sink by the authorized slot adapter before it enters this
    document.
    """
    if not isinstance(slice_doc, Mapping):
        raise HomeBuildError("stage 3 (build): slice document must be a mapping")

    route = slice_doc.get("route")
    if route != SUPPORTED_ROUTE:
        raise HomeBuildError(
            f"stage 3 (build): route {route!r} is not the authorized Home "
            f"route {SUPPORTED_ROUTE!r}"
        )

    layout_id = slice_doc.get("layout_id")
    if layout_id != SUPPORTED_LAYOUT_ID:
        raise HomeBuildError(
            f"stage 3 (build): layout {layout_id!r} is not the authorized "
            f"Home layout {SUPPORTED_LAYOUT_ID!r}"
        )

    refs = slice_doc.get("cms_content_references")
    if (
        not isinstance(refs, list)
        or len(refs) != 1
        or not isinstance(refs[0], Mapping)
    ):
        raise HomeBuildError(
            "stage 3 (build): the Home slice declares exactly one content "
            "reference; anything else is out of this renderer's authorized scope"
        )
    ref = refs[0]
    content_id = ref.get("content_id")
    record = find_content_record(content_records, content_id)

    # The approved Home ContentType definition, matched by the record's type_id.
    type_id = record.get("type_id")
    content_type = None
    for ct in content_types:
        if isinstance(ct, Mapping) and ct.get("id") == type_id:
            content_type = ct
            break
    if content_type is None:
        raise HomeBuildError(
            "stage 3 (build): the record's ContentType definition was not "
            "found; the CMS state is inconsistent"
        )

    # Publication boundary BEFORE any rendering.
    draft_preview = _enforce_publication(record.get("status"), str(content_id), draft_policy)

    # Resolve slot values through the approved adapter: it validates the
    # ContentType shape, enforces plain text, and HTML-encodes at the sink.
    resolution = resolve_content_slots(
        layout_id,
        record,
        content_type_id=type_id,
        content_type=content_type,
    )
    if not resolution.ok:
        codes = [e.code for e in resolution.errors]
        raise HomeBuildError(
            f"stage 3 (build): content slot resolution failed ({', '.join(codes)}); "
            "no document is rendered"
        )

    # P9-owned metadata. For a draft, the P9 ingestion marks robots
    # noindex/nofollow automatically (Threat Model 5.9) - the preview state
    # is machine-declared unpublishable, never promoted.
    meta = generate_metadata_from_content(
        record, base_url=canonical_domain, slug=SUPPORTED_ROUTE
    )
    head = render_html_meta_tags(meta)

    # Sink-safe interpolation: resolution.values are ALREADY HTML-encoded by
    # the adapter (encode_for_html, exactly once). No further encoding here,
    # and no raw value ever enters this f-string.
    heading = resolution.values["heading"]
    body = resolution.values["body"]

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        f"{head}\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        f"<h1>{heading}</h1>\n"
        f"<p>{body}</p>\n"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )


class _StructureChecker(HTMLParser):
    """Stdlib reparse checker for the Home document's structural assertions.

    Verifies the per_slice_dod frontend/a11y criteria that are checkable
    without a browser: fully closed element structure, exactly one h1, no
    heading-level jumps, declared language, and a viewport meta tag. This is
    a structural check only; it makes no accessibility-conformance claim
    (DEC-7103) and no rendering claim.
    """

    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[str] = []
        self.headings: List[int] = []
        self.has_lang = False
        self.has_viewport = False
        self.unclosed: List[str] = []
        self.mismatched: List[str] = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag == "html":
            for name, _value in attrs or []:
                if name == "lang":
                    self.has_lang = True
        if tag == "meta":
            for name, value in attrs or []:
                if name == "name" and (value or "").lower() == "viewport":
                    self.has_viewport = True
        if tag in self.VOID_ELEMENTS:
            return
        self.stack.append(tag)
        if len(tag) == 2 and tag[0] == "h" and tag[1].isdigit():
            self.headings.append(int(tag[1]))

    def handle_endtag(self, tag: str) -> None:
        if tag in self.VOID_ELEMENTS:
            return
        if not self.stack:
            self.mismatched.append(f"</{tag}> with empty stack")
            return
        if self.stack[-1] == tag:
            self.stack.pop()
            return
        # Tolerate implied closes only for the documented HTML void/implied
        # cases the Home document never uses; anything else is a defect.
        if tag in self.stack:
            self.mismatched.append(f"</{tag}> closes over open <{'.'.join(self.stack)}>")
            while self.stack and self.stack[-1] != tag:
                self.unclosed.append(self.stack.pop())
            if self.stack:
                self.stack.pop()
        else:
            self.mismatched.append(f"stray </{tag}>")

    def finalize(self) -> List[ReparseFinding]:
        findings: List[ReparseFinding] = []
        if self.stack:
            findings.append(ReparseFinding("UNCLOSED_ELEMENTS", str(self.stack)))
        if self.mismatched:
            findings.append(ReparseFinding("MISMATCHED_TAGS", "; ".join(self.mismatched)))
        if len(self.headings) != 1 or self.headings[:1] != [1]:
            findings.append(
                ReparseFinding(
                    "H1_COUNT",
                    f"exactly one h1 required, found headings {self.headings}",
                )
            )
        for prev, nxt in zip(self.headings, self.headings[1:]):
            if nxt > prev + 1:
                findings.append(
                    ReparseFinding(
                        "HEADING_JUMP",
                        f"h{prev} followed by h{nxt}",
                    )
                )
        if not self.has_lang:
            findings.append(ReparseFinding("LANG_MISSING", "html element lacks lang"))
        if not self.has_viewport:
            findings.append(ReparseFinding("VIEWPORT_MISSING", "no viewport meta"))
        return findings


def validate_home_document(html_text: str) -> List[ReparseFinding]:
    """Reparse the emitted document with the stdlib HTMLParser (stage 4).

    Returns the structural findings; an empty list means every structural
    assertion passed. Structural only: no accessibility conformance, no
    rendering fidelity, no performance claim.
    """
    checker = _StructureChecker()
    checker.feed(html_text)
    checker.close()
    return checker.finalize()


def build_home_slice(
    slice_doc: Mapping[str, Any],
    content_records: Sequence[Any],
    content_types: Sequence[Any],
    build_dir: str | os.PathLike[str],
    *,
    canonical_domain: str = DEFAULT_CANONICAL_DOMAIN,
    draft_policy: str = DRAFT_POLICY_FAIL,
) -> BuildResult:
    """Build the Home slice's static artifact set into ``build_dir``.

    Emits exactly the p10_to_p9_contract artifact shape: the HTML document
    for route ``/`` (as ``index.html``, the P9 audit's own route derivation),
    robots.txt, and sitemap.xml - the latter two through the P9 engines, per
    DEC-7109. The build writes nothing outside ``build_dir``.

    The sitemap is generated by ``generate_sitemap_from_cms_items``, which
    STRICTLY excludes unpublished records (Threat Model 5.9): a draft preview
    build therefore carries an empty urlset and no published route exists.
    """
    if not isinstance(slice_doc, Mapping):
        raise HomeBuildError("stage 3 (build): slice document must be a mapping")
    refs = slice_doc.get("cms_content_references")
    content_id = refs[0].get("content_id") if isinstance(refs, list) and refs and isinstance(refs[0], Mapping) else None

    document = render_home_document(
        slice_doc,
        content_records,
        content_types,
        canonical_domain=canonical_domain,
        draft_policy=draft_policy,
    )

    # Stage 4 on the in-memory document BEFORE anything is written: a
    # structurally invalid document is never emitted.
    findings = validate_home_document(document)
    if findings:
        detail = "; ".join(f"{f.code}: {f.detail}" for f in findings)
        raise HomeBuildError(f"stage 4 (reparse): structural assertions failed: {detail}")

    out = Path(build_dir)
    out.mkdir(parents=True, exist_ok=True)

    record = find_content_record(content_records, content_id)
    status = record.get("status")
    draft_preview = status != "published"

    (out / "index.html").write_text(document, encoding="utf-8")

    robots = generate_robots_txt(
        RobotsConfig(
            groups=[RobotsGroup(disallow=[])],
            sitemaps=[f"{canonical_domain}/sitemap.xml"],
        )
    )
    (out / "robots.txt").write_text(robots, encoding="utf-8")

    sitemap_model = generate_sitemap_from_cms_items(
        list(content_records), base_url=canonical_domain
    )
    sitemap_xml = generate_sitemap_xml(sitemap_model)
    (out / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")

    return BuildResult(
        build_dir=str(out),
        files=("index.html", "robots.txt", "sitemap.xml"),
        route=SUPPORTED_ROUTE,
        layout_id=str(slice_doc.get("layout_id")),
        content_id=str(content_id),
        content_status=str(status),
        draft_preview=draft_preview,
        sitemap_url_count=len(sitemap_model.entries),
    )
