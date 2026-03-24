---
phase: 04-notion-integration
plan: 02
subsystem: api
tags: [notion, notion-client, health-checks, cli, summarize]

requires:
  - phase: 04-01
    provides: "notion.py service module and NotionConfig dataclass (created in same worktree as prerequisite)"
  - phase: 03-note-generation
    provides: "summarize.py command, metadata read-merge-write pattern, run_with_spinner"
provides:
  - "summarize.py auto-pushes notes to Notion when token and parent_page_id are configured"
  - "dim hint printed when Notion not configured (exit 0, no failure)"
  - "yellow warning panel on Notion push failure (exit 0, notes safe locally)"
  - "notion_url stored in session metadata JSON (URL on success, null on skip/failure)"
  - "NotionTokenCheck and NotionDatabaseCheck health checks with WARNING severity"
  - "meet doctor registers both Notion health checks"
affects: [05-integrated-cli, meet-list]

tech-stack:
  added: [notion-client>=2.0]
  patterns:
    - "Notion push as optional post-summarize block — never gates local note saving"
    - "WARNING severity for optional service checks (mirrors WhisperModelCheck pattern)"
    - "Config read inside CLI command (get_config_dir() / config.json) to resolve Notion credentials"
    - "read-merge-write for metadata extension (notion_url added after prior Phase 3 fields)"

key-files:
  created:
    - meeting_notes/services/notion.py
    - tests/test_notion_checks.py
  modified:
    - meeting_notes/core/config.py
    - meeting_notes/cli/commands/summarize.py
    - meeting_notes/services/checks.py
    - meeting_notes/cli/commands/doctor.py
    - tests/test_summarize_command.py
    - pyproject.toml

key-decisions:
  - "Notion push placed after local notes save — local save never fails due to Notion issues"
  - "extract_title called with UTC timestamp fallback before spinner, not inside lambda"
  - "Both NotionTokenCheck and NotionDatabaseCheck use WARNING severity — Notion is optional"
  - "NotionConfig dataclass added to config.py following AudioConfig/WhisperConfig pattern"
  - "Plan 01 prerequisite outputs (notion.py, NotionConfig) created in same worktree since parallel agent hasn't merged yet"

patterns-established:
  - "Optional service push: check config -> push -> warn on failure (exit 0) pattern"
  - "Health check for optional service: WARNING not ERROR when not configured"

requirements-completed: [NOTION-01, NOTION-02, NOTION-03, NOTION-07]

duration: 5min
completed: 2026-03-22
---

# Phase 4 Plan 02: Notion CLI Integration Summary

**meet summarize auto-pushes notes to Notion via notion-client, with NotionTokenCheck and NotionDatabaseCheck WARNING-severity health checks registered in meet doctor**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-22T02:18:56Z
- **Completed:** 2026-03-22T02:23:26Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Extended summarize.py with a Notion push block: auto-pushes when configured, prints dim hint when not configured, warns with yellow panel on failure (exit 0 in all cases)
- Stored `notion_url` in session metadata JSON (URL on success, null on skip/failure) for Phase 5's meet list
- Added NotionTokenCheck and NotionDatabaseCheck to checks.py with WARNING severity, registered in doctor.py
- All 130 tests pass including 7 new Notion integration tests for summarize and 9 unit tests for health checks

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend summarize.py with Notion push block + tests** - `0a72e3d` (feat)
2. **Task 2: NotionTokenCheck + NotionDatabaseCheck health checks + doctor registration + tests** - `dc2725b` (feat)

_Note: TDD tasks include failing test commit merged into the implementation commit for parallel execution efficiency_

## Files Created/Modified

- `meeting_notes/services/notion.py` - Notion API wrapper: create_page, extract_title, _markdown_to_blocks, _split_text, _call_with_retry (created as Plan 01 prerequisite)
- `meeting_notes/core/config.py` - Added NotionConfig dataclass; extended Config with notion field and load() deserialization
- `meeting_notes/cli/commands/summarize.py` - Notion push block after note generation; notion_url stored in metadata
- `meeting_notes/services/checks.py` - NotionTokenCheck and NotionDatabaseCheck classes added
- `meeting_notes/cli/commands/doctor.py` - Registered NotionTokenCheck and NotionDatabaseCheck after OllamaModelCheck
- `tests/test_summarize_command.py` - 7 new Notion integration tests (not_configured, success, stores_url, url_null_when_not_configured, failure_warns, spinner, preserves_phase3_metadata)
- `tests/test_notion_checks.py` - 9 unit tests for both Notion health checks plus doctor registration verification
- `pyproject.toml` - Added notion-client>=2.0 to dependencies

## Decisions Made

- Plan 01 prerequisite outputs (notion.py, NotionConfig) created in this worktree since parallel wave 1 agent hasn't merged yet — following "create prerequisites needed to complete task" deviation Rule 3
- `extract_title` called before the `run_with_spinner` lambda to avoid closure scoping issues with config values
- Both NotionTokenCheck and NotionDatabaseCheck return WARNING (not ERROR) — Notion is optional, meet summarize works without it
- `_call_with_retry` in notion.py handles HTTP 429 with exponential backoff starting at 1s, up to 4 retries

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created Plan 01 prerequisite outputs (notion.py, NotionConfig) in this worktree**
- **Found during:** Task 1 (extending summarize.py)
- **Issue:** Plan 02 depends_on 04-01, but the parallel Plan 01 agent works in a different worktree and hasn't merged. notion.py and NotionConfig don't exist in this worktree.
- **Fix:** Created `meeting_notes/services/notion.py` and added `NotionConfig` to `config.py` following the exact Plan 01 spec. Added `notion-client>=2.0` to `pyproject.toml` and installed it.
- **Files modified:** meeting_notes/services/notion.py (created), meeting_notes/core/config.py, pyproject.toml
- **Verification:** Tests pass, `from meeting_notes.services.notion import create_page, extract_title` succeeds
- **Committed in:** 0a72e3d (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (blocking prerequisite)
**Impact on plan:** Necessary to unblock all Plan 02 work. When Plan 01 merges, changes are compatible (same spec).

## Issues Encountered

- `notion_client.errors.APIResponseError` constructor signature changed in v2 — takes `code, status, message, headers, raw_body_text` (not the old `response, message, code` pattern). Used correct constructor with `httpx.Headers` object in tests.

## User Setup Required

**External services require manual configuration.** Users need:

1. Create a Notion integration at: Notion > Settings > My connections > Develop or manage integrations
2. Copy the Internal Integration Secret as `notion.token` in config.json
3. Open the target Notion page, copy the 32-char page ID from URL as `notion.parent_page_id`
4. Share the parent page with the integration (page menu > Connections > Add connection)

Run `meet init` to configure (once meet init is extended with Notion setup in Phase 5).

## Known Stubs

None - all Notion integration paths are fully wired. notion_url is stored as actual URL or null (no placeholder text).

## Next Phase Readiness

- Phase 5 (Integrated CLI / meet list) can read `notion_url` from `metadata/{stem}.json` directly
- `meet init` should be extended to prompt for `notion.token` and `notion.parent_page_id`
- NotionTokenCheck and NotionDatabaseCheck are registered in doctor — users will see Notion health status

---
*Phase: 04-notion-integration*
*Completed: 2026-03-22*
