# Phase 1: Audio Capture + Health Check Design - Research

**Researched:** 2026-03-22
**Domain:** Python CLI, ffmpeg avfoundation, macOS audio, pluggable health check architecture
**Confidence:** HIGH

---

## Summary

Phase 1 establishes the entire project foundation: the Python package scaffold, core infrastructure (config, state, storage), ffmpeg-based audio capture from two avfoundation devices, and the pluggable health check architecture that every subsequent phase builds on. All prior research has already validated and locked the technical stack — this research confirms implementation-level details, verifies environment state, and surfaces the specific code patterns needed to plan precise tasks.

The environment is fully ready: ffmpeg 8.1, BlackHole 2ch (index 1), MacBook Pro Microphone (index 2), click 8.3.1, rich 14.3.3, mlx-whisper 0.4.3, and pytest 9.0.2 are all installed and functioning. Python 3.14.3 is the system Python and all key packages import successfully — see Environment Availability section for an important note on the python_requires constraint. No user data directories exist yet (fresh install state), so no migration concerns.

The two highest-risk implementation details for this phase are: (1) ffmpeg device listing must parse stderr (not stdout), and the audio section must be isolated from the video section by detecting the `AVFoundation audio devices` header line; (2) WAV header finalization requires SIGTERM to ffmpeg's process group (not SIGKILL), and `start_new_session=True` is verified to work correctly on this machine for clean `os.killpg()` termination.

**Primary recommendation:** Implement in build order — core infrastructure first (config, storage, state, health_check base), then process_manager and audio service, then CLI commands. The health_check ABC design must be finalized in Plan 1.3 before any phase-specific checks are added, because all future phases plug into it.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIO-01 | `meet record` captures system audio (BlackHole :1) + mic (:2) via ffmpeg avfoundation amix, WAV 16kHz mono pcm_s16le | ffmpeg 8.1 installed, avfoundation confirmed, amix+aresample syntax verified via test run |
| AUDIO-02 | `meet stop` sends SIGTERM → wait 5s → SIGKILL; finalizes WAV header | `start_new_session=True` + `os.killpg()` verified working on this machine |
| AUDIO-03 | Recording state (session_id, PID, output path, start time) persisted atomically to state.json; survives CLI crash | Atomic write via temp+replace verified; `os.kill(pid, 0)` stale-PID detection verified |
| AUDIO-04 | `meet record` fails with clear error if already recording | Read state.json, check PID liveness with `os.kill(pid, 0)`, exit with message |
| AUDIO-05 | Audio saved to `~/.local/share/meeting-notes/recordings/{timestamp}-{uuid}.wav` | XDG paths verified; directory does not exist yet (must be created on first run) |
| AUDIO-06 | ffmpeg uses explicit device indices (:1, :2) — never device names | Locked decision; verified device indices match expected devices on this machine |
| SETUP-01 | `meet init` wizard: collect Notion token, database ID, device indices, write config.json | Config dataclass + JSON write + interactive Click prompts |
| SETUP-02 | `meet init` triggers ~1s test recording to force macOS mic permission prompt | `ffmpeg -f avfoundation -i ":2" -t 1 /tmp/test.wav` — syntax verified |
| SETUP-03 | `meet doctor` checks all prerequisites, reports pass/fail with fix suggestions | Pluggable HealthCheck ABC — CheckResult dataclass with status/message/fix_suggestion |
| SETUP-04 | Phase 1 checks: BlackHole at :1 confirmed, ffmpeg device :2 reachable, disk >5GB | Parsing approach verified via Python + subprocess stderr capture; shutil.disk_usage verified |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.3.1 | CLI command framework | Locked decision; installed and verified |
| rich | 14.3.3 | Terminal output (spinners, panels, status) | Locked decision; installed and verified |
| ffmpeg | 8.1 | Audio capture via avfoundation | Locked decision; installed with avfoundation + audiotoolbox support |
| BlackHole 2ch | 0.6.1 | Virtual audio device for system audio capture | Installed; confirmed at device index 1 |
| Python stdlib | 3.14.3 | subprocess, signal, os, pathlib, json, dataclasses, abc, uuid, shutil | All verified working |
| pytest | 9.0.2 | Test framework | Installed; `python3 -m pytest` works |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psutil | NOT INSTALLED | Process management utilities | NOT available — use `os.kill(pid, 0)` and `os.killpg()` instead (verified) |
| tomllib | stdlib (3.11+) | TOML parsing | Available in Python 3.11+ stdlib; do not use as external dep |
| unittest.mock | stdlib | Mocking subprocess for tests | Use for health check and process manager unit tests |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `os.killpg()` | psutil | psutil is not installed; os.killpg works correctly with `start_new_session=True` |
| stdlib json | tomllib/tomlkit | JSON is locked decision; toml would require external dep |
| Click | argparse, Typer | Click is locked; Typer builds on click |

