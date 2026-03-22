import pytest


@pytest.mark.skip(reason="Wave 0 stub")
def test_check_result_dataclass():
    """CheckResult has status, message, fix_suggestion fields."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_health_check_abc_cannot_instantiate():
    """HealthCheck raises TypeError on direct instantiation."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_suite_runs_all_checks():
    """HealthCheckSuite.run_all() calls check() on all registered checks."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_suite_empty_returns_empty():
    """Empty suite returns empty list."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_blackhole_check_parses_stderr():
    """Mock ffmpeg stderr, verify name detection."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_blackhole_check_wrong_device():
    """Returns ERROR when device at index is not BlackHole."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_disk_space_check_ok():
    """Returns OK when >5GB free."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_disk_space_check_warning():
    """Returns WARNING when <5GB free."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_ffmpeg_device_check_reachable():
    """Returns OK when device index exists."""
    pass
