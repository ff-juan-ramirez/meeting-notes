# Phase 7: Notion Title at Summarize Time - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `--title` option to `meet summarize` that lets the user specify the Notion page title
at summarize time, overriding the name set at record time. The title affects only the Notion
page title — no changes to local notes filename, session metadata, or any other output.

</domain>

<decisions>
## Implementation Decisions

### Flag design
- **D-01:** The flag is `--title` (long-form only, no `-t` short alias) — consistent with
  existing `--template` and `--session` flags which are also long-form only.
- **D-02:** Usage: `meet summarize --title "Weekly Sync"` or with session:
  `meet summarize --session team-standup-20260322-143000-abc12345 --title "Weekly Sync"`

### Priority chain
- **D-03:** `--title` always wins. Full priority chain:
  1. `--title` (CLI flag, explicit at summarize time)
  2. `recording_name` from session metadata (set at `meet record "Name"` time)
  3. `extract_title(notes, fallback_ts)` (LLM-extracted heading or timestamp fallback)
- **D-04:** If `--title` is provided, it overrides `recording_name` even when `recording_name`
  is set. If `--title` is omitted, the existing Phase 5 behavior is unchanged.

### Metadata persistence
- **D-05:** `--title` is a runtime override only. It does NOT write back to session metadata JSON.
  Re-running `meet summarize` without `--title` will still use `recording_name` from metadata
  (or `extract_title()` if no `recording_name`). This keeps `--title` as a one-time override
  rather than a stored fact.

### Scope
- **D-06:** `--title` affects only the Notion page title. Local notes file keeps its existing
  stem-based name (e.g. `team-standup-20260322-meeting.md`). No filename changes, no metadata
  writes beyond what already happens.

### Claude's Discretion
- Help text wording for `--title` (e.g. "Override the Notion page title for this run")
- Whether to guard with falsy check (`if title:`) consistent with Phase 4/5 pattern — yes,
  use falsy check to handle empty string uniformly

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core implementation files
- `meeting_notes/cli/commands/summarize.py` — the command to modify; see lines 50-55 for existing
  flag definitions, lines 150-152 for current title priority logic
- `meeting_notes/services/notion.py` — `create_page()` and `extract_title()` functions; no changes
  expected here

### Prior phase patterns to follow
- `.planning/phases/05-notion-title-integration/05-01-PLAN.md` — Phase 5 plan that introduced
  `recording_name` → Notion title logic; new `--title` flag extends this chain

### Test file
- `tests/test_summarize_command.py` — existing tests; new tests for `--title` flag go here

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `read_state(metadata_path)` — already used to load session metadata; `recording_name` already
  extracted via `session_metadata.get("recording_name") if session_metadata else None`
- `extract_title(notes, fallback_ts)` — existing fallback, no changes needed
- `create_page(token, parent_page_id, title, notes_markdown)` — Notion push already takes `title`
  as a parameter; `--title` just changes what value is passed

### Established Patterns
- Falsy check for title fields: `if recording_name:` (Phase 4, Phase 5) — use `if title:` for
  the new `--title` flag
- Long-form-only Click options: `--template`, `--session` — `--title` follows the same convention
- Title priority: user-explicit > metadata > derived (established in Phase 4 D-01)

### Integration Points
- `summarize.py:50-55` — add `@click.option("--title", ...)` alongside existing options
- `summarize.py:150-152` — extend the title resolution logic to check `--title` first

</code_context>

<specifics>
## Specific Ideas

- Example invocations confirmed during discussion:
  - `meet summarize --title "Weekly Sync"`
  - `meet summarize --session team-standup-20260322-143000-abc12345 --title "Weekly Sync"`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-for-the-notes-in-notion-if-the-user-specifies-a-title-i-want-that-title-to-be-in-the-notion-note-title*
*Context gathered: 2026-03-29*
