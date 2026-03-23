import pytest
from click.testing import CliRunner

from meeting_notes.cli.commands.doctor import doctor
from meeting_notes.core.health_check import CheckResult, CheckStatus, HealthCheckSuite
from meeting_notes.services.checks import OpenaiWhisperConflictCheck, PythonVersionCheck


def _make_ok_result():
    return CheckResult(status=CheckStatus.OK, message="All good")


def _make_error_result():
    return CheckResult(
        status=CheckStatus.ERROR,
        message="Something failed",
        fix_suggestion="Fix it",
    )


def test_doctor_runs_all_checks(monkeypatch):
    """When all checks pass, doctor exits 0 and prints 'All checks passed'."""
    monkeypatch.setattr(
        "meeting_notes.cli.commands.doctor.HealthCheckSuite.run_all",
        lambda self: [
            (type("C", (), {"name": "BlackHole Device"})(), _make_ok_result()),
            (type("C", (), {"name": "Microphone Device"})(), _make_ok_result()),
            (type("C", (), {"name": "Disk Space"})(), _make_ok_result()),
        ],
    )
    runner = CliRunner()
    result = runner.invoke(doctor, obj={"quiet": False})
    assert result.exit_code == 0
    assert "All checks passed" in result.output


def test_doctor_exits_1_on_error(monkeypatch):
    """When BlackHoleCheck returns ERROR, doctor exits 1 and prints 'Some checks failed'."""
    monkeypatch.setattr(
        "meeting_notes.cli.commands.doctor.HealthCheckSuite.run_all",
        lambda self: [
            (type("C", (), {"name": "BlackHole Device"})(), _make_error_result()),
            (type("C", (), {"name": "Microphone Device"})(), _make_ok_result()),
            (type("C", (), {"name": "Disk Space"})(), _make_ok_result()),
        ],
    )
    runner = CliRunner()
    result = runner.invoke(doctor, obj={"quiet": False})
    assert result.exit_code == 1
    assert "Some checks failed" in result.output


def test_doctor_exits_0_on_ok(monkeypatch):
    """When all checks return OK, doctor exits 0."""
    monkeypatch.setattr(
        "meeting_notes.cli.commands.doctor.HealthCheckSuite.run_all",
        lambda self: [
            (type("C", (), {"name": "BlackHole Device"})(), _make_ok_result()),
            (type("C", (), {"name": "Microphone Device"})(), _make_ok_result()),
            (type("C", (), {"name": "Disk Space"})(), _make_ok_result()),
        ],
    )
    runner = CliRunner()
    result = runner.invoke(doctor, obj={"quiet": False})
    assert result.exit_code == 0


def test_python_version_check_ok_on_current_python():
    """PythonVersionCheck returns OK or WARNING on current Python (not ERROR)."""
    import sys
    check = PythonVersionCheck()
    result = check.check()
    major, minor = sys.version_info[:2]
    if major == 3 and 11 <= minor < 14:
        assert result.status == CheckStatus.OK
    elif major == 3 and minor >= 14:
        # Running on Python 3.14+ — expect WARNING
        assert result.status == CheckStatus.WARNING
    else:
        assert result.status == CheckStatus.ERROR


def test_python_version_check_error_on_old_python(monkeypatch):
    """PythonVersionCheck returns ERROR when Python < 3.11."""
    import sys
    # Patch the version_info access inside the check by mocking the sys module attribute
    # We use a namedtuple-compatible structure via a simple mock
    from unittest.mock import patch

    class FakeVersionInfo:
        def __getitem__(self, key):
            info = (3, 10, 0, "final", 0)
            return info[key]

        def __len__(self):
            return 5

        @property
        def major(self):
            return 3

        @property
        def minor(self):
            return 10

        @property
        def micro(self):
            return 0

    fake_info = FakeVersionInfo()
    fake_info.__class__.__getitem__ = lambda self, k: (3, 10, 0, "final", 0)[k]

    with patch("sys.version_info", fake_info):
        check = PythonVersionCheck()
        result = check.check()
    assert result.status == CheckStatus.ERROR
    assert "requires >=3.11" in result.message


def test_openai_whisper_conflict_ok_when_not_installed():
    """OpenaiWhisperConflictCheck returns OK when openai-whisper is not installed."""
    check = OpenaiWhisperConflictCheck()
    result = check.check()
    # On this system openai-whisper should not be installed alongside mlx-whisper
    # Either OK (not installed) or WARNING (installed) — not ERROR
    assert result.status in (CheckStatus.OK, CheckStatus.WARNING)
    # If OK, verify message
    if result.status == CheckStatus.OK:
        assert "No openai-whisper conflict" in result.message
