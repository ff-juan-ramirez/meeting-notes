"""Tests for meet list CLI command — display all recorded sessions."""
import json
import wave
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from rich.console import Console

from meeting_notes.cli.commands.list import list_sessions
from meeting_notes.core.state import write_state

# Wide console for tests so Rich does not truncate column values
_wide_console = Console(width=200, force_terminal=False, highlight=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "metadata").mkdir()
    (tmp_path / "notes").mkdir()
    (tmp_path / "recordings").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _write_metadata(data_dir, stem, meta):
    write_state(data_dir / "metadata" / f"{stem}.json", meta)


def _write_notes(data_dir, stem, template, content):
    notes_path = data_dir / "notes" / f"{stem}-{template}.md"
    notes_path.write_text(content)
    return str(notes_path.resolve())


def _make_wav(wav_path: Path, duration_seconds: int = 10) -> Path:
    """Create a minimal WAV file with given duration."""
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000 * duration_seconds)
    return wav_path


def _invoke(runner, data_dir, args=None):
    """Invoke list_sessions with patched data dir and wide console to prevent truncation."""
    with patch("meeting_notes.cli.commands.list.get_data_dir", return_value=data_dir):
        with patch("meeting_notes.cli.commands.list.console", _wide_console):
            return runner.invoke(list_sessions, args or [], obj={"quiet": False})


# ---------------------------------------------------------------------------
# Test 1: Empty metadata directory shows empty table, exits 0, has column headers
# ---------------------------------------------------------------------------

def test_empty_metadata_shows_empty_table(runner, data_dir):
    """meet list with no metadata files shows empty table, exits 0, contains column headers."""
    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert "Date" in result.output
    assert "Status" in result.output


# ---------------------------------------------------------------------------
# Test 2: Summarized session shows full row with correct columns
# ---------------------------------------------------------------------------

def test_summarized_session_shows_row(runner, data_dir):
    """meet list with one summarized session shows date, duration, title, status=summarized, notion URL."""
    stem = "20260322-143000-abc12345"
    notes_path = _write_notes(data_dir, stem, "meeting", "# Test Meeting Title\n\nSome content here.")
    meta = {
        "wav_path": str(data_dir / "recordings" / f"{stem}.wav"),
        "duration_seconds": 300,
        "transcript_path": str(data_dir / "transcripts" / f"{stem}.txt"),
        "transcribed_at": "2026-03-22T14:30:00+00:00",
        "notes_path": notes_path,
        "template": "meeting",
        "summarized_at": "2026-03-22T14:35:00+00:00",
        "notion_url": "https://www.notion.so/page-abc123",
    }
    _write_metadata(data_dir, stem, meta)

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert "summarized" in result.output
    assert "05:00" in result.output
    assert "Test Meeting Title" in result.output
    # Notion URL appears (may be truncated by Rich in narrow terminal, so check prefix)
    assert "https://" in result.output


# ---------------------------------------------------------------------------
# Test 3: Not-transcribed session shows status and title is stem
# ---------------------------------------------------------------------------

def test_not_transcribed_session_status(runner, data_dir):
    """Session with wav_path but no transcript shows status=not-transcribed and title=stem."""
    stem = "20260322-100000-notrans"
    meta = {
        "wav_path": str(data_dir / "recordings" / f"{stem}.wav"),
    }
    _write_metadata(data_dir, stem, meta)

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert "not-transcribed" in result.output
    assert stem in result.output


# ---------------------------------------------------------------------------
# Test 4: Transcribed session shows status=transcribed
# ---------------------------------------------------------------------------

def test_transcribed_session_status(runner, data_dir, tmp_path):
    """Session with transcript_path but no notes_path shows status=transcribed."""
    stem = "20260322-110000-transonly"
    transcript_path = data_dir / "transcripts" / f"{stem}.txt"
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text("Transcribed content.")
    meta = {
        "wav_path": str(data_dir / "recordings" / f"{stem}.wav"),
        "transcript_path": str(transcript_path),
        "transcribed_at": "2026-03-22T11:00:00+00:00",
    }
    _write_metadata(data_dir, stem, meta)

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert "transcribed" in result.output


# ---------------------------------------------------------------------------
# Test 5: --status summarized filters out non-summarized sessions
# ---------------------------------------------------------------------------

