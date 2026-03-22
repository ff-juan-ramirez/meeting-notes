import os
import re
import pytest
from pathlib import Path
from meeting_notes.core.storage import (
    get_config_dir,
    get_data_dir,
    ensure_dirs,
    get_recording_path,
)


def test_get_config_dir_default(monkeypatch):
    """Returns ~/.config/meeting-notes when XDG_CONFIG_HOME not set."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    result = get_config_dir()
    assert result == Path.home() / ".config" / "meeting-notes"


def test_get_config_dir_xdg_override(tmp_path, monkeypatch):
    """Honors XDG_CONFIG_HOME env var."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = get_config_dir()
    assert result == tmp_path / "meeting-notes"


def test_get_data_dir_default(monkeypatch):
    """Returns ~/.local/share/meeting-notes."""
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    result = get_data_dir()
    assert result == Path.home() / ".local" / "share" / "meeting-notes"


def test_get_data_dir_xdg_override(tmp_path, monkeypatch):
    """Honors XDG_DATA_HOME env var."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    result = get_data_dir()
    assert result == tmp_path / "meeting-notes"


def test_ensure_dirs_creates_all(tmp_path, monkeypatch):
    """Creates recordings, transcripts, notes, metadata subdirs."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    ensure_dirs()
    data_dir = tmp_path / "data" / "meeting-notes"
    assert (tmp_path / "config" / "meeting-notes").exists()
    assert (data_dir / "recordings").exists()
    assert (data_dir / "transcripts").exists()
    assert (data_dir / "notes").exists()
    assert (data_dir / "metadata").exists()


def test_recording_path_format(tmp_path, monkeypatch):
    """Path matches {timestamp}-{uuid}.wav pattern."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = get_recording_path()
    assert re.match(r"\d{8}-\d{6}-[a-f0-9]{8}\.wav", path.name)
