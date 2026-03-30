# Phase 02: Storage Foundation - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Add two pure functions to `meeting_notes/core/storage.py`:
1. `slugify(text: str) -> str` — converts an arbitrary meeting name to a URL-safe slug
2. `get_recording_path_with_slug(name: str, storage_path: str | None = None) -> Path` — like `get_recording_path()` but produces a `{slug}-{timestamp}-{uuid8}` stem

No CLI changes. No callers updated. This is the storage foundation that Phase 03 (meet record [NAME]) will build on.

</domain>

<decisions>
## Implementation Decisions

### Truncation at 80 chars
- **D-01:** Hard cut at 80 characters: `slug[:80].rstrip('-')` — simple, predictable, always within limit. Trailing hyphen from a mid-word cut is stripped.

### `get_recording_path_with_slug` Signature
- **D-02:** Accept `str` only (not `str | None`). The function is only called when a name is known. Phase 03 will call `get_recording_path()` for unnamed sessions and `get_recording_path_with_slug(name)` for named ones. Two clean, single-purpose functions — no branching inside.

### Unicode Normalization
- **D-03:** Use NFKD normalization. Handles accents (é→e, ñ→n) and compatibility characters (ligatures fi→fi, fullwidth chars). Broader coverage, no downside for meeting names.

### Claude's Discretion
- `slugify` edge case handling beyond the spec (numbers-only, very short names, etc.) — implement per common sense
- Test case selection for `slugify` beyond the minimum required cases from SLUG-01
- Internal step order within `slugify` (normalize → encode ASCII → decode → lowercase → replace non-alphanum → collapse hyphens → strip hyphens → truncate)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — SLUG-01, SLUG-02, RECORD-05 are the locked acceptance criteria for this phase

### Existing Code
- `meeting_notes/core/storage.py` — current file; `get_recording_path()` is the pattern to follow for `get_recording_path_with_slug()`
- `tests/test_storage.py` — existing test patterns (XDG monkeypatching, function isolation)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_recording_path(storage_path=None) -> Path`: generates `{timestamp}-{uuid8}.wav` stem — `get_recording_path_with_slug` follows the same structure, prepending the slug

### Established Patterns
- Pure functions, no global state
- `storage_path: str | None = None` parameter pattern used consistently for testability
- XDG_DATA_HOME env var used in tests to redirect data dir to tmp_path

### Integration Points
- Phase 03 (`meet record [NAME]`) will import and call `slugify` + `get_recording_path_with_slug` from `meeting_notes.core.storage`
- `test_storage.py` will grow with new test functions for both new functions

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond REQUIREMENTS.md — open to standard implementation approach.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-storage-foundation*
*Context gathered: 2026-03-28*
