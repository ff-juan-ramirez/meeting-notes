import pytest


@pytest.mark.skip(reason="Wave 0 stub")
def test_get_config_dir_default():
    """Returns ~/.config/meeting-notes when XDG_CONFIG_HOME not set."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_get_config_dir_xdg_override(tmp_path):
    """Honors XDG_CONFIG_HOME env var."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_get_data_dir_default():
    """Returns ~/.local/share/meeting-notes."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_get_data_dir_xdg_override(tmp_path):
    """Honors XDG_DATA_HOME env var."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_ensure_dirs_creates_all(tmp_path):
    """Creates recordings, transcripts, notes, metadata subdirs."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_recording_path_format(tmp_path):
    """Path matches {timestamp}-{uuid}.wav pattern."""
    pass
