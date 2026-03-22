import pytest
from pathlib import Path

from meeting_notes.core.config import Config, AudioConfig


def test_config_default_values():
    c = Config()
    assert c.version == 1
    assert c.audio.system_device_index == 1
    assert c.audio.microphone_device_index == 2


def test_config_save_and_load(tmp_path):
    path = tmp_path / "config.json"
    c = Config()
    c.save(path)
    loaded = Config.load(path)
    assert loaded.version == c.version
    assert loaded.audio.system_device_index == c.audio.system_device_index
    assert loaded.audio.microphone_device_index == c.audio.microphone_device_index


def test_config_load_missing_file(tmp_path):
    c = Config.load(tmp_path / "nope.json")
    assert c.version == 1
    assert c.audio.system_device_index == 1


def test_config_save_creates_parent_dirs(tmp_path):
    path = tmp_path / "a" / "b" / "config.json"
    c = Config()
    c.save(path)
    assert path.exists()