**Installation:**
```bash
# All packages already installed. For fresh install:
pip install click rich
# ffmpeg and blackhole-2ch via brew (already installed)
```

**Version verification (confirmed 2026-03-22):**
```
click:      8.3.1  (latest)
rich:       14.3.3 (latest)
mlx-whisper: 0.4.3 (latest)
pytest:     9.0.2  (latest)
ffmpeg:     8.1    (homebrew, latest)
```

---

## Architecture Patterns

### Recommended Project Structure
```
meeting_notes/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py                  # Click group entry point
│   └── commands/
│       ├── __init__.py
│       ├── record.py            # meet record + meet stop
│       ├── init.py              # meet init wizard
│       └── doctor.py            # meet doctor
│
├── core/
│   ├── __init__.py
│   ├── config.py                # Config dataclass + JSON load/save
│   ├── state.py                 # Atomic state.json read/write
│   ├── storage.py               # XDG paths + directory creation
│   ├── process_manager.py       # ffmpeg subprocess + process group management
│   └── health_check.py          # Abstract HealthCheck + HealthCheckSuite + CheckResult
│
└── services/
    ├── __init__.py
    └── audio.py                 # ffmpeg command builder + start/stop recording

pyproject.toml
tests/
├── __init__.py
├── conftest.py                  # Shared fixtures
├── test_config.py               # Config load/save tests
├── test_state.py                # Atomic write, PID detection
├── test_health_check.py         # HealthCheck ABC, suite execution
└── test_audio.py                # ffmpeg command builder (no actual recording)
```

### Pattern 1: Pluggable Health Check Architecture
**What:** Abstract base class `HealthCheck` with `check() -> CheckResult`. A `HealthCheckSuite` holds a registry of checks and runs them all. Each phase adds its own checks; `meet doctor` runs the suite.
**When to use:** Every time a new phase introduces a prerequisite that must be validated.
**Example:**
```python
# core/health_check.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class CheckStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class CheckResult:
    status: CheckStatus
    message: str
    fix_suggestion: str | None = None

class HealthCheck(ABC):
    name: str  # Human-readable name for Rich output

    @abstractmethod
    def check(self) -> CheckResult:
        pass

class HealthCheckSuite:
    def __init__(self) -> None:
        self._checks: list[HealthCheck] = []

    def register(self, check: HealthCheck) -> None:
        self._checks.append(check)

    def run_all(self) -> list[tuple[HealthCheck, CheckResult]]:
        return [(c, c.check()) for c in self._checks]
```

### Pattern 2: Atomic State File
**What:** Write to a `.tmp` file then `Path.replace()` — POSIX rename is atomic, prevents corrupt reads on crash.
**When to use:** Every write to `state.json`.
**Example:**
```python
# core/state.py
import json
from pathlib import Path

def write_state(state_path: Path, state: dict) -> None:
    tmp = state_path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(state_path)  # atomic on POSIX/macOS
```

