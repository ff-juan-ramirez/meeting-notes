import subprocess
import tempfile

import click
from rich.console import Console

from meeting_notes.core.config import AudioConfig, Config
from meeting_notes.core.storage import ensure_dirs, get_config_dir

console = Console()


@click.command()
def init():
    """Initialize meeting-notes configuration."""
    config_path = get_config_dir() / "config.json"

    console.print("[bold]Meeting Notes Setup[/bold]")
    console.print()

    # Detect audio devices
    console.print("Detecting audio devices...")
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            text=True,
        )
        console.print("[dim]" + result.stderr + "[/dim]")
    except FileNotFoundError:
        console.print("[red]ffmpeg not found. Install with: brew install ffmpeg[/red]")
        return

    # Collect device indices
    system_idx = click.prompt(
        "System audio device index (BlackHole)",
        type=int,
        default=1,
    )
    mic_idx = click.prompt(
        "Microphone device index",
        type=int,
        default=2,
    )

    # Create config
    config = Config(
        audio=AudioConfig(
            system_device_index=system_idx,
            microphone_device_index=mic_idx,
        ),
    )

    # Ensure directories exist
    ensure_dirs()

    # Save config
    config.save(config_path)
    console.print(f"[green]Config saved to {config_path}[/green]")

    # Test recording to trigger mic permission prompt (SETUP-02)
    console.print()
    console.print("Running 1-second test recording to trigger microphone permission...")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-f", "avfoundation",
                    "-i", f":{mic_idx}",
                    "-t", "1",
                    "-y",
                    tmp.name,
                ],
                capture_output=True,
                timeout=10,
            )
            console.print("[green]Microphone access confirmed.[/green]")
        except subprocess.TimeoutExpired:
            console.print("[yellow]Test recording timed out. You may need to grant microphone access manually.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Test recording failed: {e}[/yellow]")

    console.print()
    console.print("[green]Setup complete![/green] Run [bold]meet doctor[/bold] to verify your setup.")
