"""Unit tests for meet transcribe CLI command and session resolution helpers."""
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


@pytest.fixture
def recordings_dir(tmp_path):
    d = tmp_path / "recordings"
    d.mkdir()
    return d


@pytest.fixture
def transcripts_dir(tmp_path):
    d = tmp_path / "transcripts"
    d.mkdir()
    return d


@pytest.fixture
def metadata_dir(tmp_path):
    d = tmp_path / "metadata"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# resolve_latest_wav tests
# ---------------------------------------------------------------------------

def test_resolve_latest_wav(recordings_dir):
    """resolve_latest_wav() returns the most recently modified .wav file."""
    from meeting_notes.cli.commands.transcribe import resolve_latest_wav

    old_wav = recordings_dir / "20260101-120000-aabbccdd.wav"
    new_wav = recordings_dir / "20260322-143000-11223344.wav"
    old_wav.write_bytes(b"\x00" * 100)
    new_wav.write_bytes(b"\x00" * 100)

    # Force mtime: old is older
    os.utime(old_wav, (1000000, 1000000))
    os.utime(new_wav, (2000000, 2000000))

    result = resolve_latest_wav(recordings_dir)
    assert result == new_wav


def test_no_recordings_exits_with_error(recordings_dir):
    """resolve_latest_wav() raises FileNotFoundError when recordings dir is empty."""
    from meeting_notes.cli.commands.transcribe import resolve_latest_wav

    with pytest.raises(FileNotFoundError):
        resolve_latest_wav(recordings_dir)


def test_session_exact_match(recordings_dir):
    """resolve_wav_by_stem() returns exact match for given stem."""
    from meeting_notes.cli.commands.transcribe import resolve_wav_by_stem

    stem = "20260322-143000-abc12345"
    wav_file = recordings_dir / f"{stem}.wav"
    wav_file.write_bytes(b"\x00" * 100)

    result = resolve_wav_by_stem(recordings_dir, stem)
    assert result == wav_file


def test_session_exact_match_only(recordings_dir):
    """resolve_wav_by_stem() raises FileNotFoundError when stem does not match any file."""
    from meeting_notes.cli.commands.transcribe import resolve_wav_by_stem

    (recordings_dir / "20260322-143000-abc12345.wav").write_bytes(b"\x00" * 100)

    with pytest.raises(FileNotFoundError):
        resolve_wav_by_stem(recordings_dir, "20260322-143000-wrongstem")


# ---------------------------------------------------------------------------
# CLI command integration tests
# ---------------------------------------------------------------------------

def _make_env_dirs(tmp_path):
    """Create recordings, transcripts, metadata dirs under tmp_path."""
    recordings = tmp_path / "recordings"
    transcripts = tmp_path / "transcripts"
    metadata = tmp_path / "metadata"
    config_dir = tmp_path / "config"
    for d in [recordings, transcripts, metadata, config_dir]:
        d.mkdir(parents=True, exist_ok=True)
    return recordings, transcripts, metadata, config_dir


def _create_fake_wav(directory: Path, stem: str, size: int = 500) -> Path:
    """Create a fake WAV file in the directory."""
    wav = directory / f"{stem}.wav"
    wav.write_bytes(b"\x00" * size)
    return wav


def test_transcribe_command_no_session(runner, tmp_path):
    """transcribe command with no --session resolves to latest WAV."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    wav = _create_fake_wav(recordings, stem)

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": "This is a test transcript with enough words to pass validation here"}
        result = runner.invoke(transcribe, [])

    assert result.exit_code == 0
    assert stem in result.output


def test_transcribe_command_with_session(runner, tmp_path):
    """transcribe command with --session STEM resolves to exact WAV match."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_wav(recordings, stem)

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": "This is a test transcript with enough words to pass the validation check"}
        result = runner.invoke(transcribe, ["--session", stem])

    assert result.exit_code == 0
    assert stem in result.output


def test_transcript_saved_to_correct_path(runner, tmp_path):
    """transcript is saved to transcripts/{stem}.txt with transcript text content."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_wav(recordings, stem)
    expected_text = "This is the transcript content with many words so we do not get a warning about short transcripts"

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": expected_text}
        result = runner.invoke(transcribe, ["--session", stem])

    assert result.exit_code == 0
    transcript_file = transcripts / f"{stem}.txt"
    assert transcript_file.exists()
    assert transcript_file.read_text() == expected_text.strip()


def test_metadata_json(runner, tmp_path):
    """metadata JSON is saved to metadata/{stem}.json with required fields."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    wav = _create_fake_wav(recordings, stem)
    transcript_text = "This is a long enough transcript with many words to avoid short transcript warning"

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": transcript_text}
        result = runner.invoke(transcribe, ["--session", stem])

    assert result.exit_code == 0
    metadata_file = metadata / f"{stem}.json"
    assert metadata_file.exists()

    data = json.loads(metadata_file.read_text())
    assert "wav_path" in data
    assert "transcript_path" in data
    assert "transcribed_at" in data
    assert "word_count" in data
    assert "whisper_model" in data
    assert data["whisper_model"] == "mlx-community/whisper-large-v3-turbo"
    assert data["word_count"] == len(transcript_text.strip().split())


