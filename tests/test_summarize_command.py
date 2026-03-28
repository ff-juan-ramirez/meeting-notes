"""Unit tests for meet summarize CLI command and session resolution helpers."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _make_env_dirs(tmp_path):
    """Create transcripts, notes, metadata dirs under tmp_path."""
    transcripts = tmp_path / "transcripts"
    notes = tmp_path / "notes"
    metadata = tmp_path / "metadata"
    for d in [transcripts, notes, metadata]:
        d.mkdir(parents=True, exist_ok=True)
    return transcripts, notes, metadata


def _create_fake_transcript(directory, stem, content="This is a test transcript with enough words"):
    """Create a fake transcript file."""
    txt = directory / f"{stem}.txt"
    txt.write_text(content)
    return txt


# ---------------------------------------------------------------------------
# resolve_latest_transcript tests
# ---------------------------------------------------------------------------

def test_resolve_latest_transcript(tmp_path):
    """resolve_latest_transcript() returns the most recently modified .txt file."""
    from meeting_notes.cli.commands.summarize import resolve_latest_transcript

    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()

    old_txt = transcripts_dir / "20260101-120000-aabbccdd.txt"
    new_txt = transcripts_dir / "20260322-143000-11223344.txt"
    old_txt.write_text("old transcript")
    new_txt.write_text("new transcript")

    os.utime(old_txt, (1000000, 1000000))
    os.utime(new_txt, (2000000, 2000000))

    result = resolve_latest_transcript(transcripts_dir)
    assert result == new_txt


def test_no_transcripts_raises(tmp_path):
    """resolve_latest_transcript() raises FileNotFoundError when dir is empty."""
    from meeting_notes.cli.commands.summarize import resolve_latest_transcript

    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        resolve_latest_transcript(transcripts_dir)


def test_resolve_transcript_by_stem(tmp_path):
    """resolve_transcript_by_stem() returns exact match for given stem."""
    from meeting_notes.cli.commands.summarize import resolve_transcript_by_stem

    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    stem = "20260322-143000-abc12345"
    txt = transcripts_dir / f"{stem}.txt"
    txt.write_text("transcript content")

    result = resolve_transcript_by_stem(transcripts_dir, stem)
    assert result == txt


def test_resolve_transcript_by_stem_not_found(tmp_path):
    """resolve_transcript_by_stem() raises FileNotFoundError for missing stem."""
    from meeting_notes.cli.commands.summarize import resolve_transcript_by_stem

    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    (transcripts_dir / "20260322-143000-abc12345.txt").write_text("content")

    with pytest.raises(FileNotFoundError):
        resolve_transcript_by_stem(transcripts_dir, "20260322-143000-wrongstem")


# ---------------------------------------------------------------------------
# CLI command integration tests
# ---------------------------------------------------------------------------

def _make_ollama_mock():
    """Return a MagicMock for requests.post that simulates a successful Ollama response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "Generated notes text here"}
    return mock_resp


def test_summarize_command_default_template(runner, tmp_path):
    """summarize command with no --template uses 'meeting', notes saved to {stem}-meeting.md."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    notes_file = notes / f"{stem}-meeting.md"
    assert notes_file.exists()


def test_template_flag_1on1(runner, tmp_path):
    """summarize command with --template 1on1 saves notes to {stem}-1on1.md."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, ["--template", "1on1"])

    assert result.exit_code == 0
    notes_file = notes / f"{stem}-1on1.md"
    assert notes_file.exists()


def test_template_flag_minutes(runner, tmp_path):
    """summarize command with --template minutes saves notes to {stem}-minutes.md."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, ["--template", "minutes"])

    assert result.exit_code == 0
    notes_file = notes / f"{stem}-minutes.md"
    assert notes_file.exists()


def test_notes_saved_correct_path(runner, tmp_path):
    """notes file exists at notes/{stem}-{template}.md with generated content."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    notes_file = notes / f"{stem}-meeting.md"
    assert notes_file.exists()
    assert notes_file.read_text() == "Generated notes text here"


