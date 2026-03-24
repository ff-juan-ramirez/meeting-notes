---
phase: 06-exportable-git-repo
plan: 02
subsystem: cli/init
tags: [init, wizard, notion, audio-device, health-check, tdd]
dependency_graph:
  requires: [06-01]
  provides: [full_init_wizard, mask_token, inline_doctor_via_health_check_suite]
  affects: [meeting_notes/cli/commands/init.py, tests/test_init.py]
tech_stack:
  added: []
  patterns: [TDD red-green, NotionClient token validation loop, HealthCheckSuite inline (no subprocess), _parse_audio_devices for device menu]
key_files:
  created:
    - tests/test_init.py
  modified:
    - meeting_notes/cli/commands/init.py
decisions:
  - "Notion token validated via NotionClient.users.me() in a while-True loop; APIResponseError re-prompts, generic Exception saves with warning (no loop)"
  - "_parse_audio_devices() imported from services/checks.py for device menu — no duplicated ffmpeg parsing"
  - "Inline doctor in _run_inline_doctor() uses HealthCheckSuite directly (no subprocess) per D-12"
  - "fix_suggestion guard: result.status != CheckStatus.OK — consistent with doctor.py (D-04)"
  - "Test helper _fake_notion_error() uses correct APIResponseError constructor: (code, status, message, headers, raw_body_text)"
metrics:
  duration_seconds: 329
  completed_date: "2026-03-23"
  tasks: 1
  files_modified: 2
---

# Phase 6 Plan 2: meet init Full Interactive Wizard Summary

**One-liner:** `meet init` is now a full interactive wizard with audio device detection, Notion token validation loop, reconfigure/update-specific-fields branching, test recording, and inline HealthCheckSuite doctor — replacing the bare-bones skeleton.

## What Was Built

Rewrote `meeting_notes/cli/commands/init.py` from a minimal config prompter into a complete interactive wizard:

- **`mask_token()`**: Safe display helper; returns `[not set]` for None, `***` for short tokens, `tok***xyz` for normal tokens.
- **`_select_audio_devices()`**: Calls `_parse_audio_devices()` from `services/checks.py`, presents a numbered menu with actual device indices (`[0] MacBook Air Microphone`, `[1] BlackHole 2ch`, etc.), prompts for system and mic index with validation.
- **`_collect_notion_credentials()`**: Prompts for Notion token, validates via `NotionClient.users.me()`, re-prompts on `APIResponseError`, accepts on network error with warning.
- **`_update_specific_fields()`**: Shows numbered menu with current masked values, re-prompts only selected fields (comma-separated selection).
- **`_run_test_recording()`**: Runs 1-second `ffmpeg -f avfoundation` test recording to trigger macOS microphone permission (SETUP-02).
- **`_run_inline_doctor()`**: Creates `HealthCheckSuite`, registers all 11 checks in same order as `doctor.py`, prints results with `STATUS_ICONS` and fix suggestions on WARNING/ERROR only.
- **`init()` command**: Detects existing config, offers `R/U` choice; `R` re-runs full wizard, `U` updates specific fields. Fresh system runs full wizard.

Created `tests/test_init.py` with 15 tests covering all flows using `CliRunner` with `input=` simulation.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Add failing tests for meet init wizard | 18a9e2e | tests/test_init.py |
| 1 (GREEN) | Implement full wizard + fix APIResponseError test helper | ce93d7d | init.py, tests/test_init.py |

## Verification Results

- `python3 -m pytest tests/test_init.py -x -q` — 15 passed
- `python3 -m pytest tests/ -x -q` — 208 passed (all green, +15 from prior 193)
- `python3 -c "from meeting_notes.cli.commands.init import mask_token; print(mask_token('ntn_abcdefghijk'))"` — prints `ntn_***ijk`

## Decisions Made

1. **Notion token validation loop**: `APIResponseError` re-prompts; any other `Exception` (network error, timeout) saves with a yellow warning — prevents getting stuck on transient connectivity issues.

2. **No duplicate ffmpeg parsing**: `_select_audio_devices()` imports and calls `_parse_audio_devices()` from `services/checks.py` — the same parser used by `BlackHoleCheck` and `FFmpegDeviceCheck`. No duplicated logic.

3. **Inline doctor = HealthCheckSuite directly**: Per D-12, `_run_inline_doctor()` creates a `HealthCheckSuite`, registers all 11 checks, calls `run_all()` in-process. No subprocess call to `meet doctor`.

4. **fix_suggestion guard consistent with doctor.py**: Shows fix suggestions only when `result.status != CheckStatus.OK` — consistent with the D-04 fix applied in Plan 01.

5. **APIResponseError constructor fix in tests**: The `_fake_notion_error()` helper required the correct positional constructor `(code, status, message, headers, raw_body_text)` — documented in STATE.md from Phase 04. Using wrong kwargs caused `TypeError` which hit the `except Exception` branch instead of `except APIResponseError`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _fake_notion_error() constructor in tests**
- **Found during:** TDD GREEN phase (test_notion_token_invalid_prompts_reentry failed)
- **Issue:** Test helper used `APIResponseError(body=..., status=..., headers=...)` — wrong kwargs, caused `TypeError` to fire before the error could be raised, hitting `except Exception` branch instead of `except APIResponseError`
- **Fix:** Changed to correct constructor `APIResponseError(code=..., status=..., message=..., headers=httpx.Headers({}), raw_body_text=...)`
- **Files modified:** `tests/test_init.py`
- **Commit:** ce93d7d

## Known Stubs

None — all wizard flows are fully wired. `_run_inline_doctor()` registers real check classes. `_parse_audio_devices()` is the real parser (mocked in tests only).

## Self-Check: PASSED

Files exist:
- meeting_notes/cli/commands/init.py: FOUND
- tests/test_init.py: FOUND

Commits exist:
- 18a9e2e: FOUND (test RED phase)
- ce93d7d: FOUND (implementation GREEN phase)
