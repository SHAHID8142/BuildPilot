"""P8 CMS API/interface layer.

Provides a programmatic interface to the CMS service.
All methods enforce RBAC and validation.
"""
from __future__ import annotations

from typing import Any

from framework.domain.cms.auth import RBAC
from framework.domain.cms.model import Asset
from framework.domain.cms.persistence import JSONStore
from framework.domain.cms.service import CMSService


class CMSAPI:
    """Programmatic CMS API. All operations enforce RBAC."""

    def __init__(self, data_dir: str = "framework/domain/cms/data") -> None:
        self._store = JSONStore(data_dir)
        self._rbac = RBAC()
        self._service = CMSService(self._store, self._rbac)

    @property
    def rbac(self) -> RBAC:
        return self._rbac

    @property
    def service(self) -> CMSService:
        return self._service

    # --- ContentType API ---

    def create_content_type(
        self, actor_role: str, name: str, fields: list[dict]
    ) -> dict:
        return self._service.create_content_type(actor_role, name, fields)

    def get_content_type(self, type_id: str) -> dict:
        return self._service.get_content_type(type_id)

    def list_content_types(self) -> list[dict]:
        return self._service.list_content_types()

    def delete_content_type(self, actor_role: str, type_id: str) -> None:
        return self._service.delete_content_type(actor_role, type_id)

    # --- Content API ---

    def create_content(
        self,
        actor_role: str,
        type_id: str,
        title: str,
        body: str = "",
        author_id: str = "",
    ) -> dict:
        return self._service.create_content(
            actor_role, type_id, title, body, author_id
        )

    def get_content(self, content_id: str) -> dict:
        return self._service.get_content(content_id)

    def list_content(self, status: str | None = None) -> list[dict]:
        return self._service.list_content(status)

    def update_content(
        self,
        actor_role: str,
        content_id: str,
        title: str | None = None,
        body: str | None = None,
    ) -> dict:
        return self._service.update_content(
            actor_role, content_id, title, body
        )

    def delete_content(self, actor_role: str, content_id: str) -> None:
        return self._service.delete_content(actor_role, content_id)

    # --- Section API ---

    def create_section(
        self,
        actor_role: str,
        name: str,
        layout: str,
        content_ids: list[str] | None = None,
        order: int = 0,
    ) -> dict:
        return self._service.create_section(
            actor_role, name, layout, content_ids, order
        )

    def get_section(self, section_id: str) -> dict:
        return self._service.get_section(section_id)

    def list_sections(self) -> list[dict]:
        return self._service.list_sections()

    def update_section(
        self,
        actor_role: str,
        section_id: str,
        name: str | None = None,
        layout: str | None = None,
        content_ids: list[str] | None = None,
        order: int | None = None,
    ) -> dict:
        return self._service.update_section(
            actor_role, section_id, name, layout, content_ids, order
        )

    def delete_section(self, actor_role: str, section_id: str) -> None:
        return self._service.delete_section(actor_role, section_id)

    # --- Revision API ---

    def get_revisions(self, actor_role: str, content_id: str) -> list[dict]:
        return self._service.get_revisions(actor_role, content_id)

    def rollback_to_revision(
        self, actor_role: str, content_id: str, revision_id: str
    ) -> dict:
        return self._service.rollback_to_revision(
            actor_role, content_id, revision_id
        )

    # --- Asset API ---

    def register_asset(self, asset: Asset) -> dict:
        return self._service.register_asset(asset)

    def get_asset(self, asset_id: str) -> dict:
        return self._service.get_asset(asset_id)

    def list_assets(self) -> list[dict]:
        return self._service.list_assets()
