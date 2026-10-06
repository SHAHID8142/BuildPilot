"""P8 CMS application/service layer.

Connects domain model, validation, RBAC, and persistence.
All operations enforce authorization and validation.
"""
from __future__ import annotations

from typing import Any

from domain.cms.auth import RBAC, AuthorizationError
from domain.cms.model import Asset, Content, ContentType, Revision, Section
from domain.cms.persistence import JSONStore
from domain.cms.validation import (
    ValidationError,
    validate_asset,
    validate_content,
    validate_content_type,
    validate_revision,
    validate_section,
)


class CMSError(Exception):
    """Base CMS error."""


class NotFoundError(CMSError):
    """Raised when a resource is not found."""


class ConflictError(CMSError):
    """Raised when an operation conflicts with current state."""


class CMSService:
    """Main CMS service. All operations enforce RBAC and validation."""

    def __init__(self, store: JSONStore, rbac: RBAC) -> None:
        self._store = store
        self._rbac = rbac

    # --- ContentType operations ---

    def create_content_type(
        self, actor_role: str, name: str, fields: list[dict]
    ) -> dict:
        self._rbac.require_permission(actor_role, "section_create")
        ct = ContentType(name=name, fields=fields)
        data = ct.to_dict()
        validate_content_type(data)
        all_types = self._store.load("content_types", [])
        all_types.append(data)
        self._store.save("content_types", all_types)
        return data

    def get_content_type(self, type_id: str) -> dict:
        all_types = self._store.load("content_types", [])
        for ct in all_types:
            if ct["id"] == type_id:
                return ct
        raise NotFoundError(f"ContentType '{type_id}' not found")

    def list_content_types(self) -> list[dict]:
        return self._store.load("content_types", [])

    def delete_content_type(self, actor_role: str, type_id: str) -> None:
        self._rbac.require_permission(actor_role, "section_delete")
        all_types = self._store.load("content_types", [])
        filtered = [ct for ct in all_types if ct["id"] != type_id]
        if len(filtered) == len(all_types):
            raise NotFoundError(f"ContentType '{type_id}' not found")
        self._store.save("content_types", filtered)

    # --- Content operations ---

    def create_content(
        self,
        actor_role: str,
        type_id: str,
        title: str,
        body: str = "",
        author_id: str = "",
    ) -> dict:
        self._rbac.require_permission(actor_role, "content_create")
        # Verify content type exists
        self.get_content_type(type_id)
        content = Content(
            type_id=type_id, title=title, body=body, author_id=author_id
        )
        data = content.to_dict()
        validate_content(data)
        all_content = self._store.load("content", [])
        all_content.append(data)
        self._store.save("content", all_content)
        # Create initial revision
        self._create_revision(content.id, 1, body, author_id)
        return data

    def get_content(self, content_id: str) -> dict:
        all_content = self._store.load("content", [])
        for c in all_content:
            if c["id"] == content_id:
                return c
        raise NotFoundError(f"Content '{content_id}' not found")

    def list_content(self, status: str | None = None) -> list[dict]:
        all_content = self._store.load("content", [])
        if status:
            return [c for c in all_content if c["status"] == status]
        return all_content

    def update_content(
        self,
        actor_role: str,
        content_id: str,
        title: str | None = None,
        body: str | None = None,
    ) -> dict:
        self._rbac.require_permission(actor_role, "content_edit")
        all_content = self._store.load("content", [])
        for i, c in enumerate(all_content):
            if c["id"] == content_id:
                if title is not None:
                    c["title"] = title
                if body is not None:
                    c["body"] = body
                c["updated_at"] = Content(
                    type_id=c["type_id"], title=c["title"], body=c["body"]
                ).updated_at
                validate_content(c)
                all_content[i] = c
                self._store.save("content", all_content)
                # Create new revision
                revisions = self._get_revisions(content_id)
                new_version = len(revisions) + 1
                self._create_revision(
                    content_id, new_version, c["body"], c["author_id"]
                )
                return c
        raise NotFoundError(f"Content '{content_id}' not found")

    def delete_content(self, actor_role: str, content_id: str) -> None:
        self._rbac.require_permission(actor_role, "content_delete")
        all_content = self._store.load("content", [])
        filtered = [c for c in all_content if c["id"] != content_id]
        if len(filtered) == len(all_content):
            raise NotFoundError(f"Content '{content_id}' not found")
        self._store.save("content", filtered)

    # --- Section operations ---

    def create_section(
        self,
        actor_role: str,
        name: str,
        layout: str,
        content_ids: list[str] | None = None,
        order: int = 0,
    ) -> dict:
        self._rbac.require_permission(actor_role, "section_create")
        section = Section(
            name=name, layout=layout, content_ids=content_ids or [], order=order
        )
        data = section.to_dict()
        validate_section(data)
        all_sections = self._store.load("sections", [])
        all_sections.append(data)
        self._store.save("sections", all_sections)
        return data

    def get_section(self, section_id: str) -> dict:
        all_sections = self._store.load("sections", [])
        for s in all_sections:
            if s["id"] == section_id:
                return s
        raise NotFoundError(f"Section '{section_id}' not found")

    def list_sections(self) -> list[dict]:
        return self._store.load("sections", [])

    def update_section(
        self,
        actor_role: str,
        section_id: str,
        name: str | None = None,
        layout: str | None = None,
        content_ids: list[str] | None = None,
        order: int | None = None,
    ) -> dict:
        self._rbac.require_permission(actor_role, "section_edit")
        all_sections = self._store.load("sections", [])
        for i, s in enumerate(all_sections):
            if s["id"] == section_id:
                if name is not None:
                    s["name"] = name
                if layout is not None:
                    s["layout"] = layout
                if content_ids is not None:
                    s["content_ids"] = content_ids
                if order is not None:
                    s["order"] = order
                validate_section(s)
                all_sections[i] = s
                self._store.save("sections", all_sections)
                return s
        raise NotFoundError(f"Section '{section_id}' not found")

    def delete_section(self, actor_role: str, section_id: str) -> None:
        self._rbac.require_permission(actor_role, "section_delete")
        all_sections = self._store.load("sections", [])
        filtered = [s for s in all_sections if s["id"] != section_id]
        if len(filtered) == len(all_sections):
            raise NotFoundError(f"Section '{section_id}' not found")
        self._store.save("sections", filtered)

    # --- Revision operations ---

    def _create_revision(
        self, content_id: str, version: int, body: str, author_id: str
    ) -> dict:
        rev = Revision(
            content_id=content_id, version=version, body=body, author_id=author_id
        )
        data = rev.to_dict()
        validate_revision(data)
        self._store.append("revisions", data)
        return data

    def _get_revisions(self, content_id: str) -> list[dict]:
        all_revisions = self._store.read_lines("revisions")
        return [r for r in all_revisions if r["content_id"] == content_id]

    def get_revisions(self, actor_role: str, content_id: str) -> list[dict]:
        self._rbac.require_permission(actor_role, "revision_view")
        return self._get_revisions(content_id)

    def rollback_to_revision(
        self, actor_role: str, content_id: str, revision_id: str
    ) -> dict:
        self._rbac.require_permission(actor_role, "revision_rollback")
        revisions = self._get_revisions(content_id)
        target = None
        for r in revisions:
            if r["id"] == revision_id:
                target = r
                break
        if target is None:
            raise NotFoundError(f"Revision '{revision_id}' not found")
        # Update content body to the revision body
        all_content = self._store.load("content", [])
        for i, c in enumerate(all_content):
            if c["id"] == content_id:
                c["body"] = target["body"]
                c["updated_at"] = Content(
                    type_id=c["type_id"], title=c["title"], body=c["body"]
                ).updated_at
                validate_content(c)
                all_content[i] = c
                self._store.save("content", all_content)
                # Create new revision for the rollback
                new_version = len(revisions) + 1
                self._create_revision(
                    content_id, new_version, target["body"], target["author_id"]
                )
                return c
        raise NotFoundError(f"Content '{content_id}' not found")

    # --- Asset operations ---

    def register_asset(self, asset: Asset) -> dict:
        data = asset.to_dict()
        validate_asset(data)
        all_assets = self._store.load("assets", [])
        all_assets.append(data)
        self._store.save("assets", all_assets)
        return data

    def get_asset(self, asset_id: str) -> dict:
        all_assets = self._store.load("assets", [])
        for a in all_assets:
            if a["id"] == asset_id:
                return a
        raise NotFoundError(f"Asset '{asset_id}' not found")

    def list_assets(self) -> list[dict]:
        return self._store.load("assets", [])
