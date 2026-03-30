# Phase 02: Storage Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 02-storage-foundation
**Areas discussed:** Truncation at 80 chars, get_recording_path_with_slug signature, Unicode normalization depth

---

## Truncation at 80 chars

| Option | Description | Selected |
|--------|-------------|----------|
| Hard cut at 80 chars | `slug[:80].rstrip('-')` — simple, predictable, always within limit. Trailing hyphen stripped. | ✓ |
| Word-boundary cut | Drop last incomplete word so slug reads cleanly. Slightly more complex, result may be shorter than 80 chars. | |

**User's choice:** Hard cut at 80 chars (recommended default)
**Notes:** None

---

## get_recording_path_with_slug Signature

| Option | Description | Selected |
|--------|-------------|----------|
| `str` only — caller guards | `def get_recording_path_with_slug(name: str, storage_path=None)`. Phase 03 calls `get_recording_path()` or `get_recording_path_with_slug(name)` based on whether name is given. Two clean functions. | ✓ |
| `str \| None` — unified | `def get_recording_path_with_slug(name: str \| None = None, storage_path=None)`. Falls back to timestamp-only when None. Phase 03 always calls one function. | |

**User's choice:** `str` only — caller guards
**Notes:** None

---

## Unicode Normalization Depth

| Option | Description | Selected |
|--------|-------------|----------|
| NFKD | Handles accents (é→e, ñ→n) AND compatibility chars (ligatures fi→fi, fullwidth). Broader. | ✓ |
| NFD only | Accents only. Ligatures/fullwidth pass through and get stripped by ASCII filter. Simpler but narrower. | |

**User's choice:** NFKD
**Notes:** None

---

## Claude's Discretion

- `slugify` edge case handling beyond spec (numbers-only, very short names)
- Test case selection beyond minimum required by SLUG-01
- Internal step order within `slugify`

## Deferred Ideas

None.
