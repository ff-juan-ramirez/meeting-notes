import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from meeting_notes.services.audio import build_ffmpeg_command


def test_build_ffmpeg_command_structure():
    """build_ffmpeg_command returns a list starting with 'ffmpeg' ending with output path."""
    cmd = build_ffmpeg_command(1, 2, "/tmp/out.wav")
    assert isinstance(cmd, list)
    assert cmd[0] == "ffmpeg"
    assert cmd[-1] == "/tmp/out.wav"


def test_build_ffmpeg_command_uses_indices():
    """build_ffmpeg_command uses device indices :1 and :2, not device names."""
    cmd = build_ffmpeg_command(1, 2, "/tmp/out.wav")
    joined = " ".join(cmd)
    assert ":1" in joined
    assert ":2" in joined


def test_build_ffmpeg_command_has_aresample():
    """build_ffmpeg_command includes aresample=16000 filter."""
    cmd = build_ffmpeg_command(1, 2, "/tmp/out.wav")
    assert any("aresample=16000" in arg for arg in cmd)


def test_build_ffmpeg_command_has_amix():
    """build_ffmpeg_command includes amix filter to mix both audio sources."""
    cmd = build_ffmpeg_command(1, 2, "/tmp/out.wav")
    assert any("amix" in arg for arg in cmd)


def test_build_ffmpeg_command_wav_output():
    """build_ffmpeg_command uses pcm_s16le codec and .wav output."""
    cmd = build_ffmpeg_command(1, 2, "/tmp/out.wav")
    assert any("pcm_s16le" in arg for arg in cmd)
    assert cmd[-1].endswith(".wav")
