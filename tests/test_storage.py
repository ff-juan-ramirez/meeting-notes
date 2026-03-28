import os
import re
import pytest
from pathlib import Path

from meeting_notes.core.storage import (
    get_config_dir,
    get_data_dir,
    ensure_dirs,
    get_recording_path,
    slugify,
    get_recording_path_with_slug,
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


# --- slugify() tests ---

def test_slugify_basic():
    assert slugify("Weekly 1:1 with Juan") == "weekly-1-1-with-juan"


def test_slugify_unicode():
    # Accented chars should become their ASCII equivalents
    result = slugify("Reunion equipo espanol")
    assert result == "reunion-equipo-espanol"
    # Verify accented variant also normalizes
    result2 = slugify("Réunion équipe español")
    assert result2 == "reunion-equipe-espanol"


def test_slugify_colons():
    assert slugify("1:1") == "1-1"


def test_slugify_slashes():
    assert slugify("Q1/Q2 Planning") == "q1-q2-planning"


def test_slugify_whitespace_runs():
    assert slugify("  too   many   spaces  ") == "too-many-spaces"


def test_slugify_leading_trailing_hyphens():
    assert slugify("---hello---") == "hello"


def test_slugify_max_length():
    result = slugify("a" * 100)
    assert len(result) <= 80
    assert not result.endswith("-")


def test_slugify_empty_string():
    assert slugify("") == "untitled"


def test_slugify_all_punctuation():
    assert slugify("!!!@@@###") == "untitled"


def test_slugify_numbers_only():
    assert slugify("123") == "123"


# --- get_recording_path_with_slug() tests ---

def test_recording_path_with_slug_format(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = get_recording_path_with_slug("Weekly 1:1")
    assert re.match(r"weekly-1-1-\d{8}-\d{6}-[a-f0-9]{8}\.wav", path.name)


def test_recording_path_with_slug_in_recordings_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = get_recording_path_with_slug("Test Meeting")
    assert path.parent.name == "recordings"


def test_recording_path_with_slug_custom_storage(tmp_path):
    path = get_recording_path_with_slug("Test", storage_path=str(tmp_path))
    assert str(path).startswith(str(tmp_path))


def test_recording_path_with_slug_is_wav(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = get_recording_path_with_slug("Demo Session")
    assert path.suffix == ".wav"


def test_unnamed_path_unchanged(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = get_recording_path()
    assert re.match(r"\d{8}-\d{6}-[a-f0-9]{8}\.wav", path.name)
