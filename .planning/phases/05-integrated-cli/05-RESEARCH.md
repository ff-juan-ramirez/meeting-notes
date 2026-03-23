# Phase 5: Integrated CLI — Research

**Researched:** 2026-03-23
**Domain:** Click CLI wiring, Rich UX (TTY detection, spinners), session metadata JSON, `meet list` command
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Duration Storage**
- D-01: `meet stop` computes `duration_seconds` (integer) from `state.json` `start_time` field and writes it to `metadata/{stem}.json` alongside other session fields. Uses read-merge-write pattern.
- D-02: Duration display format: `mm:ss` (e.g. `45:22`). Computed at display time from `duration_seconds`.
- D-03: If `duration_seconds` absent, fall back to `wave` stdlib module to read WAV header. If WAV also unavailable, display `—`.
- D-04: If `meet stop` cannot compute duration (missing `start_time`), omit `duration_seconds` entirely — do not write `null` or `0`.
- D-05: Metadata stem for `meet stop` derived from `output_path` in `state.json` (same stem extraction as `transcribe.py`).

**`--quiet` Flag**
- D-06: `--quiet` is a global flag on the main Click group. Stored in `ctx.obj['quiet']`. All subcommands receive it via `@click.pass_context`.
- D-07: All existing commands (record, stop, transcribe, summarize, doctor, init) are retrofitted in Phase 5 to honor `--quiet`.
- D-08: In `--quiet` mode, only `[red]Error:[/red]` messages print. All progress, spinners, confirmation messages, and hints are suppressed.
- D-09: Spinners (`run_with_spinner`) must be suppressed in `--quiet` mode. Pass `quiet` flag to `run_with_spinner` or check context before calling.

**UI Centralization**
- D-10: `cli/ui.py` exposes a single shared `console = Console()` instance. All commands import from `cli/ui.py`; per-module `console = Console()` declarations are removed.
- D-11: TTY detection in `cli/ui.py`. When `sys.stdout.isatty()` is False, Rich markup is suppressed. `--json` on `meet list` always outputs clean JSON regardless of TTY.
- D-12: Error output style: keep existing inline `[red]Error:[/red] message` style — no Rich panels for errors.

**`meet list` Command**
- D-13: `cli/commands/list.py` implements `meet list`. Scans `metadata/*.json` (XDG data dir), sorted by `transcribed_at` or WAV mtime descending (newest first).
- D-14: Rich table columns (in order): Date, Duration, Title, Status, Notion URL. All columns always shown; missing values display `—`.
- D-15: Status values: `not-transcribed` (no `transcript_path` or file missing), `transcribed` (has `transcript_path`, no `notes_path`), `summarized` (has `notes_path`).
- D-16: Title for unsummarized sessions: session stem (always available).
- D-17: Title for summarized sessions: first `# Heading` from notes `.md` file via `extract_title()`. Falls back to stem.
- D-18: `--status` filter accepts `not-transcribed`, `transcribed`, `summarized`.
- D-19: `--json` outputs a JSON array to stdout — no ANSI codes, no Rich formatting. Each element includes all metadata fields plus derived `status` and `title`.
- D-20: `meet list` with no sessions shows an empty Rich table (not an error).

