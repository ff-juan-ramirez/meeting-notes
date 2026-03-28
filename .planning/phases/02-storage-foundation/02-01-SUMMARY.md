---
phase: 02-storage-foundation
plan: 01
subsystem: storage
tags: [slugify, unicodedata, re, storage, path-generation, tdd]

# Dependency graph
requires: []
provides:
  - "slugify(text: str) -> str — pure function, stdlib only (SLUG-01, SLUG-02)"
  - "get_recording_path_with_slug(name, storage_path) -> Path — {slug}-{timestamp}-{uuid8}.wav stem (RECORD-05)"
affects:
  - "03-record-stop-command: calls get_recording_path_with_slug() when [NAME] arg provided"
  - "any phase using recording file stems for session resolution"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "slugify(): NFKD normalize → ASCII encode → lowercase → re.sub non-alphanum → strip hyphens → truncate 80"
    - "get_recording_path_with_slug(): mirrors get_recording_path() pattern, slug-prefixed stem"

key-files:
  created: []
  modified:
    - "meeting_notes/core/storage.py"
    - "tests/test_storage.py"

key-decisions:
  - "slugify truncates at 80 chars with trailing hyphen strip (D-01)"
  - "get_recording_path_with_slug accepts str only, not str|None (D-02) — called only when name is known"
  - "NFKD normalization for Unicode (D-03) — handles accents, ligatures, fullwidth chars"
  - "Zero new dependencies: only unicodedata + re from stdlib (SLUG-02)"

patterns-established:
  - "slugify pattern: normalize → ASCII → lower → sub → strip → truncate"
  - "Path function pair: get_recording_path() for unnamed, get_recording_path_with_slug(name) for named — no branching inside"

requirements-completed: [SLUG-01, SLUG-02, RECORD-05]

# Metrics
duration: 3min
completed: 2026-03-28
---

# Phase 02 Plan 01: Storage Foundation Summary

**`slugify()` and `get_recording_path_with_slug()` pure functions using unicodedata+re stdlib, producing `{slug}-{timestamp}-{uuid8}.wav` stems for named recordings**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-28T16:02:21Z
- **Completed:** 2026-03-28T16:05:13Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `slugify()` pure function handles all SLUG-01 edge cases: colons (`1:1` → `1-1`), Unicode accents (é→e, ñ→n via NFKD), slashes, whitespace runs, leading/trailing hyphens, 80-char max truncation, empty/all-punctuation fallback to `"untitled"`
- `get_recording_path_with_slug(name, storage_path)` generates `{slug}-{timestamp}-{uuid8}.wav` paths following `get_recording_path()` pattern (RECORD-05)
- Zero new dependencies — purely stdlib (`unicodedata` + `re`) satisfying SLUG-02
- 15 new tests added (10 slugify, 5 path); all pass

## Task Commits

Each task was committed atomically:

1. **Task 1: TDD slugify() pure function** - `7a68a93` (feat)
2. **Task 2: TDD get_recording_path_with_slug() function** - `df26b40` (feat)

_Note: TDD tasks — RED phase (ImportError) confirmed before each GREEN implementation._

## Files Created/Modified

- `meeting_notes/core/storage.py` — Added `import re`, `import unicodedata`, `slugify()`, `get_recording_path_with_slug()`
- `tests/test_storage.py` — Added 15 new tests: 10 for `slugify`, 5 for `get_recording_path_with_slug`

## Decisions Made

- `slugify` truncates at 80 chars with `.rstrip("-")` on the slice to avoid trailing hyphens from mid-word cuts (D-01)
- `get_recording_path_with_slug` signature is `name: str` (not `str | None`) because it is only called when a name is known — Phase 03 will dispatch between the two path functions (D-02)
- NFKD normalization chosen over NFC for broader Unicode compatibility: handles accented chars, ligatures, fullwidth characters (D-03)
- No version pin on stdlib modules; no new pyproject.toml entries (SLUG-02 constraint)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Pre-existing test failure (out of scope, deferred):** `test_get_data_dir_default` was already failing before this plan because commit `cb3a91a` changed `get_data_dir()` default to `~/Documents/meeting-notes` but the test still asserts `.local/share/meeting-notes`. Not caused by Phase 02 changes. Logged in `deferred-items.md`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `slugify()` and `get_recording_path_with_slug()` are ready for Phase 03 (`meet record [NAME]`) to call
- Phase 03 will import `get_recording_path_with_slug` from `meeting_notes.core.storage` and call it when the `[NAME]` argument is provided
- Unnamed sessions continue using `get_recording_path()` — no migration needed

---
*Phase: 02-storage-foundation*
*Completed: 2026-03-28*
