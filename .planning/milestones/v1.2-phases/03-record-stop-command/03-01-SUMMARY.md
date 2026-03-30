---
phase: 03-record-stop-command
plan: 01
subsystem: record-command
tags: [click, argument, slugify, state, metadata, tdd, record, stop]

# Dependency graph
requires:
  - "02-01: slugify() and get_recording_path_with_slug() from storage.py"
provides:
  - "meet record [NAME] optional positional argument (RECORD-01)"
  - "recording_name and recording_slug stored in state.json at record time (RECORD-02, RECORD-03)"
  - "meet stop propagates recording_name/slug from state to metadata JSON (RECORD-04)"
affects:
  - "downstream phases reading recording_name from metadata for Notion titles and meet list display"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "click.argument('name', required=False, default=None) for optional positional arg"
    - "name.strip() if name else None — guard against None before strip (D-02)"
    - "state.get('recording_name') — .get() returns None for unnamed, if-guard ensures no key written"
    - "existing.get('recording_name') in stop — reads only if present, no KeyError"

key-files:
  created: []
  modified:
    - "meeting_notes/services/audio.py"
    - "meeting_notes/cli/commands/record.py"
    - "tests/test_record_command.py"

key-decisions:
  - "Optional positional arg via @click.argument('name', required=False, default=None) — not --name option (RECORD-01)"
  - "recording_name stripped via name.strip() before storage — surrounding whitespace not meaningful (D-02)"
  - "slug computed at record time from stripped name, not at stop time — state.json carries both fields"
  - "start_recording() output_path param defaults to None — existing callers unchanged, named sessions pre-compute slug path"
  - "stop propagation uses .get() with if-guards — no key written for unnamed sessions, full backward compat"

requirements-completed: [RECORD-01, RECORD-02, RECORD-03, RECORD-04]

# Metrics
duration: 254
completed: 2026-03-28
---

# Phase 03 Plan 01: Record Stop Command Summary

**Optional `[NAME]` argument wired through record/stop lifecycle: slug-prefixed WAV path, recording_name/slug in state.json, propagated to metadata on stop — 9 new tests, all 16 record tests pass**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-28T16:51:55Z
- **Completed:** 2026-03-28T16:56:09Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `start_recording(config, output_path=None)` optional parameter — named sessions pass slug-prefixed path, unnamed sessions unchanged
- `record` command accepts optional `[NAME]` positional argument via `@click.argument("name", required=False, default=None)`
- Named sessions: `recording_name` (stripped) and `recording_slug` (via `slugify()`) stored in state.json
- Named session output path uses `get_recording_path_with_slug()` for `{slug}-{timestamp}-{uuid8}.wav` stem
- Named session CLI output: `Recording started: "NAME" (PID: ...)` per D-01
- `meet stop` propagates `recording_name` and `recording_slug` from state to metadata JSON using `.get()` guard
- Unnamed sessions completely unchanged in both record and stop behavior
- 9 new tests added: 6 for Task 1 (named record, whitespace strip, unnamed unchanged, output message, audio.py with/without output_path), 3 for Task 2 (stop propagates name, unnamed no name in metadata, named preserves duration)
- All 16 record command tests pass; full suite shows 221 passing (11 pre-existing failures unrelated to this plan)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add NAME argument to meet record and wire slug/name into state** - `6460235` (feat)
2. **Task 2: Propagate recording_name and recording_slug from state to metadata in meet stop** - `a0bc045` (feat)

_Note: TDD tasks — RED phase confirmed before each GREEN implementation._

## Files Created/Modified

- `meeting_notes/services/audio.py` — Added optional `output_path: Path | None = None` param to `start_recording()`
- `meeting_notes/cli/commands/record.py` — Added NAME arg, slug logic, name/slug in state, named output message, stop propagation
- `tests/test_record_command.py` — Added 9 new tests (6 Task 1, 3 Task 2)

## Decisions Made

- Optional positional arg (`@click.argument("name", required=False, default=None)`) chosen over `--name` option — positional args are more natural for naming a recording
- `name.strip() if name else None` — guards None before calling strip; stripped value stored as `recording_name`
- `slugify(recording_name)` computed from stripped name at record time, stored alongside `recording_name`
- `start_recording()` pre-computes the slug path externally (`get_recording_path_with_slug()`), passes as `output_path` — cleaner separation of concerns
- Stop command uses `existing.get("recording_name")` + if-guard — no key written for unnamed sessions (backward compat, no `None` values in metadata)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MagicMock(spec=Config) incompatible with nested attribute assignment**

- **Found during:** Task 1 GREEN phase (test_start_recording_with_output_path)
- **Issue:** `config = MagicMock(spec=Config)` followed by `config.audio.system_device_index = 1` raises `AttributeError: Mock object has no attribute 'audio'` because spec enforcement blocks attribute access not in Config's spec
- **Fix:** Changed to `config = MagicMock()` (no spec) for audio service tests — sufficient for testing output_path parameter behavior
- **Files modified:** `tests/test_record_command.py`
- **Commit:** included in `6460235`

### Dependency Resolution (not a deviation — expected)

The plan depends on `slugify()` and `get_recording_path_with_slug()` from Phase 02 Plan 01. These were implemented in parallel worktree branch `worktree-agent-a8b8383a`. Cherry-picked commits `7a68a93` and `df26b40` into this branch to satisfy the dependency before executing plan tasks.

## Pre-existing Test Failures (Out of Scope)

The following test failures existed before this plan and were not caused by our changes:

- `tests/test_init.py` (10 failures) — `meet init` storage path prompt added in another parallel worktree changes tests' expected input sequence
- `tests/test_llm_service.py::test_templates_contain_grounding_rule` — template content changed elsewhere
- `tests/test_storage.py::test_get_data_dir_default` — pre-existing since `cb3a91a` changed default path (documented in 02-01 SUMMARY)

Logged to `deferred-items.md` for resolution.

## Known Stubs

None — all implementation is wired end-to-end.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `recording_name` and `recording_slug` are now in session metadata JSON for all named sessions
- Downstream phases (meet list, meet summarize, Notion push) can read `recording_name` from metadata for display and titles
- Unnamed sessions continue working with no migration needed

---
*Phase: 03-record-stop-command*
*Completed: 2026-03-28*
