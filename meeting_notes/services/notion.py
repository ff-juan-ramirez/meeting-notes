"""Notion API service module — pure functions, no Click/Rich imports.

Provides create_page() and extract_title() as the public API consumed by summarize.py.
Internal helpers: _split_text, _rich_text, _markdown_to_blocks, _call_with_retry.
"""
import time

from notion_client import Client
from notion_client.errors import APIResponseError

MAX_RICH_TEXT_CHARS = 1900
MAX_CHILDREN_PER_REQUEST = 100
RETRY_BASE_DELAY = 1.0
MAX_RETRIES = 4


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_title(notes_markdown: str, fallback_timestamp: str) -> str:
    """Extract title from notes: first H1 > first non-empty line > fallback_timestamp."""
    for line in notes_markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    for line in notes_markdown.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return fallback_timestamp


def create_page(token: str, parent_page_id: str, title: str, notes_markdown: str) -> str:
    """Create a Notion child page. Returns page URL (https://notion.so/{id_no_hyphens})."""
    client = Client(auth=token)
    blocks = _markdown_to_blocks(notes_markdown)

    first_batch = blocks[:MAX_CHILDREN_PER_REQUEST]
    overflow = blocks[MAX_CHILDREN_PER_REQUEST:]

    response = _call_with_retry(
        client.pages.create,
        parent={"page_id": parent_page_id},
        properties={
            "title": [{"type": "text", "text": {"content": title}}],
        },
        children=first_batch,
    )

    page_id = response["id"]

    if overflow:
        _call_with_retry(
            client.blocks.children.append,
            block_id=page_id,
            children=overflow,
        )

    return f"https://notion.so/{page_id.replace('-', '')}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_text(text: str, max_chars: int = MAX_RICH_TEXT_CHARS) -> list[str]:
    """Split text into chunks of at most max_chars, splitting at whitespace boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > max_chars:
        # Find last space at or before max_chars
        split_at = remaining.rfind(" ", 0, max_chars)
        if split_at == -1:
            # No space found — hard split at max_chars
            split_at = max_chars
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip(" ")
    if remaining:
        chunks.append(remaining)
    return chunks


def _rich_text(content: str) -> list[dict]:
    """Build a Notion rich_text array for a single text content string."""
    return [{"type": "text", "text": {"content": content}}]


def _markdown_to_blocks(markdown: str) -> list[dict]:
    """Convert markdown text to a list of Notion block dicts.

    - H1/H2/H3 lines -> heading_2 blocks
    - "- " or "* " lines -> bulleted_list_item blocks
    - Other non-empty lines -> paragraph blocks
    - Each line's text is split at MAX_RICH_TEXT_CHARS if needed
    """
    blocks = []
    for line in markdown.splitlines():
        stripped = line.rstrip()

        if stripped.startswith("# ") or stripped.startswith("## ") or stripped.startswith("### "):
            block_type = "heading_2"
            if stripped.startswith("### "):
                text = stripped[4:]
            elif stripped.startswith("## "):
                text = stripped[3:]
            else:
                text = stripped[2:]
        elif stripped.startswith("- ") or stripped.startswith("* "):
            block_type = "bulleted_list_item"
            text = stripped[2:]
        elif stripped:
            block_type = "paragraph"
            text = stripped
        else:
            continue

        for chunk in _split_text(text):
            blocks.append({
                "object": "block",
                "type": block_type,
                block_type: {"rich_text": _rich_text(chunk)},
            })

    return blocks


def _call_with_retry(fn, *args, **kwargs):
    """Call fn with retry on HTTP 429 (rate limit). Exponential backoff."""
    delay = RETRY_BASE_DELAY
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except APIResponseError as exc:
            if exc.status == 429:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise
    raise last_exc
