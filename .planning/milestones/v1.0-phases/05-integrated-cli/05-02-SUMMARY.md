---
phase: 05-integrated-cli
plan: "02"
subsystem: cli
tags: [cli, meet-list, rich-table, json-output, status-filter, duration, title-derivation, tdd]
dependency_graph:
  requires:
    - meeting_notes.cli.ui.console (from Plan 01)
    - meeting_notes.core.state.read_state
    - meeting_notes.core.storage.get_data_dir
    - meeting_notes.services.notion.extract_title
  provides:
    - meeting_notes.cli.commands.list.list_sessions (meet list CLI command)
    - Rich table display of all sessions with Date/Duration/Title/Status/Notion URL columns
    - --status filter (not-transcribed/transcribed/summarized)
    - --json clean JSON array output
    - Duration mm:ss formatting with WAV header fallback
    - Title derivation from notes # heading, fallback to session stem
    - Status derivation from notes_path/transcript_path file existence
    - Newest-first sort by transcribed_at then WAV mtime
  affects:
    - meeting_notes/cli/main.py (list_sessions registered as direct import)
tech_stack:
  added: []
  patterns:
    - Rich Table with console.print() for tabular output
    - click.Choice for --status option validation
    - json.dumps with default=str for JSON serialization of session metadata
    - wave stdlib for WAV duration extraction without dependencies
key_files:
  created:
    - meeting_notes/cli/commands/list.py
    - tests/test_cli_list.py
  modified:
    - meeting_notes/cli/main.py
decisions:
  - list_sessions registered directly in main.py (try/except ImportError guard removed — Plan 02 is now complete)
  - Wide console (width=200) patched in tests to prevent Rich table truncation in CliRunner narrow terminal
  - Test assertions use derived title ("Summary Meeting") not raw stem for filter tests — stem only appears when session has no notes heading
  - Notion URL column checked as "https://" prefix in table tests (Rich may truncate long URLs in narrow terminal)
  - _derive_status uses Path.exists() checks — both field presence and file existence required for transcribed/summarized
metrics:
  duration_seconds: 232
  completed_date: "2026-03-23"
  tasks_completed: 1
  files_created: 2
  files_modified: 1
---

# Phase 05 Plan 02: meet list Command Summary

**One-liner:** `meet list` command with Rich table (Date/Duration/Title/Status/Notion URL), `--status` filter, `--json` output, mm:ss duration with WAV fallback, and title from notes `# Heading`.

## What Was Built

Implemented the `meet list` CLI command that scans `~/.local/share/meeting-notes/metadata/*.json` files and displays all recorded sessions in a Rich table or clean JSON array.

### Files Created

**`meeting_notes/cli/commands/list.py`** (187 lines)

Core helpers:
- `_wav_duration(wav_path_str)` — reads WAV header via stdlib `wave` module, returns seconds or None
- `_format_duration(seconds)` — formats as `mm:ss`, returns em dash for None
- `_derive_status(meta)` — returns `"summarized"` / `"transcribed"` / `"not-transcribed"` based on file existence
- `_derive_title(meta, stem)` — reads notes file and calls `extract_title()` for summarized sessions, falls back to stem
- `_derive_date(meta)` — formats `transcribed_at`/`summarized_at` as `YYYY-MM-DD HH:MM`, falls back to WAV mtime
- `_sort_key(path)` — sort key for newest-first ordering (ISO string)

`list_sessions` Click command:
- `--status` option with `click.Choice(["not-transcribed", "transcribed", "summarized"])`
- `--json` flag for clean JSON output via `print(json.dumps(..., default=str))`
- `--quiet` support via `ctx.obj["quiet"]`
- Empty metadata directory returns empty table (not an error)

**`tests/test_cli_list.py`** (16 test functions, 410+ lines)

Complete test coverage:
1. Empty metadata shows column headers
2. Summarized session row with all columns
3. Not-transcribed status and stem title
4. Transcribed status
5. `--status summarized` filter
6. `--status not-transcribed` filter
7. `--json` valid JSON array, no ANSI codes
8. `--json --status` combined
9. Duration from metadata (300s → "05:00")
10. Duration from WAV header fallback
11. Duration dash when no WAV
12. Title from notes `# Heading`
13. Title fallback to stem when notes missing
14. Newest-first sort order
15. `--quiet` suppresses table output
16. No metadata directory → empty JSON array

### Files Modified

**`meeting_notes/cli/main.py`** — removed `try/except ImportError` guard, added direct import:
```python
from meeting_notes.cli.commands.list import list_sessions
main.add_command(list_sessions)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Rich table truncation in CliRunner narrow terminal**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** `CliRunner` runs with a narrow terminal width, causing Rich to truncate column values (Status "transcribed" → empty, Notion URL → "https://www.n…", Title → "Test Me…")
- **Fix:** Added `_wide_console = Console(width=200, force_terminal=False, highlight=False)` in test file and patched it via `patch("meeting_notes.cli.commands.list.console", _wide_console)` in `_invoke()` helper
- **Files modified:** `tests/test_cli_list.py`
- **Commit:** 45bd588

**2. [Rule 1 - Bug] Test assertions checked raw stem in filter test**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** `test_status_filter_summarized` checked for `stem_sum` in output but the summarized session title comes from the notes heading ("Summary Meeting"), not the stem
- **Fix:** Changed assertion to check for derived title "Summary Meeting"
- **Files modified:** `tests/test_cli_list.py`
- **Commit:** 45bd588

## Test Results

```
python3 -m pytest tests/ -x -q
176 passed in 1.26s
```

All 176 tests pass. No regressions.

## Known Stubs

None — the `meet list` command is fully wired to real session metadata. All columns derive from actual metadata JSON files. No placeholder or hardcoded values flow to UI rendering.

## Self-Check: PASSED
