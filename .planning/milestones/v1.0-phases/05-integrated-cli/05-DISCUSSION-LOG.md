# Phase 5: Integrated CLI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 05-integrated-cli
**Areas discussed:** Duration data source, --quiet flag scope, Error/output centralization, Unsummarized title

---

## Duration Data Source

| Option | Description | Selected |
|--------|-------------|----------|
| Write at meet stop | Compute from state.json start_time at stop time, write to metadata JSON | ✓ |
| Compute from WAV file | Read WAV header on the fly during meet list | |
| Skip it | Show — in duration column, defer to future phase | |

**User's choice:** Write at meet stop
**Notes:**
- Display format: `mm:ss` (e.g. 45:22)
- Fallback for old sessions (no duration_seconds): read WAV file via stdlib `wave` module
- Field name: `duration_seconds` (integer)
- Source for start time: `state.json` `start_time` field
- If start_time unavailable: omit `duration_seconds` from metadata entirely (no null/0 sentinel)

---

## --quiet Flag Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Wire globally, retrofit all | Add to main group, retrofit all existing commands in Phase 5 | ✓ |
| Wire globally, new code only | Main group flag but only meet list honors it in Phase 5 | |
| Per-command flag only | --quiet re-declared on each command individually | |

**User's choice:** Wire globally, retrofit all existing commands
**Notes:**
- Quiet mode output: errors only (all progress, spinners, confirmations suppressed)
- Pass-through mechanism: `ctx.obj['quiet']` (Click context object pattern)

---

## Error/Output Centralization

| Option | Description | Selected |
|--------|-------------|----------|
| Full refactor in Phase 5 | Replace all per-module Console() with shared cli/ui.py | ✓ |
| New code only | cli/ui.py for meet list only; existing commands unchanged | |
| Shared console + helpers | cli/ui.py exports console + print_error/warning/success helpers | |

**User's choice:** Full refactor — all existing commands import `console` from `cli/ui.py`

| Option | Description | Selected |
|--------|-------------|----------|
| console only | Just `console = Console()` in cli/ui.py | ✓ |
| console + error helpers | Also export print_error(), print_warning(), print_success() | |
| console + full UI toolkit | Console, helpers, spinner factory, TTY-aware print | |

| Option | Description | Selected |
|--------|-------------|----------|
| Keep inline [red]Error:[/red] | Preserve existing inline error style | ✓ |
| Switch to Rich panels for errors | Wrap errors in Panel(style='red') | |
| stderr for errors | Use Console(stderr=True) for error output | |

**Notes:** Minimal `cli/ui.py` — just the shared console. No helpers. Inline error style preserved.

---

## Unsummarized Title

| Option | Description | Selected |
|--------|-------------|----------|
| Filename stem | Show session stem (e.g. 20260322-143000-abc12345) | ✓ |
| — placeholder | Show dash or 'Untitled' | |
| Omit title column | No title column in meet list | |

| Option | Description | Selected |
|--------|-------------|----------|
| First line of notes file | Read first # Heading from .md at display time | ✓ |
| Store title in metadata | write title to JSON during summarize | |
| LLM-generated at list time | Run LLM call during meet list | |

**User's choice:** Stem for unsummarized; first `# Heading` from notes file for summarized (reuse `extract_title` from Phase 4)

---

## Claude's Discretion

- `--version` flag implementation (version string source, format)
- Column width / truncation policy for long titles in Rich table
- Date format in `meet list`
- Whether `meet stop` also writes `wav_path` and `start_time` to metadata

## Deferred Ideas

None
