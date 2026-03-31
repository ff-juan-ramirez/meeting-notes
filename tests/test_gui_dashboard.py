"""Dashboard view tests — DASH-01 through DASH-04."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from meeting_notes.core.config import Config


# ---------------------------------------------------------------------------
# Helper: create a minimal metadata JSON file
# ---------------------------------------------------------------------------

def _write_meta(meta_dir: Path, stem: str, meta: dict) -> Path:
    """Write a metadata JSON file and return its path."""
    path = meta_dir / f"{stem}.json"
    path.write_text(json.dumps(meta))
    return path


# ---------------------------------------------------------------------------
# DASH-01: Stats cards show correct aggregate counts
# ---------------------------------------------------------------------------

def test_dashboard_stats(qt_app, tmp_path, monkeypatch):
    """DASH-01: Dashboard shows total sessions, transcribed count, summarized count, sessions this week."""
    from meeting_notes.gui.views.dashboard import DashboardView

    # Setup metadata dir
    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir(parents=True)

    # Session 1: summarized (notes file exists)
    notes1 = tmp_path / "notes" / "session1.md"
    notes1.parent.mkdir(parents=True, exist_ok=True)
    notes1.write_text("# Meeting Notes")
    transcript1 = tmp_path / "transcripts" / "session1.txt"
    transcript1.parent.mkdir(parents=True, exist_ok=True)
    transcript1.write_text("hello world")
    recent_ts = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    _write_meta(meta_dir, "session1", {
        "notes_path": str(notes1),
        "transcript_path": str(transcript1),
        "transcribed_at": recent_ts,
    })

    # Session 2: summarized (notes file exists, older than 7 days)
    notes2 = tmp_path / "notes" / "session2.md"
    notes2.write_text("# Meeting 2")
    transcript2 = tmp_path / "transcripts" / "session2.txt"
    transcript2.write_text("meeting text")
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    _write_meta(meta_dir, "session2", {
        "notes_path": str(notes2),
        "transcript_path": str(transcript2),
        "transcribed_at": old_ts,
    })

    # Session 3: transcribed only (no notes)
    transcript3 = tmp_path / "transcripts" / "session3.txt"
    transcript3.write_text("transcript text")
    _write_meta(meta_dir, "session3", {
        "transcript_path": str(transcript3),
        "transcribed_at": old_ts,
    })

    # Session 4: not transcribed (no wav path in metadata so no mtime fallback)
    _write_meta(meta_dir, "session4", {})

    # Monkeypatch storage functions so DashboardView reads from tmp_path
    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_data_dir",
        lambda storage_path=None: tmp_path,
    )
    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_config_dir",
        lambda: tmp_path,
    )

    # Write empty state.json (idle)
    (tmp_path / "state.json").write_text("{}")

    config = Config(storage_path=str(tmp_path))
    dashboard = DashboardView(config)
    dashboard._refresh_dashboard()

    assert dashboard._stat_total.text() == "4", f"Expected 4, got {dashboard._stat_total.text()}"
    assert dashboard._stat_transcribed.text() == "3", (
        f"Expected 3 (2 summarized + 1 transcribed), got {dashboard._stat_transcribed.text()}"
    )
    assert dashboard._stat_summarized.text() == "2", f"Expected 2, got {dashboard._stat_summarized.text()}"
    # Only session1 is within 7 days
    assert dashboard._stat_week.text() == "1", f"Expected 1, got {dashboard._stat_week.text()}"


# ---------------------------------------------------------------------------
# DASH-02: Recent sessions list shows up to 5 rows, session_selected fires
# ---------------------------------------------------------------------------

def test_dashboard_recent_sessions(qt_app, tmp_path, monkeypatch):
    """DASH-02: Last 5 sessions rendered newest-first; row click emits session_selected signal."""
    from meeting_notes.gui.views.dashboard import DashboardView

    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir(parents=True)

    # Create 7 sessions so we can verify only 5 are shown
    for i in range(7):
        ts = (datetime.now(timezone.utc) - timedelta(days=i)).isoformat()
        _write_meta(meta_dir, f"session{i:02d}", {
            "transcribed_at": ts,
        })

    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_data_dir",
        lambda storage_path=None: tmp_path,
    )
    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_config_dir",
        lambda: tmp_path,
    )
    (tmp_path / "state.json").write_text("{}")

    config = Config(storage_path=str(tmp_path))
    dashboard = DashboardView(config)
    dashboard._refresh_dashboard()

    # Verify only 5 rows shown (cap enforced)
    assert dashboard._recent_list.count() == 5, (
        f"Expected 5 recent sessions, got {dashboard._recent_list.count()}"
    )

    # Capture session_selected signal
    results: list[str] = []
    dashboard.session_selected.connect(results.append)

    # Simulate clicking the first row
    dashboard._on_recent_session_clicked(0)

    assert len(results) == 1, f"Expected 1 signal emission, got {len(results)}"
    assert isinstance(results[0], str), "session_selected should emit a string"
    assert results[0] != "", "session_id should not be empty"


# ---------------------------------------------------------------------------
# DASH-03: QTimer polls state.json; pill shows idle/recording correctly
# ---------------------------------------------------------------------------

def test_dashboard_recording_indicator(qt_app, tmp_path, monkeypatch):
    """DASH-03: QTimer polls state.json; pill shows idle/recording state correctly."""
    from meeting_notes.gui.views.dashboard import DashboardView

    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_data_dir",
        lambda storage_path=None: tmp_path,
    )
    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_config_dir",
        lambda: tmp_path,
    )

    config = Config(storage_path=str(tmp_path))
    dashboard = DashboardView(config)

    # --- Active recording state ---
    # Use current process PID so check_for_stale_session returns True
    start_5_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    (tmp_path / "state.json").write_text(json.dumps({
        "pid": os.getpid(),
        "start_time": start_5_min_ago,
    }))

    dashboard._refresh_recording_state()

    pill_text = dashboard._recording_pill._label.text()
    assert pill_text.startswith("\u25cf"), (
        f"Expected pill to start with recording bullet, got: {pill_text!r}"
    )
    assert dashboard._recording_btn.text() == "Go to Record", (
        f"Expected 'Go to Record', got {dashboard._recording_btn.text()!r}"
    )

    # --- Idle state ---
    (tmp_path / "state.json").write_text("{}")
    dashboard._refresh_recording_state()

    assert dashboard._recording_pill._label.text() == "Idle", (
        f"Expected 'Idle', got {dashboard._recording_pill._label.text()!r}"
    )
    assert dashboard._recording_btn.text() == "Start Recording", (
        f"Expected 'Start Recording', got {dashboard._recording_btn.text()!r}"
    )


# ---------------------------------------------------------------------------
# DASH-04: "Start Recording" button emits navigate_requested(2)
# ---------------------------------------------------------------------------

def test_dashboard_navigate_to_record(qt_app, tmp_path, monkeypatch):
    """DASH-04: "Start Recording" button emits navigate_requested(2) signal."""
    from meeting_notes.gui.views.dashboard import DashboardView

    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_data_dir",
        lambda storage_path=None: tmp_path,
    )
    monkeypatch.setattr(
        "meeting_notes.gui.views.dashboard.get_config_dir",
        lambda: tmp_path,
    )
    (tmp_path / "state.json").write_text("{}")

    config = Config(storage_path=str(tmp_path))
    dashboard = DashboardView(config)

    results: list[int] = []
    dashboard.navigate_requested.connect(results.append)

    dashboard._recording_btn.click()

    assert results == [2], f"Expected [2], got {results}"
