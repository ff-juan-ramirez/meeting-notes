"""Transcription service: mlx-whisper wrapper with language handling, duration estimate, and spinner."""
import threading
import time
from pathlib import Path
from typing import Any, Callable

import mlx_whisper
from rich.live import Live
from rich.text import Text

from meeting_notes.core.config import Config
from meeting_notes.cli.ui import console as _console

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BYTES_PER_SECOND = 16000 * 2  # 32000 — 16kHz mono s16le
WAV_HEADER_BYTES = 44
WARN_DURATION_SECONDS = 90 * 60  # 5400
WARN_WORD_COUNT = 50
MODEL_REPO = "mlx-community/whisper-large-v3-turbo"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def seconds_to_srt_timestamp(seconds: float) -> str:
    """Convert float seconds to SRT HH:MM:SS,mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segments: list[dict], speaker_map: dict[int, str] | None = None) -> str:
    """Generate SRT subtitle content from Whisper segments.

    Args:
        segments: List of dicts with 'start', 'end', 'text' keys (from mlx_whisper).
        speaker_map: Optional {segment_index: speaker_label} for diarized output (per D-10).

    Returns:
        Complete SRT file content as a string.
    """
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_ts = seconds_to_srt_timestamp(seg["start"])
        end_ts = seconds_to_srt_timestamp(seg["end"])
        text = seg["text"].strip()
        if speaker_map and (i - 1) in speaker_map:
            text = f"{speaker_map[i - 1]}: {text}"
        lines.append(f"{i}\n{start_ts} --> {end_ts}\n{text}\n")
    return "\n".join(lines)


def transcribe_audio(wav_path: Path, config: Config) -> tuple[str, list[dict]]:
    """Run mlx-whisper on a WAV file. Returns (transcript_text, segments).

    When config.whisper.language is None, the language kwarg is omitted entirely
    so mlx-whisper auto-detects. Passing language=None explicitly would cause
    mlx-whisper to default to 'en' instead of auto-detecting.
    """
    decode_opts: dict[str, Any] = {}
    if config.whisper.language is not None:
        decode_opts["language"] = config.whisper.language

    result = mlx_whisper.transcribe(
        str(wav_path),
        path_or_hf_repo=MODEL_REPO,
        **decode_opts,
    )
    return result["text"], result["segments"]


def estimate_wav_duration_seconds(wav_path: Path) -> float:
    """Estimate duration of a 16kHz mono s16le WAV file from its file size.

    Formula: (file_size - WAV_HEADER_BYTES) / BYTES_PER_SECOND
    Returns 0.0 for files smaller than the WAV header.
    """
    size = wav_path.stat().st_size
    audio_bytes = max(0, size - WAV_HEADER_BYTES)
    return audio_bytes / BYTES_PER_SECOND


def run_with_spinner(fn: Callable[[], Any], message: str, quiet: bool = False) -> Any:
    """Run fn() in a background thread while showing a Rich spinner with elapsed time.

    When quiet=True, fn() is called directly in the current thread with no spinner.
    Returns the result of fn(). Re-raises any exception raised by fn() in the
    calling thread.
    """
    if quiet:
        return fn()

    result: dict[str, Any] = {}
    exc_holder: dict[str, BaseException] = {}

    def worker() -> None:
        try:
            result["value"] = fn()
        except Exception as exc:
            exc_holder["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    start = time.time()
    thread.start()

    with Live(console=_console, refresh_per_second=10) as live:
        while thread.is_alive():
            elapsed = time.time() - start
            live.update(Text(f"{message} [{elapsed:.0f}s]"))
            time.sleep(0.1)

    thread.join()

    if "error" in exc_holder:
        raise exc_holder["error"]

    return result["value"]