**Session Metadata Schema (complete after Phase 5)**
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
- Whether `meet stop` writes `wav_path` and `start_time` to metadata as well (to fill Phase 2 fields for sessions that never reach transcription)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLI-01 | `meet record` starts a recording session | Existing — already implemented; retrofit `--quiet` support |
| CLI-02 | `meet stop` stops the active recording session | Existing — extend to write `duration_seconds` to metadata |
| CLI-03 | `meet transcribe [--session UUID]` transcribes last or specified recording | Existing — retrofit `--quiet`, use shared console |
| CLI-04 | `meet summarize [--template] [--session UUID]` generates notes and saves to Notion | Existing — retrofit `--quiet`, suppress spinners |
| CLI-05 | `meet list` displays recordings with date, duration, title, status, Notion URL | New command — `cli/commands/list.py` |
| CLI-06 | `meet list` supports `--status` filter and `--json` output flag | New — `--status` filter + JSON array via `json.dumps` |
| CLI-07 | All commands display Rich-formatted output with color, spinners, progress bars | Existing + centralize via `cli/ui.py` |
| CLI-08 | Rich output suppressed when stdout is not a TTY | `cli/ui.py` — `Console(force_terminal=False)` when not TTY; verified Rich auto-strips markup |
| CLI-09 | `--quiet` flag suppresses all progress output for scripting | Click group `--quiet` → `ctx.obj['quiet']`; retrofit all commands |
| SETUP-05 | `meet doctor` checks Python >= 3.11, <3.14; warns if `openai-whisper` alongside `mlx-whisper` | New `PythonVersionCheck` in `services/checks.py` |
| SETUP-06 | `meet doctor` exits code 1 if any ERROR, code 0 if all pass or only warnings | Existing exit logic in `doctor.py` — confirmed current behavior matches; verify test coverage |
</phase_requirements>

---

## Summary

Phase 5 is a wiring and polish phase. No new external dependencies are required — everything builds on Click 8.3.1, Rich 14.3.3, and the stdlib. The three primary work areas are: (1) wiring the main CLI group with `--quiet` and `--version` flags and retrofitting all six existing commands; (2) creating `cli/ui.py` with a centralized console and TTY detection; and (3) implementing the new `meet list` command.

The key technical finding is that Rich 14.x already handles TTY detection automatically. When `Console()` is created and stdout is not a TTY, `console.is_terminal` is False and `console.color_system` is None — markup tags are stripped from output automatically. For `cli/ui.py`, the recommended approach is `Console(force_terminal=sys.stdout.isatty())` to make the behavior explicit rather than relying on Rich auto-detection, which can be affected by test environments. The `--json` flag path must use `json.dumps()` directly and print to stdout — never through the Rich console.

The `run_with_spinner` function in `services/transcription.py` uses its own private `_console = Console()` instance. This needs a `quiet: bool = False` parameter added; when `True`, skip the `Live` context and run `fn()` directly. This is the cleanest approach: no threading change, no context object plumbing into the service layer.

**Primary recommendation:** Create `cli/ui.py` first (no deps), then add `--quiet`/`--version` to `main.py`, then retrofit commands one by one, then implement `meet list`, then add new doctor checks. This ordering means any test that imports a retrofitted command will immediately have the shared console available.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.3.1 (installed) | CLI framework — group, commands, options, context | Already in use; `@click.pass_context` + `ctx.obj` is the canonical multi-command context-sharing pattern |
| rich | 14.3.3 (installed) | Terminal formatting — Console, Table, Live spinner | Already in use; `Console(force_terminal=...)` controls TTY behavior explicitly |
| wave (stdlib) | Python 3.14 stdlib | Read WAV header for duration fallback | No install needed; `wave.open(path).getnframes() / getframerate()` gives exact duration |
| json (stdlib) | Python 3.14 stdlib | `--json` output from `meet list` | `json.dumps(list, indent=2)` — no ANSI codes by design |
| importlib.metadata (stdlib) | Python 3.14 stdlib | Version string for `--version` flag | `importlib.metadata.version("meeting-notes")` returns `"0.1.0"` from `pyproject.toml` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sys | stdlib | `sys.stdout.isatty()`, `sys.exit()` | TTY detection in `cli/ui.py`; already used by all commands |
| datetime | stdlib | Parse `start_time` ISO 8601 for duration computation in `meet stop` | Already used by record/transcribe |
| pathlib | stdlib | File path operations throughout | Already used everywhere |

**Installation:** No new packages needed. All dependencies already installed.

---

## Architecture Patterns

### Recommended Project Structure (additions only)

