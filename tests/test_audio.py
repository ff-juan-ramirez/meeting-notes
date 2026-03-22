import pytest


@pytest.mark.skip(reason="Wave 0 stub")
def test_build_ffmpeg_command_structure():
    """Returns list with correct ffmpeg args."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_build_ffmpeg_command_uses_indices():
    """Command contains \":1\" and \":2\" (not device names)."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_build_ffmpeg_command_has_aresample():
    """Command contains \"aresample=16000\"."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_build_ffmpeg_command_has_amix():
    """Command contains \"amix\"."""
    pass


@pytest.mark.skip(reason="Wave 0 stub")
def test_build_ffmpeg_command_wav_output():
    """Command contains \"pcm_s16le\" and output ends with .wav."""
    pass