### Pattern 3: ffmpeg Process Group Management
**What:** Spawn ffmpeg with `start_new_session=True` so it gets its own process group ID (PGID == PID). Use `os.killpg(os.getpgid(pid), signal.SIGTERM)` to send SIGTERM to the entire group. Wait up to 5 seconds; escalate to SIGKILL if needed.
**When to use:** `meet stop` and `meet record` Ctrl+C handler.
**Example:**
```python
# core/process_manager.py
import os, signal, subprocess
from pathlib import Path

def start_ffmpeg(cmd: list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        cmd,
        start_new_session=True,   # new process group; PGID == PID
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def stop_gracefully(proc: subprocess.Popen, timeout: int = 5) -> None:
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait()
    except ProcessLookupError:
        pass  # already dead
```

### Pattern 4: ffmpeg Command with aresample + amix
**What:** Two avfoundation inputs by index, resampled to 16kHz before mixing, then amix, then WAV output.
**When to use:** Building the ffmpeg command in `services/audio.py`.
**Example (verified via test run):**
```python
# services/audio.py
def build_ffmpeg_command(
    system_idx: int,
    mic_idx: int,
    output_path: str,
) -> list[str]:
    return [
        "ffmpeg",
        "-f", "avfoundation", "-i", f":{system_idx}",
        "-f", "avfoundation", "-i", f":{mic_idx}",
        "-filter_complex",
        "[0:a]aresample=16000[a0];[1:a]aresample=16000[a1];"
        "[a0][a1]amix=inputs=2:normalize=0[aout]",
        "-map", "[aout]",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        "-y",
        output_path,
    ]
```

### Pattern 5: avfoundation Device Listing Parse (for BlackHoleCheck)
**What:** Run `ffmpeg -f avfoundation -list_devices true -i ""`, capture **stderr**, detect audio section boundary, parse `[N] DeviceName` lines.
**When to use:** `BlackHoleCheck.check()` and `FFmpegDeviceCheck.check()`.
**Example (verified working):**
```python
# Within BlackHoleCheck.check()
import subprocess, re

result = subprocess.run(
    ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
    capture_output=True, text=True
)
# Device list is on STDERR (not stdout)
in_audio = False
audio_devices: dict[int, str] = {}
for line in result.stderr.splitlines():
    if "AVFoundation audio devices" in line:
        in_audio = True
        continue
    if "AVFoundation video devices" in line:
        in_audio = False
        continue
    if in_audio:
        m = re.search(r'\[(\d+)\] (.+)', line)
        if m:
            audio_devices[int(m.group(1))] = m.group(2).strip()

device_name = audio_devices.get(system_device_index, "")
is_blackhole = "BlackHole" in device_name
```

### Pattern 6: Stale PID Detection for Crash Recovery
**What:** On `meet record`, read state.json if it exists. If `pid` is present, call `os.kill(pid, 0)` — if `ProcessLookupError` is raised, the PID is stale (process is dead). Clear the state and proceed.
**When to use:** Start of `meet record` command.
**Example:**
```python
# cli/commands/record.py (crash recovery check)
import os

def check_for_stale_session(state: dict) -> bool:
    pid = state.get("pid")
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True   # process is alive — real duplicate
    except ProcessLookupError:
        return False  # stale PID — safe to clear
    except PermissionError:
        return True   # process exists, not ours
```

### Pattern 7: Config Dataclass
**What:** Dataclass with type-annotated fields, loaded from JSON. Supports `version` field for future migrations.
**When to use:** `core/config.py` load/save.
**Example:**
```python
# core/config.py
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
    # notion, llm, storage fields added but not required in Phase 1

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        # Simple deserialization — expand for nested fields
        audio = AudioConfig(**data.get("audio", {}))
        return cls(version=data.get("version", 1), audio=audio)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(asdict(self), indent=2))
        tmp.replace(path)
```

