"""SummarizeWorker — runs LLM note generation and Notion push off the main thread."""
from PySide6.QtCore import QThread, Signal

from meeting_notes.core.config import Config


class SummarizeWorker(QThread):
    """QThread worker that generates notes from a transcript and optionally pushes to Notion.

    All service imports (LLM, Notion, etc.) are deferred to run() so the module
    can be imported without triggering heavy package loads at startup.

    Mirrors the logic in cli/commands/summarize.py, adapted for signal-based progress.

    Signals:
        progress(str): Status message suitable for a UI label.
        finished(str): Emitted on success with notion_url (empty string if Notion skipped).
        failed(str): Emitted on failure with the error message.
    """

    progress = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, stem: str, template: str, title: str | None,
                 config: Config) -> None:
        super().__init__()
        self._stem = stem
        self._template = template
        self._title = title
        self._config = config

    def run(self) -> None:
        try:
            from meeting_notes.services.llm import (
                load_template, build_prompt, generate_notes,
                estimate_tokens, MAX_TOKENS_BEFORE_CHUNKING,
                chunk_transcript, OLLAMA_MODEL,
            )
            from meeting_notes.core.storage import get_data_dir
            from meeting_notes.core.state import read_state, write_state
            from meeting_notes.services.notion import create_page, extract_title
            from datetime import datetime, timezone
            from pathlib import Path

            data_dir = get_data_dir(self._config.storage_path)
            transcripts_dir = data_dir / "transcripts"
            notes_dir = data_dir / "notes"
            notes_dir.mkdir(parents=True, exist_ok=True)
            metadata_dir = data_dir / "metadata"

            # Load transcript
            self.progress.emit("Loading transcript...")
            transcript_path = transcripts_dir / f"{self._stem}.txt"
            transcript_text = transcript_path.read_text().strip()
            if not transcript_text:
                self.failed.emit("Transcript is empty.")
                return

            # Load template
            template_text = load_template(self._template)

            # Determine if chunking needed (D-13: > 8000 tokens)
            token_count = estimate_tokens(transcript_text)
            if token_count > MAX_TOKENS_BEFORE_CHUNKING:
                notes = self._map_reduce(transcript_text, template_text)
            else:
                self.progress.emit("Generating notes...")
                prompt = build_prompt(template_text, transcript_text)
                notes = generate_notes(prompt)

            # Save notes
            notes_path = notes_dir / f"{self._stem}-{self._template}.md"
            notes_path.write_text(notes)

            # Update metadata (read-merge-write per D-08)
            metadata_path = metadata_dir / f"{self._stem}.json"
            existing = read_state(metadata_path) or {}
            existing.update({
                "notes_path": str(notes_path.resolve()),
                "template": self._template,
                "summarized_at": datetime.now(timezone.utc).isoformat(),
                "llm_model": OLLAMA_MODEL,
            })
            write_state(metadata_path, existing)

            # Notion push (if configured)
            notion_url = None
            if (self._config.notion.token is not None
                    and self._config.notion.parent_page_id is not None):
                self.progress.emit("Saving to Notion...")
                session_metadata = read_state(metadata_path) or {}
                recording_name = session_metadata.get("recording_name")
                if self._title:
                    notion_title = self._title
                elif recording_name:
                    notion_title = recording_name
                else:
                    fallback_ts = datetime.now(timezone.utc).strftime(
                        "Meeting Notes -- %Y-%m-%d %H:%M"
                    )
                    notion_title = extract_title(notes, fallback_ts)
                try:
                    notion_url = create_page(
                        token=self._config.notion.token,
                        parent_page_id=self._config.notion.parent_page_id,
                        title=notion_title,
                        notes_markdown=notes,
                    )
                except Exception:
                    pass  # Notion failure is non-fatal; notes saved locally

            # Update metadata with notion_url
            existing = read_state(metadata_path) or {}
            existing["notion_url"] = notion_url
            write_state(metadata_path, existing)

            self.finished.emit(notion_url or "")
        except Exception as exc:
            self.failed.emit(str(exc))

    def _map_reduce(self, transcript_text: str, template_text: str) -> str:
        """Summarize long transcripts via map-reduce chunking (D-13)."""
        from meeting_notes.services.llm import (
            build_prompt, generate_notes, chunk_transcript,
        )
        chunks = chunk_transcript(transcript_text)
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            self.progress.emit(f"Summarizing chunk {i}/{len(chunks)}...")
            prompt = build_prompt(template_text, chunk)
            chunk_summaries.append(generate_notes(prompt))
        combined = "\n\n---\n\n".join(chunk_summaries)
        self.progress.emit("Combining summaries...")
        combine_prompt = (
            "These are partial summaries of sections of a single meeting transcript. "
            "Merge them into one coherent set of notes. Remove duplicate items. "
            "Preserve all unique information. Use the same section structure as the partial summaries.\n\n"
            + combined
        )
        return generate_notes(combine_prompt)
