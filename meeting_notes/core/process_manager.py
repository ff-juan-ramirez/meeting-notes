import os
import signal
import subprocess


def start_ffmpeg(cmd: list[str]) -> subprocess.Popen:
    """Start ffmpeg as a new process group for clean termination."""
    return subprocess.Popen(
        cmd,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stop_gracefully(proc: subprocess.Popen, timeout: int = 5) -> None:
    """Stop ffmpeg: SIGTERM to process group, wait, escalate to SIGKILL."""
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait()
    except ProcessLookupError:
        pass  # already dead
