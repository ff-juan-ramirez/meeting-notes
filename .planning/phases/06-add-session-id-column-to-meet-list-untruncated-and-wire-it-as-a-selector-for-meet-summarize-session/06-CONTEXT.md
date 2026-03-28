# Phase 06: Session ID Column + meet summarize --session Selector - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a "Session ID" column to `meet list` (untruncated, appended as the last column) showing
the full file stem for each session. This gives users the exact value to pass to
`meet summarize --session <stem>`. No changes to session resolution logic — exact stem matching
already works. No slug-prefix glob matching (SESSRES-01 remains deferred).

Also add `session_id` as a field in `meet list --json` output (currently, the stem is a local
variable in `list_sessions()` and is absent from JSON).

No changes to `meet summarize` other than updating the `--session` help text to reflect
v1.2 stem format (e.g., `team-standup-20260322-143000-abc12345`).

</domain>

<decisions>
## Implementation Decisions

### Session ID definition
- **D-01:** The session ID is the full file stem as used by `--session` today:
  - Named sessions: `{slug}-{timestamp}-{uuid8}` (e.g., `team-standup-20260322-143000-abc12345`)
  - Unnamed sessions: `{timestamp}-{uuid8}` (e.g., `20260322-143000-abc12345`)
  - This is the exact value the user copies into `meet summarize --session <value>`.

### Column placement
- **D-02:** Session ID column goes **last** — after the existing "Notion URL" column. No `max_width`
  constraint (untruncated). This is the least disruptive layout change.

### Default behavior (no --session)
- **D-03:** `meet summarize` with no `--session` already resolves the latest transcript by mtime
  (`resolve_latest_transcript`). No code change required. This decision is confirmed — no
  changes to default resolution logic.

### JSON output
- **D-04:** Add `session_id` as an explicit field in the session dict inside `list_sessions()`.
  Set it to `stem` (the metadata JSON filename stem, e.g., `path.stem`). This makes `--json`
  output scriptable with `--session`. The field should appear alongside `status`, `title`,
  `date`, `duration_display`, etc.

### --session help text
- **D-05:** Update the `--session` option help string in `summarize.py` to reflect the current
  v1.2 stem format. Example: `"Session stem shown in 'meet list' (e.g. team-standup-20260322-143000-abc12345)"`.

### Claude's Discretion
- Column header label: "Session ID" or "ID" — either is acceptable; "Session ID" is clearer
- Whether to truncate very long stems in the Rich table (e.g., Rich's default wrapping vs
  no constraint) — no `max_width` is the intent; Rich will expand the table as needed
- Test case naming and fixture reuse in `test_cli_list.py`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing code (must read before planning)
- `meeting_notes/cli/commands/list.py` — `list_sessions()` function; session dict construction
  at the `sessions.append({...})` call; Rich table column definitions; `stem = path.stem` local var
- `meeting_notes/cli/commands/summarize.py` — `resolve_latest_transcript()` and
  `resolve_transcript_by_stem()`; `--session` option definition at line 53; help text to update
- `tests/test_cli_list.py` — existing test patterns (`_write_metadata`, `_write_notes`,
  `_wide_console` fixture, `CliRunner` usage) to follow for new tests

### Requirements
- `.planning/REQUIREMENTS.md` — SESSRES-01 is deferred; confirms exact stem match is sufficient
- `.planning/phases/04-meet-list-display/04-CONTEXT.md` — prior decisions for list command
  (D-01 through D-03, established `meta.get()` and falsy-check patterns)

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Where stem is derived
- `list.py`: `stem = path.stem` inside the `for path in json_files:` loop (around line 140)
- `stem` is used in `_derive_title(meta, stem)` but is NOT currently added to the session dict
  — it must be explicitly added as `"session_id": stem` in the `sessions.append({...})` call

### Rich table columns
- Current: `table.add_column("Date")`, `"Duration"`, `"Title" (max_width=40)`, `"Status"`, `"Notion URL"`
- Add: `table.add_column("Session ID")` — no `max_width` — at the end
- Corresponding `table.add_row(...)` call needs one more value: `s.get("session_id", "—")`

### JSON output gap
- `sessions.append({**meta, "status": ..., "title": ..., "date": ..., ...})` — `stem` is absent
- Fix: add `"session_id": stem` to this dict

### Summarize help text
- Current: `help="Transcript filename stem (e.g. 20260322-143000-abc12345)"`
- New: reflects v1.2 format with slug prefix

### Established Patterns
- `meta.get("recording_name")` falsy check pattern from Phases 04-05
- `_write_metadata(data_dir, stem, meta)` test fixture in `test_cli_list.py`
- `_wide_console` fixture patches Rich console to `width=200` to prevent table truncation in tests

### Integration Points
- `list_sessions()` is the only function that needs changes for the table and JSON output
- `summarize.py` only needs a help text update (no logic change)

</code_context>

<specifics>
## Specific Ideas

- User confirmed: "just display the ID" — no SESSRES-01 slug matching, no change to `--session` resolution logic
- User confirmed: "that's it" for default behavior — latest transcript by mtime is correct, no ordering alignment needed

</specifics>

<deferred>
## Deferred Ideas

- **SESSRES-01** (slug-prefix glob match): `--session team-standup` finding the right session by name prefix. Confirmed deferred — exact stem match is sufficient for now.
- `meet transcribe --session` — phase explicitly scopes to `meet summarize --session`; transcribe is unchanged.

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-add-session-id-column-to-meet-list-untruncated-and-wire-it-as-a-selector-for-meet-summarize-session*
*Context gathered: 2026-03-28*
