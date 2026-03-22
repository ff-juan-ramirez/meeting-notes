import click


@click.group()
def main() -> None:
    """Meeting notes - local capture, transcription, and Notion export."""
    pass


from meeting_notes.cli.commands.record import record, stop

main.add_command(record)
main.add_command(stop)
