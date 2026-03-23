---
phase: 05-integrated-cli
plan: "01"
subsystem: cli
tags: [cli, ui, shared-console, quiet-flag, version-flag, health-checks, metadata, tdd]
dependency_graph:
  requires: []
  provides:
    - meeting_notes.cli.ui.console (shared Rich Console with TTY detection)
    - --quiet flag propagated to all commands via ctx.obj
    - --version flag on main group
    - run_with_spinner quiet=True bypass
    - duration_seconds written to metadata on meet stop
    - PythonVersionCheck and OpenaiWhisperConflictCheck
  affects:
    - meeting_notes/cli/commands/record.py
    - meeting_notes/cli/commands/transcribe.py
    - meeting_notes/cli/commands/summarize.py
    - meeting_notes/cli/commands/doctor.py
    - meeting_notes/cli/commands/init.py
    - meeting_notes/services/transcription.py
    - meeting_notes/services/checks.py
tech_stack:
  added: []
  patterns:
    - Shared Rich Console with TTY detection via force_terminal=sys.stdout.isatty()
    - Click pass_context pattern for --quiet propagation
    - TDD (RED/GREEN) for new module + flag tests
    - quiet=False param on run_with_spinner early-returns without threading
key_files:
  created:
    - meeting_notes/cli/ui.py
    - tests/test_cli_ui.py
  modified:
    - meeting_notes/cli/main.py
    - meeting_notes/services/transcription.py
    - meeting_notes/cli/commands/record.py
    - meeting_notes/cli/commands/transcribe.py
    - meeting_notes/cli/commands/summarize.py
    - meeting_notes/cli/commands/doctor.py
    - meeting_notes/cli/commands/init.py
    - meeting_notes/services/checks.py
    - tests/test_record_command.py
    - tests/test_doctor_command.py
    - tests/test_summarize_command.py
    - tests/test_transcribe_command.py
decisions:
  - "Shared Console uses force_terminal=sys.stdout.isatty() per D-10/D-11; centralized in cli/ui.py"
  - "transcription.py imports console from cli.ui — service depends on CLI layer console (acceptable: run_with_spinner is CLI-facing)"
  - "quiet=ctx.obj.get('quiet', False) with if ctx.obj guard — safe for direct runner.invoke with obj param"
  - "list_sessions import wrapped in try/except ImportError for forward-compat with Plan 02"
  - "Error and Warning prints remain unconditional — only informational progress output guarded by quiet"
  - "meet stop: clear_state called after metadata write to avoid data loss on crash"
  - "PythonVersionCheck uses >=3.14 as WARNING not ERROR — Python 3.14 may work but is untested"
metrics:
  duration_seconds: 352
  completed_date: "2026-03-23"
  tasks_completed: 2
  files_changed: 12
---

# Phase 5 Plan 01: Shared Console, --quiet/--version, Duration Metadata, New Doctor Checks Summary

**One-liner:** Shared Rich Console with TTY detection, --quiet/--version wired into all six CLI commands via ctx.obj, meet stop writing duration_seconds to metadata JSON, and PythonVersionCheck/OpenaiWhisperConflictCheck added to meet doctor.

## What Was Built

### Task 1: cli/ui.py + main group flags + run_with_spinner quiet param (TDD)

Created `meeting_notes/cli/ui.py` as the single source of truth for the Rich Console. Added `--version` (via `@click.version_option(package_name="meeting-notes")`) and `--quiet` (via `@click.option`) to the main Click group, propagating quiet state through `ctx.obj["quiet"]`. Updated `run_with_spinner` to accept `quiet=False` — when `True`, fn() is called directly in the current thread with no threading overhead.

The `transcription.py` service now imports `_console` from `cli.ui` rather than creating its own, centralizing the console per D-10.

### Task 2: Retrofit + stop metadata + new health checks

- All five command files (record, transcribe, summarize, doctor, init) now import `console` from `meeting_notes.cli.ui` — zero local `Console()` instances remain in `cli/commands/`.
- Each command function decorated with `@click.pass_context`; non-error/non-warning `console.print` calls wrapped in `if not quiet:`.
- `meet stop` computes `duration_seconds` from `start_time` ISO string stored at record time and writes it (plus `wav_path`) to `metadata/{stem}.json` before clearing state.
- Two new health check classes added to `services/checks.py`: `PythonVersionCheck` (ERROR <3.11, WARNING >=3.14, OK otherwise) and `OpenaiWhisperConflictCheck` (WARNING if `openai-whisper` package installed).
- Both new checks registered in `doctor.py` before existing checks.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_summarize_command.py and test_transcribe_command.py run_with_spinner stubs**

- **Found during:** Task 2 (full test run after retrofitting)
- **Issue:** All existing tests that patched `run_with_spinner` used `lambda fn, msg: fn()` or `def fake_run_with_spinner(fn, message):` which did not accept the new `quiet=` keyword argument
- **Fix:** Updated all stub lambdas to `lambda fn, msg, **kw: fn()` and all named stubs to `def fake_run_with_spinner(fn, message, **kw):`
- **Files modified:** tests/test_summarize_command.py, tests/test_transcribe_command.py
- **Commit:** 6d7a6a2

## Test Results

- `python3 -m pytest tests/ -v` — 160 passed, 0 failed
- No regressions introduced

## Known Stubs

None — all functionality is wired.

## Self-Check

### Files Exist
- /meeting_notes/cli/ui.py: FOUND
- /meeting_notes/cli/main.py: FOUND (contains @click.version_option and --quiet)
- /meeting_notes/services/transcription.py: FOUND (contains quiet param)
- /meeting_notes/services/checks.py: FOUND (contains PythonVersionCheck, OpenaiWhisperConflictCheck)
- /tests/test_cli_ui.py: FOUND

### Commits
- b1ec909: test(05-01) RED phase
- 96da1da: feat(05-01) Task 1 implementation
- 6d7a6a2: feat(05-01) Task 2 implementation

## Self-Check: PASSED
