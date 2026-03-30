# Phase 04: meet list Display - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Update `meet list` to use `recording_name` as the primary session title source, before the existing LLM-heading → stem fallback chain. Only `_derive_title()` in `meeting_notes/cli/commands/list.py` changes. No new CLI flags, no new columns, no changes to other commands.

- LIST-03 (dedicated "Name" column) is explicitly deferred — out of scope for this phase.
- `meet transcribe` and `meet summarize` are unchanged.

</domain>

<decisions>
## Implementation Decisions

### Title derivation priority
- **D-01:** `recording_name` always wins — even for fully summarized sessions where an LLM heading is available. The priority chain is: `meta.get("recording_name")` → LLM heading (from notes file via `extract_title()`) → session stem. When the user explicitly named a meeting, that name is the definitive title regardless of summary state.

### `--json` output
- **D-02:** No code change needed. `recording_name` already flows into `--json` output automatically via the `**meta` spread in the sessions dict (list.py:152). The plan must include a test that verifies `recording_name` appears as a top-level field in the JSON output for named sessions — but zero new production code is required for this.

### Regression test coverage for LIST-02
- **D-03:** Add explicit regression tests for:
  1. Session with no `recording_name` field in metadata (pre-v1.2 session) → title unchanged (LLM heading or stem as before)
  2. Session with `recording_name` set to `None` or empty string → falls through to LLM-heading/stem fallback
  3. Session where `recording_name` is present → always shown as title regardless of notes state

### Claude's Discretion
- Whether the new `recording_name` check is a guard clause at the top of `_derive_title()` or an `if/elif` chain — either is fine, guard clause preferred for clarity
- Test case naming and fixture reuse within `test_cli_list.py`
- Whether `recording_name=""` (empty string) is treated the same as absent (it should be — falsy check is appropriate)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — LIST-01, LIST-02 are the locked acceptance criteria for this phase

### Existing Code (must read before planning)
- `meeting_notes/cli/commands/list.py` — `_derive_title()` at lines 54-67 is the only function being modified; lines 138-159 show the session dict construction where `**meta` spread occurs
- `tests/test_cli_list.py` — existing test patterns (`_write_metadata`, `_write_notes`, `_wide_console` fixture, `CliRunner` patterns)

</canonical_refs>

<code_context>
## Existing Code Insights

### The one function to change
- `_derive_title(meta: dict, stem: str) -> str` at `list.py:54-67`: currently checks `notes_path` then falls back to `stem`. Add `recording_name` check before both.

### `--json` free win
- `sessions.append({**meta, "status": ..., "title": ..., ...})` at line 152 — `recording_name` from metadata already appears in JSON output for free. No code change, just a test.

### Established Patterns
- `meta.get("recording_name")` is the correct read pattern (consistent with Phase 03 write pattern)
- Falsy check is appropriate (`if name := meta.get("recording_name")` or `name = meta.get("recording_name"); if name:`)
- Test fixtures: `_write_metadata(data_dir, stem, meta)` writes metadata JSON; `_write_notes(data_dir, stem, template, content)` writes notes file

### Integration Points
- `_derive_title()` is called at list.py:155 during session assembly — no other callers in this file

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond REQUIREMENTS.md — the implementation path is clear and narrow.

</specifics>

<deferred>
## Deferred Ideas

- LIST-03: Dedicated "Name" column distinct from derived title — explicitly deferred per REQUIREMENTS.md (low ROI for narrow table width)

</deferred>

---

*Phase: 04-meet-list-display*
*Context gathered: 2026-03-28*
