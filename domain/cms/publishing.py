"""P8 CMS preview/publishing workflow.

States: draft, preview, published, archived.
Only approved transitions are allowed. Authorization is enforced on every transition.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from domain.cms.auth import RBAC, AuthorizationError
from domain.cms.model import Content, Revision
from domain.cms.persistence import JSONStore
from domain.cms.validation import validate_content, validate_revision


# Valid state transitions per approved Phase 2 architecture
VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["preview", "published"],
    "preview": ["draft", "published"],
    "published": ["draft", "archived"],
    "archived": ["draft"],
}

# Which roles can perform which transitions
TRANSITION_PERMISSIONS: dict[str, str] = {
    "draft->preview": "content_preview",
    "draft->published": "content_publish",
    "preview->draft": "content_preview",
    "preview->published": "content_publish",
    "published->draft": "content_publish",
    "published->archived": "content_publish",
    "archived->draft": "content_publish",
}


class PublishingError(Exception):
    """Publishing operation failed."""


class InvalidTransitionError(PublishingError):
    """Invalid state transition."""


class PublishingService:
    """Content publishing workflow."""

    def __init__(self, store: JSONStore, rbac: RBAC) -> None:
        self._store = store
        self._rbac = rbac

    def _get_content(self, content_id: str) -> dict:
        all_content = self._store.load("content", [])
        for c in all_content:
            if c["id"] == content_id:
                return c
        raise PublishingError(f"Content '{content_id}' not found")

    def _save_content(self, content: dict) -> None:
        all_content = self._store.load("content", [])
        for i, c in enumerate(all_content):
            if c["id"] == content["id"]:
                all_content[i] = content
                self._store.save("content", all_content)
                return
        raise PublishingError(f"Content '{content['id']}' not found")

    def _create_revision(
        self, content_id: str, body: str, author_id: str
    ) -> dict:
        revisions = self._store.read_lines("revisions")
        content_revs = [r for r in revisions if r["content_id"] == content_id]
        version = len(content_revs) + 1
        rev = Revision(
            content_id=content_id,
            version=version,
            body=body,
            author_id=author_id,
        )
        data = rev.to_dict()
        validate_revision(data)
        self._store.append("revisions", data)
        return data

    def transition(
        self,
        actor_role: str,
        content_id: str,
        target_status: str,
    ) -> dict:
        """Transition content to a new status."""
        content = self._get_content(content_id)
        current_status = content["status"]

        # Check if transition is valid
        if target_status not in VALID_TRANSITIONS.get(current_status, []):
            raise InvalidTransitionError(
                f"Cannot transition from '{current_status}' to '{target_status}'"
            )

        # Check authorization
        transition_key = f"{current_status}->{target_status}"
        required_permission = TRANSITION_PERMISSIONS.get(transition_key)
        if required_permission:
            self._rbac.require_permission(actor_role, required_permission)

        # Perform transition
        content["status"] = target_status
        content["updated_at"] = datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
        if target_status == "published":
            content["published_at"] = content["updated_at"]
        elif target_status == "draft":
            content["published_at"] = None

        validate_content(content)
        self._save_content(content)

        # Create revision
        self._create_revision(content_id, content["body"], content["author_id"])

        return content

    def publish(self, actor_role: str, content_id: str) -> dict:
        """Publish content."""
        return self.transition(actor_role, content_id, "published")

    def unpublish(self, actor_role: str, content_id: str) -> dict:
        """Unpublish content back to draft."""
        return self.transition(actor_role, content_id, "draft")

    def archive(self, actor_role: str, content_id: str) -> dict:
        """Archive content."""
        return self.transition(actor_role, content_id, "archived")

    def restore(self, actor_role: str, content_id: str) -> dict:
        """Restore archived content to draft."""
        return self.transition(actor_role, content_id, "draft")

    def preview(self, actor_role: str, content_id: str) -> dict:
        """Put content into preview mode."""
        return self.transition(actor_role, content_id, "preview")

    def get_status(self, content_id: str) -> str:
        """Get current status of content."""
        return self._get_content(content_id)["status"]

    def list_by_status(self, status: str) -> list[dict]:
        """List content by status."""
        all_content = self._store.load("content", [])
        return [c for c in all_content if c["status"] == status]
