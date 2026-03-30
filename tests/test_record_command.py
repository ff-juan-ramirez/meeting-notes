import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from meeting_notes.cli.commands.record import record, stop
from meeting_notes.core.state import write_state, read_state
from meeting_notes.services.audio import start_recording


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


# ---------------------------------------------------------------------------
# Task 1 tests: Named record (RECORD-01, RECORD-02, RECORD-03)
# ---------------------------------------------------------------------------

def test_record_named_session(runner, tmp_path, state_path, config_path):
    """meet record 'Team Standup' stores recording_name, recording_slug and slug-prefixed output path."""
    mock_proc = MagicMock()
    mock_proc.pid = 99010
    output = tmp_path / "recordings" / "team-standup-20260328-100000-abc12345.wav"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record._get_config_path", return_value=config_path):
            with patch("meeting_notes.cli.commands.record.start_recording", return_value=(mock_proc, output)):
                result = runner.invoke(record, ["Team Standup"], obj={"quiet": False})

    assert result.exit_code == 0
    state = read_state(state_path)
    assert state is not None
    assert state.get("recording_name") == "Team Standup"
    assert state.get("recording_slug", "").startswith("team-standup")
    assert "team-standup" in state.get("output_path", "")


def test_record_named_session_strips_whitespace(runner, tmp_path, state_path, config_path):
    """meet record '  My Meeting  ' strips surrounding whitespace from recording_name (D-02)."""
    mock_proc = MagicMock()
    mock_proc.pid = 99011
    output = tmp_path / "recordings" / "my-meeting-20260328-100000-abc12345.wav"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record._get_config_path", return_value=config_path):
            with patch("meeting_notes.cli.commands.record.start_recording", return_value=(mock_proc, output)):
                result = runner.invoke(record, ["  My Meeting  "], obj={"quiet": False})

    assert result.exit_code == 0
    state = read_state(state_path)
    assert state is not None
    assert state.get("recording_name") == "My Meeting"


def test_record_unnamed_session_unchanged(runner, tmp_path, state_path, config_path):
    """meet record (no name arg) writes state WITHOUT recording_name or recording_slug — backward compat."""
    mock_proc = MagicMock()
    mock_proc.pid = 99012
    output = tmp_path / "recordings" / "20260328-100000-abc12345.wav"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record._get_config_path", return_value=config_path):
            with patch("meeting_notes.cli.commands.record.start_recording", return_value=(mock_proc, output)):
                result = runner.invoke(record, [], obj={"quiet": False})

    assert result.exit_code == 0
    state = read_state(state_path)
    assert state is not None
    assert "recording_name" not in state
    assert "recording_slug" not in state


def test_record_named_output_message(runner, tmp_path, state_path, config_path):
    """meet record 'Team Standup' output contains 'Recording started: \"Team Standup\"' (D-01)."""
    mock_proc = MagicMock()
    mock_proc.pid = 99013
    output = tmp_path / "recordings" / "team-standup-20260328-100000-abc12345.wav"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record._get_config_path", return_value=config_path):
            with patch("meeting_notes.cli.commands.record.start_recording", return_value=(mock_proc, output)):
                result = runner.invoke(record, ["Team Standup"], obj={"quiet": False})

    assert result.exit_code == 0
    assert 'Recording started:' in result.output
    assert 'Team Standup' in result.output


def test_start_recording_with_output_path(tmp_path):
    """start_recording(config, output_path=some_path) uses the provided path, not a generated one."""
    preset_path = tmp_path / "recordings" / "preset-recording.wav"

    config = MagicMock()
    config.storage_path = str(tmp_path)
    config.audio.system_device_index = 1
    config.audio.microphone_device_index = 2

    mock_proc = MagicMock()
    mock_proc.pid = 99014

    with patch("meeting_notes.services.audio.ensure_dirs"):
        with patch("meeting_notes.services.audio.start_ffmpeg", return_value=mock_proc):
            proc, returned_path = start_recording(config, output_path=preset_path)

    assert returned_path == preset_path
    assert proc.pid == 99014


