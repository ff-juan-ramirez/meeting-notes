import pytest


@pytest.mark.skip(reason="Wave 0 stub")
def test_config_default_values():
    """Config() has version=1, audio.system_device_index=1, audio.microphone_device_index=2."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_config_save_and_load(tmp_config_dir):
    """Save to path, load from same path, values match."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_config_load_missing_file(tmp_path):
    """Returns default Config when file doesn't exist."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_config_save_creates_parent_dirs(tmp_path):
    """Save to nested path creates directories."""
    pass
