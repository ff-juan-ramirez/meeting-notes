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
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    result = get_config_dir()
    assert str(result).endswith(".config/meeting-notes")


def test_get_config_dir_xdg_override(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert get_config_dir() == tmp_path / "meeting-notes"


def test_get_data_dir_default(monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    result = get_data_dir()
    assert str(result).endswith(".local/share/meeting-notes")


def test_get_data_dir_xdg_override(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert get_data_dir() == tmp_path / "meeting-notes"


def test_ensure_dirs_creates_all(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    ensure_dirs()
    assert (tmp_path / "config" / "meeting-notes").exists()
    assert (tmp_path / "data" / "meeting-notes" / "recordings").exists()
    assert (tmp_path / "data" / "meeting-notes" / "transcripts").exists()
    assert (tmp_path / "data" / "meeting-notes" / "notes").exists()
    assert (tmp_path / "data" / "meeting-notes" / "metadata").exists()


def test_recording_path_format(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = get_recording_path()
    assert re.match(r"\d{8}-\d{6}-[a-f0-9]{8}\.wav", path.name)
