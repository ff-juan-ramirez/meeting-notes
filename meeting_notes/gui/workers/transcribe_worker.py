"""TranscribeWorker — runs mlx-whisper transcription off the main thread."""
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from meeting_notes.core.config import Config


class TranscribeWorker(QThread):
    """QThread worker that transcribes a WAV file using the service layer.

    All ML imports (mlx_whisper, etc.) are deferred to run() so the module
    can be imported without triggering heavy package loads at startup.

    Signals:
        progress(str): Status message suitable for a UI label.
        finished(str, int): Emitted on success with (stem, word_count).
        failed(str): Emitted on failure with the error message.
    """

    progress = Signal(str)
    finished = Signal(str, int)
    failed = Signal(str)

    def __init__(self, wav_path: Path, config: Config) -> None:
        super().__init__()
        self._wav_path = wav_path
        self._config = config

    def run(self) -> None:
        try:
            from meeting_notes.services.transcription import transcribe_audio
            self.progress.emit("Transcribing audio...")
            text, segments = transcribe_audio(self._wav_path, self._config)
            # Update metadata with transcription results
            from meeting_notes.core.storage import get_data_dir
            from meeting_notes.core.state import read_state, write_state
            from datetime import datetime, timezone
            data_dir = get_data_dir(self._config.storage_path)
            metadata_path = data_dir / "metadata" / f"{self._wav_path.stem}.json"
            # Metadata update mirrors cli/commands/transcribe.py pattern
            existing = read_state(metadata_path) or {}
            transcript_dir = data_dir / "transcripts"
            transcript_dir.mkdir(parents=True, exist_ok=True)
            transcript_path = transcript_dir / f"{self._wav_path.stem}.txt"
            transcript_path.write_text(text)
            existing.update({
                "transcript_path": str(transcript_path.resolve()),
                "transcribed_at": datetime.now(timezone.utc).isoformat(),
                "word_count": len(text.split()),
            })
            write_state(metadata_path, existing)
            self.progress.emit("Transcription complete.")
            self.finished.emit(self._wav_path.stem, len(text.split()))
        except Exception as exc:
            self.failed.emit(str(exc))