def test_output_shows_path_and_word_count(runner, tmp_path):
    """output contains 'Notes saved:' and 'words'."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    assert "Notes saved:" in result.output
    assert "words" in result.output


def test_session_stem_displayed(runner, tmp_path):
    """output contains 'Session: {stem}' after generation."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    assert f"Session: {stem}" in result.output


def test_existing_notes_overwritten(runner, tmp_path):
    """pre-existing notes file is overwritten with new content (no prompt, no error)."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    existing_notes = notes / f"{stem}-meeting.md"
    existing_notes.write_text("old notes that should be replaced")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    assert existing_notes.read_text() == "Generated notes text here"


def test_metadata_extended(runner, tmp_path):
    """metadata/{stem}.json contains Phase 3 fields AND preserves Phase 2 fields."""
    from meeting_notes.cli.commands.summarize import summarize
    from meeting_notes.core.state import write_state

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    # Pre-populate with Phase 2 metadata fields
    metadata_path = metadata / f"{stem}.json"
    phase2_data = {
        "wav_path": f"/home/user/.local/share/meeting-notes/recordings/{stem}.wav",
        "transcript_path": f"/home/user/.local/share/meeting-notes/transcripts/{stem}.txt",
        "transcribed_at": "2026-03-22T14:30:01Z",
        "word_count": 250,
        "whisper_model": "mlx-community/whisper-large-v3-turbo",
    }
    write_state(metadata_path, phase2_data)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0

    data = json.loads(metadata_path.read_text())

    # Phase 3 fields must be present
    assert "notes_path" in data
    assert "template" in data
    assert "summarized_at" in data
    assert "llm_model" in data
    assert data["template"] == "meeting"
    assert data["llm_model"] == "llama3.1:8b"

    # Phase 2 fields must be preserved
    assert "wav_path" in data
    assert "transcript_path" in data
    assert "transcribed_at" in data
    assert "word_count" in data
    assert "whisper_model" in data


def test_timeout_error_message(runner, tmp_path):
    """when generate_notes raises TimeoutError, output shows 'Error:' and exits 1."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    def raise_timeout(fn, msg, **kw):
        raise TimeoutError("Ollama timed out after 120s. The model may be overloaded — try again or increase timeout.")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=raise_timeout):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 1
    assert "Error:" in result.output


def test_connection_error_message(runner, tmp_path):
    """when generate_notes raises ConnectionError, output shows 'Error:' and exits 1."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    def raise_connection_error(fn, msg, **kw):
        raise ConnectionError("Ollama is not running. Run: ollama serve")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=raise_connection_error):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "ollama serve" in result.output


def test_long_transcript_uses_chunking(runner, tmp_path):
    """transcript >32000 chars (>8000 tokens) triggers multiple generate_notes calls."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"

    # Create a transcript >32,000 chars (>8,000 tokens at 4 chars/token)
    long_content = "word " * 7000  # 35,000 chars
    _create_fake_transcript(transcripts, stem, content=long_content)

    call_count = [0]
    responses = ["chunk1 summary", "chunk2 summary", "final merged notes"]

    def fake_generate_notes(prompt, timeout=120):
        idx = call_count[0]
        call_count[0] += 1
        if idx < len(responses):
            return responses[idx]
        return "extra chunk summary"

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.generate_notes", side_effect=fake_generate_notes), \
         patch("meeting_notes.cli.commands.summarize.generate_notes", side_effect=fake_generate_notes):
        result = runner.invoke(summarize, [])

    # Should have been called N+1 times (N chunks + 1 combine step)
    assert call_count[0] >= 2
    assert result.exit_code == 0


def test_no_transcripts_shows_error(runner, tmp_path):
    """when no transcripts are available, exit code is 1 with 'Error:' in output."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    # No transcript files created

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 1
    assert "Error:" in result.output


def test_summarize_with_session(runner, tmp_path):
    """--session stem resolves the correct transcript by stem."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    other_stem = "20260322-150000-zzzzffff"
    _create_fake_transcript(transcripts, stem, "transcript for stem one")
    _create_fake_transcript(transcripts, other_stem, "transcript for stem two")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, ["--session", stem])

    assert result.exit_code == 0
    assert f"Session: {stem}" in result.output
    notes_file = notes / f"{stem}-meeting.md"
    assert notes_file.exists()