### Anti-Patterns to Avoid
- **Using device names in ffmpeg command:** Device names are not stable across macOS versions or after hardware changes. Always use integer indices (`:1`, `:2`).
- **Writing .m4a instead of WAV:** mlx-whisper cannot process .m4a. All audio output must be WAV (pcm_s16le, 16kHz, mono).
- **Sending SIGKILL directly:** SIGKILL does not let ffmpeg finalize the WAV RIFF header. Always try SIGTERM first.
- **Not capturing stderr for ffmpeg device list:** The avfoundation device list is written to stderr, not stdout. Using `stdout` capture returns nothing.
- **Parsing `ffmpeg -list_devices` without splitting audio/video sections:** Video and audio devices are both listed with `[N]` format. Must detect the `AVFoundation audio devices` header to avoid matching video device indices.
- **Using psutil for process management:** psutil is not installed in this environment. Use `os.kill(pid, 0)` for liveness checks and `os.killpg()` for termination.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Terminal output (spinners, panels, tables) | Custom ANSI escape codes | rich | Rich handles TTY detection, color codes, complex layouts; already installed |
| CLI argument parsing | Manual sys.argv parsing | click | Click handles type coercion, help text, subcommands, error messages; already installed |
| Process group management | Custom fork/exec logic | subprocess + os.killpg | Standard POSIX; `start_new_session=True` verified working |
| Atomic file writes | Custom locking | `Path.with_suffix('.tmp')` + `.replace()` | POSIX rename is atomic; no external dep needed |
| XDG directory resolution | Hardcoded `~/.config` | `os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')` | Respects user overrides; standard pattern |
| Disk space check | Reading `/proc/mounts` | `shutil.disk_usage('/')` | Cross-platform stdlib; verified working |

**Key insight:** This phase intentionally avoids external dependencies beyond click, rich, and ffmpeg. Everything else (process management, atomic writes, XDG paths, JSON config) uses stdlib. This keeps the install footprint minimal and avoids version conflicts.

---

## Common Pitfalls

### Pitfall P1: Device Index Volatility
**What goes wrong:** After plugging in USB audio, connecting AirPods, or macOS update, avfoundation re-enumerates devices and BlackHole may shift from index 1 to a different index. Recording appears to work but captures silence or wrong audio.
**Why it happens:** avfoundation index assignment is dynamic, not stable across hardware changes.
**How to avoid:** `BlackHoleCheck` must parse the device name at index 1 and verify it contains "BlackHole", not just that the index is reachable. The check must run at the start of `meet record` (or at least in `meet doctor`).
**Warning signs:** Recording completes but WAV has no audio content; meet doctor passes index check but name check would fail.

### Pitfall P2: amix Sample Rate Mismatch (Audio Artifacts)
**What goes wrong:** Without explicit resampling, if BlackHole and the microphone run at different native rates (e.g., 48kHz vs 44.1kHz), amix produces stuttering or distorted audio that still has correct file length.
**Why it happens:** amix does not auto-resample inputs; it requires matching sample rates.
**How to avoid:** Always add `aresample=16000` for each input BEFORE the amix step. The verified command is: `[0:a]aresample=16000[a0];[1:a]aresample=16000[a1];[a0][a1]amix=inputs=2:normalize=0[aout]`
**Warning signs:** WAV file has expected duration but audio is garbled; transcription produces nonsense.

### Pitfall P3: Malformed WAV Header on Crash / SIGKILL
**What goes wrong:** If ffmpeg is killed with SIGKILL (or crashes), the WAV RIFF header (which contains the final file size) is never written. The file looks like it has data but mlx-whisper rejects it as invalid.
**Why it happens:** ffmpeg writes WAV size fields into the header at the end of recording, not at the beginning.
**How to avoid:** Always use `SIGTERM` first with a 5-second wait. Document clearly in `meet stop` output. `DiskSpaceCheck` in meet doctor preemptively guards against disk-full scenarios.
**Warning signs:** mlx-whisper error "invalid audio format" or "RIFF header malformed" on a WAV that has non-zero file size.

### Pitfall P4: Microphone Permission Dialog During First Recording
**What goes wrong:** On first run, macOS shows a "Allow access to microphone?" dialog during `meet record`, causing ffmpeg to hang until the user responds. This interrupts the first real meeting recording.
**Why it happens:** macOS TCC (Transparency, Consent, Control) requires explicit per-application approval.
**How to avoid:** `meet init` must trigger a short (~1s) test recording: `ffmpeg -f avfoundation -i ":2" -t 1 /tmp/meet-permission-test.wav`. This forces the dialog before the first real meeting. Verified syntax: `ffmpeg -f avfoundation -i ":2" -t 1 /tmp/test.wav`.
**Warning signs:** First `meet record` appears to hang at startup with no output; Activity Monitor shows no CPU usage from ffmpeg.

