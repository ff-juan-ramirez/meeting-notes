import os
import signal
import subprocess
from unittest.mock import MagicMock, patch, call

import pytest

from meeting_notes.core.process_manager import start_ffmpeg, stop_gracefully


def test_start_ffmpeg_new_session():
    """start_ffmpeg calls subprocess.Popen with start_new_session=True."""
    cmd = ["ffmpeg", "-version"]
    mock_proc = MagicMock()
    with patch("meeting_notes.core.process_manager.subprocess.Popen", return_value=mock_proc) as mock_popen:
        result = start_ffmpeg(cmd)
        mock_popen.assert_called_once_with(
            cmd,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert result is mock_proc


def test_stop_gracefully_sends_sigterm():
    """stop_gracefully sends SIGTERM to the process group."""
    mock_proc = MagicMock()
    mock_proc.pid = 12345

    with patch("meeting_notes.core.process_manager.os.getpgid", return_value=12345) as mock_getpgid:
        with patch("meeting_notes.core.process_manager.os.killpg") as mock_killpg:
            stop_gracefully(mock_proc)
            mock_killpg.assert_any_call(12345, signal.SIGTERM)


def test_stop_gracefully_escalates_to_sigkill():
    """stop_gracefully sends SIGKILL when SIGTERM times out."""
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    # First call (with timeout) raises, second call (no timeout) succeeds
    mock_proc.wait.side_effect = [subprocess.TimeoutExpired(cmd="ffmpeg", timeout=5), None]

    with patch("meeting_notes.core.process_manager.os.getpgid", return_value=12345):
        with patch("meeting_notes.core.process_manager.os.killpg") as mock_killpg:
            stop_gracefully(mock_proc)
            calls = mock_killpg.call_args_list
            sigkill_calls = [c for c in calls if c == call(12345, signal.SIGKILL)]
            assert len(sigkill_calls) >= 1


def test_stop_gracefully_handles_already_dead():
    """stop_gracefully handles ProcessLookupError (process already dead)."""
    mock_proc = MagicMock()
    mock_proc.pid = 12345

    with patch("meeting_notes.core.process_manager.os.getpgid", return_value=12345):
        with patch("meeting_notes.core.process_manager.os.killpg", side_effect=ProcessLookupError):
            # Should not raise
            stop_gracefully(mock_proc)
