import subprocess
import tempfile
from pathlib import Path

import click
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

from meeting_notes.cli.ui import console, STATUS_ICONS
from meeting_notes.core.config import AudioConfig, Config, NotionConfig
from meeting_notes.core.health_check import CheckStatus, HealthCheckSuite
from meeting_notes.core.storage import ensure_dirs, get_config_dir
from meeting_notes.services.checks import (
    _parse_audio_devices,
    BlackHoleCheck,
    DiskSpaceCheck,
    FFmpegDeviceCheck,
    MlxWhisperCheck,
    NotionDatabaseCheck,
    NotionTokenCheck,
    OllamaModelCheck,
    OllamaRunningCheck,
    OpenaiWhisperConflictCheck,
    PythonVersionCheck,
    WhisperModelCheck,
)


def mask_token(token: str | None) -> str:
    """Return a masked version of the token for display."""
    if token is None:
        return "[not set]"
    if len(token) <= 8:
        return "***"
    return token[:4] + "***" + token[-3:]


def _select_audio_devices() -> tuple[int, int]:
    """Present audio device menu and return (system_idx, mic_idx)."""
    try:
        devices = _parse_audio_devices()
    except FileNotFoundError:
        console.print("[red]ffmpeg not found or no audio devices detected[/red]")
        raise SystemExit(1)

    if not devices:
        console.print("[red]ffmpeg not found or no audio devices detected[/red]")
        raise SystemExit(1)

    console.print("Audio Devices:")
    for idx, name in sorted(devices.items()):
        console.print(f"  [{idx}] {name}")

    system_idx = click.prompt(
        "System audio device index (BlackHole)", type=int, default=1
    )
    if system_idx not in devices:
        console.print(f"[yellow]Warning: no device at index {system_idx}[/yellow]")

    mic_idx = click.prompt("Microphone device index", type=int, default=2)
    if mic_idx not in devices:
        console.print(f"[yellow]Warning: no device at index {mic_idx}[/yellow]")

    return system_idx, mic_idx


def _collect_notion_credentials() -> tuple[str | None, str | None]:
    """Prompt for and validate Notion token, then prompt for page ID."""
    while True:
        token = click.prompt("Notion integration token", hide_input=True)
        try:
            client = NotionClient(auth=token)
            client.users.me()
            console.print("[green]Notion token valid.[/green]")
            break
        except APIResponseError:
            console.print("[red]Token invalid. Please check and try again.[/red]")
        except Exception as e:
            console.print(f"[yellow]Could not verify token ({e}). Saving anyway.[/yellow]")
            break

    page_id = click.prompt("Notion database/page ID")
    return token, page_id


def _update_specific_fields(config: Config, config_path: Path) -> None:
    """Show numbered field menu and re-prompt only selected fields."""
    fields = [
        ("System audio device index", str(config.audio.system_device_index)),
        ("Microphone device index", str(config.audio.microphone_device_index)),
        ("Notion token", mask_token(config.notion.token)),
        ("Notion database/page ID", config.notion.parent_page_id or "[not set]"),
        ("Whisper language", config.whisper.language or "auto"),
        ("Storage path", config.storage_path or "~/Documents/meeting-notes (default)"),
    ]
    for i, (name, value) in enumerate(fields):
        console.print(f"  [{i + 1}] {name}: {value}")

    raw = click.prompt(
        "Enter field number(s) to update (comma-separated)", type=str, default=""
    )
    if not raw.strip():
        console.print("[green]Config updated.[/green]")
        return

    try:
        selected = {int(s.strip()) for s in raw.split(",") if s.strip()}
    except ValueError:
        console.print("[yellow]Invalid selection — no fields updated.[/yellow]")
        return

    if 1 in selected:
        config.audio.system_device_index = click.prompt(
            "System audio device index (BlackHole)", type=int,
            default=config.audio.system_device_index,
        )
    if 2 in selected:
        config.audio.microphone_device_index = click.prompt(
            "Microphone device index", type=int,
            default=config.audio.microphone_device_index,
        )
    if 3 in selected:
        while True:
            token = click.prompt("Notion integration token", hide_input=True)
            try:
                client = NotionClient(auth=token)
                client.users.me()
                console.print("[green]Notion token valid.[/green]")
                config.notion.token = token
                break
            except APIResponseError:
                console.print("[red]Token invalid. Please check and try again.[/red]")
            except Exception as e:
                console.print(f"[yellow]Could not verify token ({e}). Saving anyway.[/yellow]")
                config.notion.token = token
                break
    if 4 in selected:
        config.notion.parent_page_id = click.prompt(
            "Notion database/page ID",
            default=config.notion.parent_page_id or "",
        )
    if 5 in selected:
        lang = click.prompt(
            "Whisper language (leave blank for auto)",
            default=config.whisper.language or "",
        )
        config.whisper.language = lang if lang else None
    if 6 in selected:
        path = click.prompt(
            "Storage path for recordings and transcripts (leave blank for default ~/Documents/meeting-notes)",
            default=config.storage_path or "",
        )
        config.storage_path = path if path else None

    config.save(config_path)
    console.print("[green]Config updated.[/green]")