### Pitfall P5: Python Version Mismatch Between System and Venv
**What goes wrong:** System Python is 3.14.3. The planned `python_requires = ">=3.11,<3.14"` in pyproject.toml would reject the installed Python at install time. This is a direct conflict.
**Why it happens:** The original requirement `<3.14` was set conservatively because mlx-whisper had not been tested on 3.14. But mlx-whisper 0.4.3 imports and runs correctly on Python 3.14.3 on this machine.
**How to avoid:** Update `python_requires` to `">=3.11,<3.15"` or `">=3.11"` to allow 3.14. See Environment Availability section for full analysis. Alternatively, install Python 3.13 via `brew install python@3.13` and create a dedicated venv.
**Warning signs:** `pip install .` fails with "Requires-Python" incompatibility during Phase 6.

### Pitfall P6: ffmpeg stderr Goes to Terminal During Recording
**What goes wrong:** By default, ffmpeg writes progress/stats to stderr. When recording in the background, this output appears on the terminal and looks like errors.
**Why it happens:** ffmpeg default behavior.
**How to avoid:** Redirect stderr to `subprocess.DEVNULL` when starting the recording process. If debugging is needed, redirect to a log file.

### Pitfall P7: Signal Handler Race Condition in Click
**What goes wrong:** Click installs its own SIGINT handler for standalone mode. If `meet record` and `meet stop` both set signal handlers, there can be double-handling.
**Why it happens:** Click catches exceptions including `KeyboardInterrupt`.
**How to avoid:** Set `standalone_mode=False` on the `meet record` Click command, or use `@click.pass_context` and handle the signal setup explicitly. Register signal handlers in the Click callback before blocking.

---

## Runtime State Inventory

This is a greenfield phase — no existing runtime state to migrate.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — `~/.config/meeting-notes/` and `~/.local/share/meeting-notes/` do not exist | Directories created on first `meet record` or `meet init` |
| Live service config | None — no running meeting-notes services | None |
| OS-registered state | None — no launchd plists, cron jobs, or task scheduler entries | None |
| Secrets/env vars | None — `NOTION_TOKEN` not yet set | None |
| Build artifacts | None — no prior installation | None |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.x | All code | Yes | 3.14.3 | — (see note below) |
| ffmpeg with avfoundation | AUDIO-01 to AUDIO-06 | Yes | 8.1 | None — blocking if absent |
| BlackHole 2ch | AUDIO-01, SETUP-04 | Yes | 0.6.1 cask | None — user must install |
| click | CLI layer | Yes | 8.3.1 | — |
| rich | CLI output | Yes | 14.3.3 | — |
| mlx-whisper | Not Phase 1, but installed | Yes | 0.4.3 | — |
| pytest | Tests | Yes | 9.0.2 | — |
| psutil | process management | No | — | Use `os.kill(pid, 0)` + `os.killpg()` (verified) |
| uv | Package management | No | — | Use `pip install` |
| Python 3.11/3.12/3.13 | venv if 3.14 excluded | No | — | `brew install python@3.13` |

**Python version note (HIGH importance):** The system Python is 3.14.3. The project's existing research suggests `python_requires = ">=3.11,<3.14"`, but:
- mlx-whisper 0.4.3 imports and runs on 3.14.3 (verified)
- click 8.3.1, rich 14.3.3, all stdlib modules work on 3.14.3 (verified)
- No Python 3.11/3.12/3.13 is installed; only `python@3.14` is in brew
- **Recommendation:** Use `python_requires = ">=3.11,<3.15"` to include 3.14. If strict 3.11/3.12 is required, `brew install python@3.13` before Phase 6 packaging.

**Missing dependencies with no fallback:**
- None — all Phase 1 required dependencies are available.

