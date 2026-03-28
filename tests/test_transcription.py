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
    """transcribe_audio() calls mlx_whisper.transcribe with the correct path and returns (text, segments)."""
    from meeting_notes.services import transcription as trans_module

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"\x00" * 1000)

    mock_transcribe = MagicMock(return_value={"text": "Hello world", "segments": []})
    monkeypatch.setattr(trans_module.mlx_whisper, "transcribe", mock_transcribe)

    cfg = Config()
    text, segments = trans_module.transcribe_audio(wav_file, cfg)

    assert text == "Hello world"
    assert segments == []
    mock_transcribe.assert_called_once()
    call_args = mock_transcribe.call_args
    assert call_args[0][0] == str(wav_file)


def test_transcribe_audio_uses_correct_model(tmp_path, monkeypatch):
    """transcribe_audio() passes path_or_hf_repo='mlx-community/whisper-large-v3-turbo'."""
    from meeting_notes.services import transcription as trans_module

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"\x00" * 1000)

    mock_transcribe = MagicMock(return_value={"text": "hello", "segments": []})
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
        return {"text": "auto-detected language text", "segments": []}

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
        return {"text": "English text", "segments": []}

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


# ---------------------------------------------------------------------------
# SRT generation tests
# ---------------------------------------------------------------------------

def test_srt_timestamp_format():
    """seconds_to_srt_timestamp() converts float seconds to HH:MM:SS,mmm format."""
    from meeting_notes.services.transcription import seconds_to_srt_timestamp

    assert seconds_to_srt_timestamp(0.0) == "00:00:00,000"
    assert seconds_to_srt_timestamp(3661.5) == "01:01:01,500"
    assert seconds_to_srt_timestamp(59.999) == "00:00:59,999"


def test_generate_srt():
    """generate_srt() produces valid SRT with 1-based indices and HH:MM:SS,mmm timestamps."""
    from meeting_notes.services.transcription import generate_srt

    segments = [
        {"start": 0.0, "end": 2.5, "text": " Hello world"},
        {"start": 3.0, "end": 5.0, "text": " Goodbye"},
    ]
    srt = generate_srt(segments)
    assert "1\n00:00:00,000 --> 00:00:02,500\nHello world" in srt
    assert "2\n00:00:03,000 --> 00:00:05,000\nGoodbye" in srt


def test_generate_srt_with_speakers():
    """generate_srt() with speaker_map prefixes speaker tag on each entry."""
    from meeting_notes.services.transcription import generate_srt

    segments = [
        {"start": 0.0, "end": 2.0, "text": " Hello"},
        {"start": 2.0, "end": 4.0, "text": " Hi there"},
    ]
    speaker_map = {0: "SPEAKER_00", 1: "SPEAKER_01"}
    srt = generate_srt(segments, speaker_map=speaker_map)
    assert "SPEAKER_00: Hello" in srt
    assert "SPEAKER_01: Hi there" in srt


def test_transcribe_returns_segments(tmp_path, monkeypatch):
    """transcribe_audio() returns (text, segments) tuple instead of just text."""
    from meeting_notes.services import transcription as trans_module

    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"\x00" * 1000)

    fake_segments = [{"start": 0.0, "end": 2.0, "text": " Hello"}]
    monkeypatch.setattr(
        trans_module.mlx_whisper,
        "transcribe",
        lambda *a, **kw: {"text": "Hello", "segments": fake_segments},
    )

    cfg = Config()
    text, segments = trans_module.transcribe_audio(wav_file, cfg)
    assert text == "Hello"
    assert segments == fake_segments


# ---------------------------------------------------------------------------
# Diarization function tests
# ---------------------------------------------------------------------------

