# Phase 4: Notion Integration - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Save generated meeting notes to a Notion page automatically after `meet summarize`. Notes saved as child pages under a user-configured parent page. Adds Notion health checks to `meet doctor`.

New capabilities (meet list display, database properties, sync-back from Notion) belong in other phases.

</domain>

<decisions>
## Implementation Decisions

### Save Trigger

- **D-01:** `meet summarize` auto-saves to Notion when token is configured — no `--save` flag required. Running `meet summarize` always triggers Notion push if configured.
- **D-02:** If token is not configured (missing from config.json), print a one-line hint after local save: `"Notion not configured — run meet init to set up."` Do not fail, do not silently skip.
- **D-03:** Terminal output after successful Notion push extends the Phase 3 pattern: existing `"Notes saved: <path> (N words)"` line is followed by `"Notion: https://notion.so/..."`. Two lines, not merged.
- **D-04:** Show a Rich spinner `"Saving to Notion..."` during the API call — consistent with Phase 2/3 spinner pattern.
- **D-05:** Notion URL is stored in session metadata JSON (`notion_url` field) so Phase 5's `meet list` can display it.

### Notion Target

- **D-06:** Target is a **parent page** — each meeting note becomes a child page under it. No database rows, no structured properties. Simple, easy to set up in Notion.
- **D-07:** Notion token and parent page ID are stored in `~/.config/meeting-notes/config.json` only. No env var fallback.

### Page Title

- **D-08:** Title is extracted from the generated notes file — first `# Heading` (H1) found; fall back to the first non-empty line if no H1 exists. No separate LLM call.
- **D-09:** If title extraction fails (empty or very short notes), fall back to timestamp: `"Meeting Notes — {YYYY-MM-DD HH:MM}"`.

### Notion Failure Handling

- **D-10:** If the Notion push fails after notes are successfully saved locally, **warn and continue** (exit 0). Notes are safe locally — never penalize local-only use.
- **D-11:** Failure warning is a Rich `[yellow]` warning panel showing: `"Notion upload failed: <reason>"` with the local notes path. User knows their notes are safe.

### Doctor Check Severity

- **D-12:** Two separate health checks: `NotionTokenCheck` (token set in config + API call succeeds) and `NotionDatabaseCheck` (target parent page ID set + accessible). Matches ROADMAP plan 4.2.
- **D-13:** `NotionTokenCheck` → **WARNING** (not ERROR) when token is missing. Notion is optional — `meet summarize` works without it. Fix suggestion: `"Run: meet init to configure Notion."`
- **D-14:** `NotionDatabaseCheck` → **WARNING** when parent page ID is missing or inaccessible. Same rationale as D-13.

### Claude's Discretion

- Block structure for Notion pages: implement headings as `heading_2` blocks and bullet lists as `bulleted_list_item` blocks. Split text at ≤1,900 chars per block (NOTION-04). Retry logic: exponential backoff on HTTP 429 (NOTION-05). These are architectural implementation details — follow the ROADMAP pitfalls P14 and P15.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Architecture
- `.planning/ROADMAP.md` §Phase 4 — Plan specs (4.1, 4.2) and pitfalls P14–P17
- `.planning/PROJECT.md` — Constraints (notion-client SDK, config.json location, no cloud)
- `.planning/REQUIREMENTS.md` §Notion Integration — NOTION-01 to NOTION-07
- `.planning/REQUIREMENTS.md` §Setup & Health Check — SETUP-03, SETUP-04 (doctor check pattern)

### Existing Code Patterns
- `meeting_notes/services/llm.py` — Model for `services/notion.py` (pure functions, no Click/Rich)
- `meeting_notes/cli/commands/summarize.py` — File to extend with Notion push after note generation
- `meeting_notes/core/config.py` — Where `NotionConfig` dataclass must be added (token + parent_page_id)
- `meeting_notes/services/checks.py` — Where `NotionTokenCheck` and `NotionDatabaseCheck` get registered
- `meeting_notes/core/health_check.py` — HealthCheck ABC that new checks must subclass
- `.planning/phases/03-note-generation/03-CONTEXT.md` — Phase 3 decisions; metadata schema (D-08) that Phase 4 extends with `notion_url`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `services/transcription.py`: `run_with_spinner(task_fn, message)` — reuse pattern for "Saving to Notion..." spinner
- `core/state.py`: `write_state()` / `read_state()` — atomic read-merge-write for extending `metadata/{stem}.json` with `notion_url`
- `core/config.py`: `Config` dataclass — add `NotionConfig` dataclass (token, parent_page_id) following `AudioConfig`/`WhisperConfig` pattern

### Established Patterns
- Notion service: pure functions in `services/notion.py`, no Click/Rich imports (mirrors `services/llm.py`)
- CLI command extension: `summarize.py` calls `NotionService.create_page()` after notes generation — same file, no new command
- Health checks: `HealthCheck` subclass with `check() -> CheckResult`; register in `services/checks.py`
- Metadata JSON: read existing `{stem}.json` → add `notion_url` field → write back atomically (Phase 3 D-08 pattern)

### Integration Points
- `core/config.py` — add `NotionConfig` and `Config.notion` field; `meet init` and `meet doctor` already read from this
- `cli/commands/summarize.py` — add Notion push block after `generate_notes()` succeeds
- `services/checks.py` — register `NotionTokenCheck` and `NotionDatabaseCheck`
- `metadata/{stem}.json` — Phase 4 adds `notion_url` field (or `None` if push skipped/failed)

</code_context>

<specifics>
## Specific Ideas

- The "Notion not configured" hint (D-02) should print with a muted style (e.g., Rich `dim`) — not a warning, just a discovery nudge.
- Session metadata: store `notion_url` as the full page URL on success, `null` if skipped or failed. Phase 5's `meet list` reads this field directly.
- `NotionDatabaseCheck` should also verify the token is valid (not just present) via a lightweight API call — e.g., `GET /v1/pages/{page_id}`. Mirrors how `OllamaRunningCheck` tests the live service.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-notion-integration*
*Context gathered: 2026-03-22*