def test_spinner_shown(runner, tmp_path):
    """run_with_spinner is called with a message containing 'Generating notes...' (LLM-07)."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)

    mock_spinner = MagicMock(return_value="Generated notes text here")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", mock_spinner), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    assert mock_spinner.call_count >= 1
    # The second positional arg (message) of the first call must contain "Generating notes..."
    first_call_message = mock_spinner.call_args_list[0][0][1]
    assert "Generating notes..." in first_call_message


# ---------------------------------------------------------------------------
# Helpers for Notion tests
# ---------------------------------------------------------------------------

def _create_config(config_dir, token=None, parent_page_id=None):
    """Create a config.json in config_dir with optional notion section."""
    config = {"version": 1, "audio": {}, "whisper": {}}
    if token or parent_page_id:
        config["notion"] = {}
        if token:
            config["notion"]["token"] = token
        if parent_page_id:
            config["notion"]["parent_page_id"] = parent_page_id
    (config_dir / "config.json").write_text(json.dumps(config))


# ---------------------------------------------------------------------------
# Notion integration tests
# ---------------------------------------------------------------------------

def test_summarize_notion_not_configured(runner, tmp_path):
    """When config has no notion token, output contains 'Notion not configured', exit code 0, no API call."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path)  # no notion section

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page") as mock_create_page:
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    assert "Notion not configured" in result.output
    mock_create_page.assert_not_called()


def test_summarize_notion_success(runner, tmp_path):
    """When config has token+page_id and create_page succeeds, output contains Notion URL, exit code 0."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", return_value="https://notion.so/abc123"):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    assert "Notion: https://notion.so/abc123" in result.output


def test_summarize_stores_notion_url(runner, tmp_path):
    """After successful Notion push, metadata JSON contains notion_url with the URL."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", return_value="https://notion.so/abc123"):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    metadata_path = metadata / f"{stem}.json"
    data = json.loads(metadata_path.read_text())
    assert data["notion_url"] == "https://notion.so/abc123"


def test_summarize_notion_url_null_when_not_configured(runner, tmp_path):
    """When Notion not configured, metadata JSON contains notion_url: null."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path)  # no notion section

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    metadata_path = metadata / f"{stem}.json"
    data = json.loads(metadata_path.read_text())
    assert data["notion_url"] is None


def test_summarize_notion_failure_warns(runner, tmp_path):
    """When create_page raises Exception, output contains 'Notion upload failed', exit code 0."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", side_effect=RuntimeError("API error")):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    assert "Notion upload failed" in result.output
    metadata_path = metadata / f"{stem}.json"
    data = json.loads(metadata_path.read_text())
    assert data["notion_url"] is None


