import pytest
import shutil

from meeting_notes.core.health_check import (
    CheckResult,
    CheckStatus,
    HealthCheck,
    HealthCheckSuite,
)
from meeting_notes.services.checks import (
    BlackHoleCheck,
    DiskSpaceCheck,
    FFmpegDeviceCheck,
)

MOCK_FFMPEG_STDERR = """[AVFoundation indev @ 0x...] AVFoundation video devices:
[AVFoundation indev @ 0x...] [0] FaceTime HD Camera
[AVFoundation indev @ 0x...] AVFoundation audio devices:
[AVFoundation indev @ 0x...] [0] MacBook Pro Speakers
[AVFoundation indev @ 0x...] [1] BlackHole 2ch
[AVFoundation indev @ 0x...] [2] MacBook Pro Microphone
"""

MOCK_FFMPEG_STDERR_WRONG = """[AVFoundation indev @ 0x...] AVFoundation video devices:
[AVFoundation indev @ 0x...] [0] FaceTime HD Camera
[AVFoundation indev @ 0x...] AVFoundation audio devices:
[AVFoundation indev @ 0x...] [0] MacBook Pro Speakers
[AVFoundation indev @ 0x...] [1] MacBook Pro Microphone
[AVFoundation indev @ 0x...] [2] MacBook Pro Microphone
"""


def test_check_result_dataclass():
    result = CheckResult(
        status=CheckStatus.OK,
        message="All good",
        fix_suggestion="No fix needed",
    )
    assert result.status == CheckStatus.OK
    assert result.message == "All good"
    assert result.fix_suggestion == "No fix needed"

    # Test without optional field
    result2 = CheckResult(status=CheckStatus.ERROR, message="Something failed")
    assert result2.fix_suggestion is None


def test_health_check_abc_cannot_instantiate():
    with pytest.raises(TypeError):
        HealthCheck()


def test_suite_runs_all_checks():
    class AlwaysOK(HealthCheck):
        name = "Always OK"

        def check(self) -> CheckResult:
            return CheckResult(status=CheckStatus.OK, message="OK")

    class AlwaysError(HealthCheck):
        name = "Always Error"

        def check(self) -> CheckResult:
            return CheckResult(status=CheckStatus.ERROR, message="Error")

    suite = HealthCheckSuite()
    suite.register(AlwaysOK())
    suite.register(AlwaysError())

    results = suite.run_all()
    assert len(results) == 2
    assert results[0][1].status == CheckStatus.OK
    assert results[1][1].status == CheckStatus.ERROR


def test_suite_empty_returns_empty():
    suite = HealthCheckSuite()
    assert suite.run_all() == []


def test_blackhole_check_parses_stderr(monkeypatch):
    monkeypatch.setattr(
        "meeting_notes.services.checks.subprocess.run",
        lambda *a, **kw: type("R", (), {"stderr": MOCK_FFMPEG_STDERR})(),
    )
    result = BlackHoleCheck(device_index=1).check()
    assert result.status == CheckStatus.OK
    assert "BlackHole" in result.message


def test_blackhole_check_wrong_device(monkeypatch):
    monkeypatch.setattr(
        "meeting_notes.services.checks.subprocess.run",
        lambda *a, **kw: type("R", (), {"stderr": MOCK_FFMPEG_STDERR_WRONG})(),
    )
    result = BlackHoleCheck(device_index=1).check()
    assert result.status == CheckStatus.ERROR
    assert "not BlackHole" in result.message


def test_disk_space_check_ok(monkeypatch):
    DiskUsage = type("DiskUsage", (), {"free": 10 * 1024 ** 3})  # 10GB
    monkeypatch.setattr(shutil, "disk_usage", lambda path: DiskUsage())
    result = DiskSpaceCheck().check()
    assert result.status == CheckStatus.OK


def test_disk_space_check_warning(monkeypatch):
    DiskUsage = type("DiskUsage", (), {"free": 3 * 1024 ** 3})  # 3GB
    monkeypatch.setattr(shutil, "disk_usage", lambda path: DiskUsage())
    result = DiskSpaceCheck().check()
    assert result.status == CheckStatus.WARNING


def test_ffmpeg_device_check_reachable(monkeypatch):
    monkeypatch.setattr(
        "meeting_notes.services.checks.subprocess.run",
        lambda *a, **kw: type("R", (), {"stderr": MOCK_FFMPEG_STDERR})(),
    )
    result = FFmpegDeviceCheck(device_index=2).check()
    assert result.status == CheckStatus.OK
    assert "MacBook Pro Microphone" in result.message
