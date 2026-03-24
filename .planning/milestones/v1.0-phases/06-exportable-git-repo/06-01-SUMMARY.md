---
phase: 06-exportable-git-repo
plan: 01
subsystem: cli/doctor
tags: [verbose, health-check, doctor, ui]
dependency_graph:
  requires: []
  provides: [verbose_detail_protocol, STATUS_ICONS_shared_constant]
  affects: [meeting_notes/cli/commands/doctor.py, meeting_notes/core/health_check.py, meeting_notes/services/checks.py, meeting_notes/cli/ui.py]
tech_stack:
  added: []
  patterns: [verbose_detail protocol on HealthCheck, STATUS_ICONS as shared constant in ui.py]
key_files:
  created: []
  modified:
    - meeting_notes/core/health_check.py
    - meeting_notes/services/checks.py
    - meeting_notes/cli/ui.py
    - meeting_notes/cli/commands/doctor.py
    - tests/test_doctor_command.py
decisions:
  - "STATUS_ICONS moved to cli/ui.py so Plan 02 (meet init) can reuse it without circular imports"
  - "verbose_detail() returns str | None on base — None means no verbose line emitted (D-03)"
  - "quiet wins over verbose (D-06): if quiet: verbose = False applied before any output"
  - "fix_suggestion guard changed to result.status != CheckStatus.OK (D-04)"
metrics:
  duration_seconds: 163
  completed_date: "2026-03-23"
  tasks: 2
  files_modified: 5
---

# Phase 6 Plan 1: Doctor --verbose flag + verbose_detail protocol Summary

**One-liner:** `meet doctor --verbose` now emits inline dim detail lines per check via a `verbose_detail()` protocol on all HealthCheck subclasses, with `STATUS_ICONS` moved to `cli/ui.py` for reuse by Plan 02.

## What Was Built

Added a `--verbose` flag to `meet doctor` that shows inline detail lines under each health check. Implemented `verbose_detail()` on all 9 relevant check classes (not `OpenaiWhisperConflictCheck` per D-03). Moved `STATUS_ICONS` from `doctor.py` to `cli/ui.py` as a shared constant. Fixed the `fix_suggestion` guard to only show on WARNING/ERROR (D-04).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add verbose_detail() to HealthCheck base + all check subclasses + move STATUS_ICONS to ui.py | a27330d | health_check.py, checks.py, ui.py, test_doctor_command.py |
| 2 | Wire --verbose flag into doctor command and fix fix_suggestion guard | ed3a49f | doctor.py, test_doctor_command.py |

## Verification Results

- `python3 -m pytest tests/test_doctor_command.py -x -q` — 23 passed
- `python3 -m pytest tests/ -x -q` — 193 passed (all green)
- `python3 -c "from meeting_notes.cli.ui import STATUS_ICONS; print(STATUS_ICONS)"` — confirmed
- `python3 -c "from meeting_notes.core.health_check import HealthCheck; print(HealthCheck.verbose_detail)"` — confirmed

## Decisions Made

1. **STATUS_ICONS in ui.py**: Moved from doctor.py to cli/ui.py so Plan 02 (meet init) can `from meeting_notes.cli.ui import STATUS_ICONS` without circular imports. Both doctor.py and future init.py share the same canonical dict.

2. **verbose_detail() returns None on base**: The base class protocol returns None, meaning "no detail to show." Subclasses opt in by overriding. OpenaiWhisperConflictCheck deliberately does not override (D-03) — it has no meaningful verbose data.

3. **quiet wins over verbose (D-06)**: `if quiet: verbose = False` applied immediately after resolving `quiet` from context, before any output loop.

4. **fix_suggestion guard fixed (D-04)**: Changed from `if result.fix_suggestion:` to `if result.fix_suggestion and result.status != CheckStatus.OK:` — fix suggestions never appear on OK-status results.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None — all verbose_detail() implementations are fully wired. No placeholder data.

## Self-Check: PASSED

Files exist:
- meeting_notes/core/health_check.py: FOUND
- meeting_notes/services/checks.py: FOUND
- meeting_notes/cli/ui.py: FOUND
- meeting_notes/cli/commands/doctor.py: FOUND
- tests/test_doctor_command.py: FOUND

Commits exist:
- a27330d: FOUND
- ed3a49f: FOUND
