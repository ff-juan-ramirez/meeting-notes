import importlib.metadata
import re
import shutil
import subprocess
from pathlib import Path

import requests
from huggingface_hub import HfApi
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

from meeting_notes.core.health_check import CheckResult, CheckStatus, HealthCheck


def _parse_audio_devices() -> dict[int, str]:
    """Parse ffmpeg avfoundation device list from stderr."""
    result = subprocess.run(
        ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True,
        text=True,
    )
    in_audio = False
    devices: dict[int, str] = {}
    for line in result.stderr.splitlines():
        if "AVFoundation audio devices" in line:
            in_audio = True
            continue
        if "AVFoundation video devices" in line:
            in_audio = False
            continue
        if in_audio:
            m = re.search(r"\[(\d+)\] (.+)", line)
            if m:
                devices[int(m.group(1))] = m.group(2).strip()
    return devices


class BlackHoleCheck(HealthCheck):
    """Verify that the device at the system audio index is BlackHole."""

    name = "BlackHole Device"

    def __init__(self, device_index: int = 1) -> None:
        self.device_index = device_index

    def check(self) -> CheckResult:
        try:
            devices = _parse_audio_devices()
        except FileNotFoundError:
            return CheckResult(
                status=CheckStatus.ERROR,
                message="ffmpeg not found",
                fix_suggestion="Install ffmpeg: brew install ffmpeg",
            )

        device_name = devices.get(self.device_index)
        if device_name is None:
            return CheckResult(
                status=CheckStatus.ERROR,
                message=f"No audio device at index {self.device_index}",
                fix_suggestion=f"Check Audio MIDI Setup. Expected BlackHole at index {self.device_index}.",
            )

        if "BlackHole" not in device_name:
            return CheckResult(
                status=CheckStatus.ERROR,
                message=f"Device at index {self.device_index} is '{device_name}', not BlackHole",
                fix_suggestion="Install BlackHole: brew install blackhole-2ch. Then reconfigure in Audio MIDI Setup.",
            )

        return CheckResult(
            status=CheckStatus.OK,
            message=f"BlackHole found at index {self.device_index}: {device_name}",
        )

    def verbose_detail(self) -> str | None:
        try:
            devices = _parse_audio_devices()
            device_name = devices.get(self.device_index)
            return device_name
        except Exception:
            return None


class FFmpegDeviceCheck(HealthCheck):
    """Verify that the microphone device at configured index is reachable."""

    name = "Microphone Device"

    def __init__(self, device_index: int = 2) -> None:
        self.device_index = device_index

    def check(self) -> CheckResult:
        try:
            devices = _parse_audio_devices()
        except FileNotFoundError:
            return CheckResult(
                status=CheckStatus.ERROR,
                message="ffmpeg not found",
                fix_suggestion="Install ffmpeg: brew install ffmpeg",
            )

        device_name = devices.get(self.device_index)
        if device_name is None:
            return CheckResult(
                status=CheckStatus.ERROR,
                message=f"No audio device at index {self.device_index}",
                fix_suggestion=f"Run 'ffmpeg -f avfoundation -list_devices true -i \"\"' to see available devices.",
            )

        return CheckResult(
            status=CheckStatus.OK,
            message=f"Microphone device found at index {self.device_index}: {device_name}",
        )

    def verbose_detail(self) -> str | None:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            first_line = result.stdout.splitlines()[0] if result.stdout.splitlines() else None
            return first_line
        except Exception:
            return None


class DiskSpaceCheck(HealthCheck):
    """Verify sufficient disk space for recordings (>5GB)."""

    name = "Disk Space"

    MIN_BYTES = 5 * 1024 * 1024 * 1024  # 5GB

    def check(self) -> CheckResult:
        usage = shutil.disk_usage("/")
        free_gb = usage.free / (1024**3)

        if usage.free < self.MIN_BYTES:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Low disk space: {free_gb:.1f} GB free (minimum 5 GB recommended)",
                fix_suggestion="Free up disk space before recording.",
            )

        return CheckResult(
            status=CheckStatus.OK,
            message=f"Disk space OK: {free_gb:.1f} GB free",
        )

    def verbose_detail(self) -> str | None:
        usage = shutil.disk_usage("/")
        return f"{usage.free / (1024**3):.1f} GB free"


HF_HUB_CACHE = Path.home() / ".cache" / "huggingface" / "hub"
MODEL_CACHE_DIR = HF_HUB_CACHE / "models--mlx-community--whisper-large-v3-turbo"
PYANNOTE_DIARIZATION_CACHE = HF_HUB_CACHE / "models--pyannote--speaker-diarization-3.1"
PYANNOTE_SEGMENTATION_CACHE = HF_HUB_CACHE / "models--pyannote--segmentation-3.0"


