import pytest


@pytest.mark.skip(reason="Wave 0 stub")
def test_write_state_creates_file(tmp_state_file):
    """write_state creates state.json."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_atomic_write_uses_temp_replace(tmp_state_file):
    """Temp file used then replaced (mock or check)."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_read_state_returns_dict(tmp_state_file):
    """read_state returns the written dict."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_read_state_missing_file(tmp_path):
    """Returns None or empty dict for missing file."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_stale_pid_detection_dead_process():
    """check_for_stale_session returns False for dead PID."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_stale_pid_detection_live_process():
    """check_for_stale_session returns True for live PID."""
    pass
