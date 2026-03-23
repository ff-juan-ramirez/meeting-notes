"""Unit tests for meeting_notes.services.notion — Wave 0 stubs."""
import pytest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# extract_title
# ---------------------------------------------------------------------------

def test_extract_title_h1():
    from meeting_notes.services.notion import extract_title
    result = extract_title("# My Title\nContent", "fallback")
    assert result == "My Title"


def test_extract_title_no_h1():
    from meeting_notes.services.notion import extract_title
    result = extract_title("Just a line\nMore text", "fallback")
    assert result == "Just a line"


def test_extract_title_empty():
    from meeting_notes.services.notion import extract_title
    result = extract_title("", "Meeting Notes — 2026-03-22 14:30")
    assert result == "Meeting Notes — 2026-03-22 14:30"


# ---------------------------------------------------------------------------
# _split_text
# ---------------------------------------------------------------------------

def test_split_text_short():
    from meeting_notes.services.notion import _split_text
    result = _split_text("short text")
    assert result == ["short text"]


def test_split_text_long():
    from meeting_notes.services.notion import _split_text
    long_text = "x " * 1000  # 2000 chars
    result = _split_text(long_text)
    assert isinstance(result, list)
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 1900


def test_split_text_boundary():
    from meeting_notes.services.notion import _split_text
    # Build a 2000-char string where last space before 1900 is at position 1898
    word = "a" * 100  # 100 chars
    # Create text: multiple words separated by spaces
    text = " ".join(["a" * 100 for _ in range(20)])  # 100*20 + 19 spaces = 2019 chars
    result = _split_text(text)
    for chunk in result:
        # Should not split mid-word (no chunk should start/end mid-word unless forced)
        assert len(chunk) <= 1900


# ---------------------------------------------------------------------------
# _markdown_to_blocks
# ---------------------------------------------------------------------------

def test_markdown_to_blocks_heading():
    from meeting_notes.services.notion import _markdown_to_blocks
    blocks = _markdown_to_blocks("## Summary")
    assert len(blocks) >= 1
    assert blocks[0]["type"] == "heading_2"


def test_markdown_to_blocks_bullet():
    from meeting_notes.services.notion import _markdown_to_blocks
    blocks = _markdown_to_blocks("- Item")
    assert len(blocks) >= 1
    assert blocks[0]["type"] == "bulleted_list_item"


def test_markdown_to_blocks_paragraph():
    from meeting_notes.services.notion import _markdown_to_blocks
    blocks = _markdown_to_blocks("Plain text")
    assert len(blocks) >= 1
    assert blocks[0]["type"] == "paragraph"


def test_markdown_to_blocks_h1_becomes_heading2():
    from meeting_notes.services.notion import _markdown_to_blocks
    blocks = _markdown_to_blocks("# Title")
    assert len(blocks) >= 1
    assert blocks[0]["type"] == "heading_2"


# ---------------------------------------------------------------------------
# create_page
# ---------------------------------------------------------------------------

def test_create_page_calls_api():
    from meeting_notes.services.notion import create_page
    mock_client = MagicMock()
    mock_client.pages.create.return_value = {"id": "abc-123-def"}

    with patch("meeting_notes.services.notion.Client", return_value=mock_client):
        create_page("token", "parent-id", "Test Title", "# Test\nContent")

    mock_client.pages.create.assert_called_once()
    call_kwargs = mock_client.pages.create.call_args[1]
    assert call_kwargs["parent"] == {"page_id": "parent-id"}
    assert call_kwargs["properties"]["title"] == [{"type": "text", "text": {"content": "Test Title"}}]


def test_create_page_returns_url():
    from meeting_notes.services.notion import create_page
    mock_client = MagicMock()
    mock_client.pages.create.return_value = {"id": "abc-123-def-456"}

    with patch("meeting_notes.services.notion.Client", return_value=mock_client):
        url = create_page("token", "parent-id", "Title", "Content")

    assert url == "https://notion.so/abc123def456"


def test_create_page_overflow_blocks():
    from meeting_notes.services.notion import create_page
    mock_client = MagicMock()
    mock_client.pages.create.return_value = {"id": "page-id-123"}

    # Create markdown with >100 lines (each becomes a block)
    markdown = "\n".join([f"Line {i}" for i in range(110)])

    with patch("meeting_notes.services.notion.Client", return_value=mock_client):
        create_page("token", "parent-id", "Title", markdown)

    # blocks.children.append should be called for overflow
    mock_client.blocks.children.append.assert_called()


# ---------------------------------------------------------------------------
# _call_with_retry
# ---------------------------------------------------------------------------

def test_call_with_retry_429():
    from meeting_notes.services.notion import _call_with_retry
    from notion_client.errors import APIResponseError

    call_count = 0

    def mock_fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            error = MagicMock(spec=APIResponseError)
            error.status = 429
            raise error
        return "success"

    with patch("meeting_notes.services.notion.time") as mock_time:
        result = _call_with_retry(mock_fn)

    assert result == "success"
    assert call_count == 3


def test_call_with_retry_non_429_raises():
    from meeting_notes.services.notion import _call_with_retry
    from notion_client.errors import APIResponseError

    error = MagicMock(spec=APIResponseError)
    error.status = 403

    def mock_fn():
        raise error

    with pytest.raises(Exception):
        _call_with_retry(mock_fn)
