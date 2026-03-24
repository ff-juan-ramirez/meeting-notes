---
phase: 02-local-transcription
plan: 03
subsystem: transcription
tags: [bug-fix, silent-exit, ensure_dirs, exception-handler, regression-test, gap-closure]

# Dependency graph
requires:
  - phase: 02-local-transcription
    plan: 01
    provides: meet transcribe command, storage.ensure_dirs()
provides:
  - ensure_dirs() called at transcribe command entry — guarantees data dirs exist on fresh system
  - Broadened exception handler (FileNotFoundError | OSError) — defense-in-depth for Python 3.14
  - Two regression tests for no-recordings-dir scenario
affects: [02-UAT]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Call ensure_dirs() as first line of any CLI command that reads from data dirs
    - Broaden exception handlers to (FileNotFoundError, OSError) when globbing user data dirs

key-files:
  created: []
  modified:
    - meeting_notes/cli/commands/transcribe.py
    - tests/test_transcribe_command.py

decisions:
  - ensure_dirs() called before any data dir access — prevents silent failure on fresh install
  - OSError added to exception handler as defense-in-depth (Python 3.14 glob may raise it)

# Metrics
metrics:
  duration_seconds: 124
  completed_date: "2026-03-22"
  tasks_completed: 1
  files_changed: 2
---

# Phase 02 Plan 03: Silent-Exit Bug Fix Summary

**One-liner:** ensure_dirs() call + OSError broadening closes silent-exit on fresh system for meet transcribe

## What Was Built

Fixed the silent-exit bug in `meet transcribe` when run on a fresh system where the data directories
(`~/.local/share/meeting-notes/`) have never been created. The bug was diagnosed during UAT: the command
produced no output whatsoever — no spinner, no error, no completion message.

Root cause: `recordings_dir.glob("*.wav")` on a non-existent directory may raise `OSError` on Python 3.14
instead of returning an empty list, and the existing `except FileNotFoundError` handler did not catch it.
Additionally, no `ensure_dirs()` call meant the directories were never created even on success.

Two fixes applied:
1. `ensure_dirs()` call added as the first line of `transcribe()` — always creates data dirs before use
2. Exception handler broadened from `FileNotFoundError` to `(FileNotFoundError, OSError)` — catches both

Two regression tests added to confirm the behavior is locked in.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix silent exit on fresh system and add regression test | 5f60103 | transcribe.py, test_transcribe_command.py |

## Verification

All verification checks passed:

1. `pytest tests/test_transcribe_command.py -x -q` — 14 passed (including 2 new regression tests)
2. `pytest tests/ -x -q` — 76 passed (full suite green)
3. `grep -n "ensure_dirs()" meeting_notes/cli/commands/transcribe.py` — line 57
4. `grep -n "OSError" meeting_notes/cli/commands/transcribe.py` — line 68

## Deviations from Plan

### TDD RED Phase Note

The two new regression tests passed immediately without the implementation changes. This is because on
this machine (Python 3.14 / macOS), `Path.glob("*.wav")` on a non-existent directory returns an empty
list rather than raising OSError. The `resolve_latest_wav` function then raises `FileNotFoundError`
which the existing handler catches.

Despite this, the implementation changes (ensure_dirs + OSError broadening) were applied as written in
the plan — they are correct defense-in-depth regardless of per-machine glob behavior.

No other deviations.

## Known Stubs

None.

## Self-Check: PASSED
