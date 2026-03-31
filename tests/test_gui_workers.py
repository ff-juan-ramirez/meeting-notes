"""Tests for GUI worker thread signal behavior.

Requirements: SESS-06, SESS-07 (worker thread safety).
"""
import sys
import wave
from pathlib import Path

import pytest

from meeting_notes.core.config import Config
from meeting_notes.core.state import write_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wav(path: Path, duration_s: int = 1, sample_rate: int = 16000) -> None:
    """Write a minimal valid WAV file to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = duration_s * sample_rate
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_frames)


def _make_config(tmp_path: Path) -> Config:
    """Config with no Notion token — skips Notion push in SummarizeWorker."""
    return Config(storage_path=str(tmp_path))


# ---------------------------------------------------------------------------
# SESS-06: TranscribeWorker signals
# ---------------------------------------------------------------------------

def test_transcribe_worker_signals(qt_app, tmp_path, monkeypatch):
    """SESS-06: TranscribeWorker emits finished(stem, word_count) on success."""
    # Set up directories and WAV file
    wav_path = tmp_path / "recordings" / "test-session.wav"
    _make_wav(wav_path)
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    meta = {"wav_path": str(wav_path)}
    write_state(metadata_dir / "test-session.json", meta)

    # Monkeypatch transcribe_audio to avoid actual ML call
    monkeypatch.setattr(
        "meeting_notes.services.transcription.transcribe_audio",
        lambda wav_path, config: ("hello world", []),
    )

    from meeting_notes.gui.workers.transcribe_worker import TranscribeWorker

    config = _make_config(tmp_path)
    worker = TranscribeWorker(wav_path, config)

    results = []
    worker.finished.connect(lambda stem, wc: results.append(("finished", stem, wc)))
    worker.failed.connect(lambda msg: results.append(("failed", msg)))

    worker.start()
    worker.wait(10_000)  # 10s timeout
    # Process queued cross-thread signal deliveries
    from PySide6.QtWidgets import QApplication
    QApplication.instance().processEvents()

    assert len(results) == 1
    event_type, stem, word_count = results[0]
    assert event_type == "finished"
    assert stem == "test-session"
    assert word_count == 2  # "hello world" -> 2 words


# ---------------------------------------------------------------------------
# SESS-07: SummarizeWorker signals
# ---------------------------------------------------------------------------

def test_summarize_worker_signals(qt_app, tmp_path, monkeypatch):
    """SESS-07: SummarizeWorker emits finished(notion_url) on success."""
    # Set up directories
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Write a fake transcript
    transcript_path = transcripts_dir / "sum-session.txt"
    transcript_path.write_text("Hello, this is a meeting transcript with enough text.")

    # Write metadata
    meta = {
        "wav_path": str(tmp_path / "recordings" / "sum-session.wav"),
        "transcript_path": str(transcript_path),
    }
    write_state(metadata_dir / "sum-session.json", meta)

    # Monkeypatch the entire service layer to avoid real LLM/Notion calls
    monkeypatch.setattr(
        "meeting_notes.services.llm.load_template",
        lambda name: "Summarize this: {transcript}",
    )
    monkeypatch.setattr(
        "meeting_notes.services.llm.estimate_tokens",
        lambda text: 10,  # below chunking threshold
    )
    monkeypatch.setattr(
        "meeting_notes.services.llm.build_prompt",
        lambda template, transcript: f"Prompt: {transcript[:20]}",
    )
    monkeypatch.setattr(
        "meeting_notes.services.llm.generate_notes",
        lambda prompt: "# Meeting Notes\n\nSome generated notes.",
    )

    from meeting_notes.gui.workers.summarize_worker import SummarizeWorker

    config = _make_config(tmp_path)
    # No Notion token => notion push skipped, notion_url = ""
    worker = SummarizeWorker("sum-session", "meeting", None, config)

    results = []
    worker.finished.connect(lambda url: results.append(("finished", url)))
    worker.failed.connect(lambda msg: results.append(("failed", msg)))

    worker.start()
    worker.wait(10_000)
    from PySide6.QtWidgets import QApplication
    QApplication.instance().processEvents()

    assert len(results) == 1
    event_type, notion_url = results[0]
    assert event_type == "finished"
    # No Notion configured -> empty string
    assert isinstance(notion_url, str)


# ---------------------------------------------------------------------------
# Worker failed signal
# ---------------------------------------------------------------------------

def test_worker_failed_signal(qt_app, tmp_path, monkeypatch):
    """TranscribeWorker emits failed(str) when transcribe_audio raises."""
    wav_path = tmp_path / "recordings" / "fail-session.wav"
    _make_wav(wav_path)
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    write_state(metadata_dir / "fail-session.json", {"wav_path": str(wav_path)})

    monkeypatch.setattr(
        "meeting_notes.services.transcription.transcribe_audio",
        lambda wav_path, config: (_ for _ in ()).throw(RuntimeError("test error")),
    )

    from meeting_notes.gui.workers.transcribe_worker import TranscribeWorker

    config = _make_config(tmp_path)
    worker = TranscribeWorker(wav_path, config)

    results = []
    worker.finished.connect(lambda stem, wc: results.append(("finished", stem, wc)))
    worker.failed.connect(lambda msg: results.append(("failed", msg)))

    worker.start()
    worker.wait(10_000)
    from PySide6.QtWidgets import QApplication
    QApplication.instance().processEvents()

    assert len(results) == 1
    event_type, error_msg = results[0]
    assert event_type == "failed"
    assert "test error" in error_msg


# ---------------------------------------------------------------------------
# No ML imports at module level
# ---------------------------------------------------------------------------

def test_worker_no_ml_import_at_module_level(qt_app):
    """Importing worker modules must not add mlx_whisper/pyannote/torchaudio to sys.modules."""
    # Remove any pre-existing ML modules from sys.modules to ensure clean check
    ml_modules = [
        k for k in list(sys.modules)
        if k.startswith(("mlx_whisper", "pyannote", "torchaudio"))
    ]
    for mod in ml_modules:
        sys.modules.pop(mod, None)

    # Import worker modules (may already be imported; that's fine —
    # the key constraint is they don't TRIGGER ML imports at import time)
    import meeting_notes.gui.workers.transcribe_worker  # noqa: F401
    import meeting_notes.gui.workers.summarize_worker  # noqa: F401

    for forbidden in ("mlx_whisper", "pyannote", "pyannote.audio", "torchaudio"):
        assert forbidden not in sys.modules, (
            f"{forbidden} was imported at module level in worker modules"
        )
