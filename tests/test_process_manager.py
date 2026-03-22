import pytest


@pytest.mark.skip(reason="Wave 0 stub")
def test_start_ffmpeg_new_session():
    """subprocess.Popen called with start_new_session=True."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_stop_gracefully_sends_sigterm():
    """SIGTERM sent to process group."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_stop_gracefully_escalates_to_sigkill():
    """On timeout, SIGKILL sent."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_stop_gracefully_handles_already_dead():
    """ProcessLookupError is caught."""
    pass
