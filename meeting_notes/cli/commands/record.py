import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import click

from meeting_notes.cli.ui import console
from meeting_notes.core.config import Config
from meeting_notes.core.state import (
    check_for_stale_session,
    clear_state,
    read_state,
    write_state,
)
from meeting_notes.core.storage import get_config_dir, get_data_dir
from meeting_notes.services.audio import start_recording, stop_recording


def _get_state_path():
    return get_config_dir() / "state.json"


def _get_config_path():
    return get_config_dir() / "config.json"


@click.command()
@click.pass_context
def record(ctx: click.Context):
    """Start a recording session."""
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    state_path = _get_state_path()
    config_path = _get_config_path()

    # Check for existing session
    existing = read_state(state_path)
    if existing is not None:
        if check_for_stale_session(existing):
            console.print("[red]Error:[/red] Already recording. Run 'meet stop' first.")
            sys.exit(1)
        else:
            # Stale PID — clear and proceed
            console.print("[yellow]Warning:[/yellow] Cleared stale recording session.")
            clear_state(state_path)

    config = Config.load(config_path)
    proc, output_path = start_recording(config)

    session_id = uuid4().hex
    state = {
        "session_id": session_id,
        "pid": proc.pid,
        "output_path": str(output_path),
        "start_time": datetime.now(timezone.utc).isoformat(),
    }
    write_state(state_path, state)

    if not quiet:
        console.print(f"[green]Recording started[/green] (PID: {proc.pid})")
        console.print(f"Output: {output_path}")
        console.print("Run [bold]meet stop[/bold] to finish recording.")


@click.command()
@click.pass_context
def stop(ctx: click.Context):
    """Stop the active recording session."""
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    state_path = _get_state_path()

    existing = read_state(state_path)
    if existing is None:
        console.print("[red]Error:[/red] No active recording session.")
        sys.exit(1)

    pid = existing.get("pid")
    if pid is None:
        console.print("[red]Error:[/red] Invalid session state (no PID).")
        clear_state(state_path)
        sys.exit(1)

    # Create a process object pointing to the stored PID
    import subprocess
    try:
        proc = subprocess.Popen.__new__(subprocess.Popen)
        proc.pid = pid
        proc.returncode = None
        stop_recording(proc)
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Error stopping ffmpeg: {e}")

    output_path_str = existing.get("output_path")

    # Compute duration and write metadata (per D-01, D-04, D-05)
    if output_path_str:
        stem = Path(output_path_str).stem
        metadata_dir = get_data_dir() / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = metadata_dir / f"{stem}.json"

        meta = read_state(metadata_path) or {}

        # Compute duration from start_time (per D-01)
        start_time_str = existing.get("start_time")
        if start_time_str:
            start = datetime.fromisoformat(start_time_str)
            now = datetime.now(timezone.utc)
            duration_seconds = int((now - start).total_seconds())
            meta["duration_seconds"] = duration_seconds
        # Per D-04: if start_time missing, omit duration_seconds entirely

        # Also write wav_path for sessions that may never reach transcription
        meta["wav_path"] = str(Path(output_path_str).resolve())

        write_state(metadata_path, meta)

    clear_state(state_path)

    if not quiet:
        console.print("[green]Recording stopped.[/green]")
        console.print(f"Saved: {output_path_str or 'unknown'}")
