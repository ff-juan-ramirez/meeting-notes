import sys
from rich.console import Console

from meeting_notes.core.health_check import CheckStatus

console = Console(force_terminal=sys.stdout.isatty())

STATUS_ICONS = {
    CheckStatus.OK: "[green]\u2713[/green]",
    CheckStatus.WARNING: "[yellow]![/yellow]",
    CheckStatus.ERROR: "[red]\u2717[/red]",
}
