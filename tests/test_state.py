import os
import pytest
from pathlib import Path
from meeting_notes.core.state import write_state, read_state, clear_state, check_for_stale_session


def test_write_state_creates_file(tmp_state_file):
    """write_state creates state.json."""
    data = {"session_id": "abc123", "pid": 1234}
    write_state(tmp_state_file, data)
    assert tmp_state_file.exists()


def test_atomic_write_uses_temp_replace(tmp_state_file):
    """Temp file used then replaced (no .tmp file remains after write)."""
    data = {"session_id": "abc123"}
    write_state(tmp_state_file, data)
    tmp_file = tmp_state_file.with_suffix(".tmp")
    assert not tmp_file.exists()


def test_read_state_returns_dict(tmp_state_file):
    """read_state returns the written dict."""
    data = {"session_id": "abc123", "pid": 1234}
    write_state(tmp_state_file, data)
    result = read_state(tmp_state_file)
    assert result == data


def test_read_state_missing_file(tmp_path):
    """Returns None for missing file."""
    result = read_state(tmp_path / "nonexistent.json")
    assert result is None


def test_stale_pid_detection_dead_process():
    """check_for_stale_session returns False for dead PID."""
    state = {"pid": 99999999}
    assert check_for_stale_session(state) is False


def test_stale_pid_detection_live_process():
    """check_for_stale_session returns True for live PID."""
    state = {"pid": os.getpid()}
    assert check_for_stale_session(state) is True


def test_stale_pid_detection_no_pid():
    """check_for_stale_session returns False when no PID in state."""
    assert check_for_stale_session({}) is False


def test_clear_state_removes_file(tmp_state_file):
    """write state, clear it, assert file gone."""
    write_state(tmp_state_file, {"key": "value"})
    assert tmp_state_file.exists()
    clear_state(tmp_state_file)
    assert not tmp_state_file.exists()
