"""meet summarize CLI command — generates structured notes from a transcript via Ollama."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from meeting_notes.cli.ui import console
from meeting_notes.core.config import Config
from meeting_notes.core.state import read_state, write_state
from meeting_notes.core.storage import ensure_dirs, get_data_dir, get_config_dir
from meeting_notes.services.llm import (
    OLLAMA_MODEL,
    MAX_TOKENS_BEFORE_CHUNKING,
    VALID_TEMPLATES,
    build_prompt,
    chunk_transcript,
    estimate_tokens,
    generate_notes,
    load_template,
)
from meeting_notes.services.notion import create_page, extract_title
from meeting_notes.services.transcription import run_with_spinner


# ---------------------------------------------------------------------------
# Session resolution helpers (for transcripts)
# ---------------------------------------------------------------------------

def resolve_latest_transcript(transcripts_dir: Path) -> Path:
    """Return the most recently modified .txt file. Raises FileNotFoundError if none."""
    txts = sorted(transcripts_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime)
    if not txts:
        raise FileNotFoundError("No transcripts found in transcripts directory.")
    return txts[-1]


def resolve_transcript_by_stem(transcripts_dir: Path, stem: str) -> Path:
    """Return transcript matching exact stem. Raises FileNotFoundError if not found."""
    candidate = transcripts_dir / f"{stem}.txt"
    if not candidate.exists():
        raise FileNotFoundError(f"No transcript found for session: {stem}")
    return candidate


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

@click.command()
@click.option("--template", default="meeting", type=click.Choice(["meeting", "minutes", "1on1"]),
              help="Note template (default: meeting)")
@click.option("--session", default=None, help="Transcript filename stem (e.g. 20260322-143000-abc12345)")
@click.pass_context
def summarize(ctx: click.Context, template: str, session: str | None) -> None:
    """Generate structured notes from a transcript using Ollama llama3.1:8b."""
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    ensure_dirs()
    transcripts_dir = get_data_dir() / "transcripts"
    notes_dir = get_data_dir() / "notes"
    metadata_dir = get_data_dir() / "metadata"

    # --- Resolve transcript file ---
    try:
        if session is None:
            transcript_path = resolve_latest_transcript(transcripts_dir)
        else:
            transcript_path = resolve_transcript_by_stem(transcripts_dir, session)
    except (FileNotFoundError, OSError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    stem = transcript_path.stem
    transcript_text = transcript_path.read_text().strip()

    if not transcript_text:
        console.print("[red]Error:[/red] Transcript is empty.")
        sys.exit(1)

    # --- Load template ---
    template_text = load_template(template)

    # --- Determine if chunking needed (per D-13) ---
    token_count = estimate_tokens(transcript_text)

    try:
        if token_count > MAX_TOKENS_BEFORE_CHUNKING:
            # Map-reduce path: chunk, summarize each, combine
            notes = _map_reduce_summarize(transcript_text, template_text, template, quiet=quiet)
        else:
            # Single-pass path
            prompt = build_prompt(template_text, transcript_text)
            notes = run_with_spinner(
                lambda: generate_notes(prompt),
                "Generating notes...",
                quiet=quiet,
            )
    except TimeoutError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)
    except ConnectionError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)
    except RuntimeError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    # --- Save notes (overwrite silently per D-07) ---
    notes_path = notes_dir / f"{stem}-{template}.md"
    notes_path.write_text(notes)

    word_count = len(notes.split())

    # --- Extend metadata with Phase 3 fields (read-merge-write per D-08, avoiding Pitfall 4) ---
    metadata_path = metadata_dir / f"{stem}.json"
    existing = read_state(metadata_path) or {}
    existing.update({
        "notes_path": str(notes_path.resolve()),
        "template": template,
        "summarized_at": datetime.now(timezone.utc).isoformat(),
        "llm_model": OLLAMA_MODEL,
    })
    write_state(metadata_path, existing)

    # --- Success output (per D-05, D-06) ---
    if not quiet:
        console.print(f"Notes saved: {notes_path} ({word_count} words)")

    # --- Notion push (per D-01, D-02, D-03, D-04, D-10, D-11) ---
    config_path = get_config_dir() / "config.json"
    config = Config.load(config_path)

    notion_url = None
    if config.notion.token is None or config.notion.parent_page_id is None:
        if not quiet:
            console.print("[dim]Notion not configured — run meet init to set up.[/dim]")
    else:
        fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
        title = extract_title(notes, fallback_ts)
        try:
            notion_url = run_with_spinner(
                lambda: create_page(
                    token=config.notion.token,
                    parent_page_id=config.notion.parent_page_id,
                    title=title,
                    notes_markdown=notes,
                ),
                "Saving to Notion...",
                quiet=quiet,
            )
            if not quiet:
                console.print(f"Notion: {notion_url}")
        except Exception as exc:
            from rich.panel import Panel
            console.print(Panel(
                f"[yellow]Notion upload failed: {exc}[/yellow]\nNotes saved locally: {notes_path}",
                style="yellow",
            ))

    # --- Extend metadata with notion_url (read-merge-write per Pitfall 4) ---
    existing = read_state(metadata_path) or {}
    existing["notion_url"] = notion_url
    write_state(metadata_path, existing)

    if not quiet:
        console.print(f"Session: {stem}")


def _map_reduce_summarize(transcript_text: str, template_text: str, template_name: str, quiet: bool = False) -> str:
    """Map-reduce summarization for long transcripts (per D-13).

    1. Chunk transcript into ~6,000-token pieces
    2. Summarize each chunk independently
    3. Combine summaries via a second LLM call
    """
    chunks = chunk_transcript(transcript_text)

    # Map: summarize each chunk
    chunk_summaries = []
    for i, chunk in enumerate(chunks, 1):
        prompt = build_prompt(template_text, chunk)
        summary = run_with_spinner(
            lambda p=prompt: generate_notes(p),
            f"Generating notes (chunk {i}/{len(chunks)})...",
            quiet=quiet,
        )
        chunk_summaries.append(summary)

    # Reduce: combine summaries
    combined_text = "\n\n---\n\n".join(chunk_summaries)
    combine_prompt = (
        f"These are partial summaries of sections of a single meeting transcript. "
        f"Merge them into one coherent set of notes. Remove duplicate items. "
        f"Preserve all unique information. Use the same section structure as the partial summaries.\n\n"
        f"{combined_text}"
    )
    final_notes = run_with_spinner(
        lambda: generate_notes(combine_prompt),
        "Combining summaries...",
        quiet=quiet,
    )
    return final_notes