```
meeting_notes/cli/
├── main.py              # Extended: --quiet, --version, list command, pass_context
├── ui.py                # NEW: shared console = Console(force_terminal=...)
└── commands/
    ├── list.py          # NEW: meet list implementation
    ├── record.py        # Modified: shared console, --quiet retrofit
    ├── stop.py          # Modified: duration_seconds computation, metadata write
    ├── transcribe.py    # Modified: shared console, --quiet retrofit
    ├── summarize.py     # Modified: shared console, --quiet retrofit
    ├── doctor.py        # Modified: shared console, --quiet retrofit; new checks registered
    └── init.py          # Modified: shared console, --quiet retrofit
```

### Pattern 1: Click Group with `--quiet` and Context Object

**What:** Global flags on the Click group propagate to all subcommands via `ctx.obj`.
**When to use:** Any flag that must be available to every subcommand without repeating the option.

```python
# cli/main.py
import click
from importlib.metadata import version

@click.group()
@click.version_option(package_name="meeting-notes")
@click.option("--quiet", is_flag=True, default=False, help="Suppress all progress output.")
@click.pass_context
def main(ctx: click.Context, quiet: bool) -> None:
    """Meeting notes - local capture, transcription, and Notion export."""
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet
```

```python
# In a subcommand — access quiet flag
@click.command()
@click.pass_context
def record(ctx: click.Context) -> None:
    quiet = ctx.obj.get("quiet", False)
    if not quiet:
        console.print("[green]Recording started[/green]")
```

Source: Verified with `click.testing.CliRunner` — `ctx.obj['quiet']` correctly reflects `--quiet` flag.

### Pattern 2: Centralized Console with TTY Detection

**What:** Single `Console` instance in `cli/ui.py`. All commands import from here. TTY state locked at import time.
**When to use:** Any module that prints output.

```python
# cli/ui.py
import sys
from rich.console import Console

# force_terminal=True only when stdout is a real TTY.
# When False, Rich sets color_system=None and strips markup tags.
console = Console(force_terminal=sys.stdout.isatty())
```

Verified: `Console(force_terminal=False)` sets `is_terminal=False`, `color_system=None`; markup is stripped in output.

```python
# In any command module — replace local Console() declaration
from meeting_notes.cli.ui import console
```

### Pattern 3: Suppress Spinner in `--quiet` Mode

**What:** Add `quiet: bool = False` parameter to `run_with_spinner`. When `True`, call `fn()` directly without threading or spinner.

```python
# services/transcription.py
def run_with_spinner(fn: Callable[[], Any], message: str, quiet: bool = False) -> Any:
    if quiet:
        return fn()
    # ... existing threading + Live spinner implementation
```

Callers pass `quiet=ctx.obj.get("quiet", False)`. The service layer stays clean — no Click context import.

### Pattern 4: `meet stop` Duration Computation and Metadata Write

**What:** After stopping ffmpeg, compute `duration_seconds` from `state.json` `start_time`, write to metadata using read-merge-write.

```python
# cli/commands/record.py — inside stop() command
from datetime import datetime, timezone
from pathlib import Path

start_time_str = existing.get("start_time")
duration_seconds = None
if start_time_str:
    start = datetime.fromisoformat(start_time_str)
    now = datetime.now(timezone.utc)
    duration_seconds = int((now - start).total_seconds())

output_path_str = existing.get("output_path")
if output_path_str:
    stem = Path(output_path_str).stem
    metadata_dir = get_data_dir() / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = metadata_dir / f"{stem}.json"
    meta = read_state(metadata_path) or {}
    if duration_seconds is not None:
        meta["duration_seconds"] = duration_seconds
    # D-04: omit duration_seconds entirely if not computed — no null/0
    write_state(metadata_path, meta)
```

### Pattern 5: `meet list` — Scan, Sort, Derive, Display

**What:** Scan `metadata/*.json`, derive status and title, render Rich table or JSON.

