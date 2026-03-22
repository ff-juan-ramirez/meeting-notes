import pytest


@pytest.mark.skip(reason="Wave 0 stub")
def test_record_creates_session():
    """meet record writes state.json with session_id and pid."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_record_fails_if_already_recording():
    """Exits with error when active session exists."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_stop_terminates_ffmpeg():
    """meet stop reads PID and calls stop_gracefully."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_stop_clears_state():
    """state.json cleared after stop."""
    pass
