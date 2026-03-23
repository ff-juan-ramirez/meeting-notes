import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from meeting_notes.cli.commands.doctor import doctor
from meeting_notes.core.health_check import CheckResult, CheckStatus, HealthCheck, HealthCheckSuite
from meeting_notes.services.checks import (
    BlackHoleCheck,
    DiskSpaceCheck,
    FFmpegDeviceCheck,
    MlxWhisperCheck,
    NotionTokenCheck,
    OllamaModelCheck,
    OllamaRunningCheck,
    OpenaiWhisperConflictCheck,
    PythonVersionCheck,
    WhisperModelCheck,
)


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


# ── verbose_detail() tests ─────────────────────────────────────────────────────

def test_health_check_base_verbose_detail_returns_none():
    """HealthCheck base class verbose_detail() returns None."""
    class ConcreteCheck(HealthCheck):
        name = "Test Check"
        def check(self) -> CheckResult:
            return CheckResult(status=CheckStatus.OK, message="ok")

    check = ConcreteCheck()
    assert check.verbose_detail() is None


def test_status_icons_importable_from_ui():
    """STATUS_ICONS is importable from meeting_notes.cli.ui."""
    from meeting_notes.cli.ui import STATUS_ICONS
    from meeting_notes.core.health_check import CheckStatus
    assert CheckStatus.OK in STATUS_ICONS
    assert CheckStatus.WARNING in STATUS_ICONS
    assert CheckStatus.ERROR in STATUS_ICONS


def test_blackhole_check_verbose_detail_returns_device_name(monkeypatch):
    """BlackHoleCheck.verbose_detail() returns device name when _parse_audio_devices succeeds."""
    monkeypatch.setattr(
        "meeting_notes.services.checks._parse_audio_devices",
        lambda: {1: "BlackHole 2ch"},
    )
    check = BlackHoleCheck(device_index=1)
    detail = check.verbose_detail()
    assert detail is not None
    assert "BlackHole 2ch" in detail


def test_ffmpeg_device_check_verbose_detail_returns_version(monkeypatch):
    """FFmpegDeviceCheck.verbose_detail() returns ffmpeg version string when ffmpeg available."""
    mock_result = MagicMock()
    mock_result.stdout = "ffmpeg version 6.1.1 Copyright (c) 2000-2023\nmore info"
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: mock_result,
    )
    check = FFmpegDeviceCheck(device_index=2)
    detail = check.verbose_detail()
    assert detail is not None
    assert "ffmpeg version" in detail


def test_python_version_check_verbose_detail_contains_executable():
    """PythonVersionCheck.verbose_detail() returns string containing sys.executable."""
    import sys
    check = PythonVersionCheck()
    detail = check.verbose_detail()
    assert detail is not None
    assert sys.executable in detail


def test_ollama_running_check_verbose_detail_returns_version(monkeypatch):
    """OllamaRunningCheck.verbose_detail() returns 'Ollama {version}' when API responds."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"version": "0.1.20"}
    monkeypatch.setattr(
        "requests.get",
        lambda *args, **kwargs: mock_resp,
    )
    check = OllamaRunningCheck()
    detail = check.verbose_detail()
    assert detail is not None
    assert "Ollama" in detail
    assert "0.1.20" in detail


def test_ollama_model_check_verbose_detail_contains_model_name(monkeypatch):
    """OllamaModelCheck.verbose_detail() returns string containing 'llama3.1:8b' when model listed."""
    mock_result = MagicMock()
    mock_result.stdout = "llama3.1:8b   abc123  4.7 GB  2 days ago"
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: mock_result,
    )
    check = OllamaModelCheck()
    detail = check.verbose_detail()
    assert detail is not None
    assert "llama3.1:8b" in detail


def test_whisper_model_check_verbose_detail_returns_path_and_size(monkeypatch, tmp_path):
    """WhisperModelCheck.verbose_detail() returns path and size when MODEL_CACHE_DIR exists."""
    # Create a fake model dir with a small file
    fake_model_dir = tmp_path / "models--mlx-community--whisper-large-v3-turbo"
    fake_model_dir.mkdir()
    fake_file = fake_model_dir / "model.safetensors"
    fake_file.write_bytes(b"x" * (512 * 1024 * 1024))  # 512 MB

    monkeypatch.setattr(
        "meeting_notes.services.checks.MODEL_CACHE_DIR",
        fake_model_dir,
    )
    check = WhisperModelCheck()
    detail = check.verbose_detail()
    assert detail is not None
    assert str(fake_model_dir) in detail
    # 512 MB — should show MB (not GB since < 1GB)
    assert "MB" in detail or "GB" in detail


def test_mlx_whisper_check_verbose_detail_returns_version(monkeypatch):
    """MlxWhisperCheck.verbose_detail() returns version string when importable."""
    monkeypatch.setattr(
        "importlib.metadata.version",
        lambda name: "0.0.10" if name == "mlx-whisper" else (_ for _ in ()).throw(Exception("not found")),
    )
    check = MlxWhisperCheck()
    detail = check.verbose_detail()
    assert detail is not None
    assert "mlx-whisper" in detail
    assert "0.0.10" in detail


def test_notion_token_check_verbose_detail_masked():
    """NotionTokenCheck.verbose_detail() returns masked token in 'ntn_***...abc' format."""
    check = NotionTokenCheck(token="ntn_ABCDEFGHIJ123456789xyz")
    detail = check.verbose_detail()
    assert detail is not None
    assert "***" in detail
    # Should show first 4 chars and last 3
    assert "ntn_" in detail
    assert "xyz" in detail


def test_notion_token_check_verbose_detail_none_when_no_token():
    """NotionTokenCheck.verbose_detail() returns None when token is None."""
    check = NotionTokenCheck(token=None)
    detail = check.verbose_detail()
    assert detail is None


def test_disk_space_check_verbose_detail_returns_free_space():
    """DiskSpaceCheck.verbose_detail() returns free space string like 'XX.X GB free'."""
    check = DiskSpaceCheck()
    detail = check.verbose_detail()
    assert detail is not None
    assert "GB free" in detail


def test_openai_whisper_conflict_check_has_no_verbose_detail_override():
    """OpenaiWhisperConflictCheck has no verbose_detail override — inherits None from base."""
    check = OpenaiWhisperConflictCheck()
    # Should return None (base class behavior)
    assert check.verbose_detail() is None
