import pytest
from pathlib import Path

from meeting_notes.core.config import Config, AudioConfig, NotionConfig


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


def test_notion_config_defaults():
    nc = NotionConfig()
    assert nc.token is None
    assert nc.parent_page_id is None


def test_config_has_notion_field():
    c = Config()
    assert hasattr(c, "notion")
    assert isinstance(c.notion, NotionConfig)


def test_config_load_with_notion_section(tmp_path):
    path = tmp_path / "config.json"
    import json
    data = {
        "version": 1,
        "audio": {"system_device_index": 1, "microphone_device_index": 2},
        "whisper": {"language": None},
        "notion": {"token": "secret_abc", "parent_page_id": "page123"},
    }
    path.write_text(json.dumps(data))
    config = Config.load(path)
    assert config.notion.token == "secret_abc"
    assert config.notion.parent_page_id == "page123"


def test_config_load_without_notion_section(tmp_path):
    path = tmp_path / "config.json"
    import json
    data = {"version": 1, "audio": {}, "whisper": {}}
    path.write_text(json.dumps(data))
    config = Config.load(path)
    assert config.notion.token is None
    assert config.notion.parent_page_id is None


def test_config_save_round_trip_with_notion(tmp_path):
    path = tmp_path / "config.json"
    c = Config()
    c.notion = NotionConfig(token="x", parent_page_id="y")
    c.save(path)
    loaded = Config.load(path)
    assert loaded.notion.token == "x"
    assert loaded.notion.parent_page_id == "y"
