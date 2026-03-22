"""Unit tests for meeting_notes.services.transcription and Config WhisperConfig extension."""
import json
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meeting_notes.core.config import Config, WhisperConfig


# ---------------------------------------------------------------------------
# WhisperConfig / Config tests
# ---------------------------------------------------------------------------

def test_whisper_config_defaults():
    """WhisperConfig defaults to language=None."""
    cfg = WhisperConfig()
    assert cfg.language is None


def test_config_has_whisper_field():
    """Config includes whisper field defaulting to WhisperConfig()."""
    cfg = Config()
    assert hasattr(cfg, "whisper")
    assert isinstance(cfg.whisper, WhisperConfig)
    assert cfg.whisper.language is None


def test_config_load_without_whisper_key(tmp_path):
    """Config.load() with no 'whisper' key in JSON returns WhisperConfig(language=None)."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"version": 1, "audio": {}}))
    cfg = Config.load(config_file)
    assert isinstance(cfg.whisper, WhisperConfig)
    assert cfg.whisper.language is None


def test_config_load_with_whisper_language_string(tmp_path):
    """Config.load() with 'whisper': {'language': 'es'} returns WhisperConfig(language='es')."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"version": 1, "whisper": {"language": "es"}}))
    cfg = Config.load(config_file)
    assert cfg.whisper.language == "es"


def test_config_load_with_whisper_language_null(tmp_path):
    """Config.load() with 'whisper': {'language': null} returns WhisperConfig(language=None)."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"version": 1, "whisper": {"language": None}}))
    cfg = Config.load(config_file)
    assert cfg.whisper.language is None


# ---------------------------------------------------------------------------
# transcribe_audio tests
# ---------------------------------------------------------------------------

def test_transcribe_audio_calls_mlx_whisper(tmp_path, monkeypatch):
    """transcribe_audio() calls mlx_whisper.transcribe with the correct path and returns result['text']."""
    from meeting_notes.services import transcription as trans_module

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"\x00" * 1000)

    mock_transcribe = MagicMock(return_value={"text": "Hello world"})
    monkeypatch.setattr(trans_module.mlx_whisper, "transcribe", mock_transcribe)

    cfg = Config()
    result = trans_module.transcribe_audio(wav_file, cfg)

    assert result == "Hello world"
    mock_transcribe.assert_called_once()
    call_args = mock_transcribe.call_args
    assert call_args[0][0] == str(wav_file)


def test_transcribe_audio_uses_correct_model(tmp_path, monkeypatch):
    """transcribe_audio() passes path_or_hf_repo='mlx-community/whisper-large-v3-turbo'."""
    from meeting_notes.services import transcription as trans_module

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"\x00" * 1000)

    mock_transcribe = MagicMock(return_value={"text": "hello"})
    monkeypatch.setattr(trans_module.mlx_whisper, "transcribe", mock_transcribe)

    cfg = Config()
    trans_module.transcribe_audio(wav_file, cfg)

    call_kwargs = mock_transcribe.call_args[1]
    assert call_kwargs.get("path_or_hf_repo") == "mlx-community/whisper-large-v3-turbo"


def test_language_none_omits_kwarg(tmp_path, monkeypatch):
    """transcribe_audio() with config.whisper.language=None does NOT pass language kwarg."""
    from meeting_notes.services import transcription as trans_module

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"\x00" * 1000)

    captured_kwargs = {}

    def fake_transcribe(path, **kwargs):
        captured_kwargs.update(kwargs)
        return {"text": "auto-detected language text"}

    monkeypatch.setattr(trans_module.mlx_whisper, "transcribe", fake_transcribe)

    cfg = Config()
    cfg.whisper.language = None
    trans_module.transcribe_audio(wav_file, cfg)

    assert "language" not in captured_kwargs


def test_language_string_passes_kwarg(tmp_path, monkeypatch):
    """transcribe_audio() with config.whisper.language='en' passes language='en' as kwarg."""
    from meeting_notes.services import transcription as trans_module

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"\x00" * 1000)

    captured_kwargs = {}

    def fake_transcribe(path, **kwargs):
        captured_kwargs.update(kwargs)
        return {"text": "English text"}

    monkeypatch.setattr(trans_module.mlx_whisper, "transcribe", fake_transcribe)

    cfg = Config()
    cfg.whisper.language = "en"
    trans_module.transcribe_audio(wav_file, cfg)

    assert captured_kwargs.get("language") == "en"


# ---------------------------------------------------------------------------
# estimate_wav_duration_seconds tests
# ---------------------------------------------------------------------------

def test_estimate_wav_duration(tmp_path):
    """estimate_wav_duration_seconds() returns correct duration for known file size.

    16kHz mono s16le: BYTES_PER_SECOND = 32000
    File size = 32000 * 60 + 44 (WAV header) = 1,920,044 bytes => 60.0 seconds
    """
    from meeting_notes.services.transcription import estimate_wav_duration_seconds, WAV_HEADER_BYTES, BYTES_PER_SECOND

    wav_file = tmp_path / "test.wav"
    # 60 seconds of audio + header
    file_size = BYTES_PER_SECOND * 60 + WAV_HEADER_BYTES
    wav_file.write_bytes(b"\x00" * file_size)

    duration = estimate_wav_duration_seconds(wav_file)
    assert duration == pytest.approx(60.0)


def test_estimate_wav_duration_small_file(tmp_path):
    """estimate_wav_duration_seconds() returns 0.0 for file smaller than header."""
    from meeting_notes.services.transcription import estimate_wav_duration_seconds

    wav_file = tmp_path / "tiny.wav"
    wav_file.write_bytes(b"\x00" * 10)  # Less than 44 bytes

    duration = estimate_wav_duration_seconds(wav_file)
    assert duration == 0.0


# ---------------------------------------------------------------------------
# run_with_spinner tests
# ---------------------------------------------------------------------------

def test_run_with_spinner_returns_result(monkeypatch):
    """run_with_spinner() returns the result of the background function."""
    from meeting_notes.services.transcription import run_with_spinner

    mock_live = MagicMock()
    mock_live.__enter__ = MagicMock(return_value=mock_live)
    mock_live.__exit__ = MagicMock(return_value=False)

    with patch("meeting_notes.services.transcription.Live", return_value=mock_live):
        result = run_with_spinner(lambda: "the result", "Processing...")

    assert result == "the result"


def test_run_with_spinner_reraises_exception(monkeypatch):
    """run_with_spinner() re-raises exceptions from the background function."""
    from meeting_notes.services.transcription import run_with_spinner

    mock_live = MagicMock()
    mock_live.__enter__ = MagicMock(return_value=mock_live)
    mock_live.__exit__ = MagicMock(return_value=False)

    def failing_fn():
        raise ValueError("transcription failed")

    with patch("meeting_notes.services.transcription.Live", return_value=mock_live):
        with pytest.raises(ValueError, match="transcription failed"):
            run_with_spinner(failing_fn, "Processing...")
