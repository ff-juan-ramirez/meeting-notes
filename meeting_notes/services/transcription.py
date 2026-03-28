"""Transcription service: mlx-whisper wrapper with language handling, duration estimate, and spinner."""
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

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


def run_diarization(wav_path: Path, hf_token: str) -> Any:
    """Run pyannote speaker diarization pipeline on a WAV file.

    Args:
        wav_path: Path to mono 16kHz WAV file.
        hf_token: HuggingFace access token for gated model.

    Returns:
        pyannote Annotation object with speaker turns.

    Raises:
        Exception: Any pipeline error (network, auth, model loading).
    """
    # speechbrain 1.0.3 calls torchaudio.list_audio_backends() at import time,
    # but torchaudio 2.9+ removed that API. Provide a no-op shim so speechbrain's
    # backend check succeeds (it just logs a warning when the list is empty).
    # Remove this once speechbrain releases a fix (tracked upstream:
    # https://github.com/speechbrain/speechbrain/issues/3012).
    import torchaudio as _torchaudio
    if not hasattr(_torchaudio, "list_audio_backends"):
        _torchaudio.list_audio_backends = lambda: []  # type: ignore[attr-defined]

    from pyannote.audio import Pipeline  # type: ignore[import]

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )

    # torchcodec (pyannote 4.x audio backend) fails to load on this system because
    # the installed torchcodec .dylib requires a PyTorch symbol not present in
    # torch 2.10.0.  When torchcodec is unavailable, pyannote's io.py leaves
    # AudioDecoder undefined, so passing a file path to the pipeline raises
    # "NameError: name 'AudioDecoder' is not defined".
    #
    # Workaround: pre-load the waveform with soundfile (always available) and
    # pass {"waveform": tensor, "sample_rate": int} to the pipeline.  pyannote's
    # Audio class has an explicit fast-path for this dict format (io.py lines
    # 313-317 and 362-392) that completely bypasses AudioDecoder.
    import soundfile as _sf  # type: ignore[import]
    import torch as _torch

    _audio_data, _sr = _sf.read(str(wav_path), dtype="float32", always_2d=True)
    # soundfile returns (time, channel); pyannote expects (channel, time)
    _waveform = _torch.from_numpy(_audio_data.T)
    audio_input = {"waveform": _waveform, "sample_rate": _sr}

    result = pipeline(audio_input)

    # pyannote 4.x returns a DiarizeOutput dataclass instead of a plain Annotation.
    # DiarizeOutput.exclusive_speaker_diarization is an Annotation with non-overlapping
    # turns — the right choice for mapping speech turns to transcript segments.
    # Unwrap here so all downstream code (assign_speakers_to_segments, transcribe.py
    # speaker_turns loop) can call .itertracks(yield_label=True) without change.
    if hasattr(result, "exclusive_speaker_diarization"):
        return result.exclusive_speaker_diarization

    return result  # pyannote 3.x: already an Annotation


def assign_speakers_to_segments(
    segments: list[dict],
    diarization: Any,
) -> dict[int, str]:
    """Return {segment_index: speaker_label} by maximum overlap.

    For each Whisper segment [start, end], find the pyannote speaker turn
    with the most temporal overlap. Ties broken by iteration order.
    """
    speaker_map = {}
    for idx, seg in enumerate(segments):
        seg_start = seg["start"]
        seg_end = seg["end"]
        if seg_end <= seg_start:
            continue

        best_speaker: Optional[str] = None
        best_overlap = 0.0

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            overlap_start = max(seg_start, turn.start)
            overlap_end = min(seg_end, turn.end)
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker

        if best_speaker is not None:
            speaker_map[idx] = best_speaker

    return speaker_map


def build_diarized_txt(segments: list[dict], speaker_map: dict[int, str]) -> str:
    """Group consecutive segments from the same speaker into paragraphs (per D-09).

    Format:
        SPEAKER_00:
        Hello, welcome to the call.

        SPEAKER_01:
        Thanks for setting this up.
    """
    lines = []
    current_speaker: Optional[str] = None
    current_texts: list[str] = []

    for idx, seg in enumerate(segments):
        speaker = speaker_map.get(idx)
        text = seg["text"].strip()
        if not text:
            continue
        if speaker != current_speaker:
            if current_speaker is not None and current_texts:
                lines.append(f"{current_speaker}:")
                lines.append(" ".join(current_texts))
                lines.append("")
            current_speaker = speaker
            current_texts = [text]
        else:
            current_texts.append(text)

    # Flush final speaker block
    if current_speaker is not None and current_texts:
        lines.append(f"{current_speaker}:")
        lines.append(" ".join(current_texts))

    return "\n".join(lines)


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