```python
# cli/commands/list.py — skeleton
import json
import sys
from pathlib import Path

import click
from rich.table import Table

from meeting_notes.cli.ui import console
from meeting_notes.core.storage import get_data_dir
from meeting_notes.core.state import read_state
from meeting_notes.services.notion import extract_title


@click.command(name="list")
@click.option("--status", default=None,
              type=click.Choice(["not-transcribed", "transcribed", "summarized"]))
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def list_sessions(ctx: click.Context, status: str | None, output_json: bool) -> None:
    """List all recorded sessions."""
    metadata_dir = get_data_dir() / "metadata"
    # Scan + sort
    jsons = sorted(metadata_dir.glob("*.json"), key=_sort_key, reverse=True)
    sessions = []
    for path in jsons:
        meta = read_state(path) or {}
        derived = _derive_fields(meta, path.stem)
        if status and derived["status"] != status:
            continue
        sessions.append({**meta, **derived})

    if output_json:
        print(json.dumps(sessions, indent=2))
        return

    # Rich table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Date")
    table.add_column("Duration")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Notion URL")
    for s in sessions:
        table.add_row(
            s.get("date", "—"),
            s.get("duration_display", "—"),
            s.get("title", "—"),
            s.get("status", "—"),
            s.get("notion_url") or "—",
        )
    console.print(table)
```

### Pattern 6: WAV Duration Fallback via `wave` Module

**What:** When `duration_seconds` absent from metadata, read WAV header via stdlib `wave`.

```python
import wave

def _wav_duration(wav_path_str: str | None) -> int | None:
    """Read duration from WAV header. Returns None if unavailable."""
    if not wav_path_str:
        return None
    try:
        with wave.open(wav_path_str, "rb") as wf:
            return int(wf.getnframes() / wf.getframerate())
    except Exception:
        return None
```

Verified: `wave.open(path, "rb").getnframes() / getframerate()` gives exact seconds. Works for the 16kHz mono WAV format used throughout the project.

### Pattern 7: `meet list` Sort Key

**What:** Sort metadata files by `transcribed_at` (ISO 8601 string sorts lexicographically), fall back to WAV mtime for sessions not yet transcribed.

```python
def _sort_key(json_path: Path):
    meta = read_state(json_path) or {}
    ts = meta.get("transcribed_at")
    if ts:
        return ts  # ISO 8601 strings sort correctly lexicographically
    # Fall back to file mtime
    return str(json_path.stat().st_mtime)
```

### Pattern 8: `PythonVersionCheck` (SETUP-05)

**What:** New HealthCheck subclass checking Python >= 3.11, < 3.14; warns if `openai-whisper` importable alongside `mlx-whisper`.

```python
import sys
import importlib.metadata
from meeting_notes.core.health_check import CheckResult, CheckStatus, HealthCheck

class PythonVersionCheck(HealthCheck):
    name = "Python Version"

    def check(self) -> CheckResult:
        vi = sys.version_info
        if vi < (3, 11):
            return CheckResult(
                status=CheckStatus.ERROR,
                message=f"Python {vi.major}.{vi.minor} is below minimum 3.11",
                fix_suggestion="Upgrade Python to 3.11 or newer.",
            )
        # NOTE: pyproject.toml allows <3.15; SETUP-05 warns on >=3.14
        if vi >= (3, 14):
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Python {vi.major}.{vi.minor} is above tested range (3.11–3.13)",
            )
        # Check for conflicting whisper package
        try:
            importlib.metadata.version("openai-whisper")
            return CheckResult(
                status=CheckStatus.WARNING,
                message="openai-whisper is installed alongside mlx-whisper — may cause conflicts",
                fix_suggestion="Uninstall openai-whisper: pip uninstall openai-whisper",
            )
        except importlib.metadata.PackageNotFoundError:
            pass
        return CheckResult(
            status=CheckStatus.OK,
            message=f"Python {vi.major}.{vi.minor}.{vi.micro}",
        )
```

Note: `pyproject.toml` specifies `requires-python = ">=3.11,<3.15"` but SETUP-05 specifies `<3.14`. Use WARNING severity for >= 3.14 (consistent with DiskSpaceCheck: non-fatal advisory). Current environment is Python 3.14.3 — test suite still passes.

### Pattern 9: Duration Format Utility

**What:** Format integer seconds as `mm:ss` string.

```python
def _format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"
```

### Anti-Patterns to Avoid

