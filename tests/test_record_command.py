import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from meeting_notes.cli.commands.record import record, stop
from meeting_notes.core.state import write_state, read_state


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def state_path(tmp_path):
    return tmp_path / "state.json"


@pytest.fixture
def config_path(tmp_path):
    return tmp_path / "config.json"


def test_record_creates_session(runner, tmp_path, state_path, config_path):
    """meet record writes state.json with session_id, pid, output_path."""
    mock_proc = MagicMock()
    mock_proc.pid = 99001
    output = Path("/tmp/test-recording.wav")

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record._get_config_path", return_value=config_path):
            with patch("meeting_notes.cli.commands.record.start_recording", return_value=(mock_proc, output)):
                result = runner.invoke(record, obj={"quiet": False})

    assert result.exit_code == 0
    state = read_state(state_path)
    assert state is not None
    assert "session_id" in state
    assert "pid" in state
    assert "output_path" in state
    assert state["pid"] == 99001


def test_record_fails_if_already_recording(runner, tmp_path, state_path, config_path):
    """meet record exits with error when live PID already in state."""
    # Write state with current process PID (guaranteed live)
    write_state(state_path, {"session_id": "existing", "pid": os.getpid(), "output_path": "/tmp/old.wav"})

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record._get_config_path", return_value=config_path):
            result = runner.invoke(record, obj={"quiet": False})

    assert result.exit_code != 0
    assert "Already recording" in result.output


def test_record_clears_stale_session(runner, tmp_path, state_path, config_path):
    """meet record clears stale state and starts new session when PID is dead."""
    # Write state with dead PID
    write_state(state_path, {"session_id": "old", "pid": 99999999, "output_path": "/tmp/old.wav"})

    mock_proc = MagicMock()
    mock_proc.pid = 99002
    output = Path("/tmp/new-recording.wav")

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record._get_config_path", return_value=config_path):
            with patch("meeting_notes.cli.commands.record.start_recording", return_value=(mock_proc, output)):
                result = runner.invoke(record, obj={"quiet": False})

    assert result.exit_code == 0
    state = read_state(state_path)
    assert state is not None
    assert state["session_id"] != "old"


def test_stop_terminates_ffmpeg(runner, tmp_path, state_path):
    """meet stop reads PID and calls stop_recording."""
    write_state(state_path, {"session_id": "abc", "pid": 99003, "output_path": str(tmp_path / "rec.wav")})

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record.stop_recording") as mock_stop:
            with patch("meeting_notes.cli.commands.record.get_data_dir", return_value=tmp_path):
                result = runner.invoke(stop, obj={"quiet": False})

    assert result.exit_code == 0
    assert mock_stop.called


def test_stop_clears_state(runner, tmp_path, state_path):
    """meet stop clears state.json after stopping."""
    write_state(state_path, {"session_id": "abc", "pid": 99003, "output_path": str(tmp_path / "rec.wav")})

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record.stop_recording"):
            with patch("meeting_notes.cli.commands.record.get_data_dir", return_value=tmp_path):
                result = runner.invoke(stop, obj={"quiet": False})

    assert result.exit_code == 0
    assert not state_path.exists()


def test_stop_no_active_recording(runner, tmp_path, state_path):
    """meet stop prints error when no active recording session."""
    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        result = runner.invoke(stop, obj={"quiet": False})

    assert "No active recording" in result.output


def test_stop_writes_duration_metadata(runner, tmp_path, state_path):
    """meet stop writes duration_seconds to metadata/{stem}.json."""
    start_time = datetime.now(timezone.utc) - timedelta(seconds=300)
    write_state(state_path, {
        "session_id": "abc",
        "pid": 99003,
        "output_path": str(tmp_path / "recordings" / "20260322-143000-abc12345.wav"),
        "start_time": start_time.isoformat(),
    })
    metadata_dir = tmp_path / "metadata"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record.stop_recording"):
            with patch("meeting_notes.cli.commands.record.get_data_dir", return_value=tmp_path):
                result = runner.invoke(stop, obj={"quiet": False})

    assert result.exit_code == 0
    metadata_path = metadata_dir / "20260322-143000-abc12345.json"
    meta = read_state(metadata_path)
    assert meta is not None
    assert "duration_seconds" in meta
    assert 298 <= meta["duration_seconds"] <= 302  # ~300s with tolerance
