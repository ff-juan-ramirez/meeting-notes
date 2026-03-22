---
phase: 01-audio-capture-health-check-design
plan: 02
subsystem: audio-capture
tags: [ffmpeg, audio, cli, process-management, tdd]
one_liner: "ffmpeg two-device amix recording pipeline with SIGTERM/SIGKILL process lifecycle and meet record/stop CLI commands"

dependency_graph:
  requires:
    - meeting_notes/core/config.py (AudioConfig, Config)
    - meeting_notes/core/storage.py (get_config_dir, get_data_dir, ensure_dirs, get_recording_path)
    - meeting_notes/core/state.py (write_state, read_state, clear_state, check_for_stale_session)
  provides:
    - meeting_notes/core/process_manager.py (start_ffmpeg, stop_gracefully)
    - meeting_notes/services/audio.py (build_ffmpeg_command, start_recording, stop_recording)
    - meeting_notes/cli/commands/record.py (record, stop)
  affects:
    - meeting_notes/cli/main.py (registered record and stop commands)

tech_stack:
  added: []
  patterns:
    - ffmpeg avfoundation two-device capture with amix filter
    - POSIX process group management (start_new_session=True, os.killpg)
    - SIGTERM -> wait(5s) -> SIGKILL escalation pattern
    - atomic state.json write via temp+replace
    - Click CLI commands with CliRunner testing

key_files:
  created:
    - meeting_notes/core/process_manager.py
    - meeting_notes/services/audio.py
    - meeting_notes/cli/commands/record.py
    - meeting_notes/core/config.py
    - meeting_notes/core/storage.py
    - meeting_notes/core/state.py
    - pyproject.toml
    - tests/test_process_manager.py
    - tests/test_audio.py
    - tests/test_record_command.py
    - tests/test_config.py
    - tests/test_storage.py
    - tests/test_state.py
    - tests/conftest.py
  modified:
    - meeting_notes/cli/main.py (added record/stop commands)

decisions:
  - "Used setuptools.build_meta backend (not setuptools.backends._legacy which is unavailable in setuptools 82+)"
  - "Fixed test_stop_gracefully_escalates_to_sigkill mock: side_effect=[TimeoutExpired, None] so second proc.wait() call (no-timeout) succeeds"
  - "Included plan 01-01 scaffold as prerequisite (worktree started fresh with no prior execution)"

metrics:
  duration_seconds: 244
  completed_date: "2026-03-22T20:16:39Z"
  tasks_completed: 2
  files_created: 20
  tests_passing: 33
---

# Phase 1 Plan 02: Audio Capture Pipeline Summary

**One-liner:** ffmpeg two-device amix recording pipeline with SIGTERM/SIGKILL process lifecycle and meet record/stop CLI commands

## Objective

Implement the core audio capture pipeline: ffmpeg process management (start/stop with graceful termination), audio service (command builder + start/stop), and the `meet record` / `meet stop` CLI commands.

## Tasks Completed

### Task 1: process_manager.py and audio.py (TDD)

**Commits:** `68587e4`

Implemented the two foundational modules:

- `meeting_notes/core/process_manager.py`: `start_ffmpeg` launches ffmpeg with `start_new_session=True` for process group management. `stop_gracefully` sends SIGTERM to the process group via `os.killpg`, waits up to 5 seconds, then escalates to SIGKILL on timeout. `ProcessLookupError` is caught for already-dead processes.

- `meeting_notes/services/audio.py`: `build_ffmpeg_command` constructs the ffmpeg command with two avfoundation inputs by device index (`:1`, `:2`), `aresample=16000` on both, `amix=inputs=2:normalize=0`, WAV `pcm_s16le` output. `start_recording` calls `ensure_dirs()`, gets a timestamped recording path, builds the command, and delegates to `start_ffmpeg`. `stop_recording` delegates to `stop_gracefully`.

Also created the full project scaffold (required as 01-01 prerequisite): pyproject.toml, package __init__ files, core/config.py, core/storage.py, core/state.py, cli/main.py, tests/conftest.py, and all Wave 0 test stubs.

**Tests:** 9 passing (test_process_manager.py + test_audio.py), plus 18 core tests (config/storage/state).

### Task 2: meet record and meet stop CLI commands (TDD)

**Commits:** `71472de`

Implemented:

- `meeting_notes/cli/commands/record.py`: `record` command checks for existing session (live PID = error with "Already recording", stale PID = clear and proceed), starts ffmpeg via `start_recording`, writes atomic state.json with session_id/pid/output_path/start_time. `stop` command reads PID from state.json, terminates ffmpeg via `stop_recording`, clears state.

- `meeting_notes/cli/main.py`: Updated to import and register `record` and `stop` commands.

**Tests:** 6 passing (test_record_command.py using Click's CliRunner with monkeypatched state/config paths).

## Verification

```
pytest tests/test_process_manager.py tests/test_audio.py tests/test_record_command.py tests/test_config.py tests/test_storage.py tests/test_state.py -v
33 passed in 0.04s
```

`meet record --help` shows "Start a recording session."
`meet stop --help` shows "Stop the active recording session."

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pyproject.toml build backend**
- **Found during:** Initial package installation
- **Issue:** Plan specified `setuptools.backends._legacy:_Backend` which doesn't exist in setuptools 82+
- **Fix:** Changed to `setuptools.build_meta` (standard setuptools backend)
- **Files modified:** pyproject.toml
- **Commit:** 68587e4

**2. [Rule 1 - Bug] Fixed SIGKILL escalation test mock**
- **Found during:** Task 1 TDD GREEN phase
- **Issue:** `mock_proc.wait.side_effect = TimeoutExpired(...)` caused ALL calls to raise, including the unconditional `proc.wait()` after SIGKILL
- **Fix:** Changed to `side_effect = [TimeoutExpired(...), None]` so first call raises, second succeeds
- **Files modified:** tests/test_process_manager.py
- **Commit:** 68587e4

**3. [Rule 3 - Blocking] Created 01-01 scaffold as prerequisite**
- **Found during:** Initial file check
- **Issue:** This worktree started with no project files — plan 01-01 (wave 1) outputs were missing
- **Fix:** Created all foundation files (pyproject.toml, package structure, core modules, test infrastructure) before implementing plan 01-02 tasks
- **Commit:** 68587e4

## Known Stubs

None — all implemented functionality is complete and tested. Wave 0 stub files (`test_health_check.py`, `test_doctor_command.py`) contain properly marked `pytest.mark.skip` stubs for Plan 01-03.

## Self-Check: PASSED
