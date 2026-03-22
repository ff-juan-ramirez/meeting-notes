import os
import pytest
from pathlib import Path

from meeting_notes.core.state import (
    write_state,
    read_state,
    clear_state,
    check_for_stale_session,
)


def test_write_state_creates_file(tmp_path):
    state_path = tmp_path / "state.json"
    write_state(state_path, {"session_id": "abc", "pid": 1234})
    assert state_path.exists()


def test_atomic_write_uses_temp_replace(tmp_path):
    state_path = tmp_path / "state.json"
    write_state(state_path, {"key": "value"})
    # Temp file should be gone after atomic replace
    assert not (tmp_path / "state.tmp").exists()
    assert state_path.exists()


def test_read_state_returns_dict(tmp_path):
    state_path = tmp_path / "state.json"
    data = {"session_id": "xyz", "pid": 5678}
    write_state(state_path, data)
    result = read_state(state_path)
    assert result == data


def test_read_state_missing_file(tmp_path):
    result = read_state(tmp_path / "nonexistent.json")
    assert result is None


def test_stale_pid_detection_dead_process():
    state = {"pid": 99999999}
    assert check_for_stale_session(state) == False


def test_stale_pid_detection_live_process():
    state = {"pid": os.getpid()}
    assert check_for_stale_session(state) == True


def test_stale_pid_detection_no_pid():
    assert check_for_stale_session({}) == False


def test_clear_state_removes_file(tmp_path):
    state_path = tmp_path / "state.json"
    write_state(state_path, {"key": "val"})
    assert state_path.exists()
    clear_state(state_path)
    assert not state_path.exists()