def test_summarize_notion_spinner(runner, tmp_path):
    """run_with_spinner is called with message containing 'Saving to Notion...'."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")

    spinner_messages = []

    def fake_spinner(fn, msg, **kw):
        spinner_messages.append(msg)
        return fn()

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=fake_spinner), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", return_value="https://notion.so/abc123"):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    assert any("Saving to Notion" in m for m in spinner_messages)


def test_summarize_preserves_phase3_metadata(runner, tmp_path):
    """After Notion push, metadata still contains notes_path, template, summarized_at, llm_model."""
    from meeting_notes.cli.commands.summarize import summarize
    from meeting_notes.core.state import write_state

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")

    # Pre-populate with Phase 2 metadata fields
    metadata_path = metadata / f"{stem}.json"
    phase2_data = {
        "wav_path": f"/home/user/.local/share/meeting-notes/recordings/{stem}.wav",
        "transcript_path": f"/home/user/.local/share/meeting-notes/transcripts/{stem}.txt",
        "transcribed_at": "2026-03-22T14:30:01Z",
        "word_count": 250,
        "whisper_model": "mlx-community/whisper-large-v3-turbo",
    }
    write_state(metadata_path, phase2_data)

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", return_value="https://notion.so/abc123"):
        result = runner.invoke(summarize, [])

    assert result.exit_code == 0
    data = json.loads(metadata_path.read_text())

    # Phase 3 fields must be present
    assert "notes_path" in data
    assert "template" in data
    assert "summarized_at" in data
    assert "llm_model" in data
    assert "notion_url" in data
    assert data["notion_url"] == "https://notion.so/abc123"

    # Phase 2 fields must be preserved
    assert "wav_path" in data
    assert "transcript_path" in data
    assert "transcribed_at" in data
    assert "word_count" in data
    assert "whisper_model" in data


# ---------------------------------------------------------------------------
# Wave 0 stubs — diarized transcript preference
# ---------------------------------------------------------------------------

def test_prefers_diarized_transcript(runner, tmp_path):
    """meet summarize uses diarized_transcript_path from metadata when available."""
    import json

    transcripts = tmp_path / "transcripts"
    notes = tmp_path / "notes"
    metadata_dir = tmp_path / "metadata"
    for d in [transcripts, notes, metadata_dir]:
        d.mkdir()

    stem = "20260327-100000-aabbccdd"

    # Write transcript with diarized content
    transcript_path = transcripts / f"{stem}.txt"
    transcript_path.write_text("SPEAKER_00:\nHello world\n\nSPEAKER_01:\nGoodbye")

    # Write metadata indicating diarization succeeded
    meta_path = metadata_dir / f"{stem}.json"
    meta_path.write_text(json.dumps({
        "transcript_path": str(transcript_path),
        "diarized_transcript_path": str(transcript_path),
        "diarization_succeeded": True,
    }))

    with patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.Config.load") as mock_config_load, \
         patch("meeting_notes.cli.commands.summarize.ensure_dirs"), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()):

        from meeting_notes.core.config import Config
        mock_config_load.return_value = Config()

        from meeting_notes.cli.commands.summarize import summarize
        result = runner.invoke(summarize, ["--session", stem], obj={"quiet": False})

    assert result.exit_code == 0, f"Exit code was {result.exit_code}, output: {result.output}"


# ---------------------------------------------------------------------------
# NOTION-01: recording_name priority for Notion page title
# ---------------------------------------------------------------------------

def test_summarize_notion_uses_recording_name(runner, tmp_path):
    """When metadata has recording_name, Notion page title is that name (NOTION-01)."""
    from meeting_notes.cli.commands.summarize import summarize
    from meeting_notes.core.state import write_state

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "my-standup-20260328-090000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")

    # Pre-populate metadata with recording_name
    metadata_path = metadata / f"{stem}.json"
    write_state(metadata_path, {"recording_name": "My Standup"})

    mock_create_page = MagicMock(return_value="https://notion.so/abc123")
    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", mock_create_page):
        result = runner.invoke(summarize, ["--session", stem])

    assert result.exit_code == 0
    mock_create_page.assert_called_once()
    call_kwargs = mock_create_page.call_args[1]
    assert call_kwargs["title"] == "My Standup"


def test_summarize_notion_unnamed_uses_extract_title(runner, tmp_path):
    """When metadata has no recording_name, Notion title comes from extract_title (NOTION-01 regression)."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260328-090000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")
    # No metadata pre-populated — no recording_name

    mock_create_page = MagicMock(return_value="https://notion.so/abc123")
    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", mock_create_page):
        result = runner.invoke(summarize, ["--session", stem])

    assert result.exit_code == 0
    mock_create_page.assert_called_once()
    call_kwargs = mock_create_page.call_args[1]
    # Title must NOT be a recording_name — it should be from extract_title
    # extract_title on "Generated notes text here" (no H1) falls back to timestamp pattern
    assert "Meeting Notes" in call_kwargs["title"] or call_kwargs["title"] == "Generated notes text here"


def test_summarize_notion_no_metadata_unaffected(runner, tmp_path):
    """When no metadata file exists (pre-v1.2), Notion title from extract_title, no AttributeError (NOTION-01 regression)."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260328-090000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")
    # Explicitly NO metadata file — simulates pre-v1.2 session

    mock_create_page = MagicMock(return_value="https://notion.so/abc123")
    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", mock_create_page):
        result = runner.invoke(summarize, ["--session", stem])

    assert result.exit_code == 0
    mock_create_page.assert_called_once()
    # No crash = session_metadata None guard works
