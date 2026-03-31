"""Tests for Sessions view requirements SESS-01 through SESS-08."""
import json
import wave
from pathlib import Path

import pytest

from meeting_notes.core.config import Config
from meeting_notes.core.state import write_state
from meeting_notes.gui.views.sessions import SessionsView


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wav(path: Path, duration_s: int = 2, sample_rate: int = 16000) -> None:
    """Write a minimal valid WAV file to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = duration_s * sample_rate
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_frames)


def _make_metadata(
    tmp_path: Path,
    stem: str,
    *,
    has_transcript: bool = False,
    has_notes: bool = False,
    has_notion: bool = False,
    has_wav: bool = True,
    recording_name: str | None = None,
) -> dict:
    """Create fake session metadata and associated files. Return the metadata dict."""
    recordings_dir = tmp_path / "recordings"
    transcripts_dir = tmp_path / "transcripts"
    notes_dir = tmp_path / "notes"
    metadata_dir = tmp_path / "metadata"

    for d in [recordings_dir, transcripts_dir, notes_dir, metadata_dir]:
        d.mkdir(parents=True, exist_ok=True)

    meta: dict = {}

    if has_wav:
        wav_path = recordings_dir / f"{stem}.wav"
        _make_wav(wav_path)
        meta["wav_path"] = str(wav_path)

    if has_transcript:
        transcript_path = transcripts_dir / f"{stem}.txt"
        transcript_path.write_text("hello world this is a test transcript")
        meta["transcript_path"] = str(transcript_path)
        meta["transcribed_at"] = "2026-03-24T10:00:00+00:00"
        meta["word_count"] = 7

    if has_notes:
        notes_path = notes_dir / f"{stem}-meeting.md"
        notes_path.write_text("# Meeting Notes\n\nSome notes here.")
        meta["notes_path"] = str(notes_path)
        meta["summarized_at"] = "2026-03-24T10:05:00+00:00"

    if has_notion:
        meta["notion_url"] = f"https://notion.so/{stem}"

    if recording_name:
        meta["recording_name"] = recording_name

    metadata_path = metadata_dir / f"{stem}.json"
    write_state(metadata_path, meta)
    return meta


def _make_config(tmp_path: Path) -> Config:
    """Create a Config pointing at tmp_path for storage."""
    return Config(storage_path=str(tmp_path))


# ---------------------------------------------------------------------------
# SESS-01: Session list populated
# ---------------------------------------------------------------------------

def test_sessions_list_populated(qt_app, tmp_path, monkeypatch):
    """SESS-01: _refresh_sessions populates list widget with all sessions."""
    _make_metadata(tmp_path, "session-001", has_wav=True)
    _make_metadata(tmp_path, "session-002", has_transcript=True)
    _make_metadata(tmp_path, "session-003", has_notes=True, has_transcript=True)

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Test Title",
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    view._refresh_sessions()

    assert view._list_widget.count() == 3


# ---------------------------------------------------------------------------
# SESS-02: Filter by status
# ---------------------------------------------------------------------------

def test_sessions_filter_status(qt_app, tmp_path, monkeypatch):
    """SESS-02: Changing filter QComboBox filters the visible rows."""
    _make_metadata(tmp_path, "sess-not-tx", has_wav=True)
    _make_metadata(tmp_path, "sess-tx", has_transcript=True)
    _make_metadata(tmp_path, "sess-sum", has_notes=True, has_transcript=True)

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Title",
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    view._refresh_sessions()

    # Default filter is "All" — should show 3
    assert view._list_widget.count() == 3

    # Switch to "Transcribed" (status == "transcribed")
    idx = view._filter_combo.findText("Transcribed")
    view._filter_combo.setCurrentIndex(idx)
    assert view._list_widget.count() == 1

    # Switch back to "All"
    idx_all = view._filter_combo.findText("All")
    view._filter_combo.setCurrentIndex(idx_all)
    assert view._list_widget.count() == 3


# ---------------------------------------------------------------------------
# SESS-03: Detail panel loads session
# ---------------------------------------------------------------------------

def test_detail_panel_loads_session(qt_app, tmp_path, monkeypatch):
    """SESS-03: Selecting a session populates detail panel metadata fields."""
    _make_metadata(
        tmp_path,
        "detail-test",
        has_wav=True,
        has_transcript=True,
        recording_name="My Meeting",
    )

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Title",
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    view._refresh_sessions()

    assert view._list_widget.count() == 1

    # Trigger selection of first row
    view._on_session_selected(0)

    # Detail stack should switch to index 1 (detail panel)
    assert view._detail_stack.currentIndex() == 1

    # Title label should contain the recording_name
    assert view._lbl_title.text() == "My Meeting"

    # Date label should not be empty (transcribed_at is set)
    assert view._lbl_date.text() != ""


# ---------------------------------------------------------------------------
# SESS-04: Pipeline indicator steps
# ---------------------------------------------------------------------------

def test_pipeline_indicator_steps(qt_app, tmp_path, monkeypatch):
    """SESS-04: Pipeline step frames show step-done or step-pending based on session state."""
    _make_metadata(tmp_path, "pipe-test", has_wav=True, has_transcript=True)

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Title",
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    view._refresh_sessions()
    view._on_session_selected(0)

    # Steps: Recorded=done, Transcribed=done, Summarized=pending, Notion=pending
    styles = [f.property("style") for f in view._pipeline_frames]
    assert styles[0] == "step-done"     # Recorded
    assert styles[1] == "step-done"     # Transcribed
    assert styles[2] == "step-pending"  # Summarized
    assert styles[3] == "step-pending"  # Notion


# ---------------------------------------------------------------------------
# SESS-05: Open Notion URL
# ---------------------------------------------------------------------------

def test_open_notion_url(qt_app, tmp_path, monkeypatch):
    """SESS-05: _open_notion calls QDesktopServices.openUrl with correct QUrl."""
    _make_metadata(
        tmp_path, "notion-test",
        has_wav=True, has_transcript=True, has_notes=True, has_notion=True,
    )

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Title",
    )

    captured_urls = []
    monkeypatch.setattr(
        "meeting_notes.gui.views.sessions.QDesktopServices.openUrl",
        lambda url: captured_urls.append(url),
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    view._refresh_sessions()
    view._on_session_selected(0)
    view._open_notion()

    assert len(captured_urls) == 1
    assert "notion-test" in captured_urls[0].toString()


# ---------------------------------------------------------------------------
# SESS-06: Transcribe from detail
# ---------------------------------------------------------------------------

def test_transcribe_from_detail(qt_app, tmp_path, monkeypatch):
    """SESS-06: _start_transcribe disables buttons and creates TranscribeWorker."""
    _make_metadata(tmp_path, "tx-test", has_wav=True)

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Title",
    )

    class FakeWorker:
        """Minimal fake that satisfies the double-start guard."""
        def __init__(self, wav_path, config):
            pass

        def isRunning(self):
            return False

        def start(self):
            pass

        def deleteLater(self):
            pass

        class _FakeSignal:
            def connect(self, fn):
                pass

        progress = _FakeSignal()
        finished = _FakeSignal()
        failed = _FakeSignal()

    monkeypatch.setattr(
        "meeting_notes.gui.views.sessions.TranscribeWorker",
        FakeWorker,
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    view._refresh_sessions()
    view._on_session_selected(0)

    # Transcribe button should be enabled (wav exists, not transcribed)
    assert view._btn_transcribe.isEnabled()

    view._start_transcribe()

    # All buttons should be disabled after starting worker
    assert not view._btn_transcribe.isEnabled()
    assert not view._btn_summarize.isEnabled()
    assert not view._btn_notion.isEnabled()


# ---------------------------------------------------------------------------
# SESS-07: Summarize from detail
# ---------------------------------------------------------------------------

def test_summarize_from_detail(qt_app, tmp_path, monkeypatch):
    """SESS-07: _start_summarize disables buttons and creates SummarizeWorker."""
    _make_metadata(tmp_path, "sum-test", has_wav=True, has_transcript=True)

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Title",
    )

    class FakeWorker:
        def __init__(self, stem, template, title, config):
            pass

        def isRunning(self):
            return False

        def start(self):
            pass

        def deleteLater(self):
            pass

        class _FakeSignal:
            def connect(self, fn):
                pass

        progress = _FakeSignal()
        finished = _FakeSignal()
        failed = _FakeSignal()

    monkeypatch.setattr(
        "meeting_notes.gui.views.sessions.SummarizeWorker",
        FakeWorker,
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    # Manually seed template combo (showEvent not called in test)
    view._template_combo.addItem("meeting")
    view._refresh_sessions()
    view._on_session_selected(0)

    # Summarize button should be enabled (has transcript, template available)
    assert view._btn_summarize.isEnabled()

    view._start_summarize()

    assert not view._btn_transcribe.isEnabled()
    assert not view._btn_summarize.isEnabled()
    assert not view._btn_notion.isEnabled()


# ---------------------------------------------------------------------------
# SESS-08: Tab content
# ---------------------------------------------------------------------------

def test_detail_tabs_content(qt_app, tmp_path, monkeypatch):
    """SESS-08: Transcript tab shows file content; SRT tab shows placeholder when missing."""
    _make_metadata(tmp_path, "tabs-test", has_wav=True, has_transcript=True, has_notes=True)

    monkeypatch.setattr(
        "meeting_notes.services.notion.extract_title",
        lambda notes_text, fallback: "Title",
    )

    config = _make_config(tmp_path)
    view = SessionsView(config)
    view._refresh_sessions()
    view._on_session_selected(0)

    # Tab 0: Transcript should contain the text we wrote
    transcript_text = view._tab_transcript.toPlainText()
    assert "hello world" in transcript_text

    # Tab 2: SRT should show placeholder (no .srt file created)
    srt_text = view._tab_srt.toPlainText()
    assert srt_text == "No SRT file."
