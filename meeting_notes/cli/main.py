import click


@click.group()
def main() -> None:
    """Meeting notes - local capture, transcription, and Notion export."""
    pass


from meeting_notes.cli.commands.record import record, stop
from meeting_notes.cli.commands.doctor import doctor
from meeting_notes.cli.commands.init import init

main.add_command(record)
main.add_command(stop)
main.add_command(doctor)
main.add_command(init)
