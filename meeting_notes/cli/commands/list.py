"""meet list CLI command — display all recorded sessions."""
import json
import sys
import wave
from datetime import datetime
from pathlib import Path

import click
from rich.table import Table

from meeting_notes.cli.ui import console
from meeting_notes.core.config import Config
from meeting_notes.core.state import read_state
from meeting_notes.core.storage import get_config_dir, get_data_dir
from meeting_notes.services.notion import extract_title


def _wav_duration(wav_path_str: str | None) -> int | None:
    """Read duration from WAV header. Returns None if unavailable (per D-03)."""
    if not wav_path_str:
        return None
    try:
        with wave.open(wav_path_str, "rb") as wf:
            return int(wf.getnframes() / wf.getframerate())
    except Exception:
        return None


def _format_duration(seconds: int | None) -> str:
    """Format seconds as mm:ss (per D-02). Returns em dash if None."""
    if seconds is None:
        return "\u2014"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def _derive_status(meta: dict) -> str:
    """Derive session status from metadata fields (per D-15).

    - not-transcribed: no transcript_path or file not found
    - transcribed: has transcript_path but no notes_path
    - summarized: has notes_path and file exists
    """
    notes_path = meta.get("notes_path")
    if notes_path and Path(notes_path).exists():
        return "summarized"
    transcript_path = meta.get("transcript_path")
    if transcript_path and Path(transcript_path).exists():
        return "transcribed"
    return "not-transcribed"


def _derive_title(meta: dict, stem: str) -> str:
    """Derive session title (per D-16, D-17).

    Summarized: first # Heading from notes file via extract_title().
    Otherwise: session stem.
    """
    notes_path = meta.get("notes_path")
    if notes_path and Path(notes_path).exists():
        try:
            notes_text = Path(notes_path).read_text()
            return extract_title(notes_text, stem)
        except Exception:
            return stem
    return stem


def _derive_date(meta: dict) -> str:
    """Derive display date from metadata. Format: YYYY-MM-DD HH:MM."""
    for field in ("transcribed_at", "summarized_at"):
        ts = meta.get(field)
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                return dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass
    # Fallback: try WAV mtime
    wav_path = meta.get("wav_path")
    if wav_path:
        try:
            mtime = Path(wav_path).stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except (OSError, ValueError):
            pass
    return "\u2014"


def _sort_key(metadata_path: Path) -> str:
    """Sort key for metadata files: transcribed_at ISO string, or WAV mtime as ISO (per D-13)."""
    meta = read_state(metadata_path)
    if meta:
        ts = meta.get("transcribed_at")
        if ts:
            return ts
        wav_path = meta.get("wav_path")
        if wav_path:
            try:
                mtime = Path(wav_path).stat().st_mtime
                return datetime.fromtimestamp(mtime).isoformat()
            except (OSError, ValueError):
                pass
    return ""


@click.command(name="list")
@click.option("--status", "filter_status", default=None,
              type=click.Choice(["not-transcribed", "transcribed", "summarized"]),
              help="Filter sessions by status.")
@click.option("--json", "output_json", is_flag=True, default=False,
              help="Output as JSON array (no ANSI codes).")
@click.pass_context
def list_sessions(ctx: click.Context, filter_status: str | None, output_json: bool) -> None:
    """List all recorded sessions."""
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    config = Config.load(get_config_dir() / "config.json")
    metadata_dir = get_data_dir(config.storage_path) / "metadata"

    if not metadata_dir.exists():
        if output_json:
            print(json.dumps([], indent=2))
            return
        if not quiet:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Date")
            table.add_column("Duration")
            table.add_column("Title")
            table.add_column("Status")
            table.add_column("Notion URL")
            console.print(table)
        return

    # Scan and sort (per D-13 — newest first)
    json_files = sorted(metadata_dir.glob("*.json"), key=_sort_key, reverse=True)

    sessions = []
    for path in json_files:
        meta = read_state(path) or {}
        stem = path.stem

        status = _derive_status(meta)
        if filter_status and status != filter_status:
            continue

        # Duration: metadata field first, then WAV fallback (per D-03)
        duration_seconds = meta.get("duration_seconds")
        if duration_seconds is None:
            duration_seconds = _wav_duration(meta.get("wav_path"))

        sessions.append({
            **meta,
            "status": status,
            "title": _derive_title(meta, stem),
            "date": _derive_date(meta),
            "duration_display": _format_duration(duration_seconds),
            "duration_seconds": duration_seconds,
        })

    # --json path: clean JSON, no Rich, no ANSI (per D-19)
    if output_json:
        print(json.dumps(sessions, indent=2, default=str))
        return

    if quiet:
        return

    # Rich table (per D-14, D-20)
    table = Table(show_header=True, header_style="bold")
    table.add_column("Date")
    table.add_column("Duration")
    table.add_column("Title", max_width=40)
    table.add_column("Status")
    table.add_column("Notion URL")

    for s in sessions:
        table.add_row(
            s.get("date", "\u2014"),
            s.get("duration_display", "\u2014"),
            s.get("title", "\u2014"),
            s.get("status", "\u2014"),
            s.get("notion_url") or "\u2014",
        )

    console.print(table)