- **Per-module `console = Console()` instances:** These will not respect TTY state set in `cli/ui.py`. Replace all six occurrences (record.py, stop is in record.py, transcribe.py, summarize.py, doctor.py, init.py).
- **Passing `ctx.obj` into service layer:** `services/transcription.py` must not import from `cli`. Pass `quiet: bool` as a plain parameter.
- **Writing `duration_seconds: null`:** D-04 is explicit — omit the key entirely when duration cannot be computed. JSON `null` is a lie (it implies the field was computed).
- **Checking TTY at print time vs. at Console creation time:** Rich reads `color_system` at Console construction. Late TTY checks create inconsistency. Lock at import via `sys.stdout.isatty()` in `ui.py`.
- **Printing JSON through `console.print()`:** Rich will wrap JSON in markup rendering. Use `print(json.dumps(...))` directly for `--json` output.
- **Using `click.command(name="list")` without aliasing:** Python `list` is a builtin — the function must be named `list_sessions` (or similar) with `@click.command(name="list")`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| `--version` flag | Custom callback | `@click.version_option(package_name="meeting-notes")` | Auto-reads `0.1.0` from `pyproject.toml` via `importlib.metadata`; verified working |
| WAV duration reading | Custom byte-offset arithmetic | `wave.open(path).getnframes() / getframerate()` | Exact frame count, handles all valid WAVs; stdlib, no deps |
| TTY detection | Manual `os.isatty(sys.stdout.fileno())` | `sys.stdout.isatty()` | Same result, handles StringIO/pipes gracefully |
| Passing context to subcommands | Global variable | `ctx.ensure_object(dict)` + `ctx.obj` | Click's canonical pattern; tested and works |
| JSON serialization of metadata | Custom loop | `json.dumps(sessions, indent=2)` | Handles None → null, nested dicts, all primitive types |

**Key insight:** The project already imports Click and Rich correctly. The only risk is coupling — service layer (`run_with_spinner`) must take a plain `quiet: bool`, not a Click context, to preserve testability.

---

## Common Pitfalls

### Pitfall 1: Python `list` builtin conflict
**What goes wrong:** `@click.command()` named `list` — Python raises `SyntaxError` or shadows the builtin depending on scope.
**Why it happens:** `list` is a Python keyword/builtin. Naming a function `list` replaces it in module scope.
**How to avoid:** Name the function `list_sessions` (or `list_cmd`) and add `@click.command(name="list")`.
**Warning signs:** Import errors from `from meeting_notes.cli.commands.list import list` — builtin conflict.

### Pitfall 2: `run_with_spinner` uses its own `_console` instance
**What goes wrong:** Even after centralizing to `cli/ui.py`, spinners still appear in non-TTY or `--quiet` contexts because `transcription.py` has `_console = Console()`.
**Why it happens:** `transcription.py` creates its own console at module load time — this is the existing code.
**How to avoid:** Add `quiet: bool = False` parameter to `run_with_spinner`. When `quiet=True`, bypass the threading + `Live` loop entirely and call `fn()` directly.
**Warning signs:** Spinner markup in piped output (ANSI codes in `meet transcribe | tee log.txt`).

### Pitfall 3: `meet stop` calls `clear_state()` before computing duration
**What goes wrong:** `start_time` is read from `state.json`, but `clear_state()` deletes the file. If duration is computed after clear, `start_time` is gone.
**Why it happens:** Current `stop()` calls `clear_state()` early.
**How to avoid:** Compute `duration_seconds` before calling `clear_state()`. Extract all needed fields from `existing` dict first.
**Warning signs:** `duration_seconds` always absent in metadata; no test failures because the field is optional.

### Pitfall 4: Metadata read-merge-write order in `meet stop`
**What goes wrong:** `meet stop` overwrites the full metadata file, losing Phase 2 fields (`transcript_path`, `transcribed_at`, etc.) set by earlier commands.
**Why it happens:** Using `write_state(path, {"duration_seconds": X})` instead of the merge pattern.
**How to avoid:** Always use `existing = read_state(path) or {}; existing.update({...}); write_state(path, existing)`. This is the established project pattern (used in summarize.py, transcribe.py).
**Warning signs:** `meet list` shows `not-transcribed` status for sessions that were transcribed.

