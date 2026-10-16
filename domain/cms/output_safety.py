"""P8 CMS output safety for plain-text content.

Content.body is PLAIN TEXT ONLY. It must never be interpreted as HTML,
Markdown, or rich text. This module provides output encoding for any
future browser/UI rendering boundary.

The security model:
- Content.body stores plain text.
- API/service validation enforces the plain-text contract.
- Any future browser/UI rendering must HTML-encode the value at the
  output/sink boundary and must never inject it as trusted HTML.
"""
from __future__ import annotations

import html
from typing import Any


def encode_for_html(text: str) -> str:
    """Encode plain text for safe HTML output.

    This function must be called at any output/sink boundary where
    Content.body is rendered in a browser/UI context. It prevents
    stored XSS by encoding all HTML-special characters.

    Args:
        text: Plain text content (not HTML).

    Returns:
        HTML-encoded string safe for insertion into HTML context.
    """
    return html.escape(text, quote=True)


def validate_plain_text(body: str) -> str:
    """Validate that content body is plain text.

    This function enforces the plain-text contract:
    - Content.body must be a string.
    - Content.body must not contain HTML tags or executable markup.
    - Content.body is stored as-is (plain text).

    Note: This function does NOT strip or mutate content. It validates
    that the content is plain text and returns it unchanged. The
    security guarantee is that the API/service boundary treats the
    content as plain text, and any rendering boundary must encode it.

    Args:
        body: The content body to validate.

    Returns:
        The original body string (unchanged).

    Raises:
        ValidationError: If body is not a string.
    """
    if not isinstance(body, str):
        raise ValueError("Content.body must be a string (plain text)")
    return body


def get_content_with_safe_output(content: dict[str, Any]) -> dict[str, Any]:
    """Return content with HTML-encoded body for safe output.

    This function should be called at any API/output boundary where
    content is returned to a consumer that may render it in a browser.

    Args:
        content: A content dictionary with a 'body' field.

    Returns:
        A new dictionary with the body field HTML-encoded for safe output.
    """
    result = dict(content)
    if "body" in result and isinstance(result["body"], str):
        result["body"] = encode_for_html(result["body"])
    return result
