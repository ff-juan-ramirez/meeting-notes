import subprocess
from pathlib import Path

from meeting_notes.core.config import Config
from meeting_notes.core.process_manager import start_ffmpeg, stop_gracefully
from meeting_notes.core.storage import ensure_dirs, get_recording_path, get_config_dir


def build_ffmpeg_command(
    system_idx: int,
    mic_idx: int,
    output_path: str,
) -> list[str]:
    """Build ffmpeg command for two-device avfoundation capture with amix."""
    return [
        "ffmpeg",
        "-f", "avfoundation", "-i", f":{system_idx}",
        "-f", "avfoundation", "-i", f":{mic_idx}",
        "-filter_complex",
        "[0:a]aresample=16000[a0];[1:a]aresample=16000[a1];"
        "[a0][a1]amix=inputs=2:normalize=0[aout]",
        "-map", "[aout]",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        "-y",
        output_path,
    ]


def start_recording(config: Config) -> tuple[subprocess.Popen, Path]:
    """Start a recording session. Returns (process, output_path)."""
    ensure_dirs(config.storage_path)
    output_path = get_recording_path(config.storage_path)
    cmd = build_ffmpeg_command(
        config.audio.system_device_index,
        config.audio.microphone_device_index,
        str(output_path),
    )
    proc = start_ffmpeg(cmd)
    return proc, output_path


def stop_recording(proc: subprocess.Popen) -> None:
    """Stop a recording session gracefully."""
    stop_gracefully(proc)
