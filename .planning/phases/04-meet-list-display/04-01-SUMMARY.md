---
phase: 04-meet-list-display
plan: "01"
subsystem: cli/list
tags: [tdd, list-command, recording-name, title-derivation]
dependency_graph:
  requires: [Phase 03 meet stop propagates recording_name to metadata JSON]
  provides: [meet list shows user-given name as session title]
  affects: [meeting_notes/cli/commands/list.py]
tech_stack:
  added: []
  patterns: [guard clause, falsy check for optional metadata field]
key_files:
  created: []
  modified:
    - meeting_notes/cli/commands/list.py
    - tests/test_cli_list.py
decisions:
  - "recording_name guard clause at top of _derive_title() — before notes_path check — ensures user-given name always wins (D-01)"
  - "Falsy check (if recording_name:) handles None, empty string, and missing key uniformly per D-03 discretion"
  - "No code change needed for --json output: recording_name already flows via **meta spread (D-02)"
metrics:
  duration_seconds: 54
  completed_date: "2026-03-28"
  tasks_completed: 2
  files_modified: 2
---

# Phase 04 Plan 01: recording_name Title Derivation in meet list Summary

`_derive_title()` updated with recording_name guard clause: user-given name takes highest priority over LLM heading and stem fallback, backed by 6 new regression and feature tests.

## What Was Built

Added a guard clause at the top of `_derive_title()` in `meeting_notes/cli/commands/list.py` that checks `meta.get("recording_name")` before the existing LLM heading / stem fallback chain. The check is falsy (`if recording_name:`) so None, empty string, and missing key all fall through unchanged.

No changes to `--json` output path were needed — `recording_name` already flowed into the sessions dict via `**meta` spread at line 152.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 (TDD RED) | 6 new tests covering recording_name (3 failing) | db8e929 | tests/test_cli_list.py |
| 2 (TDD GREEN) | recording_name guard clause in _derive_title | ed549b0 | meeting_notes/cli/commands/list.py |

## Test Results

All 22 tests pass (16 pre-existing + 6 new), zero regressions.

New tests cover:
- `test_named_session_shows_recording_name_as_title` — recording_name displayed as title (LIST-01)
- `test_recording_name_wins_over_llm_heading` — recording_name over LLM heading (D-01)
- `test_no_recording_name_field_uses_llm_heading` — pre-v1.2 regression (LIST-02)
- `test_recording_name_none_falls_through` — None value fallthrough (D-03)
- `test_recording_name_empty_falls_through` — empty string fallthrough (D-03)
- `test_json_output_includes_recording_name_and_title` — JSON field and title (D-02)

## Decisions Made

1. Guard clause at top of `_derive_title()` before notes_path check — recording_name always wins per D-01
2. Falsy check handles None/empty string/missing uniformly per D-03 discretion
3. No code change for --json: free win via **meta spread already in place

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None — recording_name is wired from actual metadata written by `meet stop` (Phase 03). No placeholder values.

## Self-Check: PASSED

- `meeting_notes/cli/commands/list.py` — modified, guard clause present
- `tests/test_cli_list.py` — 6 new test functions added
- Commit db8e929 — test(04-01) red phase
- Commit ed549b0 — feat(04-01) green phase