class MlxWhisperCheck(HealthCheck):
    """Verify that mlx-whisper is importable."""

    name = "mlx-whisper"

    def check(self) -> CheckResult:
        try:
            import mlx_whisper  # noqa: F401
            return CheckResult(status=CheckStatus.OK, message="mlx-whisper importable")
        except ImportError:
            return CheckResult(
                status=CheckStatus.ERROR,
                message="mlx-whisper not installed",
                fix_suggestion="pip install mlx-whisper",
            )

    def verbose_detail(self) -> str | None:
        try:
            ver = importlib.metadata.version("mlx-whisper")
            return f"mlx-whisper {ver}"
        except Exception:
            return None


class WhisperModelCheck(HealthCheck):
    """Verify that whisper-large-v3-turbo model is cached locally."""

    name = "Whisper Model Cache"

    def check(self) -> CheckResult:
        if MODEL_CACHE_DIR.exists():
            return CheckResult(
                status=CheckStatus.OK,
                message=f"Whisper model cached at {MODEL_CACHE_DIR}",
            )
        return CheckResult(
            status=CheckStatus.WARNING,
            message="Whisper model not cached — will download on first use (run: meet transcribe)",
            fix_suggestion="Run: meet transcribe (auto-downloads on first use)",
        )

    def verbose_detail(self) -> str | None:
        if not MODEL_CACHE_DIR.exists():
            return None
        try:
            total_bytes = sum(
                f.stat().st_size for f in MODEL_CACHE_DIR.rglob("*") if f.is_file()
            )
            if total_bytes >= 1024**3:
                size_str = f"{total_bytes / (1024**3):.1f} GB"
            else:
                size_str = f"{total_bytes / (1024**2):.0f} MB"
            return f"{MODEL_CACHE_DIR} ({size_str})"
        except Exception:
            return None


class OllamaRunningCheck(HealthCheck):
    """Verify that Ollama server is running at localhost:11434."""

    name = "Ollama Service"

    def check(self) -> CheckResult:
        try:
            resp = requests.get("http://localhost:11434", timeout=5)
            if resp.status_code == 200:
                return CheckResult(status=CheckStatus.OK, message="Ollama is running")
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
        return CheckResult(
            status=CheckStatus.ERROR,
            message="Ollama is not running",
            fix_suggestion="Run: ollama serve",
        )

    def verbose_detail(self) -> str | None:
        try:
            resp = requests.get("http://localhost:11434/api/version", timeout=5)
            if resp.status_code == 200:
                version = resp.json().get("version", "unknown")
                return f"Ollama {version}"
        except Exception:
            pass
        return None


class OllamaModelCheck(HealthCheck):
    """Verify that llama3.1:8b model is available in Ollama."""

    name = "Ollama Model (llama3.1:8b)"

    def check(self) -> CheckResult:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10,
            )
            if "llama3.1:8b" in result.stdout:
                return CheckResult(
                    status=CheckStatus.OK,
                    message="llama3.1:8b model is available",
                )
            return CheckResult(
                status=CheckStatus.ERROR,
                message="llama3.1:8b model not found in ollama list",
                fix_suggestion="Run: ollama pull llama3.1:8b",
            )
        except FileNotFoundError:
            return CheckResult(
                status=CheckStatus.ERROR,
                message="ollama CLI not found",
                fix_suggestion="Install Ollama: https://ollama.com",
            )

    def verbose_detail(self) -> str | None:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10,
            )
            if "llama3.1:8b" in result.stdout:
                return "llama3.1:8b confirmed in local library"
        except Exception:
            pass
        return None


class NotionTokenCheck(HealthCheck):
    """Verify Notion token is set in config and API call succeeds."""

    name = "Notion Token"

    def __init__(self, token: str | None) -> None:
        self.token = token

    def check(self) -> CheckResult:
        if not self.token:
            return CheckResult(
                status=CheckStatus.WARNING,
                message="Notion token not configured",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        try:
            client = NotionClient(auth=self.token)
            client.users.me()
            return CheckResult(status=CheckStatus.OK, message="Notion token valid")
        except APIResponseError as exc:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Notion token invalid: {exc}",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        except Exception as exc:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Notion API unreachable: {exc}",
                fix_suggestion="Check network or Notion token.",
            )

    def verbose_detail(self) -> str | None:
        if not self.token:
            return None
        if len(self.token) > 7:
            return f"Token: {self.token[:4]}***{self.token[-3:]}"
        return "Token: ***"


class NotionDatabaseCheck(HealthCheck):
    """Verify parent page ID is set and accessible."""

    name = "Notion Parent Page"

    def __init__(self, token: str | None, parent_page_id: str | None) -> None:
        self.token = token
        self.parent_page_id = parent_page_id

    def check(self) -> CheckResult:
        if not self.parent_page_id:
            return CheckResult(
                status=CheckStatus.WARNING,
                message="Notion parent page ID not configured",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        if not self.token:
            return CheckResult(
                status=CheckStatus.WARNING,
                message="Notion token not set — cannot verify parent page",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        try:
            client = NotionClient(auth=self.token)
            client.pages.retrieve(page_id=self.parent_page_id)
            return CheckResult(status=CheckStatus.OK, message="Notion parent page accessible")
        except APIResponseError as exc:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Notion parent page inaccessible: {exc}",
                fix_suggestion="Check page ID and that the integration has access.",
            )


class PythonVersionCheck(HealthCheck):
    """Verify Python version is >=3.11 and <3.14."""

    name = "Python Version"

    def check(self) -> CheckResult:
        import sys
        major, minor = sys.version_info[:2]
        version_str = f"{major}.{minor}.{sys.version_info[2]}"
        if major < 3 or (major == 3 and minor < 11):
            return CheckResult(
                status=CheckStatus.ERROR,
                message=f"Python {version_str} — requires >=3.11, <3.14",
                fix_suggestion="Install Python 3.11-3.13 from python.org or via pyenv",
            )
        if major == 3 and minor >= 14:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Python {version_str} — not officially tested with >=3.14",
                fix_suggestion="Consider Python 3.11-3.13 for best compatibility",
            )
        return CheckResult(
            status=CheckStatus.OK,
            message=f"Python {version_str}",
        )

    def verbose_detail(self) -> str | None:
        import sys
        return f"{sys.version} ({sys.executable})"


