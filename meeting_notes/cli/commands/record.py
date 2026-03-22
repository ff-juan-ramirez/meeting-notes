import os
import signal
import sys
from datetime import datetime, timezone
from uuid import uuid4

import click
from rich.console import Console

from meeting_notes.core.config import Config
from meeting_notes.core.state import (
    check_for_stale_session,
    clear_state,
    read_state,
    write_state,
)
from meeting_notes.core.storage import get_config_dir
from meeting_notes.services.audio import start_recording, stop_recording

console = Console()


def _get_state_path():
    return get_config_dir() / "state.json"


def _get_config_path():
    return get_config_dir() / "config.json"


@click.command()
def record():
    """Start a recording session."""
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

    console.print(f"[green]Recording started[/green] (PID: {proc.pid})")
    console.print(f"Output: {output_path}")
    console.print("Run [bold]meet stop[/bold] to finish recording.")


@click.command()
def stop():
    """Stop the active recording session."""
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

    output_path = existing.get("output_path", "unknown")
    clear_state(state_path)

    console.print("[green]Recording stopped.[/green]")
    console.print(f"Saved: {output_path}")