def _run_test_recording(mic_idx: int) -> None:
    """Run a 1-second test recording to trigger microphone permission."""
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
            console.print(
                "[yellow]Test recording timed out. You may need to grant microphone access manually.[/yellow]"
            )
        except Exception as e:
            console.print(f"[yellow]Test recording failed: {e}[/yellow]")


def _run_inline_doctor(config: Config) -> None:
    """Run all health checks inline (no subprocess), display results."""
    console.print("\n[bold]Running system check...[/bold]\n")
    suite = HealthCheckSuite()
    suite.register(PythonVersionCheck())
    suite.register(OpenaiWhisperConflictCheck())
    suite.register(BlackHoleCheck(config.audio.system_device_index))
    suite.register(FFmpegDeviceCheck(config.audio.microphone_device_index))
    suite.register(DiskSpaceCheck())
    suite.register(MlxWhisperCheck())
    suite.register(WhisperModelCheck())
    suite.register(OllamaRunningCheck())
    suite.register(OllamaModelCheck())
    suite.register(NotionTokenCheck(config.notion.token))
    suite.register(NotionDatabaseCheck(config.notion.token, config.notion.parent_page_id))

    results = suite.run_all()
    for check, result in results:
        icon = STATUS_ICONS[result.status]
        console.print(f"  {icon} {check.name}: {result.message}")
        if result.fix_suggestion and result.status != CheckStatus.OK:
            console.print(f"    [dim]Fix: {result.fix_suggestion}[/dim]")


@click.command()
@click.pass_context
def init(ctx: click.Context):
    """Initialize meeting-notes configuration."""
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    config_path = get_config_dir() / "config.json"

    if not quiet:
        console.print("[bold]Meeting Notes Setup[/bold]\n")

    # D-08: Check for existing config
    if config_path.exists():
        config = Config.load(config_path)
        console.print("[bold]Config already exists.[/bold]")
        choice = click.prompt(
            "(R)econfigure everything from scratch, or (U)pdate specific fields?",
            type=click.Choice(["R", "r", "U", "u"]),
            default="U",
        ).upper()
        if choice == "U":
            _update_specific_fields(config, config_path)
            # Still run test recording + inline doctor after update
            _run_test_recording(config.audio.microphone_device_index)
            _run_inline_doctor(config)
            return

    # Full wizard flow
    ensure_dirs()

    # Step 1: Audio device selection (D-10)
    system_idx, mic_idx = _select_audio_devices()

    # Step 2: Storage path
    console.print("\nWhere should recordings and transcripts be saved?")
    storage_input = click.prompt(
        "Storage path (leave blank for default ~/Documents/meeting-notes)",
        default="",
    )
    storage_path = storage_input if storage_input else None

    # Step 3: Notion credentials (D-07, D-11)
    token, page_id = _collect_notion_credentials()

    # Step 4: Build and save config
    config = Config(
        storage_path=storage_path,
        audio=AudioConfig(system_device_index=system_idx, microphone_device_index=mic_idx),
        notion=NotionConfig(token=token, parent_page_id=page_id),
    )
    config.save(config_path)
    console.print(f"\n[green]Config saved to {config_path}[/green]")

    # Step 5: Test recording (D-13, SETUP-02) — after config write, before doctor
    _run_test_recording(mic_idx)

    # Step 6: Inline doctor (D-12) — last step
    _run_inline_doctor(config)

    console.print("\n[green]Setup complete![/green]")