### Pitfall 5: `--json` output routed through Rich console
**What goes wrong:** `console.print(json.dumps(data))` may add Rich markup or newlines in non-TTY mode, or strip brackets/braces it misinterprets as markup.
**Why it happens:** Rich treats `[` as potential markup start.
**How to avoid:** For `--json`, use `print(json.dumps(sessions, indent=2))` — plain Python print to stdout.
**Warning signs:** Malformed JSON output when piping `meet list --json | jq .`.

### Pitfall 6: Sorting by `transcribed_at` excludes sessions never transcribed
**What goes wrong:** Sessions only stopped (not transcribed) have no `transcribed_at` field and sort together at the bottom, regardless of recording time.
**Why it happens:** Simple `sorted(key=lambda m: m.get("transcribed_at", ""))` puts all None values at start.
**How to avoid:** Fall back to JSON file mtime for sessions without `transcribed_at` (D-13 decision). The JSON file mtime is set when `meet stop` writes metadata.
**Warning signs:** New unprocessed sessions appear at the bottom of `meet list` instead of top.

### Pitfall 7: `openai-whisper` conflict detection reports ERROR vs WARNING
**What goes wrong:** Returning `CheckStatus.ERROR` for the openai-whisper warning causes `meet doctor` to exit 1, blocking users even when the conflict is benign.
**Why it happens:** Treating a warning-level advisory as a fatal error.
**How to avoid:** Use `CheckStatus.WARNING` for both Python version advisory (>= 3.14) and openai-whisper presence. Pattern is consistent with DiskSpaceCheck (WARNING for low disk).
**Warning signs:** `meet doctor` exits 1 on machines that happen to have both whisper packages but otherwise work fine.

### Pitfall 8: SETUP-06 exit code — behavior already present, needs test coverage
**What goes wrong:** `meet doctor` exit code behavior (exit 1 on ERROR, exit 0 on all-OK/warnings-only) is already implemented in `doctor.py` — no code change needed. But there is no existing test verifying exit code 0 on all-warnings case.
**Why it happens:** Test exists for exit 1 (`test_doctor_exits_1_on_error`) and exit 0 on all-OK (`test_doctor_exits_0_on_ok`) but not the all-warnings case.
**How to avoid:** Add test for exit code 0 when all checks return WARNING (no ERROR).
**Warning signs:** SETUP-06 marked as "done" without test coverage of the WARNING-only code path.

---

## Code Examples

### Verified Click `--version` with `package_name`

```python
# Source: click 8.3.1, verified in project venv
@click.group()
@click.version_option(package_name="meeting-notes")
def main() -> None:
    ...
# Result: "meet, version 0.1.0" — reads from pyproject.toml via importlib.metadata
```

### Verified Rich Console Non-TTY Behavior

```python
# Source: Rich 14.3.3, verified in project venv
# When sys.stdout.isatty() is False:
console = Console()
# console.is_terminal == False
# console.color_system == None
# console.print("[bold]hello[/bold]") outputs: "hello\n" (markup stripped)

# Explicit TTY control:
console = Console(force_terminal=sys.stdout.isatty())
```

### Verified `wave` stdlib Duration Reading

```python
# Source: Python 3.14.3 stdlib, verified
import wave
with wave.open(str(wav_path), "rb") as wf:
    duration_seconds = int(wf.getnframes() / wf.getframerate())
# Exact result: 3-second WAV → 3, 5-second WAV → 5
```

### Verified Click Context Object Pattern

```python
# Source: click 8.3.1, verified with CliRunner
@click.group()
@click.option("--quiet", is_flag=True, default=False)
@click.pass_context
def main(ctx, quiet):
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet

@main.command()
@click.pass_context
def record(ctx):
    quiet = ctx.obj.get("quiet", False)
    # quiet=True when invoked as: meet --quiet record
```