**Missing dependencies with fallback:**
- `psutil` — not installed; `os.kill(pid, 0)` and `os.killpg()` are sufficient substitutes (verified).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (Wave 0 — add `[tool.pytest.ini_options]` section) |
| Quick run command | `python3 -m pytest tests/ -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDIO-01 | ffmpeg command built with correct args (aresample, amix, WAV, indices) | unit | `pytest tests/test_audio.py::test_build_ffmpeg_command -x` | Wave 0 |
| AUDIO-02 | stop_gracefully sends SIGTERM, waits, escalates to SIGKILL on timeout | unit (mock) | `pytest tests/test_process_manager.py::test_stop_gracefully -x` | Wave 0 |
| AUDIO-03 | Atomic write persists state; crash-safe temp+replace pattern | unit | `pytest tests/test_state.py::test_atomic_write -x` | Wave 0 |
| AUDIO-04 | Duplicate session detection: live PID → error; stale PID → clear and proceed | unit | `pytest tests/test_state.py::test_stale_pid_detection -x` | Wave 0 |
| AUDIO-05 | Output path follows `{timestamp}-{uuid}.wav` in XDG data dir | unit | `pytest tests/test_storage.py::test_recording_path -x` | Wave 0 |
| AUDIO-06 | ffmpeg command uses `:1` and `:2` (indices, not names) | unit | covered by AUDIO-01 test | Wave 0 |
| SETUP-03 | HealthCheckSuite runs all registered checks; returns results | unit | `pytest tests/test_health_check.py::test_suite_runs_all_checks -x` | Wave 0 |
| SETUP-04 | BlackHoleCheck parses stderr correctly; confirms name contains "BlackHole" | unit (mock subprocess) | `pytest tests/test_health_check.py::test_blackhole_check_parses_stderr -x` | Wave 0 |
| SETUP-04 | DiskSpaceCheck returns WARNING when < 5GB | unit (mock shutil) | `pytest tests/test_health_check.py::test_disk_space_check -x` | Wave 0 |

**Manual-only tests (cannot be automated without hardware):**
- SETUP-02: `meet init` mic permission prompt (requires first-run macOS TCC dialog)
- AUDIO-01 (integration): Actual recording produces valid WAV (requires mic access)

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/ -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` — empty init file
- [ ] `tests/conftest.py` — shared fixtures (tmp_path for state/config tests, mock subprocess fixture)
- [ ] `tests/test_config.py` — covers AUDIO-05, Config load/save, XDG path resolution
- [ ] `tests/test_state.py` — covers AUDIO-03, AUDIO-04 (atomic write, stale PID)
- [ ] `tests/test_storage.py` — covers AUDIO-05 (recording path generation)
- [ ] `tests/test_health_check.py` — covers SETUP-03, SETUP-04 (ABC, suite, BlackHoleCheck, DiskSpaceCheck)
- [ ] `tests/test_audio.py` — covers AUDIO-01, AUDIO-06 (ffmpeg command builder)
- [ ] `tests/test_process_manager.py` — covers AUDIO-02 (SIGTERM/SIGKILL, mock subprocess)
- [ ] `pyproject.toml` — must exist with `[tool.pytest.ini_options]` and `testpaths = ["tests"]`

---

## Code Examples

### pyproject.toml (PEP 621)
```toml
[project]
name = "meeting-notes"
version = "0.1.0"
description = "Local meeting capture, transcription, and Notion notes"
requires-python = ">=3.11,<3.15"
dependencies = [
    "click>=8.1",
    "rich>=13.0",
]

[project.scripts]
meet = "meeting_notes.cli.main:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Click entry point pattern
```python
# meeting_notes/cli/main.py
import click

@click.group()
def main() -> None:
    """Meeting notes CLI."""
    pass

from meeting_notes.cli.commands.record import record, stop
from meeting_notes.cli.commands.init import init
from meeting_notes.cli.commands.doctor import doctor

main.add_command(record)
main.add_command(stop)
main.add_command(init)
main.add_command(doctor)
```

### Rich status output pattern
```python
from rich.console import Console
from rich.status import Status

console = Console()

with Status("[green]Recording...[/green]", console=console) as status:
    # blocking wait for stop signal
    pass
