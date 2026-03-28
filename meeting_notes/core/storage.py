import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def get_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / "meeting-notes"
    return Path.home() / ".config" / "meeting-notes"


def get_data_dir(storage_path: str | None = None) -> Path:
    if storage_path:
        return Path(storage_path).expanduser()
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / "meeting-notes"
    return Path.home() / "Documents" / "meeting-notes"


def ensure_dirs(storage_path: str | None = None) -> None:
    for d in [
        get_config_dir(),
        get_data_dir(storage_path) / "recordings",
        get_data_dir(storage_path) / "transcripts",
        get_data_dir(storage_path) / "notes",
        get_data_dir(storage_path) / "metadata",
    ]:
        d.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug. Pure function, stdlib only (SLUG-02)."""
    if not text or not text.strip():
        return "untitled"
    # NFKD normalization (D-03): é→e, ñ→n, ligatures expanded
    slug = unicodedata.normalize("NFKD", text)
    # Drop non-ASCII (accent marks become empty after NFKD decomposition)
    slug = slug.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    slug = slug.lower()
    # Replace any non-alphanumeric char with hyphen
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    # Truncate to 80 chars (D-01), strip trailing hyphen from mid-word cut
    slug = slug[:80].rstrip("-")
    # Fallback for all-punctuation input
    return slug if slug else "untitled"


def get_recording_path(storage_path: str | None = None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_id = uuid4().hex[:8]
    return get_data_dir(storage_path) / "recordings" / f"{timestamp}-{session_id}.wav"
