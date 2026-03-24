import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class AudioConfig:
    system_device_index: int = 1
    microphone_device_index: int = 2


@dataclass
class WhisperConfig:
    language: str | None = None  # None = auto-detect, string = forced language


@dataclass
class NotionConfig:
    token: str | None = None
    parent_page_id: str | None = None


@dataclass
class Config:
    version: int = 1
    storage_path: str | None = None
    audio: AudioConfig = field(default_factory=AudioConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    notion: NotionConfig = field(default_factory=NotionConfig)

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        audio = AudioConfig(**data.get("audio", {}))
        whisper_data = data.get("whisper", {})
        whisper = WhisperConfig(language=whisper_data.get("language", None))
        notion_data = data.get("notion", {})
        notion = NotionConfig(
            token=notion_data.get("token", None),
            parent_page_id=notion_data.get("parent_page_id", None),
        )
        return cls(
            version=data.get("version", 1),
            storage_path=data.get("storage_path", None),
            audio=audio,
            whisper=whisper,
            notion=notion,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2))
        tmp.replace(path)