class OpenaiWhisperConflictCheck(HealthCheck):
    """Verify that openai-whisper is not installed alongside mlx-whisper."""

    name = "OpenAI Whisper Conflict"

    def check(self) -> CheckResult:
        try:
            import importlib.util
            spec = importlib.util.find_spec("whisper")
            if spec is not None:
                # Check if it's openai-whisper (not mlx-whisper)
                origin = str(spec.origin) if spec.origin else ""
                if "openai" in origin or "whisper" in origin:
                    # Try to distinguish: openai-whisper has whisper.load_model
                    try:
                        import importlib.metadata as im
                        im.version("openai-whisper")
                        return CheckResult(
                            status=CheckStatus.WARNING,
                            message="openai-whisper is installed alongside mlx-whisper",
                            fix_suggestion="Run: pip uninstall openai-whisper",
                        )
                    except im.PackageNotFoundError:
                        pass
        except Exception:
            pass
        return CheckResult(
            status=CheckStatus.OK,
            message="No openai-whisper conflict detected",
        )


class PyannoteCheck(HealthCheck):
    """Verify that pyannote.audio is importable (per D-13)."""

    name = "pyannote.audio"

    def check(self) -> CheckResult:
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import pyannote.audio  # noqa: F401
            return CheckResult(status=CheckStatus.OK, message="pyannote.audio importable")
        except ImportError:
            return CheckResult(
                status=CheckStatus.ERROR,
                message="pyannote.audio not installed — speaker diarization unavailable",
                fix_suggestion="pip install 'pyannote.audio==3.3.2'",
            )

    def verbose_detail(self) -> str | None:
        try:
            ver = importlib.metadata.version("pyannote-audio")
            return f"pyannote.audio {ver}"
        except Exception:
            return None


class HuggingFaceTokenCheck(HealthCheck):
    """Verify HF token is present in config and can reach HuggingFace (per D-14)."""

    name = "HuggingFace Token"

    def __init__(self, token: str | None) -> None:
        self.token = token

    def check(self) -> CheckResult:
        if not self.token:
            return CheckResult(
                status=CheckStatus.WARNING,
                message="HuggingFace token not configured — speaker diarization disabled",
                fix_suggestion="Run: meet init to configure HuggingFace token",
            )
        try:
            HfApi().whoami(token=self.token)
            return CheckResult(status=CheckStatus.OK, message="HuggingFace token valid")
        except Exception as exc:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"HuggingFace token validation failed: {exc}",
                fix_suggestion="Check token at https://hf.co/settings/tokens",
            )

    def verbose_detail(self) -> str | None:
        if not self.token:
            return None
        if len(self.token) > 7:
            return f"Token: {self.token[:4]}***{self.token[-3:]}"
        return "Token: ***"


class PyannoteModelCheck(HealthCheck):
    """Verify pyannote/speaker-diarization-3.1 model is cached locally (per D-15)."""

    name = "Pyannote Model Cache"

    def check(self) -> CheckResult:
        if PYANNOTE_DIARIZATION_CACHE.exists():
            return CheckResult(
                status=CheckStatus.OK,
                message="pyannote/speaker-diarization-3.1 model cached locally",
            )
        return CheckResult(
            status=CheckStatus.WARNING,
            message="pyannote/speaker-diarization-3.1 not cached — will download on first use",
            fix_suggestion=(
                "Run: meet transcribe (auto-downloads). "
                "First, accept conditions at huggingface.co/pyannote/speaker-diarization-3.1 "
                "and huggingface.co/pyannote/segmentation-3.0"
            ),
        )

    def verbose_detail(self) -> str | None:
        if not PYANNOTE_DIARIZATION_CACHE.exists():
            return None
        try:
            total_bytes = sum(
                f.stat().st_size for f in PYANNOTE_DIARIZATION_CACHE.rglob("*") if f.is_file()
            )
            if total_bytes >= 1024**3:
                size_str = f"{total_bytes / (1024**3):.1f} GB"
            else:
                size_str = f"{total_bytes / (1024**2):.0f} MB"
            return f"{PYANNOTE_DIARIZATION_CACHE} ({size_str})"
        except Exception:
            return None
