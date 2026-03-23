import sys

import click
from rich.console import Console
from rich.panel import Panel

from meeting_notes.core.config import Config
from meeting_notes.core.health_check import CheckStatus, HealthCheckSuite
from meeting_notes.core.storage import get_config_dir
from meeting_notes.services.checks import (
    BlackHoleCheck,
    DiskSpaceCheck,
    FFmpegDeviceCheck,
    MlxWhisperCheck,
    OllamaModelCheck,
    OllamaRunningCheck,
    WhisperModelCheck,
)

console = Console()

STATUS_ICONS = {
    CheckStatus.OK: "[green]\u2713[/green]",
    CheckStatus.WARNING: "[yellow]![/yellow]",
    CheckStatus.ERROR: "[red]\u2717[/red]",
}


@click.command()
def doctor():
    """Check system prerequisites for meeting-notes."""
    config_path = get_config_dir() / "config.json"
    config = Config.load(config_path)

    suite = HealthCheckSuite()
    suite.register(BlackHoleCheck(config.audio.system_device_index))
    suite.register(FFmpegDeviceCheck(config.audio.microphone_device_index))
    suite.register(DiskSpaceCheck())
    suite.register(MlxWhisperCheck())
    suite.register(WhisperModelCheck())
    suite.register(OllamaRunningCheck())
    suite.register(OllamaModelCheck())

    console.print(Panel("[bold]Meeting Notes - System Check[/bold]"))
    console.print()

    results = suite.run_all()
    has_error = False

    for check, result in results:
        icon = STATUS_ICONS[result.status]
        console.print(f"  {icon} {check.name}: {result.message}")
        if result.fix_suggestion:
            console.print(f"    [dim]Fix: {result.fix_suggestion}[/dim]")
        if result.status == CheckStatus.ERROR:
            has_error = True

    console.print()
    if has_error:
        console.print("[red]Some checks failed.[/red] Fix the issues above and run 'meet doctor' again.")
        sys.exit(1)
    else:
        console.print("[green]All checks passed![/green]")
