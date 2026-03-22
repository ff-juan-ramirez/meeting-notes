import pytest
from pathlib import Path


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Temporary XDG_CONFIG_HOME for isolated config tests."""
    config_dir = tmp_path / ".config" / "meeting-notes"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Temporary XDG_DATA_HOME for isolated data tests."""
    data_dir = tmp_path / ".local" / "share" / "meeting-notes"
    data_dir.mkdir(parents=True)
    return data_dir


@pytest.fixture
def tmp_state_file(tmp_config_dir):
    """Path for a temporary state.json file."""
    return tmp_config_dir / "state.json"
