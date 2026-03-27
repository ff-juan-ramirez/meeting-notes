"""meet transcribe CLI command — transcribes a WAV recording via mlx-whisper."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from meeting_notes.cli.ui import console
from meeting_notes.core.config import Config
from meeting_notes.core.state import write_state
from meeting_notes.core.storage import ensure_dirs, get_config_dir, get_data_dir
from meeting_notes.services.transcription import (
    WARN_DURATION_SECONDS,
    WARN_WORD_COUNT,
    MODEL_REPO,
    estimate_wav_duration_seconds,
    generate_srt,
    run_with_spinner,
    transcribe_audio,
)

# HuggingFace Hub model cache path for download detection
_MODEL_CACHE_DIR = (
    Path.home() / ".cache" / "huggingface" / "hub" / "models--mlx-community--whisper-large-v3-turbo"
)


# ---------------------------------------------------------------------------
# Session resolution helpers
# ---------------------------------------------------------------------------

def resolve_latest_wav(recordings_dir: Path) -> Path:
    """Return the most recently modified WAV file. Raises FileNotFoundError if none found."""
    wavs = sorted(recordings_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime)
    if not wavs:
        raise FileNotFoundError("No recordings found in recordings directory.")
    return wavs[-1]


def resolve_wav_by_stem(recordings_dir: Path, stem: str) -> Path:
    """Return the WAV file matching the exact stem. Raises FileNotFoundError if not found."""
    candidate = recordings_dir / f"{stem}.wav"
    if not candidate.exists():
        raise FileNotFoundError(f"No recording found for session: {stem}")
    return candidate


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

@click.command()
@click.option("--session", default=None, help="WAV filename stem (e.g. 20260322-143000-abc12345)")
@click.pass_context
def transcribe(ctx: click.Context, session: str | None) -> None:
    """Transcribe a WAV recording to text using mlx-whisper."""
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # --- Load config first so storage_path is available ---
    config = Config.load(get_config_dir() / "config.json")

    ensure_dirs(config.storage_path)
    recordings_dir = get_data_dir(config.storage_path) / "recordings"
    transcripts_dir = get_data_dir(config.storage_path) / "transcripts"
    metadata_dir = get_data_dir(config.storage_path) / "metadata"

    # --- Resolve WAV file ---
    try:
        if session is None:
            wav_path = resolve_latest_wav(recordings_dir)
        else:
            wav_path = resolve_wav_by_stem(recordings_dir, session)
    except (FileNotFoundError, OSError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    stem = wav_path.stem

    # --- Duration warning ---
    duration = estimate_wav_duration_seconds(wav_path)
    if duration > WARN_DURATION_SECONDS:
        console.print(
            "[yellow]Warning:[/yellow] Recording is over 90 minutes. "
            "Transcription may cause memory pressure on Apple Silicon."
        )

    # --- Run transcription with spinner ---
    if _MODEL_CACHE_DIR.exists():
        spinner_message = "Transcribing..."
    else:
        spinner_message = "Downloading model and transcribing..."

    text, segments = run_with_spinner(lambda: transcribe_audio(wav_path, config), spinner_message, quiet=quiet)
    text = text.strip()

    # --- Word count warning ---
    word_count = len(text.split())
    if word_count < WARN_WORD_COUNT:
        console.print(
            f"[yellow]Warning:[/yellow] Transcript may be empty — check audio routing ({word_count} words)"
        )

    # --- Save transcript ---
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = transcripts_dir / f"{stem}.txt"
    transcript_path.write_text(text)

    # --- Save SRT (per D-01, D-02, D-03) ---
    srt_content = generate_srt(segments)
    srt_path = transcripts_dir / f"{stem}.srt"
    srt_path.write_text(srt_content)

    # --- Save metadata ---
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = metadata_dir / f"{stem}.json"
    metadata = {
        "wav_path": str(wav_path.resolve()),
        "transcript_path": str(transcript_path.resolve()),
        "srt_path": str(srt_path.resolve()),
        "transcribed_at": datetime.now(timezone.utc).isoformat(),
        "word_count": word_count,
        "whisper_model": MODEL_REPO,
        "diarization_succeeded": False,
        "diarized_transcript_path": None,
        "speaker_turns": [],
    }
    write_state(metadata_path, metadata)

    # --- Success output ---
    if not quiet:
        console.print(f"[green]Transcription complete[/green] ({word_count} words)")
        console.print(f"Session: {stem}")
