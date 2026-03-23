"""Unit tests for meeting_notes.services.llm."""
import requests
from unittest.mock import MagicMock, patch

import pytest

from meeting_notes.services.llm import (
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_URL,
    build_prompt,
    chunk_transcript,
    estimate_tokens,
    generate_notes,
    load_template,
)


# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------

def test_estimate_tokens():
    assert estimate_tokens("a" * 400) == 100
    assert estimate_tokens("") == 0


# ---------------------------------------------------------------------------
# chunk_transcript
# ---------------------------------------------------------------------------

def test_chunk_transcript_short():
    """Text under 24000 chars returns a single chunk."""
    text = "Hello world " * 100  # 1200 chars
    chunks = chunk_transcript(text)
    assert len(chunks) == 1
    # Short text is returned as-is (no splitting, no stripping)
    assert chunks[0] == text


def test_chunk_transcript_long():
    """Text of 50000 chars returns 3 chunks, each <= 24000 chars."""
    text = "x" * 50000
    chunks = chunk_transcript(text)
    assert len(chunks) == 3
    for chunk in chunks:
        assert len(chunk) <= 24000


def test_chunk_transcript_splits_on_newline():
    """Text with newlines splits at newline boundary, not mid-text."""
    # Build text: 23990 chars then newline then more text
    part_a = "a" * 23990
    part_b = "b" * 100
    text = part_a + "\n" + part_b
    chunks = chunk_transcript(text)
    # Should split at the newline, not at char 24000
    assert len(chunks) == 2
    assert chunks[0] == part_a
    assert chunks[1] == part_b


# ---------------------------------------------------------------------------
# load_template
# ---------------------------------------------------------------------------

def test_load_template_meeting():
    t = load_template("meeting")
    assert "## Summary" in t


def test_load_template_minutes():
    t = load_template("minutes")
    assert "## Attendees" in t


def test_load_template_1on1():
    t = load_template("1on1")
    assert "**Project Work**" in t


def test_load_template_invalid():
    with pytest.raises(ValueError, match="Invalid template"):
        load_template("invalid")


def test_templates_contain_grounding_rule():
    grounding_rule = "Base your notes ONLY on what is said in the transcript"
    for name in ("meeting", "minutes", "1on1"):
        t = load_template(name)
        assert grounding_rule in t, f"Template '{name}' missing grounding rule"


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------

def test_build_prompt():
    result = build_prompt("Hello {transcript}", "world")
    assert result == "Hello world"


# ---------------------------------------------------------------------------
# generate_notes — mocked HTTP
# ---------------------------------------------------------------------------

def test_generate_notes_calls_api():
    """Verify generate_notes POSTs to the correct URL with correct payload."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "notes"}

    prompt = "test prompt"
    with patch("meeting_notes.services.llm.requests.post", return_value=mock_response) as mock_post:
        generate_notes(prompt)
        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.1:8b", "prompt": prompt, "stream": False},
            timeout=120,
        )


def test_generate_notes_returns_response():
    """Verify generate_notes returns the 'response' field from the JSON body."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "generated notes"}

    with patch("meeting_notes.services.llm.requests.post", return_value=mock_response):
        result = generate_notes("some prompt")
    assert result == "generated notes"


def test_generate_notes_timeout():
    """Verify generate_notes raises TimeoutError on requests.exceptions.Timeout."""
    with patch(
        "meeting_notes.services.llm.requests.post",
        side_effect=requests.exceptions.Timeout,
    ):
        with pytest.raises(TimeoutError):
            generate_notes("prompt")


def test_generate_notes_connection_error():
    """Verify generate_notes raises ConnectionError when Ollama is not running."""
    with patch(
        "meeting_notes.services.llm.requests.post",
        side_effect=requests.exceptions.ConnectionError,
    ):
        with pytest.raises(ConnectionError):
            generate_notes("prompt")


def test_generate_notes_non_200():
    """Verify generate_notes raises RuntimeError on non-200 HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("meeting_notes.services.llm.requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError, match="HTTP 500"):
            generate_notes("prompt")
