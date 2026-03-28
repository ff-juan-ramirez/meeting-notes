# Phase 05: Notion Title Integration - Research

**Researched:** 2026-03-28
**Domain:** CLI command modification (meet summarize), Notion title selection logic
**Confidence:** HIGH

## Summary

Phase 05 is a minimal, surgical change to `meet summarize`. The only behavior to add is: when building the Notion page title, check `meta.get("recording_name")` first — if truthy, use it directly; otherwise fall through to the existing `extract_title(notes, fallback_ts)` call. This mirrors the identical pattern already shipped in Phase 04 for `meet list` (`_derive_title()` in `list.py`).

The change touches exactly one location in `summarize.py` (the Notion push block, lines 150-151) and requires new test cases in `test_summarize_command.py`. No new dependencies, no new files, no schema changes. Session metadata already contains `recording_name` when populated by `meet stop` (Phase 03). Unnamed sessions and pre-v1.2 sessions have `recording_name` absent or `None`, so the falsy guard leaves them unaffected.

All 41 existing tests in `test_summarize_command.py` and `test_notion_service.py` pass green as of this research. The Phase 04 implementation of `_derive_title()` is the canonical reference for how to apply the same pattern here.

**Primary recommendation:** Copy the `recording_name` falsy-guard pattern from `_derive_title()` in `list.py` into the Notion title derivation block in `summarize.py`. One guard clause, two new tests.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NOTION-01 | `meet summarize` uses `meta.get("recording_name")` as the Notion page title before `extract_title()` fallback; unnamed and pre-v1.2 sessions are unaffected | Metadata is already loaded into `session_metadata` dict before the Notion block. Guard clause pattern proven in Phase 04 `_derive_title()`. `extract_title()` remains the fallback path unchanged. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| notion-client | already installed | Notion API client | already in use throughout the project |
| click | already installed | CLI framework | project-wide CLI framework |
| pytest | 9.x (already installed) | Test framework | project standard |

No new dependencies are introduced by this phase.

**Installation:** None required.

## Architecture Patterns

### Relevant Project Structure
```
meeting_notes/
├── cli/
│   └── commands/
│       ├── summarize.py   # MODIFIED: Notion title derivation block
│       └── list.py        # REFERENCE: _derive_title() pattern to replicate
├── services/
│   └── notion.py          # NO CHANGE: extract_title() stays as fallback
tests/
└── test_summarize_command.py  # MODIFIED: 2 new test cases added
```

### Pattern 1: Recording Name Guard Clause (from Phase 04 — HIGH confidence)

**What:** Before calling `extract_title()`, check `meta.get("recording_name")`. If truthy, use it as the title and skip `extract_title()`.

**When to use:** Any place a "best title" needs to be derived from session metadata.

**Proven implementation (from `meeting_notes/cli/commands/list.py` lines 54-69):**
```python
def _derive_title(meta: dict, stem: str) -> str:
    """Derive session title.

    Priority: recording_name (user-given) > LLM heading (from notes) > stem.
    """
    recording_name = meta.get("recording_name")
    if recording_name:
        return recording_name
    notes_path = meta.get("notes_path")
    if notes_path and Path(notes_path).exists():
        try:
            notes_text = Path(notes_path).read_text()
            return extract_title(notes_text, stem)
        except Exception:
            return stem
    return stem
```

**Decision from STATE.md (Phase 04):** "recording_name guard clause at top of _derive_title() before notes_path check — user-given name always wins (D-01)" and "Falsy check (if recording_name:) handles None, empty string, and missing key uniformly per D-03 discretion"

### Exact Change Required in summarize.py

The Notion block (lines 143-175) currently derives the title as:

```python
fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
title = extract_title(notes, fallback_ts)
```

This becomes a three-priority derivation:

```python
fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
recording_name = session_metadata.get("recording_name") if session_metadata else None
title = recording_name if recording_name else extract_title(notes, fallback_ts)
```

**Key fact:** `session_metadata` is already loaded earlier in `summarize()` (line 82: `session_metadata = read_state(metadata_path)`). It is in scope at the Notion block. No additional file reads needed.

### Anti-Patterns to Avoid

