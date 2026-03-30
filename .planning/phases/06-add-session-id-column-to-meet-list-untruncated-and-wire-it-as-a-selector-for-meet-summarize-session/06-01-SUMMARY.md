---
phase: 06-add-session-id-column-to-meet-list-untruncated-and-wire-it-as-a-selector-for-meet-summarize-session
plan: "01"
subsystem: CLI / meet list
tags: [cli, meet-list, session-id, meet-summarize, tdd]
dependency_graph:
  requires: []
  provides: [session_id in meet list table and JSON, updated --session help text]
  affects: [meeting_notes/cli/commands/list.py, meeting_notes/cli/commands/summarize.py]
tech_stack:
  added: []
  patterns: [TDD red-green, Rich table add_column, Click option help text]
key_files:
  created: []
  modified:
    - meeting_notes/cli/commands/list.py
    - meeting_notes/cli/commands/summarize.py
    - tests/test_cli_list.py
decisions:
  - Session ID column added last (after Notion URL) with no max_width — untruncated by design (D-02)
  - session_id key in JSON output set to path.stem — exact value needed for --session round-trip (D-04)
  - summarize --session help text updated to reflect v1.2 slug-prefixed stem format (D-05)
metrics:
  duration_seconds: 420
  completed_date: "2026-03-28"
  tasks: 1
  files_modified: 3
requirements:
  - SESSID-01
  - SESSID-02
  - SESSID-03
---

# Phase 06 Plan 01: Session ID Column in meet list — Summary

**One-liner:** Added untruncated Session ID column to meet list Rich table and --json output, letting users copy-paste the exact stem into meet summarize --session.

## What Was Built

- `meet list` Rich table now shows a "Session ID" column (last column, no max_width) containing the full file stem for each session — both named (`team-standup-20260322-143000-abc12345`) and unnamed (`20260322-143000-abc12345`) formats
- `meet list --json` output includes a `session_id` field in each session object, equal to the metadata file stem
- `meet summarize --session` help text updated from the old timestamp-only example to the v1.2 slug-prefixed format: `"Session stem shown in 'meet list' (e.g. team-standup-20260322-143000-abc12345)"`
- 4 new TDD tests added to `tests/test_cli_list.py`; all 26 tests pass

## Tasks

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 (RED) | Failing tests for session_id column | 3b8e815 | tests/test_cli_list.py |
| 1 (GREEN) | Implementation: session_id in list + summarize help | 515c7b0 | meeting_notes/cli/commands/list.py, meeting_notes/cli/commands/summarize.py |

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Session ID column goes last, no max_width | Least disruptive layout change; stem must be readable untruncated (D-02) |
| session_id = path.stem (not session dict key) | Stem is the exact value --session accepts; explicit field makes JSON scriptable (D-04) |
| Help text updated to slug-prefix example | Users of v1.2+ recording names need to see the full format (D-05) |

## Deviations from Plan

None — plan executed exactly as written.

## Test Results

- `tests/test_cli_list.py`: 26 passed (4 new + 22 existing)
- `tests/` (excluding pre-existing failures): 239 passed
- Pre-existing failures NOT caused by this plan:
  - `tests/test_llm_service.py::test_templates_contain_grounding_rule` — template grounding rule missing (pre-existing)
  - `tests/test_storage.py::test_get_data_dir_default` — XDG path mismatch on this machine (pre-existing)

## Known Stubs

None — session_id is wired to `path.stem`, which is the real value from disk.

## Self-Check: PASSED
