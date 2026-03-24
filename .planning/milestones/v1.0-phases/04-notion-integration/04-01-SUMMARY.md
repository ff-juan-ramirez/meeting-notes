---
phase: 04-notion-integration
plan: 01
subsystem: notion-service
tags: [notion, config, service-layer, tdd]
dependency_graph:
  requires: []
  provides: [notion-service, notion-config]
  affects: [meet-summarize, meet-doctor]
tech_stack:
  added: [notion-client>=2.0]
  patterns: [pure-function-service, dataclass-config, exponential-backoff-retry]
key_files:
  created:
    - meeting_notes/services/notion.py
    - tests/test_notion_service.py
  modified:
    - meeting_notes/core/config.py
    - tests/test_config.py
    - pyproject.toml
decisions:
  - "APIResponseError requires real constructor args (code, status, message, headers, raw_body_text) — MagicMock(spec=APIResponseError) cannot be raised, so tests use real instances"
  - "All heading levels (H1, H2, H3) convert to heading_2 blocks — consistent with RESEARCH.md guidance"
  - "_call_with_retry catches exc.status == 429 from notion_client.errors.APIResponseError with exponential doubling starting at 1.0s"
metrics:
  duration_seconds: 147
  completed_date: "2026-03-23"
  tasks_completed: 2
  files_changed: 5
---

# Phase 4 Plan 1: Notion Service Layer and Config Extension Summary

## One-liner

Notion API wrapper with create_page, extract_title, markdown_to_blocks, split_text, and call_with_retry, plus NotionConfig dataclass extending Config with token and parent_page_id fields.

## What Was Built

### Task 1: NotionConfig dataclass + Config extension + test stubs (TDD RED)

- Added `NotionConfig` dataclass to `meeting_notes/core/config.py` with `token: str | None = None` and `parent_page_id: str | None = None` fields
- Extended `Config` dataclass with `notion: NotionConfig = field(default_factory=NotionConfig)`
- Extended `Config.load()` to deserialize the "notion" section via `notion_data = data.get("notion", {})`
- Added `notion-client>=2.0` to `pyproject.toml` dependencies
- Extended `tests/test_config.py` with 5 new tests for NotionConfig (all passing)
- Created `tests/test_notion_service.py` with 15 Wave 0 stubs covering all service functions (failing — notion.py not yet created)

### Task 2: Implement services/notion.py (TDD GREEN)

Created `meeting_notes/services/notion.py` as a pure-function module (no Click/Rich) mirroring `services/llm.py`:

- `extract_title(notes_markdown, fallback_timestamp)` — returns first H1 stripped of "# " prefix; falls back to first non-empty line; falls back to timestamp
- `create_page(token, parent_page_id, title, notes_markdown)` — instantiates Client(auth=token), converts markdown to blocks, calls pages.create(), handles overflow >100 blocks via blocks.children.append(), returns URL as `https://notion.so/{id_no_hyphens}`
- `_split_text(text, max_chars=1900)` — splits at last whitespace before limit; hard-splits if no whitespace found
- `_rich_text(content)` — returns Notion rich_text array
- `_markdown_to_blocks(markdown)` — converts H1/H2/H3 to heading_2, "- "/"* " to bulleted_list_item, other non-empty lines to paragraph
- `_call_with_retry(fn, *args, **kwargs)` — retries up to 4 times on APIResponseError with status 429, doubles delay from 1.0s; raises immediately on non-429 errors

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_call_with_retry test using unraisable MagicMock**

- **Found during:** Task 2 (TDD GREEN phase)
- **Issue:** Test used `MagicMock(spec=APIResponseError)` and tried to `raise` it — fails with `TypeError: exceptions must derive from BaseException` because MagicMock instances are not real exceptions
- **Fix:** Replaced with `_make_api_error(status)` helper that constructs a real `APIResponseError` instance with required constructor args (`code`, `status`, `message`, `headers`, `raw_body_text`)
- **Files modified:** `tests/test_notion_service.py`
- **Commit:** 13b8865

## Known Stubs

None — all service functions are fully implemented and wired up.

## Decisions Made

1. `APIResponseError` requires real constructor args — `MagicMock(spec=...)` cannot be raised; tests use real instances with `httpx.Headers()` as empty headers
2. All heading levels (H1, H2, H3) map to `heading_2` blocks per RESEARCH.md guidance ("implement headings as heading_2 blocks")
3. `_call_with_retry` reads `exc.status` directly on `APIResponseError` instance per notion_client v3.0.0 API

## Self-Check: PASSED

- meeting_notes/services/notion.py: FOUND
- meeting_notes/core/config.py: FOUND
- tests/test_notion_service.py: FOUND
- tests/test_config.py: FOUND
- Commit 035720b (Task 1): FOUND
- Commit 13b8865 (Task 2): FOUND
- All 134 tests pass