- **Do not move the change into `extract_title()`:** `extract_title()` lives in `services/notion.py` and is a pure function operating only on notes markdown text. It has no access to session metadata. The fix belongs in `summarize.py` at the call site.
- **Do not add a new parameter to `extract_title()`:** The function signature is stable and used in `list.py` too. Changing it would require updating both callers and all existing tests.
- **Do not use `session_metadata.get("recording_name", None)`:** The plain `.get("recording_name")` is consistent with Phase 04 style. Both return `None` for absent keys; the explicit `None` default adds no value.
- **Do not guard with `is not None`:** Use falsy check (`if recording_name:`) to uniformly handle `None`, empty string, and missing key — same decision as Phase 04 D-03.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Title priority logic | Custom dispatcher class | Simple if-guard | One-liner guard is the Phase 04 proven pattern; a class adds zero value |
| Metadata access | New helper function | Direct `session_metadata.get(...)` | Dict is already in scope; wrapping it adds indirection with no benefit |

**Key insight:** This phase is a 3-line code change with 2 test cases. Resist over-engineering.

## Common Pitfalls

### Pitfall 1: session_metadata May Be None
**What goes wrong:** If no metadata file exists for a session (e.g. pre-v1.2 session with no .json), `read_state()` returns `None`. Calling `None.get("recording_name")` raises `AttributeError`.
**Why it happens:** `read_state()` returns `None` on missing or unreadable file (confirmed in `state.py`).
**How to avoid:** Guard with `session_metadata.get("recording_name") if session_metadata else None` — or check `if session_metadata` before the `.get()`. The existing code already handles this pattern at line 83: `if session_metadata and session_metadata.get("diarized_transcript_path")`.
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'get'` in tests with no pre-populated metadata file.

### Pitfall 2: recording_name Read AFTER Metadata Has Already Been Rewritten
**What goes wrong:** `session_metadata` is loaded at line 82, but the metadata is then extended and rewritten at lines 130-137 via a fresh `read_state()` call into `existing`. If someone accidentally tries to read `recording_name` from the second `existing = read_state(metadata_path) or {}` dict (line 173), it is the same data, but relying on the second read is fragile.
**Why it happens:** Two `read_state()` calls exist in `summarize()`. The first (line 82) is for diarization check and is the right one to use for `recording_name`.
**How to avoid:** Read `recording_name` from `session_metadata` (first read, line 82), not from `existing` (second read, line 173). Both contain the same data in practice, but using the semantically correct variable is cleaner.

### Pitfall 3: Test Does Not Actually Verify Title Passed to create_page
**What goes wrong:** A test creates metadata with `recording_name` but only checks exit code, missing that `create_page` was called with the wrong title.
**Why it happens:** Most existing Notion tests in `test_summarize_command.py` patch `create_page` with `return_value` only and do not inspect call args.
**How to avoid:** Use `mock_create_page.call_args` or `mock_create_page.assert_called_once_with(token=..., parent_page_id=..., title="My Recording Name", ...)` to assert the exact title passed.

### Pitfall 4: Forgetting the Unnamed Session Regression Test
**What goes wrong:** Phase delivers the named-session feature but doesn't prove that sessions without `recording_name` still use `extract_title()`.
**Why it happens:** Easy to write only the happy-path test.
**How to avoid:** Write at least one test where metadata has no `recording_name` key and assert `create_page` receives the LLM-extracted title (i.e., the H1 from the generated notes).

## Code Examples

### Minimal Change to summarize.py (Notion title block)
```python
# Source: derived from list.py _derive_title() pattern (Phase 04 D-01/D-03)
# Before (line 151 in current summarize.py):
fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
title = extract_title(notes, fallback_ts)

# After:
fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
recording_name = session_metadata.get("recording_name") if session_metadata else None
title = recording_name if recording_name else extract_title(notes, fallback_ts)
```

### Test Pattern: Named Session Uses recording_name as Title
```python
def test_summarize_notion_uses_recording_name(runner, tmp_path):
    """When metadata has recording_name, create_page receives it as title."""
    from meeting_notes.cli.commands.summarize import summarize
    from meeting_notes.core.state import write_state

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "my-standup-20260328-090000-abc12345"
    _create_fake_transcript(transcripts, stem)
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")

    # Pre-populate metadata with recording_name
    metadata_path = metadata / f"{stem}.json"
    write_state(metadata_path, {"recording_name": "My Standup"})

    mock_create_page = MagicMock(return_value="https://notion.so/abc123")
    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", mock_create_page):
        result = runner.invoke(summarize, ["--session", stem])

    assert result.exit_code == 0
    call_kwargs = mock_create_page.call_args[1]
    assert call_kwargs["title"] == "My Standup"
