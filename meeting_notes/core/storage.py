import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def get_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / "meeting-notes"
    return Path.home() / ".config" / "meeting-notes"


def get_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / "meeting-notes"
    return Path.home() / ".local" / "share" / "meeting-notes"


def ensure_dirs() -> None:
    for d in [
        get_config_dir(),
        get_data_dir() / "recordings",
        get_data_dir() / "transcripts",
        get_data_dir() / "notes",
        get_data_dir() / "metadata",
    ]:
        d.mkdir(parents=True, exist_ok=True)


def get_recording_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_id = uuid4().hex[:8]
    return get_data_dir() / "recordings" / f"{timestamp}-{session_id}.wav"
