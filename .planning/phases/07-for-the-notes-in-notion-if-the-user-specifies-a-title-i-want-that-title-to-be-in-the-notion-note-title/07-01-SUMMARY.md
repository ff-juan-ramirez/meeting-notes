---
phase: 07
plan: 01
subsystem: cli/summarize
tags: [cli, notion, title, tdd]
dependency_graph:
  requires: [meeting_notes/cli/commands/summarize.py, meeting_notes/services/notion.py]
  provides: [--title flag on meet summarize command]
  affects: [Notion page title only — no local filename or metadata changes]
tech_stack:
  added: []
  patterns: [click.option long-form-only, falsy guard for title, 3-level priority chain]
key_files:
  created: []
  modified:
    - meeting_notes/cli/commands/summarize.py
    - tests/test_summarize_command.py
decisions:
  - "--title uses falsy check (if title:) to treat empty string same as None"
  - "notion_title local variable used to avoid shadowing the Click title param"
  - "session_metadata loaded before Notion push block to support recording_name lookup"
metrics:
  duration_s: 236
  completed: "2026-03-29"
  tasks: 2
  files: 2
---

# Phase 7 Plan 01: --title Flag for Notion Page Title Override Summary

**One-liner:** Added `--title` CLI flag to `meet summarize` implementing a 3-level priority chain: `--title` > `recording_name` (metadata) > `extract_title` (LLM fallback).

## What Was Built

The `meet summarize` command now accepts an optional `--title` flag that lets users specify a custom Notion page title at summarize time. This addresses the case where a user did not name the recording at `meet record` time but wants a meaningful title in Notion.

### Priority chain (D-03):
1. `--title "Custom Title"` (CLI flag, highest priority)
2. `recording_name` from session metadata (set at `meet record "Name"` time)
3. `extract_title(notes, fallback_ts)` (LLM-extracted heading or timestamp fallback)

### Key behaviors:
- `--title` overrides `recording_name` even when both are present
- Empty `--title ""` is treated as falsy — falls through to lower-priority sources
- `--title` is a runtime-only override — NOT persisted to session metadata JSON
- Local notes filename is unaffected (`{stem}-{template}.md` unchanged)

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add failing tests for --title flag (TDD RED) | 899ce1f | tests/test_summarize_command.py |
| 2 | Implement --title flag on meet summarize (TDD GREEN) | 08b6c65 | meeting_notes/cli/commands/summarize.py |

## Verification Results

- `python -m pytest tests/test_summarize_command.py -k "title_flag" -x` — 5 passed
- `python -m pytest tests/test_summarize_command.py -x` — 30 passed (all tests including 5 new)
- `meet summarize --help` shows `--title TEXT  Override the Notion page title for this run`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added session_metadata loading before Notion push block**
- **Found during:** Task 2
- **Issue:** The worktree's summarize.py did not load `session_metadata` from disk before the Notion push section. The main repo version (Phase 5) had this, but the worktree's baseline was an older revision without it. Referencing `session_metadata` without defining it would cause a `NameError` at runtime.
- **Fix:** Added `session_metadata = read_state(metadata_path)` before the Notion push block (after the Phase 3 metadata write). This mirrors the main repo pattern.
- **Files modified:** `meeting_notes/cli/commands/summarize.py`
- **Commit:** 08b6c65

## Known Stubs

None — all functionality is fully wired.

## Self-Check: PASSED

- `meeting_notes/cli/commands/summarize.py` — FOUND (contains `--title` option and priority chain)
- `tests/test_summarize_command.py` — FOUND (contains 5 new `title_flag` tests)
- Commit `899ce1f` — FOUND
- Commit `08b6c65` — FOUND
