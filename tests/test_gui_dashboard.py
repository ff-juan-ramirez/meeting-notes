"""Wave 0 test stubs for Dashboard view requirements.

All stubs are skipped pending implementation in Wave 1+.
Requirements: DASH-01 through DASH-04.
"""
import pytest


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_dashboard_stats(qt_app):
    """DASH-01: Dashboard shows total sessions, transcribed count, summarized count, sessions this week.

    When the Dashboard view becomes visible, four stat cards render with counts
    derived from on-disk session metadata: Total Sessions, Transcribed,
    Summarized, and This Week (sessions recorded in the last 7 days).
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_dashboard_recent_sessions(qt_app):
    """DASH-02: Last 5 sessions rendered newest-first; row click emits session_selected signal.

    The "Recent Sessions" section shows up to 5 sessions sorted newest-first.
    Clicking a row emits DashboardView.session_selected(session_id) so that
    MainWindow can navigate to Sessions view and pre-select the matching row.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_dashboard_recording_indicator(qt_app):
    """DASH-03: QTimer polls state.json; pill shows idle/recording state correctly.

    A QTimer fires every 2 seconds while the Dashboard view is visible.
    When state.json has an active recording, StatusPill shows the recording
    state ("● Recording • H:MM:SS") with a red background.
    When idle, the pill shows "Idle" with a gray background.
    """
    pass


@pytest.mark.skip(reason="Wave 0 stub -- implementation pending")
def test_dashboard_navigate_to_record(qt_app):
    """DASH-04: "Start Recording" button emits navigate_requested(2) signal.

    Clicking the "Start Recording" (or "Go to Record" when recording is active)
    button emits DashboardView.navigate_requested(2) which causes MainWindow
    to switch the sidebar selection and stacked widget to the Record view.
    """
    pass
