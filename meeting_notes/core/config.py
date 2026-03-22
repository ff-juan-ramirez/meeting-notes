import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class AudioConfig:
    system_device_index: int = 1
    microphone_device_index: int = 2


@dataclass
class Config:
    version: int = 1
    audio: AudioConfig = field(default_factory=AudioConfig)

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        audio = AudioConfig(**data.get("audio", {}))
        return cls(version=data.get("version", 1), audio=audio)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2))
        tmp.replace(path)