def test_speaker_segment_merge():
    """assign_speakers_to_segments() assigns speakers by max overlap."""
    from meeting_notes.services.transcription import assign_speakers_to_segments
    from unittest.mock import MagicMock

    segments = [
        {"start": 0.0, "end": 3.0, "text": " Hello"},     # overlaps mostly with turn 0-2.5 (SPEAKER_00)
        {"start": 3.0, "end": 6.0, "text": " Goodbye"},    # overlaps mostly with turn 2.5-6.0 (SPEAKER_01)
    ]

    # Build a mock diarization Annotation-like object
    turns = [
        (MagicMock(start=0.0, end=2.5), None, "SPEAKER_00"),
        (MagicMock(start=2.5, end=6.0), None, "SPEAKER_01"),
    ]
    diarization = MagicMock()
    diarization.itertracks.return_value = turns

    speaker_map = assign_speakers_to_segments(segments, diarization)
    assert speaker_map[0] == "SPEAKER_00"
    assert speaker_map[1] == "SPEAKER_01"


def test_diarized_txt_grouping():
    """build_diarized_txt() groups consecutive same-speaker segments."""
    from meeting_notes.services.transcription import build_diarized_txt

    segments = [
        {"start": 0.0, "end": 1.0, "text": " Hello"},
        {"start": 1.0, "end": 2.0, "text": " welcome"},
        {"start": 2.0, "end": 3.0, "text": " Thanks"},
        {"start": 3.0, "end": 4.0, "text": " sure"},
    ]
    speaker_map = {0: "SPEAKER_00", 1: "SPEAKER_00", 2: "SPEAKER_01", 3: "SPEAKER_01"}
    txt = build_diarized_txt(segments, speaker_map)
    assert "SPEAKER_00:" in txt
    assert "Hello welcome" in txt
    assert "SPEAKER_01:" in txt
    assert "Thanks sure" in txt


