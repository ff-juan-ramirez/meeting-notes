# Phase 5: Integrated CLI - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire all commands into a cohesive CLI with full UX polish. Delivers:
- `meet list` command — scans metadata, displays Rich table, supports `--status` filter and `--json`
- Global `--quiet` flag — retrofitted across all commands
- Shared `cli/ui.py` — centralized console, TTY detection
- `meet stop` extended to write session metadata (duration)
- End-to-end flow: `meet record` → `meet stop` → `meet transcribe` → `meet summarize` → `meet list`

New capabilities (shell completion, search, database schema creation) belong in other phases.

</domain>

<decisions>
## Implementation Decisions

### Duration Storage

- **D-01:** `meet stop` computes `duration_seconds` (integer) from `state.json` `start_time` field and writes it to `metadata/{stem}.json` alongside other session fields (`output_path`, etc.). Uses read-merge-write pattern (same as transcribe/summarize).
- **D-02:** Duration display format in `meet list`: `mm:ss` (e.g. `45:22`). Computed at display time from `duration_seconds`.
- **D-03:** If `duration_seconds` is absent from metadata (session recorded before Phase 5 or `start_time` was missing), fall back to reading WAV file header via stdlib `wave` module (no extra deps). If WAV file is also unavailable, display `—`.
- **D-04:** If `meet stop` cannot compute duration (missing `start_time` in `state.json`), omit `duration_seconds` from metadata entirely — do not write `null` or `0`. The WAV fallback in `meet list` handles this case.
- **D-05:** Metadata stem for `meet stop` is derived from `output_path` in `state.json` (same stem extraction pattern used in `transcribe.py`).

### `--quiet` Flag

- **D-06:** `--quiet` is a global flag on the main Click group (`cli/main.py`). Stored in `ctx.obj['quiet']` (boolean). All subcommands receive it via `@click.pass_context`.
- **D-07:** All existing commands — `record`, `stop`, `transcribe`, `summarize`, `doctor`, `init` — are retrofitted in Phase 5 to honor `--quiet`.
- **D-08:** In `--quiet` mode, only `[red]Error:[/red]` messages are printed. All progress output, spinners, confirmation messages, and hints are suppressed.
- **D-09:** Spinners (Rich `run_with_spinner` in transcription/LLM/Notion) must also be suppressed in `--quiet` mode. Pass `quiet` flag to `run_with_spinner` or check context before calling it.

### UI Centralization

- **D-10:** `cli/ui.py` exposes a single shared `console = Console()` instance. All commands import `console` from `cli/ui.py` — the per-module `console = Console()` declarations are removed.
- **D-11:** TTY detection is handled in `cli/ui.py`. When `sys.stdout.isatty()` is False, Rich markup is suppressed (use `Console(highlight=False)` or equivalent). `--json` on `meet list` always outputs clean JSON regardless of TTY.
- **D-12:** Error output style: keep existing inline `[red]Error:[/red] message` style (no change to Rich panels for errors). No visual regression.

### `meet list` Command

- **D-13:** `cli/commands/list.py` implements `meet list`. Scans `metadata/*.json` (XDG data dir), sorted by `transcribed_at` or WAV mtime descending (newest first).
- **D-14:** Rich table columns (in order): Date, Duration, Title, Status, Notion URL. All columns always shown; missing values display `—`.
- **D-15:** Status values derived from metadata fields:
  - `not-transcribed` — no `transcript_path` field or file not found
  - `transcribed` — has `transcript_path` but no `notes_path`
  - `summarized` — has `notes_path`
- **D-16:** Title for **unsummarized** sessions: the session stem (e.g. `20260322-143000-abc12345`). Always available.
- **D-17:** Title for **summarized** sessions: first `# Heading` from the notes `.md` file (same extraction logic as Phase 4 `extract_title()`). Falls back to stem if extraction fails.
- **D-18:** `--status` filter accepts `not-transcribed`, `transcribed`, `summarized`. Filters table rows.
- **D-19:** `--json` flag outputs a JSON array to stdout — no ANSI codes, no Rich formatting. Each element includes all metadata fields from the JSON file plus the derived `status` and `title` fields.
- **D-20:** `meet list` with no sessions shows an empty Rich table (not an error). Consistent with "no active data" states elsewhere.

### Session Metadata Schema

