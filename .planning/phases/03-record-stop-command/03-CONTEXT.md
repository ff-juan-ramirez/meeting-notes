# Phase 03: Record/Stop Command - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend `meet record` with an optional positional NAME argument and wire the name/slug through the state → metadata lifecycle:

1. `meet record [NAME]` — accepts an optional NAME; unnamed invocation is unchanged (RECORD-01)
2. `recording_name` stored verbatim (post-strip) in `state.json` at record time (RECORD-02)
3. `recording_slug` computed via `slugify(name)` at record time and stored in `state.json` (RECORD-03)
4. `meet stop` propagates `recording_name` and `recording_slug` from `state.json` to session metadata JSON before clearing state (RECORD-04)

No changes to `meet list`, `meet transcribe`, or `meet summarize` — those are Phases 04 and 05.

</domain>

<decisions>
## Implementation Decisions

### CLI Output for Named Recording
- **D-01:** When NAME is provided, echo it in the "Recording started" output: `Recording started: "1:1 with Gabriel" (PID: X)` + `Output: path`. Unnamed sessions keep the current output unchanged. Users benefit from confirmation the name was captured.

### NAME Whitespace Handling
- **D-02:** Strip surrounding whitespace from NAME before storing as `recording_name`. Shell-quoting accidents shouldn't embed leading/trailing spaces in the stored name. "Verbatim" in RECORD-02 means the user's intended name, post-strip.

### Claude's Discretion
- How `start_recording` interface is adapted to accept a pre-computed output path for named sessions (pass path as argument vs. generate inside audio.py)
- Whether `meet stop` output changes for named sessions (can show name from state if present — reasonable UX improvement, but not required)
- Test structure: whether named/unnamed session tests go in existing `test_record_command.py` or a new test section

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — RECORD-01, RECORD-02, RECORD-03, RECORD-04 are the locked acceptance criteria for this phase

### Existing Code (must read before planning)
- `meeting_notes/cli/commands/record.py` — current `record` and `stop` commands; this is the primary file being modified
- `meeting_notes/core/storage.py` — `slugify()` and `get_recording_path_with_slug()` already implemented here (Phase 02)
- `meeting_notes/core/state.py` — `write_state`, `read_state`, `clear_state` — state management primitives used by both commands
- `tests/test_record_command.py` — existing test patterns (patching `_get_state_path`, `_get_config_path`, `start_recording`, `get_data_dir`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `slugify(name: str) -> str` in `core/storage.py` — call this to compute `recording_slug`
- `get_recording_path_with_slug(name, storage_path)` in `core/storage.py` — use for named sessions instead of `get_recording_path()`
- `write_state` / `read_state` in `core/state.py` — already used by both commands

### Established Patterns
- State dict in `record` command: `{"session_id", "pid", "output_path", "start_time"}` — add `recording_name` and `recording_slug` as optional fields
- Metadata read-merge-write pattern in `stop` command (see lines 106-121 in `record.py`) — propagate name/slug into existing `meta` dict using `.get()` reads from state
- `_get_state_path()` / `_get_config_path()` private helpers for testability via `patch`

### Integration Points
- `start_recording(config)` currently generates the output path internally — needs to accept a pre-computed path for named sessions, OR the path is generated before calling `start_recording` and passed in
- `stop` command already reads full `existing` state dict — `recording_name` and `recording_slug` are just additional keys to propagate to metadata

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

*Phase: 03-record-stop-command*
*Context gathered: 2026-03-28*
