"""Wave 0 test stubs for Sessions view requirements.

All stubs are skipped pending implementation in Wave 1+.
Requirements: SESS-01 through SESS-08.
"""
import pytest


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_sessions_list_populated(qt_app):
    """SESS-01: SessionsView._refresh_sessions populates list widget with session rows.

    When the Sessions view becomes visible, _refresh_sessions() reads all sessions
    from disk via list_sessions() and adds a SessionRowWidget for each session to
    the QListWidget. The list count should match the number of sessions on disk.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_sessions_filter_status(qt_app):
    """SESS-02: Changing filter QComboBox filters the visible rows.

    When the user changes the status filter QComboBox from "All" to a specific
    status (e.g., "Transcribed"), only session rows matching that status remain
    visible. Changing back to "All" restores all rows.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_detail_panel_loads_session(qt_app):
    """SESS-03: Selecting a session populates detail panel metadata fields.

    When a session row is clicked (currentItemChanged), the detail panel shows
    the session title, date, duration, word count, and pipeline step indicator.
    The right panel switches from the empty-state label to the populated detail view.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_pipeline_indicator_steps(qt_app):
    """SESS-04: Pipeline steps show green fill for completed steps, border-only for pending.

    The pipeline indicator renders 4 steps: Recorded, Transcribed, Summarized, Notion.
    Steps completed by the session show QFrame[style="step-done"] (green fill).
    Steps not yet done show QFrame[style="step-pending"] (border-only circle).
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_open_notion_url(qt_app):
    """SESS-05: Open Notion button calls QDesktopServices.openUrl with correct URL.

    When the "Open in Notion" button is clicked and a session has a notion_url
    in metadata, QDesktopServices.openUrl is called with a QUrl wrapping the
    stored notion_url value. The button is disabled when notion_url is None.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_transcribe_from_detail(qt_app):
    """SESS-06: Transcribe button disables all buttons, starts TranscribeWorker, re-enables on finished.

    Clicking "Transcribe" disables all three action buttons and the status label
    becomes visible with progress text. When TranscribeWorker emits finished(),
    buttons re-enable and the detail panel refreshes from disk.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_summarize_from_detail(qt_app):
    """SESS-07: Summarize button uses selected template and optional title override.

    Clicking "Summarize" reads the selected template from the QComboBox and the
    optional title from the QLineEdit. A SummarizeWorker is created with those
    parameters and started. All action buttons disable until the worker finishes.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_detail_tabs_content(qt_app):
    """SESS-08: Tab widget shows transcript, notes, SRT in read-only QPlainTextEdit.

    The detail panel QTabWidget has three tabs: "Transcript", "Notes", "SRT".
    Each tab contains a QPlainTextEdit in ReadOnly mode. When the file does not
    exist, the placeholder text is shown ("Not yet transcribed." etc.).
    """
    pass
