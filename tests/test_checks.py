"""Unit tests for pyannote-related health checks (Phase 1)."""
import pytest

from meeting_notes.core.health_check import CheckResult, CheckStatus


@pytest.mark.skip(reason="Wave 0 stub — implementation pending")
def test_pyannote_check_error():
    """PyannoteCheck returns ERROR when pyannote.audio is not importable."""
    from meeting_notes.services.checks import PyannoteCheck
    # Will mock builtins.__import__ to raise ImportError for pyannote.audio
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation pending")
def test_hf_token_check_warning_no_token():
    """HuggingFaceTokenCheck returns WARNING when token is None."""
    from meeting_notes.services.checks import HuggingFaceTokenCheck
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation pending")
def test_pyannote_model_check_warning(tmp_path):
    """PyannoteModelCheck returns WARNING when model cache dir does not exist."""
    from meeting_notes.services.checks import PyannoteModelCheck
    pass