```

### XDG path resolution
```python
# core/storage.py
import os
from pathlib import Path

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
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ffmpeg device names | Device indices (:1, :2) | macOS Ventura+ | Names change; indices are stable within a session |
| Aggregate Device in macOS | Two inputs + amix filter | Pre-2022 | Aggregate Device has latency/reliability issues |
| `python setup.py` | `pyproject.toml` (PEP 621) | Python 3.11/PEP 517/518 | setup.py is deprecated |
| ffmpeg SIGINT only | SIGTERM + SIGKILL escalation | ffmpeg 4.x+ | SIGINT not always sufficient for WAV finalization from external process |

**Deprecated/outdated:**
- `setup.py`: Use pyproject.toml with setuptools backend
- `python -m pytest` with `setup.cfg`: Use `[tool.pytest.ini_options]` in pyproject.toml
- `signal.SIGINT` to ffmpeg from Python: avfoundation capture needs `SIGTERM` to process group for clean WAV close

---

## Open Questions

1. **Python version constraint: `<3.14` vs `<3.15`**
   - What we know: All packages (mlx-whisper, click, rich) work on Python 3.14.3 (verified). Only Python 3.14 is installed on this machine.
   - What's unclear: Were there specific 3.14 breaking changes that motivated the `<3.14` constraint in prior research? mlx-whisper 0.4.3 appears to have resolved any earlier issues.
   - Recommendation: Relax to `">=3.11,<3.15"` in pyproject.toml. If `python_requires` must remain `<3.14`, install `python@3.13` via brew before Phase 6 packaging. **This decision must be made in Plan 1.1** before writing pyproject.toml.

2. **Signal handler conflict with Click's standalone mode**
   - What we know: Click catches `KeyboardInterrupt` in standalone mode and exits. The recording command needs to intercept SIGINT to gracefully stop ffmpeg.
   - What's unclear: Whether `standalone_mode=False` or a custom signal handler is the right approach for this specific use case.
   - Recommendation: Use `@click.pass_context` + set `standalone_mode=False` on the `record` command, then register signal handlers explicitly in the callback. Alternatively, use Click's `ctx.with_resource()` pattern.

3. **`meet stop` implementation: file-based or in-process?**
   - What we know: STATE.md says `meet stop` reads `state.json` for the PID and sends SIGTERM. This means `meet record` writes the PID and exits, while ffmpeg continues as a background process.
   - What's unclear: Whether `meet record` blocks (waiting for stop signal) or detaches. The architecture in ARCHITECTURE.md implies `meet record` stores PID and the user runs `meet stop` as a separate command — implying detached recording.
   - Recommendation: `meet record` should detach (ffmpeg runs in background, `meet record` exits), persisting PID to state.json. `meet stop` is a separate command that reads the PID and terminates the process.

---

## Sources

### Primary (HIGH confidence)
- Direct environment verification (2026-03-22) — ffmpeg 8.1, BlackHole 2ch 0.6.1, Python 3.14.3, all packages
- `.planning/research/STACK.md` — locked stack decisions
- `.planning/research/ARCHITECTURE.md` — locked architecture decisions
- `.planning/research/PITFALLS.md` — validated pitfalls P1-P5
- `.planning/REQUIREMENTS.md` — requirements AUDIO-01 to SETUP-04
- Verified code execution: ffmpeg command syntax, avfoundation device parsing, atomic write, PID detection, process group management

### Secondary (MEDIUM confidence)
- `.planning/research/FEATURES.md` — feature scoping decisions
- ffmpeg 8.1 avfoundation documentation (confirmed via `ffmpeg -version` and test run)

### Tertiary (LOW confidence)
- Python 3.14 compatibility with mlx-whisper: tested locally but no official release notes confirm long-term support

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified installed and importable
- Architecture patterns: HIGH — all key patterns verified via live code execution
- Pitfalls: HIGH — verified against actual environment (real device indices, real ffmpeg behavior)
- Python version question: MEDIUM — empirically works but no official statement

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable tooling; re-verify before Phase 2 if mlx-whisper updates)
