import re
import shutil
import subprocess
from pathlib import Path

import requests

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


HF_HUB_CACHE = Path.home() / ".cache" / "huggingface" / "hub"
MODEL_CACHE_DIR = HF_HUB_CACHE / "models--mlx-community--whisper-large-v3-turbo"


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
