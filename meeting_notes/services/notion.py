"""Notion service: create meeting note pages via notion-client SDK."""
import time
from notion_client import Client
from notion_client.errors import APIResponseError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_RICH_TEXT_CHARS = 1900
MAX_CHILDREN_PER_REQUEST = 100
RETRY_BASE_DELAY = 1.0
MAX_RETRIES = 4


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_title(notes_markdown: str, fallback_timestamp: str) -> str:
    """Extract page title from generated notes markdown.

    Returns the first H1 heading text (stripped of "# " prefix).
    If no H1 found, returns the first non-empty line.
    If all lines are empty, returns fallback_timestamp.
    """
    for line in notes_markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    for line in notes_markdown.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return fallback_timestamp


def create_page(token: str, parent_page_id: str, title: str, notes_markdown: str) -> str:
    """Create a Notion child page under parent_page_id with markdown content.

    Returns the URL of the created page.
    Handles >100 blocks by appending overflow via blocks.children.append().
    """
    client = Client(auth=token)
    blocks = _markdown_to_blocks(notes_markdown)

    first_batch = blocks[:MAX_CHILDREN_PER_REQUEST]
    overflow = blocks[MAX_CHILDREN_PER_REQUEST:]

    response = _call_with_retry(
        client.pages.create,
        parent={"page_id": parent_page_id},
        properties={
            "title": [{"type": "text", "text": {"content": title}}]
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
    """Split text into chunks of at most max_chars characters.

    Splits at whitespace boundaries when possible. If no whitespace found
    within the limit, splits hard at max_chars.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    while len(text) > max_chars:
        split_at = text.rfind(" ", 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip(" ")
    if text:
        chunks.append(text)
    return chunks


def _rich_text(content: str) -> list[dict]:
    """Build a Notion rich_text array for the given content string."""
    return [{"type": "text", "text": {"content": content}}]


def _markdown_to_blocks(markdown: str) -> list[dict]:
    """Convert markdown text to a list of Notion block objects.

    - Lines starting with "# ", "## ", "### " become heading_2 blocks
    - Lines starting with "- " or "* " become bulleted_list_item blocks
    - Other non-empty lines become paragraph blocks
    - Empty lines are skipped
    - Long lines are split into multiple blocks of the same type
    """
    blocks = []
    for line in markdown.splitlines():
        if not line.strip():
            continue

        if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
            # Strip heading prefix (handle 1-3 hashes)
            if line.startswith("### "):
                text = line[4:].strip()
            elif line.startswith("## "):
                text = line[3:].strip()
            else:
                text = line[2:].strip()
            block_type = "heading_2"
        elif line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            block_type = "bulleted_list_item"
        else:
            text = line.strip()
            block_type = "paragraph"

        for chunk in _split_text(text):
            blocks.append({
                "object": "block",
                "type": block_type,
                block_type: {"rich_text": _rich_text(chunk)},
            })

    return blocks


def _call_with_retry(fn, *args, **kwargs):
    """Call fn(*args, **kwargs) with exponential backoff on HTTP 429.

    Retries up to MAX_RETRIES times. Raises immediately on non-429 errors.
    """
    delay = RETRY_BASE_DELAY
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except APIResponseError as exc:
            if exc.status == 429 and attempt < MAX_RETRIES:
                time.sleep(delay)
                delay *= 2
            else:
                raise
