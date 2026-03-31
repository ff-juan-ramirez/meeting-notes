"""Unit tests for meeting_notes.services.llm."""
import requests
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meeting_notes.services.llm import (
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_URL,
    BUILTIN_TEMPLATES_DIR,
    USER_TEMPLATES_DIR,
    build_prompt,
    chunk_transcript,
    delete_template,
    duplicate_template,
    estimate_tokens,
    generate_notes,
    list_templates,
    load_template,
    save_template,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_templates_dir(tmp_path, monkeypatch):
    """Redirect USER_TEMPLATES_DIR to a temp directory for isolation."""
    d = tmp_path / "templates"
    d.mkdir()
    monkeypatch.setattr("meeting_notes.services.llm.USER_TEMPLATES_DIR", d)
    return d


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
# list_templates
# ---------------------------------------------------------------------------

def test_list_templates_builtins(user_templates_dir):
    """list_templates() returns 3 dicts with builtin=True for meeting, minutes, 1on1."""
    templates = list_templates()
    builtin_names = {t["name"] for t in templates if t["builtin"]}
    assert builtin_names == {"meeting", "minutes", "1on1"}
    for t in templates:
        assert "name" in t
        assert "path" in t
        assert "builtin" in t


def test_list_templates_user(user_templates_dir):
    """list_templates() includes user-created .txt files with builtin=False."""
    (user_templates_dir / "custom.txt").write_text("my custom template")
    templates = list_templates()
    user_templates = [t for t in templates if not t["builtin"]]
    assert len(user_templates) == 1
    assert user_templates[0]["name"] == "custom"
    assert user_templates[0]["builtin"] is False
    # Total: 3 builtins + 1 user
    assert len(templates) == 4


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
    with pytest.raises(ValueError, match="Template not found"):
        load_template("nonexistent_template_xyz")


def test_load_template_user_precedence(user_templates_dir):
    """User template with same name as built-in takes precedence."""
    (user_templates_dir / "meeting.txt").write_text("user override content")
    result = load_template("meeting")
    assert result == "user override content"


def test_templates_contain_grounding_rule():
    grounding_rule = "Base your notes ONLY on what is said in the transcript"
    for name in ("meeting", "minutes", "1on1"):
        t = load_template(name)
        assert grounding_rule in t, f"Template '{name}' missing grounding rule"


# ---------------------------------------------------------------------------
# save_template
# ---------------------------------------------------------------------------

def test_save_template(user_templates_dir):
    """save_template() creates file at USER_TEMPLATES_DIR/name.txt."""
    path = save_template("custom", "my template content")
    assert path == user_templates_dir / "custom.txt"
    assert path.exists()
    assert path.read_text() == "my template content"


def test_save_template_builtin_collision(user_templates_dir):
    """save_template() raises ValueError when name collides with a built-in."""
    with pytest.raises(ValueError, match="built-in template"):
        save_template("meeting", "some content")


# ---------------------------------------------------------------------------
# delete_template
# ---------------------------------------------------------------------------

def test_delete_template(user_templates_dir):
    """delete_template() removes the user template file."""
    (user_templates_dir / "custom.txt").write_text("to be deleted")
    delete_template("custom")
    assert not (user_templates_dir / "custom.txt").exists()


def test_delete_template_builtin(user_templates_dir):
    """delete_template() raises ValueError for built-in template names."""
    with pytest.raises(ValueError, match="built-in"):
        delete_template("meeting")


def test_delete_template_not_found(user_templates_dir):
    """delete_template() raises FileNotFoundError for non-existent user template."""
    with pytest.raises(FileNotFoundError):
        delete_template("nonexistent_xyz")


# ---------------------------------------------------------------------------
# duplicate_template
# ---------------------------------------------------------------------------

def test_duplicate_template(user_templates_dir):
    """duplicate_template() creates user template with source template content."""
    path = duplicate_template("meeting", "my-meeting")
    assert path == user_templates_dir / "my-meeting.txt"
    assert path.exists()
    # Content should match the original meeting template
    original = load_template("meeting")
    # The user dir now has "my-meeting.txt" which is the duplicate
    assert path.read_text() == original


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
