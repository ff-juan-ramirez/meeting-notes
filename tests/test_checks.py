"""Tests for pyannote health checks added in plan 01-02."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# PyannoteCheck tests
# ---------------------------------------------------------------------------

def test_pyannote_check_error(monkeypatch):
    """PyannoteCheck returns ERROR when pyannote.audio is not importable."""
    from meeting_notes.services.checks import PyannoteCheck
    from meeting_notes.core.health_check import CheckStatus

    # Simulate pyannote.audio not installed
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "pyannote.audio" or name.startswith("pyannote"):
            raise ImportError("No module named 'pyannote'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    result = PyannoteCheck().check()
    assert result.status == CheckStatus.ERROR
    assert "pyannote" in result.message.lower()


def test_pyannote_check_ok(monkeypatch):
    """PyannoteCheck returns OK when pyannote.audio is importable."""
    from meeting_notes.services.checks import PyannoteCheck
    from meeting_notes.core.health_check import CheckStatus

    fake_pyannote = MagicMock()

    with patch.dict("sys.modules", {"pyannote": fake_pyannote, "pyannote.audio": fake_pyannote}):
        result = PyannoteCheck().check()

    assert result.status == CheckStatus.OK


# ---------------------------------------------------------------------------
# HuggingFaceTokenCheck tests
# ---------------------------------------------------------------------------

def test_hf_token_check_warning_no_token():
    """HuggingFaceTokenCheck returns WARNING when token is None."""
    from meeting_notes.services.checks import HuggingFaceTokenCheck
    from meeting_notes.core.health_check import CheckStatus

    result = HuggingFaceTokenCheck(token=None).check()
    assert result.status == CheckStatus.WARNING
    assert "token" in result.message.lower() or "not configured" in result.message.lower()


def test_hf_token_check_ok_valid_token(monkeypatch):
    """HuggingFaceTokenCheck returns OK when HfApi().whoami succeeds."""
    from meeting_notes.services.checks import HuggingFaceTokenCheck
    from meeting_notes.core.health_check import CheckStatus

    mock_api = MagicMock()
    mock_api.return_value.whoami.return_value = {"name": "testuser"}

    with patch("meeting_notes.services.checks.HfApi", mock_api):
        result = HuggingFaceTokenCheck(token="hf_test123").check()

    assert result.status == CheckStatus.OK


def test_hf_token_check_warning_invalid_token(monkeypatch):
    """HuggingFaceTokenCheck returns WARNING when HfApi().whoami raises."""
    from meeting_notes.services.checks import HuggingFaceTokenCheck
    from meeting_notes.core.health_check import CheckStatus

    mock_api = MagicMock()
    mock_api.return_value.whoami.side_effect = Exception("Unauthorized")

    with patch("meeting_notes.services.checks.HfApi", mock_api):
        result = HuggingFaceTokenCheck(token="hf_bad_token").check()

    assert result.status == CheckStatus.WARNING


def test_hf_token_check_verbose_detail_masked():
    """verbose_detail() returns masked token string."""
    from meeting_notes.services.checks import HuggingFaceTokenCheck

    check = HuggingFaceTokenCheck(token="hf_test1234567")
    detail = check.verbose_detail()
    assert detail is not None
    assert "***" in detail


def test_hf_token_check_verbose_detail_none_when_no_token():
    """verbose_detail() returns None when token is None."""
    from meeting_notes.services.checks import HuggingFaceTokenCheck

    check = HuggingFaceTokenCheck(token=None)
    assert check.verbose_detail() is None


# ---------------------------------------------------------------------------
# PyannoteModelCheck tests
# ---------------------------------------------------------------------------

def test_pyannote_model_check_warning(tmp_path, monkeypatch):
    """PyannoteModelCheck returns WARNING when model cache dir does not exist."""
    from meeting_notes.services import checks as checks_module
    from meeting_notes.core.health_check import CheckStatus

    # Point cache to a non-existent dir
    monkeypatch.setattr(checks_module, "PYANNOTE_DIARIZATION_CACHE", tmp_path / "nonexistent")

    from meeting_notes.services.checks import PyannoteModelCheck
    result = PyannoteModelCheck().check()
    assert result.status == CheckStatus.WARNING
    assert "not cached" in result.message.lower() or "download" in result.message.lower()


def test_pyannote_model_check_ok(tmp_path, monkeypatch):
    """PyannoteModelCheck returns OK when model cache dir exists."""
    from meeting_notes.services import checks as checks_module
    from meeting_notes.core.health_check import CheckStatus

    cache_dir = tmp_path / "models--pyannote--speaker-diarization-3.1"
    cache_dir.mkdir()
    monkeypatch.setattr(checks_module, "PYANNOTE_DIARIZATION_CACHE", cache_dir)

    from meeting_notes.services.checks import PyannoteModelCheck
    result = PyannoteModelCheck().check()
    assert result.status == CheckStatus.OK


# ---------------------------------------------------------------------------
# PYANNOTE_DIARIZATION_CACHE constant
# ---------------------------------------------------------------------------

def test_pyannote_diarization_cache_constant():
    """PYANNOTE_DIARIZATION_CACHE constant is defined in checks module."""
    from meeting_notes.services import checks
    assert hasattr(checks, "PYANNOTE_DIARIZATION_CACHE")
    assert "pyannote" in str(checks.PYANNOTE_DIARIZATION_CACHE).lower()
