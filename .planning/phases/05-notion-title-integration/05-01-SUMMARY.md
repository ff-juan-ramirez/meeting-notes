---
phase: 05-notion-title-integration
plan: "01"
subsystem: cli
tags: [notion, recording_name, title, summarize, tdd]

# Dependency graph
requires:
  - phase: 04-meet-list-display
    provides: recording_name field in session metadata JSON (written by meet stop, read by meet list)
  - phase: 03-record-stop-command
    provides: recording_name stored in session metadata via meet stop
provides:
  - recording_name priority guard in meet summarize Notion title derivation
  - TDD tests for all three NOTION-01 scenarios (named, unnamed, no-metadata)
affects: [notion-title, meet-summarize, v1.2-named-recordings]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "recording_name falsy-guard before extract_title() — mirrors _derive_title() pattern from Phase 04 list.py"

key-files:
  created: []
  modified:
    - meeting_notes/cli/commands/summarize.py
    - tests/test_summarize_command.py

key-decisions:
  - "recording_name guard uses falsy check (if recording_name) to uniformly handle None, empty string, missing key — consistent with Phase 04 D-03"
  - "Change reads session_metadata (first read_state at line 82), not existing (second read at line 173) — semantically correct per RESEARCH.md Pitfall 2"
  - "session_metadata.get('recording_name') if session_metadata else None guards against pre-v1.2 sessions where metadata is None"

patterns-established:
  - "recording_name guard pattern: session_metadata.get('recording_name') if session_metadata else None — use this in any future title derivation from session metadata"

requirements-completed: [NOTION-01]

# Metrics
duration: 3min
completed: 2026-03-28
---

# Phase 05 Plan 01: Notion Title Integration Summary

**recording_name priority guard added to meet summarize Notion title derivation using TDD — named sessions now get their user-given name as Notion page title instead of LLM-extracted heading**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-28T17:36:18Z
- **Completed:** 2026-03-28T17:39:02Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Added recording_name guard clause in summarize.py Notion block (1 new line, 1 modified line)
- Named sessions (with recording_name in metadata) now use that name as the Notion page title
- Unnamed and pre-v1.2 sessions fall through to extract_title unchanged — no regressions
- 3 new TDD tests cover all three scenarios: named, unnamed, no-metadata

## Task Commits

1. **Task 1: RED — Write failing tests** - `656b33f` (test)
2. **Task 2: GREEN — Add recording_name guard clause** - `b00e070` (feat)

_TDD: RED commit with 3 failing tests, then GREEN commit with implementation making all 29 pass._

## Files Created/Modified

- `meeting_notes/cli/commands/summarize.py` - Added recording_name guard before extract_title call in Notion push block (lines 151-152)
- `tests/test_summarize_command.py` - Added 3 new tests: test_summarize_notion_uses_recording_name, test_summarize_notion_unnamed_uses_extract_title, test_summarize_notion_no_metadata_unaffected

## Decisions Made

- recording_name guard uses falsy check (`if recording_name`) to uniformly handle None, empty string, and missing key — consistent with Phase 04 D-03 decision
- Read `recording_name` from `session_metadata` (first `read_state` at line 82), not `existing` (second `read_state` at line 173) — semantically correct, avoids Pitfall 2 from RESEARCH.md
- `session_metadata.get("recording_name") if session_metadata else None` guards against pre-v1.2 sessions where `read_state()` returns None for missing files

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing test failures discovered (out of scope per deviation rules, logged for reference):
- `tests/test_llm_service.py::test_templates_contain_grounding_rule` — meeting template missing grounding rule string (pre-existing)
- `tests/test_storage.py::test_get_data_dir_default` — XDG path mismatch on this machine (pre-existing, machine-specific)

Neither failure was caused by this plan's changes. Not fixed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- NOTION-01 requirement satisfied — Phase 05 is the final phase of v1.2 Named Recordings feature
- All three NOTION-01 scenarios tested and passing
- No blockers for v1.2 milestone completion

---
*Phase: 05-notion-title-integration*
*Completed: 2026-03-28*
