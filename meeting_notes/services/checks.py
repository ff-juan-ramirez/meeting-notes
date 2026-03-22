import re
import shutil
import subprocess

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
