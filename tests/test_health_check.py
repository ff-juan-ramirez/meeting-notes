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


from meeting_notes.services.checks import MlxWhisperCheck, OllamaModelCheck, OllamaRunningCheck, WhisperModelCheck


def test_mlx_whisper_check_ok():
    """MlxWhisperCheck returns OK when mlx_whisper is importable."""
    result = MlxWhisperCheck().check()
    assert result.status == CheckStatus.OK
    assert "mlx-whisper importable" in result.message


def test_mlx_whisper_check_error(monkeypatch):
    """MlxWhisperCheck returns ERROR when mlx_whisper cannot be imported."""
    import builtins
    original_import = builtins.__import__
    def mock_import(name, *args, **kwargs):
        if name == "mlx_whisper":
            raise ImportError("No module named 'mlx_whisper'")
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", mock_import)
    result = MlxWhisperCheck().check()
    assert result.status == CheckStatus.ERROR
    assert "not installed" in result.message
    assert result.fix_suggestion == "pip install mlx-whisper"


def test_whisper_model_check_ok(tmp_path, monkeypatch):
    """WhisperModelCheck returns OK when model cache directory exists."""
    fake_cache = tmp_path / "models--mlx-community--whisper-large-v3-turbo"
    fake_cache.mkdir()
    monkeypatch.setattr(
        "meeting_notes.services.checks.MODEL_CACHE_DIR", fake_cache
    )
    result = WhisperModelCheck().check()
    assert result.status == CheckStatus.OK
    assert "Whisper model cached at" in result.message


def test_whisper_model_check_warning(tmp_path, monkeypatch):
    """WhisperModelCheck returns WARNING (not ERROR) when model not cached — per D-08."""
    fake_cache = tmp_path / "nonexistent-model-dir"
    monkeypatch.setattr(
        "meeting_notes.services.checks.MODEL_CACHE_DIR", fake_cache
    )
    result = WhisperModelCheck().check()
    assert result.status == CheckStatus.WARNING  # NOT ERROR — per D-08
    assert "not cached" in result.message
    assert "meet transcribe" in result.fix_suggestion


def test_ollama_running_check_ok(monkeypatch):
    """OllamaRunningCheck returns OK when localhost:11434 responds 200."""
    mock_resp = type("Response", (), {"status_code": 200})()
    monkeypatch.setattr(
        "meeting_notes.services.checks.requests.get",
        lambda *a, **kw: mock_resp,
    )
    result = OllamaRunningCheck().check()
    assert result.status == CheckStatus.OK
    assert "running" in result.message


def test_ollama_running_check_error(monkeypatch):
    """OllamaRunningCheck returns ERROR when Ollama is not reachable."""
    import requests as req
    monkeypatch.setattr(
        "meeting_notes.services.checks.requests.get",
        lambda *a, **kw: (_ for _ in ()).throw(req.exceptions.ConnectionError()),
    )
    result = OllamaRunningCheck().check()
    assert result.status == CheckStatus.ERROR
    assert "not running" in result.message
    assert result.fix_suggestion == "Run: ollama serve"


def test_ollama_model_check_ok(monkeypatch):
    """OllamaModelCheck returns OK when llama3.1:8b in ollama list."""
    mock_result = type("R", (), {
        "stdout": "NAME               ID              SIZE      MODIFIED\nllama3.1:8b        46e0c10c039e    4.9 GB    32 hours ago\n"
    })()
    monkeypatch.setattr(
        "meeting_notes.services.checks.subprocess.run",
        lambda *a, **kw: mock_result,
    )
    result = OllamaModelCheck().check()
    assert result.status == CheckStatus.OK
    assert "llama3.1:8b" in result.message


def test_ollama_model_check_error(monkeypatch):
    """OllamaModelCheck returns ERROR when model not in ollama list."""
    mock_result = type("R", (), {
        "stdout": "NAME               ID              SIZE      MODIFIED\nllama3.2:latest    a80c4f17acd5    2.0 GB    34 hours ago\n"
    })()
    monkeypatch.setattr(
        "meeting_notes.services.checks.subprocess.run",
        lambda *a, **kw: mock_result,
    )
    result = OllamaModelCheck().check()
    assert result.status == CheckStatus.ERROR
    assert "not found" in result.message
    assert result.fix_suggestion == "Run: ollama pull llama3.1:8b"


def test_ollama_model_check_cli_not_found(monkeypatch):
    """OllamaModelCheck returns ERROR when ollama CLI is not installed."""
    def raise_fnf(*a, **kw):
        raise FileNotFoundError("ollama not found")
    monkeypatch.setattr(
        "meeting_notes.services.checks.subprocess.run",
        raise_fnf,
    )
    result = OllamaModelCheck().check()
    assert result.status == CheckStatus.ERROR
    assert "not found" in result.message
    assert "ollama.com" in result.fix_suggestion