def test_short_transcript_warning(runner, tmp_path):
    """warning is printed when word_count < 50."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_wav(recordings, stem)

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": "short text"}  # < 50 words
        result = runner.invoke(transcribe, ["--session", stem])

    assert "check audio routing" in result.output


def test_long_recording_warning(runner, tmp_path):
    """warning is printed when WAV duration > 90 minutes."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"

    # 90+ minutes of audio at 32000 bytes/sec: 5401 * 32000 + 44 bytes
    big_size = 5401 * 32000 + 44  # just over 90 minutes
    wav = recordings / f"{stem}.wav"
    wav.write_bytes(b"\x00" * big_size)

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": "This transcript has enough words to avoid the short transcript warning triggered on small files"}
        result = runner.invoke(transcribe, ["--session", stem])

    assert "90 minutes" in result.output or "memory pressure" in result.output


def test_session_stem_displayed(runner, tmp_path):
    """session stem is displayed after successful transcription."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_wav(recordings, stem)

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": "This is a transcript with enough words to avoid the short warning test"}
        result = runner.invoke(transcribe, ["--session", stem])

    assert f"Session: {stem}" in result.output


def test_existing_transcript_overwritten(runner, tmp_path):
    """existing transcript is overwritten silently (no prompt, no error)."""
    from meeting_notes.cli.commands.transcribe import transcribe

    recordings, transcripts, metadata, config_dir = _make_env_dirs(tmp_path)
    stem = "20260322-143000-abc12345"
    _create_fake_wav(recordings, stem)

    # Write existing transcript
    existing_transcript = transcripts / f"{stem}.txt"
    existing_transcript.write_text("old transcript content that should be overwritten")

    new_text = "This is the new transcript content with enough words to avoid the short transcript warning check"

    def fake_run_with_spinner(fn, message, **kw):
        return fn()

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir), \
         patch("meeting_notes.cli.commands.transcribe.run_with_spinner", side_effect=fake_run_with_spinner), \
         patch("meeting_notes.services.transcription.mlx_whisper") as mock_mlx:
        mock_mlx.transcribe.return_value = {"text": new_text}
        result = runner.invoke(transcribe, ["--session", stem])

    assert result.exit_code == 0
    assert existing_transcript.read_text() == new_text.strip()


# ---------------------------------------------------------------------------
# Fresh system / no recordings directory tests (regression for silent-exit bug)
# ---------------------------------------------------------------------------

def test_transcribe_no_recordings_dir_shows_error(runner, tmp_path):
    """transcribe command prints red error and exits 1 when recordings dir does not exist (no --session)."""
    from meeting_notes.cli.commands.transcribe import transcribe

    # tmp_path has no subdirectories — simulates a fresh system before ensure_dirs() was ever called
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir):
        result = runner.invoke(transcribe, [])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "No recordings found" in result.output


def test_transcribe_no_recordings_dir_with_session_shows_error(runner, tmp_path):
    """transcribe command prints red error and exits 1 when recordings dir does not exist (with --session)."""
    from meeting_notes.cli.commands.transcribe import transcribe

    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    with patch("meeting_notes.cli.commands.transcribe.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.transcribe.get_config_dir", return_value=config_dir):
        result = runner.invoke(transcribe, ["--session", "some-stem"])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "No recording found for session" in result.output


# ---------------------------------------------------------------------------
# Wave 0 stubs — SRT output + diarization integration
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Wave 0 stub — implementation pending")
def test_srt_file_created(runner, tmp_path):
    """meet transcribe writes a .srt file alongside the .txt file."""
    pass

@pytest.mark.skip(reason="Wave 0 stub — implementation pending")
def test_metadata_includes_srt_fields(runner, tmp_path):
    """Metadata JSON includes srt_path and diarization_succeeded fields."""
    pass

@pytest.mark.skip(reason="Wave 0 stub — implementation pending")
def test_diarization_skips_without_hf_token(runner, tmp_path):
    """When HF token is missing, diarization is skipped with a yellow warning."""
    pass

@pytest.mark.skip(reason="Wave 0 stub — implementation pending")
def test_diarization_graceful_failure(runner, tmp_path):
    """When diarization raises an exception, transcription continues without speaker labels."""
    pass