```

### Test Pattern: Unnamed Session Falls Through to extract_title
```python
def test_summarize_notion_unnamed_uses_extract_title(runner, tmp_path):
    """When metadata has no recording_name, create_page receives LLM-extracted title."""
    from meeting_notes.cli.commands.summarize import summarize

    transcripts, notes, metadata = _make_env_dirs(tmp_path)
    stem = "20260328-090000-abc12345"
    # Notes content with H1 heading — extract_title should return "My Meeting"
    _create_fake_transcript(transcripts, stem, content="regular transcript text")
    _create_config(tmp_path, token="secret_test", parent_page_id="page123")
    # No recording_name in metadata (or no metadata at all)

    mock_create_page = MagicMock(return_value="https://notion.so/abc123")

    def fake_spinner(fn, msg, **kw):
        result = fn()
        # Patch notes content to have an H1 for extract_title to find
        return "# My Meeting\n\nContent here" if "Generating" in msg else result

    with patch("meeting_notes.cli.commands.summarize.get_data_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.get_config_dir", return_value=tmp_path), \
         patch("meeting_notes.cli.commands.summarize.run_with_spinner", side_effect=lambda fn, msg, **kw: fn()), \
         patch("meeting_notes.services.llm.requests.post", return_value=_make_ollama_mock()), \
         patch("meeting_notes.cli.commands.summarize.create_page", mock_create_page):
        runner.invoke(summarize, ["--session", stem])

    # Title must NOT be recording_name (None/absent) — should be from extract_title or fallback
    call_kwargs = mock_create_page.call_args[1]
    # The key assertion: title is NOT a recording_name value
    assert call_kwargs["title"] != "My Standup"
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | none (pyproject.toml or auto-detected) |
| Quick run command | `python3 -m pytest tests/test_summarize_command.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NOTION-01 | Named session uses recording_name as Notion title | unit | `python3 -m pytest tests/test_summarize_command.py -k "recording_name" -x` | Wave 0 gap |
| NOTION-01 | Unnamed session falls through to extract_title | unit | `python3 -m pytest tests/test_summarize_command.py -k "unnamed" -x` | Wave 0 gap |
| NOTION-01 | Pre-v1.2 session (no metadata) is unaffected | unit | `python3 -m pytest tests/test_summarize_command.py -k "pre_v12 or no_metadata" -x` | Wave 0 gap |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_summarize_command.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_summarize_command.py` — add `test_summarize_notion_uses_recording_name` (NOTION-01 named path)
- [ ] `tests/test_summarize_command.py` — add `test_summarize_notion_unnamed_uses_extract_title` (NOTION-01 unnamed regression)
- [ ] `tests/test_summarize_command.py` — add `test_summarize_notion_no_metadata_unaffected` (NOTION-01 pre-v1.2 regression)

*(All gaps are additions to an existing test file — no new files or framework config needed.)*

## Environment Availability

Step 2.6: SKIPPED (no external dependencies — this is a pure code modification with no new tools, services, or runtimes required).

## Sources

### Primary (HIGH confidence)
- `meeting_notes/cli/commands/summarize.py` — exact current implementation, title derivation at lines 150-151
- `meeting_notes/cli/commands/list.py` — `_derive_title()` pattern to replicate (lines 54-69)
- `meeting_notes/services/notion.py` — `extract_title()` function (lines 21-31), confirmed no change needed
- `.planning/STATE.md` — Phase 04 decisions D-01 and D-03 on recording_name guard and falsy check
- `.planning/REQUIREMENTS.md` — NOTION-01 exact wording

### Secondary (MEDIUM confidence)
- `tests/test_summarize_command.py` — existing test structure (41 tests, all passing) — informs new test patterns
- `tests/test_notion_service.py` — confirms `_make_api_error` helper pattern for any Notion error tests needed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, all existing
- Architecture: HIGH — pattern directly observed in Phase 04 list.py, session_metadata already in scope
- Pitfalls: HIGH — derived from direct code inspection and Phase 04 decisions

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable codebase, no external dependencies)
