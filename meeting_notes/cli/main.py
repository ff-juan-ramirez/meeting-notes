import click


@click.group()
@click.version_option(package_name="meeting-notes")
@click.option("--quiet", is_flag=True, default=False, help="Suppress all progress output.")
@click.pass_context
def main(ctx: click.Context, quiet: bool) -> None:
    """Meeting notes - local capture, transcription, and Notion export."""
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet


from meeting_notes.cli.commands.record import record, stop
from meeting_notes.cli.commands.doctor import doctor
from meeting_notes.cli.commands.init import init
from meeting_notes.cli.commands.transcribe import transcribe
from meeting_notes.cli.commands.summarize import summarize

main.add_command(record)
main.add_command(stop)
main.add_command(doctor)
main.add_command(init)
main.add_command(transcribe)
main.add_command(summarize)

from meeting_notes.cli.commands.list import list_sessions

main.add_command(list_sessions)