def _make_real_wav(tmp_path: Path) -> Path:
    """Create a minimal valid mono 16kHz WAV file for tests that use soundfile."""
    import struct
    import wave

    wav_file = tmp_path / "test.wav"
    with wave.open(str(wav_file), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # 0.1 second of silence (1600 samples)
        wf.writeframes(struct.pack("<1600h", *([0] * 1600)))
    return wav_file


def test_run_diarization_shims_list_audio_backends(tmp_path, monkeypatch):
    """run_diarization() patches torchaudio.list_audio_backends when missing.

    speechbrain 1.0.3 calls torchaudio.list_audio_backends() at import time,
    but torchaudio 2.9+ removed that API. The shim must be installed before
    pyannote.audio.Pipeline is imported so that the speechbrain import chain
    does not raise AttributeError.
    """
    import torchaudio
    from meeting_notes.services import transcription as trans_module
    from unittest.mock import MagicMock, patch

    wav_file = _make_real_wav(tmp_path)

    # Simulate torchaudio without list_audio_backends (i.e. torchaudio 2.9+)
    original = torchaudio.__dict__.pop("list_audio_backends", None)
    try:
        assert not hasattr(torchaudio, "list_audio_backends"), (
            "Test precondition failed: list_audio_backends must be absent"
        )

        # Simulate a plain pyannote Annotation (no exclusive_speaker_diarization attr).
        # Using spec=['itertracks'] ensures hasattr check returns False, so
        # run_diarization returns the annotation directly rather than unwrapping.
        fake_annotation = MagicMock(spec=["itertracks"])
        fake_pipeline = MagicMock(return_value=fake_annotation)

        # Pipeline is imported locally inside run_diarization, so patch at source.
        with patch("pyannote.audio.Pipeline") as MockPipeline:
            MockPipeline.from_pretrained.return_value = fake_pipeline
            result = trans_module.run_diarization(wav_file, "hf-fake-token")

        # The shim must now be present on torchaudio
        assert hasattr(torchaudio, "list_audio_backends"), (
            "run_diarization must install list_audio_backends shim on torchaudio"
        )
        assert torchaudio.list_audio_backends() == [], (
            "Shim must return empty list so speechbrain logs a warning, not an error"
        )
        assert result is fake_annotation
    finally:
        # Restore original state
        if original is not None:
            torchaudio.list_audio_backends = original
        else:
            torchaudio.__dict__.pop("list_audio_backends", None)


def test_run_diarization_passes_waveform_dict_to_pipeline(tmp_path, monkeypatch):
    """run_diarization() pre-loads audio with soundfile and passes a waveform dict.

    torchcodec (pyannote 4.x audio backend) fails to load on systems where its
    .dylib requires a PyTorch symbol not present in the installed torch version.
    When torchcodec is unavailable, pyannote's io.py leaves AudioDecoder undefined.
    Passing a file-path string to the pipeline triggers AudioDecoder and raises
    NameError. The fix: pre-load with soundfile and pass
    {"waveform": tensor, "sample_rate": int} so pyannote's waveform fast-path is
    used instead.
    """
    import torch
    from meeting_notes.services import transcription as trans_module
    from unittest.mock import MagicMock, patch, call

    wav_file = _make_real_wav(tmp_path)

    # Simulate a plain pyannote Annotation (no exclusive_speaker_diarization attr).
    # Using spec=['itertracks'] ensures hasattr check returns False, so
    # run_diarization returns the annotation directly rather than unwrapping.
    fake_annotation = MagicMock(spec=["itertracks"])
    fake_pipeline = MagicMock(return_value=fake_annotation)

    with patch("pyannote.audio.Pipeline") as MockPipeline:
        MockPipeline.from_pretrained.return_value = fake_pipeline
        result = trans_module.run_diarization(wav_file, "hf-fake-token")

    # Pipeline must be called with a dict, not a string path
    assert fake_pipeline.call_count == 1
    call_arg = fake_pipeline.call_args[0][0]
    assert isinstance(call_arg, dict), (
        "run_diarization must pass a waveform dict, not a path string, "
        "to avoid AudioDecoder (torchcodec) which may be unavailable"
    )
    assert "waveform" in call_arg, "dict must have 'waveform' key"
    assert "sample_rate" in call_arg, "dict must have 'sample_rate' key"
    assert isinstance(call_arg["waveform"], torch.Tensor), "'waveform' must be a torch.Tensor"
    assert call_arg["waveform"].shape[0] == 1, "waveform must be (channel, time) with channel=1 for mono"
    assert call_arg["sample_rate"] == 16000
    assert result is fake_annotation


def test_run_diarization_unwraps_diarize_output(tmp_path):
    """run_diarization() unwraps pyannote 4.x DiarizeOutput into an Annotation.

    pyannote 4.x pipeline() returns a DiarizeOutput dataclass with fields
    `speaker_diarization` and `exclusive_speaker_diarization`. All downstream
    code (assign_speakers_to_segments, transcribe.py speaker_turns loop) calls
    .itertracks(yield_label=True) on the return value. run_diarization() must
    detect DiarizeOutput and return exclusive_speaker_diarization (the non-
    overlapping annotation, optimal for mapping speech turns to transcript segments).
    """
    from meeting_notes.services import transcription as trans_module
    from unittest.mock import MagicMock, patch

    wav_file = _make_real_wav(tmp_path)

    # Simulate pyannote 4.x DiarizeOutput
    fake_exclusive_annotation = MagicMock(spec=["itertracks"])
    fake_diarize_output = MagicMock()
    fake_diarize_output.exclusive_speaker_diarization = fake_exclusive_annotation
    fake_pipeline = MagicMock(return_value=fake_diarize_output)

    with patch("pyannote.audio.Pipeline") as MockPipeline:
        MockPipeline.from_pretrained.return_value = fake_pipeline
        result = trans_module.run_diarization(wav_file, "hf-fake-token")

    assert result is fake_exclusive_annotation, (
        "run_diarization must unwrap DiarizeOutput and return "
        "exclusive_speaker_diarization so callers can call .itertracks()"
    )
