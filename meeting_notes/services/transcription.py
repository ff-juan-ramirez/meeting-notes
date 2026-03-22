"""Transcription service: mlx-whisper wrapper with language handling, duration estimate, and spinner."""
import threading
import time
from pathlib import Path
from typing import Any, Callable

import mlx_whisper
from rich.console import Console
from rich.live import Live
from rich.text import Text

from meeting_notes.core.config import Config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BYTES_PER_SECOND = 16000 * 2  # 32000 — 16kHz mono s16le
WAV_HEADER_BYTES = 44
WARN_DURATION_SECONDS = 90 * 60  # 5400
WARN_WORD_COUNT = 50
MODEL_REPO = "mlx-community/whisper-large-v3-turbo"

_console = Console()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transcribe_audio(wav_path: Path, config: Config) -> str:
    """Run mlx-whisper on a WAV file. Returns transcript text.

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
    return result["text"]


def estimate_wav_duration_seconds(wav_path: Path) -> float:
    """Estimate duration of a 16kHz mono s16le WAV file from its file size.

    Formula: (file_size - WAV_HEADER_BYTES) / BYTES_PER_SECOND
    Returns 0.0 for files smaller than the WAV header.
    """
    size = wav_path.stat().st_size
    audio_bytes = max(0, size - WAV_HEADER_BYTES)
    return audio_bytes / BYTES_PER_SECOND


def run_with_spinner(fn: Callable[[], Any], message: str) -> Any:
    """Run fn() in a background thread while showing a Rich spinner with elapsed time.

    Returns the result of fn(). Re-raises any exception raised by fn() in the
    calling thread.
    """
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