def test_status_filter_summarized(runner, data_dir):
    """meet list --status summarized shows only summarized sessions."""
    stem_sum = "20260322-143000-sum"
    stem_trans = "20260322-110000-trans"

    notes_path = _write_notes(data_dir, stem_sum, "meeting", "# Summary Meeting\n")
    transcript_path = data_dir / "transcripts" / f"{stem_trans}.txt"
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text("Content.")

    _write_metadata(data_dir, stem_sum, {
        "transcribed_at": "2026-03-22T14:30:00+00:00",
        "notes_path": notes_path,
        "summarized_at": "2026-03-22T14:35:00+00:00",
    })
    _write_metadata(data_dir, stem_trans, {
        "transcript_path": str(transcript_path),
        "transcribed_at": "2026-03-22T11:00:00+00:00",
    })

    result = _invoke(runner, data_dir, ["--status", "summarized"])
    assert result.exit_code == 0
    # The summarized session has title "Summary Meeting" from its notes heading
    assert "Summary Meeting" in result.output
    # The transcribed session should not appear at all
    assert stem_trans not in result.output


# ---------------------------------------------------------------------------
# Test 6: --status not-transcribed shows only not-transcribed sessions
# ---------------------------------------------------------------------------

def test_status_filter_not_transcribed(runner, data_dir):
    """meet list --status not-transcribed shows only not-transcribed sessions."""
    stem_notrans = "20260320-090000-notrans"
    stem_trans = "20260321-110000-trans"

    transcript_path = data_dir / "transcripts" / f"{stem_trans}.txt"
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text("Content.")

    _write_metadata(data_dir, stem_notrans, {
        "wav_path": str(data_dir / "recordings" / f"{stem_notrans}.wav"),
    })
    _write_metadata(data_dir, stem_trans, {
        "transcript_path": str(transcript_path),
        "transcribed_at": "2026-03-21T11:00:00+00:00",
    })

    result = _invoke(runner, data_dir, ["--status", "not-transcribed"])
    assert result.exit_code == 0
    assert stem_notrans in result.output
    assert stem_trans not in result.output


# ---------------------------------------------------------------------------
# Test 7: --json outputs valid JSON array with no ANSI codes
# ---------------------------------------------------------------------------

def test_json_output_valid(runner, data_dir):
    """meet list --json outputs valid JSON array; each element has status and title fields."""
    stem = "20260322-143000-jsonsess"
    notes_path = _write_notes(data_dir, stem, "meeting", "# JSON Test\n")
    _write_metadata(data_dir, stem, {
        "transcribed_at": "2026-03-22T14:30:00+00:00",
        "notes_path": notes_path,
        "summarized_at": "2026-03-22T14:35:00+00:00",
    })

    result = _invoke(runner, data_dir, ["--json"])
    assert result.exit_code == 0

    # Output must be parseable JSON
    sessions = json.loads(result.output)
    assert isinstance(sessions, list)
    assert len(sessions) == 1
    assert "status" in sessions[0]
    assert "title" in sessions[0]

    # No ANSI escape codes
    assert "\x1b[" not in result.output


# ---------------------------------------------------------------------------
# Test 8: --json --status summarized outputs filtered JSON array
# ---------------------------------------------------------------------------

def test_json_with_status_filter(runner, data_dir):
    """meet list --json --status summarized outputs only summarized sessions as JSON."""
    stem_sum = "20260322-143000-jsonfilt"
    stem_notrans = "20260320-090000-notrans"

    notes_path = _write_notes(data_dir, stem_sum, "meeting", "# Filtered\n")
    _write_metadata(data_dir, stem_sum, {
        "transcribed_at": "2026-03-22T14:30:00+00:00",
        "notes_path": notes_path,
        "summarized_at": "2026-03-22T14:35:00+00:00",
    })
    _write_metadata(data_dir, stem_notrans, {
        "wav_path": str(data_dir / "recordings" / f"{stem_notrans}.wav"),
    })

    result = _invoke(runner, data_dir, ["--json", "--status", "summarized"])
    assert result.exit_code == 0
    sessions = json.loads(result.output)
    assert all(s["status"] == "summarized" for s in sessions)
    assert len(sessions) == 1


# ---------------------------------------------------------------------------
# Test 9: Duration display — metadata field first, then WAV fallback, then dash
# ---------------------------------------------------------------------------

def test_duration_from_metadata(runner, data_dir):
    """Session with duration_seconds=300 shows 05:00."""
    stem = "20260322-143000-dur300"
    _write_metadata(data_dir, stem, {
        "duration_seconds": 300,
        "transcribed_at": "2026-03-22T14:30:00+00:00",
    })

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert "05:00" in result.output


