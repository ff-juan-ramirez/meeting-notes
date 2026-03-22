import pytest
from click.testing import CliRunner

from meeting_notes.cli.commands.doctor import doctor
from meeting_notes.core.health_check import CheckResult, CheckStatus, HealthCheckSuite


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
    result = runner.invoke(doctor)
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
    result = runner.invoke(doctor)
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
    result = runner.invoke(doctor)
    assert result.exit_code == 0