Complete metadata fields after Phase 5 (written across phases, read by `meet list`):
- `wav_path` (Phase 2 / Phase 5 stop) — absolute path to WAV
- `transcript_path` (Phase 2) — absolute path to transcript `.txt`
- `transcribed_at` (Phase 2) — ISO 8601 timestamp
- `word_count` (Phase 2) — transcript word count
- `whisper_model` (Phase 2) — model identifier
- `notes_path` (Phase 3) — absolute path to notes `.md`
- `template` (Phase 3) — `meeting` | `minutes` | `1on1`
- `summarized_at` (Phase 3) — ISO 8601 timestamp
- `llm_model` (Phase 3) — model identifier
- `notion_url` (Phase 4) — Notion page URL or `null`
- `duration_seconds` (Phase 5 / `meet stop`) — integer seconds or absent

### Claude's Discretion

- `--version` flag implementation on main group (version string source, format)
- Column width / truncation policy for long titles in Rich table
- Date format in `meet list` (suggest `YYYY-MM-DD HH:MM`)
- Whether `meet stop` writes `wav_path` and `start_time` to metadata as well (would fill Phase 2 fields for sessions that never reach transcription)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Architecture
- `.planning/ROADMAP.md` §Phase 5 — Plan specs (5.1, 5.2) and pitfalls P18
- `.planning/PROJECT.md` — Tech stack constraints (Click, Rich, Python 3.14, XDG dirs)
- `.planning/REQUIREMENTS.md` §CLI Commands — CLI-01 to CLI-09
- `.planning/REQUIREMENTS.md` §Setup & Health Check — SETUP-05, SETUP-06

### Prior Phase Decisions
- `.planning/phases/02-local-transcription/02-CONTEXT.md` — Session resolution pattern (D-01–D-04), metadata schema (D-10–D-11)
- `.planning/phases/03-note-generation/03-CONTEXT.md` — Metadata extension pattern (D-08), session stem pattern (D-06)
- `.planning/phases/04-notion-integration/04-CONTEXT.md` — `notion_url` in metadata (D-05), `extract_title()` logic (D-08, D-09)

### Existing Code Patterns
- `meeting_notes/cli/main.py` — Current Click group (to be extended with `--quiet`, `--version`, `list` command)
- `meeting_notes/cli/commands/record.py` — State read/write pattern; `state.json` fields (`start_time`, `output_path`, `session_id`)
- `meeting_notes/cli/commands/summarize.py` — `run_with_spinner` usage; metadata read-merge-write pattern; `extract_title` usage
- `meeting_notes/services/transcription.py` — `run_with_spinner(task_fn, message)` — needs `quiet` parameter
- `meeting_notes/core/state.py` — Atomic `write_state` / `read_state` — used by `meet stop` for metadata write
- `meeting_notes/core/storage.py` — `get_data_dir()`, `ensure_dirs()` — metadata dir at `get_data_dir() / "metadata"`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `services/transcription.py::run_with_spinner(task_fn, message)` — Used by transcribe, summarize, and Notion push. Needs a `quiet: bool = False` parameter added so callers can suppress spinner in `--quiet` mode.
- `core/state.py::read_state` / `write_state` — Atomic JSON helpers used by transcribe.py and summarize.py for metadata. `meet stop` will follow the same pattern.
- `services/notion.py::extract_title(notes, fallback)` — First `# Heading` extraction logic. `meet list` reuses this for the title column.
- `core/storage.py::get_data_dir()` — Returns XDG data dir. `metadata/` subdirectory already created by `ensure_dirs()`.

### Established Patterns
- Session stem: derived from `wav_path.stem` (e.g. `20260322-143000-abc12345`) — consistent across all commands
- Metadata read-merge-write: `existing = read_state(path) or {}; existing.update({...}); write_state(path, existing)` — do NOT overwrite existing fields
- Error output: `console.print(f"[red]Error:[/red] {msg}"); sys.exit(1)` — keep this style
- Spinner pattern: `run_with_spinner(lambda: fn(), "Message...")` — wraps blocking calls

### Integration Points
- `cli/main.py` — Add `--quiet` to group, `--version` flag, `@click.pass_context`, `ctx.ensure_object(dict)`, import and register `list` command
- `cli/commands/record.py::stop()` — Extend to compute `duration_seconds` and write metadata JSON
- Each existing command — Replace local `console = Console()` with `from meeting_notes.cli.ui import console`; add `ctx.obj.get('quiet')` check before non-error prints

</code_context>

<specifics>
## Specific Ideas

- Duration stored as integer seconds in metadata; displayed as `mm:ss` at list time
- `--quiet` passes via `ctx.obj['quiet']` (Click context object pattern)
- `cli/ui.py` is minimal: just `console = Console()` — no helper functions yet
- Inline `[red]Error:[/red]` error style preserved — no change from existing pattern
- `meet list` title: stem for unsummarized, first `# Heading` for summarized (reusing `extract_title`)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-integrated-cli*
*Context gathered: 2026-03-22*