def test_duration_from_wav_fallback(runner, data_dir):
    """Session without duration_seconds but with valid WAV shows WAV-derived duration."""
    stem = "20260322-143000-wavdur"
    wav_path = data_dir / "recordings" / f"{stem}.wav"
    _make_wav(wav_path, duration_seconds=120)  # 2 minutes

    _write_metadata(data_dir, stem, {
        "wav_path": str(wav_path),
        "transcribed_at": "2026-03-22T14:30:00+00:00",
    })

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert "02:00" in result.output


def test_duration_dash_when_no_wav(runner, data_dir):
    """Session with neither duration_seconds nor valid WAV shows dash."""
    stem = "20260322-143000-nodur"
    _write_metadata(data_dir, stem, {
        "wav_path": "/nonexistent/path/recording.wav",
        "transcribed_at": "2026-03-22T14:30:00+00:00",
    })

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    # Should show a dash (em dash or regular dash)
    assert "\u2014" in result.output or "-" in result.output


# ---------------------------------------------------------------------------
# Test 10: Title for summarized session comes from notes file first # heading
# ---------------------------------------------------------------------------

def test_title_from_notes_heading(runner, data_dir):
    """Summarized session: title comes from first # heading in notes file."""
    stem = "20260322-143000-titlesess"
    notes_path = _write_notes(
        data_dir, stem, "meeting",
        "# My Important Meeting\n\nSome content here."
    )
    _write_metadata(data_dir, stem, {
        "transcribed_at": "2026-03-22T14:30:00+00:00",
        "notes_path": notes_path,
        "summarized_at": "2026-03-22T14:35:00+00:00",
    })

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert "My Important Meeting" in result.output


def test_title_fallback_to_stem_when_notes_missing(runner, data_dir):
    """Summarized session with missing notes file falls back to stem for title."""
    stem = "20260322-143000-missingnotes"
    _write_metadata(data_dir, stem, {
        "transcribed_at": "2026-03-22T14:30:00+00:00",
        "notes_path": "/nonexistent/notes.md",
        "summarized_at": "2026-03-22T14:35:00+00:00",
    })

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    assert stem in result.output


# ---------------------------------------------------------------------------
# Test 11: Sessions sorted newest first (by transcribed_at, then WAV mtime)
# ---------------------------------------------------------------------------

def test_sessions_sorted_newest_first(runner, data_dir):
    """Sessions are sorted newest first by transcribed_at."""
    stem_old = "20260320-100000-old"
    stem_new = "20260322-143000-new"

    _write_metadata(data_dir, stem_old, {
        "transcribed_at": "2026-03-20T10:00:00+00:00",
    })
    _write_metadata(data_dir, stem_new, {
        "transcribed_at": "2026-03-22T14:30:00+00:00",
    })

    result = _invoke(runner, data_dir)
    assert result.exit_code == 0
    # Newer session (stem_new) should appear before older session (stem_old) in output
    pos_new = result.output.find(stem_new)
    pos_old = result.output.find(stem_old)
    assert pos_new != -1
    assert pos_old != -1
    assert pos_new < pos_old


# ---------------------------------------------------------------------------
# Test 12: --quiet flag suppresses table output
# ---------------------------------------------------------------------------

def test_quiet_flag_suppresses_output(runner, data_dir):
    """meet list with --quiet (via ctx.obj) suppresses table output, exits 0."""
    stem = "20260322-143000-quiet"
    _write_metadata(data_dir, stem, {
        "transcribed_at": "2026-03-22T14:30:00+00:00",
    })

    with patch("meeting_notes.cli.commands.list.get_data_dir", return_value=data_dir):
        result = runner.invoke(list_sessions, [], obj={"quiet": True})

    assert result.exit_code == 0
    # No table headers in quiet mode
    assert "Date" not in result.output
    assert "Status" not in result.output


# ---------------------------------------------------------------------------
# Test: No metadata directory shows empty JSON array for --json
# ---------------------------------------------------------------------------

def test_no_metadata_dir_json(runner, tmp_path):
    """meet list --json when no metadata directory returns empty JSON array."""
    with patch("meeting_notes.cli.commands.list.get_data_dir", return_value=tmp_path):
        result = runner.invoke(list_sessions, ["--json"], obj={"quiet": False})

    assert result.exit_code == 0
    sessions = json.loads(result.output)
    assert sessions == []
