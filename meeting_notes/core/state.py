import json
import os
from pathlib import Path
from typing import Any


def write_state(state_path: Path, state: dict[str, Any]) -> None:
    """Write state atomically via temp file + POSIX rename."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(state_path)


def read_state(state_path: Path) -> dict[str, Any] | None:
    """Read state from JSON file. Returns None if file doesn't exist."""
    if not state_path.exists():
        return None
    return json.loads(state_path.read_text())


def clear_state(state_path: Path) -> None:
    """Remove state file if it exists."""
    if state_path.exists():
        state_path.unlink()


def check_for_stale_session(state: dict[str, Any]) -> bool:
    """Check if recorded PID is still alive.

    Returns True if process IS alive (real duplicate session).
    Returns False if process is dead (stale PID, safe to clear).
    Returns False if no PID in state.
    """
    pid = state.get("pid")
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True   # process is alive
    except ProcessLookupError:
        return False  # stale PID
    except PermissionError:
        return True   # process exists, not ours