### `extract_title` reuse for `meet list` title column

```python
# Source: meeting_notes/services/notion.py — already implemented
from meeting_notes.services.notion import extract_title

# For summarized sessions:
notes_text = Path(meta["notes_path"]).read_text()
title = extract_title(notes_text, fallback_timestamp=stem)
# Returns: first "# Heading" content, or first non-empty line, or stem
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-module `console = Console()` in each command file | Single shared `console` from `cli/ui.py` | Phase 5 | TTY state consistent across all output |
| No `--quiet` flag | Global `--quiet` on Click group via `ctx.obj` | Phase 5 | Safe for scripting; all spinners suppressible |
| No `meet list` command | `meet list` with Rich table + `--json` + `--status` filter | Phase 5 | Full session lifecycle visible |
| `run_with_spinner` always shows spinner | `run_with_spinner(fn, msg, quiet=False)` | Phase 5 | `--quiet` suppresses blocking-call spinners |

---

## Open Questions

1. **`meet stop` writing `wav_path` to metadata (Claude's discretion)**
   - What we know: Phase 2 (`meet transcribe`) writes `wav_path` to metadata. Sessions that are stopped but never transcribed have metadata only from Phase 5 stop.
   - What's unclear: Should `meet stop` also write `wav_path` to metadata so `meet list` can show these sessions and use the WAV duration fallback?
   - Recommendation: YES — write `wav_path` in `meet stop`. This makes the WAV fallback (D-03) work for all stopped sessions, not just transcribed ones. Low risk: read-merge-write pattern won't overwrite Phase 2's `wav_path` if already set.

2. **Date column format in `meet list` (Claude's discretion)**
   - What we know: CONTEXT.md suggests `YYYY-MM-DD HH:MM`. `transcribed_at` is ISO 8601 UTC.
   - Recommendation: Parse `transcribed_at` with `datetime.fromisoformat()`, format as `YYYY-MM-DD HH:MM` local time via `.astimezone()`. For sessions without `transcribed_at`, derive from stem (format is `YYYYMMDD-HHMMSS-xxxx`).

3. **`PythonVersionCheck` upper bound: `<3.14` vs current Python 3.14.3**
   - What we know: SETUP-05 says "warn if >= 3.14". The project runs on Python 3.14.3 and all 150 tests pass.
   - What's unclear: Should the check be a WARNING or ERROR for 3.14+?
   - Recommendation: WARNING severity. The code actually works on 3.14.3 — the requirement says "warn", not "fail". Consistent with WARNING-for-non-blocking-issues pattern in this codebase.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | Yes | 3.14.3 | — |
| click | CLI framework | Yes | 8.3.1 | — |
| rich | TUI output | Yes | 14.3.3 | — |
| pytest | Test suite | Yes | 9.0.2 (from cache filename) | — |
| wave (stdlib) | WAV duration fallback | Yes | stdlib | — |
| importlib.metadata (stdlib) | `--version` flag | Yes | stdlib | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` testpaths = ["tests"] |
| Quick run command | `python3 -m pytest tests/test_record_command.py tests/test_transcribe_command.py tests/test_summarize_command.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | `meet record` honors `--quiet` (no output in quiet mode) | unit | `pytest tests/test_record_command.py -x -q` | Partial (retrofit) |
| CLI-02 | `meet stop` writes `duration_seconds` to metadata | unit | `pytest tests/test_record_command.py -x -q` | Partial (new assertions needed) |
| CLI-02 | `meet stop` omits `duration_seconds` when `start_time` absent (D-04) | unit | `pytest tests/test_record_command.py -x -q` | No — Wave 0 |
| CLI-02 | `meet stop` computes duration before clearing state | unit | `pytest tests/test_record_command.py -x -q` | No — Wave 0 |
| CLI-05 | `meet list` shows all sessions with correct columns | unit | `pytest tests/test_list_command.py -x -q` | No — Wave 0 |
| CLI-05 | `meet list` with no sessions shows empty table (not error) | unit | `pytest tests/test_list_command.py -x -q` | No — Wave 0 |
| CLI-05 | Duration display: WAV fallback when `duration_seconds` absent | unit | `pytest tests/test_list_command.py -x -q` | No — Wave 0 |
| CLI-05 | Duration display: `—` when both absent | unit | `pytest tests/test_list_command.py -x -q` | No — Wave 0 |
| CLI-06 | `--status` filter narrows rows | unit | `pytest tests/test_list_command.py -x -q` | No — Wave 0 |
| CLI-06 | `--json` produces clean JSON array, no ANSI codes | unit | `pytest tests/test_list_command.py -x -q` | No — Wave 0 |
| CLI-07 | Rich table renders in TTY context | unit | `pytest tests/test_list_command.py -x -q` | No — Wave 0 |
| CLI-08 | Rich markup stripped in non-TTY output | unit | `pytest tests/test_ui.py -x -q` | No — Wave 0 |
| CLI-09 | `--quiet` suppresses all non-error output | unit | `pytest tests/test_record_command.py tests/test_transcribe_command.py tests/test_summarize_command.py -x -q` | Partial (new assertions) |
| CLI-09 | `--quiet` suppresses spinner in `run_with_spinner` | unit | `pytest tests/test_transcription.py -x -q` | Partial (new param test needed) |
| SETUP-05 | `PythonVersionCheck` returns OK for valid range | unit | `pytest tests/test_health_check.py -x -q` | No — Wave 0 |
| SETUP-05 | `PythonVersionCheck` returns WARNING for >= 3.14 | unit | `pytest tests/test_health_check.py -x -q` | No — Wave 0 |
| SETUP-05 | `PythonVersionCheck` returns WARNING when openai-whisper detected | unit | `pytest tests/test_health_check.py -x -q` | No — Wave 0 |
| SETUP-05 | `PythonVersionCheck` registered in `meet doctor` | unit | `pytest tests/test_doctor_command.py -x -q` | No — Wave 0 |
| SETUP-06 | `meet doctor` exits 0 when all checks return WARNING | unit | `pytest tests/test_doctor_command.py -x -q` | No — Wave 0 (gap) |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/ -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_list_command.py` — covers CLI-05, CLI-06, CLI-07, duration fallback
- [ ] `tests/test_ui.py` — covers CLI-08 (TTY detection, console non-TTY behavior)
- [ ] Add TTY/quiet assertions to `tests/test_record_command.py` — stop duration write, `--quiet` behavior
- [ ] Add `quiet=True` parameter test to `tests/test_transcription.py` — `run_with_spinner` quiet path
- [ ] Add WARNING-only exit-code-0 test to `tests/test_doctor_command.py` — SETUP-06 gap

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection — `meeting_notes/cli/main.py`, `commands/record.py`, `commands/summarize.py`, `commands/transcribe.py`, `commands/doctor.py`, `commands/init.py`, `services/transcription.py`, `services/checks.py`, `core/state.py`, `core/storage.py`, `core/config.py`
- `pyproject.toml` — confirmed `version = "0.1.0"`, `click>=8.1`, `rich>=13.0`, pytest config
- Runtime verification — click 8.3.1 `version_option(package_name=)`, Rich 14.3.3 `Console(force_terminal=False)`, `wave` stdlib duration reading, Click context object pattern — all verified with `python3 -c` in project venv

### Secondary (MEDIUM confidence)
- `.planning/phases/05-integrated-cli/05-CONTEXT.md` — locked decisions D-01 through D-20 (authoritative for this phase)
- `.planning/REQUIREMENTS.md` — CLI-01 to CLI-09, SETUP-05, SETUP-06

### Tertiary (LOW confidence)
None — all critical claims verified against installed packages.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — packages installed, versions confirmed, no new deps required
- Architecture patterns: HIGH — all code patterns verified with `python3 -c` in project venv; Click and Rich behavior confirmed
- Pitfalls: HIGH — derived from direct code reading (existing `stop()` clear-before-compute risk is concrete) and confirmed behavioral tests

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable ecosystem — click/rich APIs not changing)