def test_start_recording_without_output_path(tmp_path):
    """start_recording(config) still generates path via get_recording_path() — no regression."""
    config = MagicMock()
    config.storage_path = str(tmp_path)
    config.audio.system_device_index = 1
    config.audio.microphone_device_index = 2

    mock_proc = MagicMock()
    mock_proc.pid = 99015
    generated_path = tmp_path / "recordings" / "20260328-100000-abc12345.wav"

    with patch("meeting_notes.services.audio.ensure_dirs"):
        with patch("meeting_notes.services.audio.get_recording_path", return_value=generated_path):
            with patch("meeting_notes.services.audio.start_ffmpeg", return_value=mock_proc):
                proc, returned_path = start_recording(config)

    assert returned_path == generated_path
    assert proc.pid == 99015


# ---------------------------------------------------------------------------
# Task 2 tests: meet stop propagates recording_name/slug to metadata (RECORD-04)
# ---------------------------------------------------------------------------

def test_stop_propagates_name_to_metadata(runner, tmp_path, state_path):
    """meet stop copies recording_name and recording_slug from state to metadata JSON."""
    start_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    wav_name = "team-standup-20260328-143000-abc12345.wav"
    write_state(state_path, {
        "session_id": "abc",
        "pid": 99003,
        "output_path": str(tmp_path / "recordings" / wav_name),
        "start_time": start_time.isoformat(),
        "recording_name": "Team Standup",
        "recording_slug": "team-standup",
    })
    metadata_dir = tmp_path / "metadata"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record.stop_recording"):
            with patch("meeting_notes.cli.commands.record.get_data_dir", return_value=tmp_path):
                result = runner.invoke(stop, obj={"quiet": False})

    assert result.exit_code == 0
    metadata_path = metadata_dir / wav_name.replace(".wav", ".json")
    meta = read_state(metadata_path)
    assert meta is not None
    assert meta["recording_name"] == "Team Standup"
    assert meta["recording_slug"] == "team-standup"


def test_stop_unnamed_session_no_name_in_metadata(runner, tmp_path, state_path):
    """meet stop does NOT add recording_name/slug to metadata for unnamed sessions."""
    start_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    wav_name = "20260328-143000-abc12345.wav"
    write_state(state_path, {
        "session_id": "abc",
        "pid": 99003,
        "output_path": str(tmp_path / "recordings" / wav_name),
        "start_time": start_time.isoformat(),
    })
    metadata_dir = tmp_path / "metadata"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record.stop_recording"):
            with patch("meeting_notes.cli.commands.record.get_data_dir", return_value=tmp_path):
                result = runner.invoke(stop, obj={"quiet": False})

    assert result.exit_code == 0
    metadata_path = metadata_dir / wav_name.replace(".wav", ".json")
    meta = read_state(metadata_path)
    assert meta is not None
    assert "recording_name" not in meta
    assert "recording_slug" not in meta


def test_stop_named_session_still_writes_duration(runner, tmp_path, state_path):
    """meet stop writes both duration_seconds AND recording_name for named sessions."""
    start_time = datetime.now(timezone.utc) - timedelta(seconds=300)
    wav_name = "team-standup-20260328-143000-abc12345.wav"
    write_state(state_path, {
        "session_id": "abc",
        "pid": 99003,
        "output_path": str(tmp_path / "recordings" / wav_name),
        "start_time": start_time.isoformat(),
        "recording_name": "Team Standup",
        "recording_slug": "team-standup",
    })
    metadata_dir = tmp_path / "metadata"

    with patch("meeting_notes.cli.commands.record._get_state_path", return_value=state_path):
        with patch("meeting_notes.cli.commands.record.stop_recording"):
            with patch("meeting_notes.cli.commands.record.get_data_dir", return_value=tmp_path):
                result = runner.invoke(stop, obj={"quiet": False})

    assert result.exit_code == 0
    metadata_path = metadata_dir / wav_name.replace(".wav", ".json")
    meta = read_state(metadata_path)
    assert meta is not None
    assert "duration_seconds" in meta
    assert 298 <= meta["duration_seconds"] <= 302
    assert meta["recording_name"] == "Team Standup"
