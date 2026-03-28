# Architecture Research: Named Recordings Integration

**Domain:** Local meeting audio capture + transcription + LLM note generation CLI
**Milestone:** v1.2 — Named Recordings
**Researched:** 2026-03-27
**Confidence:** HIGH — based on direct code inspection of all affected modules

---

## Integration Question Answers

### Q1: Where should the name be introduced?

**Recommendation: Both `state.json` at record time AND the session metadata JSON at stop time.**

The name must live in `state.json` because `meet stop` does not receive the name as a CLI argument — it has no context beyond what is in the state file. When `meet stop` writes the session metadata JSON, it reads `state.json`, so the name must already be there.

The name must also be written to the session metadata JSON at stop time (alongside `wav_path`, `duration_seconds`) so every downstream command (`meet transcribe`, `meet summarize`, `meet list`) can access it without reading `state.json`, which is cleared by `meet stop`.

**Data flow:**
```
meet record [NAME]
  → slugify(NAME) → recording_slug
  → get_recording_path_with_slug(slug)  → recordings/{slug}-{timestamp}.wav
  → write_state(state.json, {
        ...,
        "name": NAME,              # raw user input
        "slug": recording_slug,    # pre-computed slug
    })

meet stop
  → read state.json → has name + slug
  → writes metadata/{slug}-{timestamp}.json with:
        "name": NAME,
        "slug": recording_slug,
        "wav_path": ...
  → clears state.json
```

---

### Q2: Output filename strategy

**Recommendation: `{slug}-{timestamp}.wav` (slug-first, timestamp-suffix).**

Do not use slug-only — timestamps prevent collisions if two recordings share a name in the same day. Do not use timestamp-only with name in metadata only — that makes the file system opaque and breaks shell tab-completion workflows.

**Rationale for slug-first order:**

- `ls recordings/` groups recordings by name, not by date — easier to find "1-1-with-gabriel" across sessions
- The timestamp still guarantees uniqueness
- Matches the pattern users already have a mental model for (slugified-name as the primary identifier)

**Example output filenames:**
```
recordings/1-1-with-gabriel-20240322-143022.wav
transcripts/1-1-with-gabriel-20240322-143022.txt
transcripts/1-1-with-gabriel-20240322-143022.srt
notes/1-1-with-gabriel-20240322-143022-meeting.md
metadata/1-1-with-gabriel-20240322-143022.json
```

**Anonymous sessions (no name provided):**

Retain the existing format unchanged: `{timestamp}-{uuid8}.wav`. The `{uuid8}` suffix already prevents collisions and is how all v1.0 sessions were stored. This preserves backward compatibility with existing session metadata JSON files.

---

### Q3: Slugification approach

**Recommendation: `unicodedata.normalize` + ASCII transliteration + lowercase + punctuation-to-dash + collapse + strip.**

Use Python's standard library `unicodedata` module — no new dependency required.

**Algorithm:**

```python
import re
import unicodedata

def slugify(name: str) -> str:
    """Convert a human name to a filename-safe slug.

    Examples:
        "1:1 with Gabriel"   -> "1-1-with-gabriel"
        "Q1 Review & Budget" -> "q1-review-budget"
        "Réunion d'équipe"   -> "reunion-d-equipe"
        "  Multiple   Spaces " -> "multiple-spaces"
    """
    # 1. Unicode normalize to NFD, then encode to ASCII dropping combining chars
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    # 2. Lowercase
    name = name.lower()
    # 3. Replace colons (e.g. "1:1") with hyphens before general punctuation pass
    name = name.replace(":", "-")
    # 4. Replace any non-alphanumeric, non-hyphen character with a hyphen
    name = re.sub(r"[^a-z0-9\-]+", "-", name)
    # 5. Collapse consecutive hyphens
    name = re.sub(r"-{2,}", "-", name)
    # 6. Strip leading/trailing hyphens
    name = name.strip("-")
    return name or "recording"  # fallback if input reduces to empty string
```

**Key cases handled:**

| Input | Output |
|-------|--------|
| `"1:1 with Gabriel"` | `"1-1-with-gabriel"` |
| `"Q1 Review & Budget"` | `"q1-review-budget"` |
| `"Réunion d'équipe"` | `"reunion-d-equipe"` |
| `"  "` (whitespace only) | `"recording"` (fallback) |
| `""` (empty) | `"recording"` (fallback) |
| `"all/slashes\and*stars"` | `"all-slashes-and-stars"` |

**Where to live:** `meeting_notes/core/storage.py` — alongside `get_recording_path()`. This is a pure function with no I/O and no new imports.

---

### Q4: New function in `storage.py`

The existing `get_recording_path()` generates `{timestamp}-{uuid8}.wav`. A new sibling function handles the named case:

```python
def get_recording_path_with_slug(
    slug: str,
    storage_path: str | None = None,
) -> Path:
    """Return path for a named recording: {slug}-{timestamp}.wav"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return get_data_dir(storage_path) / "recordings" / f"{slug}-{timestamp}.wav"
```

The existing `get_recording_path()` is not modified — unnamed sessions continue to use it unchanged.

---

### Q5: Which commands need updating?

| Command | Change Required | Nature of Change |
|---------|----------------|------------------|
| `meet record` | Yes | New optional `[NAME]` argument; slugify; call `get_recording_path_with_slug`; write `name`+`slug` to state.json |
| `meet stop` | Yes | Read `name`/`slug` from state.json; include in metadata JSON; derive metadata filename from stem |
| `meet transcribe` | Minimal | Stem-based resolution already works; no slug awareness needed. Session resolution by latest WAV or `--session STEM` unchanged |
| `meet summarize` | Yes | Notion title: prefer `name` from metadata over `extract_title()` from notes content when available |
| `meet list` | Yes | `_derive_title()` must check `meta.get("name")` first, before reading notes file for H1 |
| `meet doctor` | No | No changes — no new system prerequisites |
| `meet init` | No | No changes — name is per-session, not a config concern |

---

### Q6: Name flow from `record` to `list` to Notion

```
meet record "1:1 with Gabriel"
  ├─ slug = slugify("1:1 with Gabriel")  → "1-1-with-gabriel"
  ├─ wav_path = recordings/1-1-with-gabriel-20240322-143022.wav
  └─ state.json = { "name": "1:1 with Gabriel", "slug": "1-1-with-gabriel",
                    "pid": ..., "output_path": ..., "start_time": ... }

meet stop
  ├─ reads state.json → has name="1:1 with Gabriel", slug="1-1-with-gabriel"
  ├─ stem = "1-1-with-gabriel-20240322-143022"  (from Path(output_path).stem)
  ├─ metadata path = metadata/1-1-with-gabriel-20240322-143022.json
  └─ metadata/1-1-with-gabriel-20240322-143022.json = {
         "name": "1:1 with Gabriel",
         "slug": "1-1-with-gabriel",
         "wav_path": ".../recordings/1-1-with-gabriel-20240322-143022.wav",
         "duration_seconds": ...
     }

meet transcribe [--session 1-1-with-gabriel-20240322-143022]
  ├─ resolve_wav_by_stem() / resolve_latest_wav() → unchanged
  ├─ stem = "1-1-with-gabriel-20240322-143022"
  ├─ transcripts/1-1-with-gabriel-20240322-143022.txt
  ├─ transcripts/1-1-with-gabriel-20240322-143022.srt
  └─ metadata JSON: read-merge-write (preserves "name", "slug" from stop)

meet summarize
  ├─ stem = "1-1-with-gabriel-20240322-143022"
  ├─ notes/1-1-with-gabriel-20240322-143022-meeting.md
  ├─ Notion title = meta.get("name") or extract_title(notes, fallback_ts)
  └─ metadata JSON: read-merge-write (preserves all fields)

meet list
  └─ _derive_title() = meta.get("name") or [existing H1/stem logic]

meet list --json
  └─ "name": "1:1 with Gabriel" appears in each session object
```

---

## Component Boundaries — What Changes

### New: `meeting_notes/core/storage.py`

**New function:** `slugify(name: str) -> str`
**New function:** `get_recording_path_with_slug(slug: str, storage_path: str | None = None) -> Path`
**Unchanged:** `get_recording_path()`, `get_data_dir()`, `get_config_dir()`, `ensure_dirs()`

### Modified: `meeting_notes/services/audio.py`

`start_recording(config)` currently calls `get_recording_path()` directly. The name must be passed in:

**Option A (recommended):** Add optional `slug: str | None = None` parameter to `start_recording()`. When present, calls `get_recording_path_with_slug(slug)`. When absent, calls `get_recording_path()`. This keeps the service layer responsible for path selection and keeps `record.py` thin.

```python
def start_recording(config: Config, slug: str | None = None) -> tuple[subprocess.Popen, Path]:
    ensure_dirs(config.storage_path)
    if slug:
        output_path = get_recording_path_with_slug(slug, config.storage_path)
    else:
        output_path = get_recording_path(config.storage_path)
    ...
```

### Modified: `meeting_notes/cli/commands/record.py`

**`record` command:**
- Add `@click.argument("name", default=None, required=False)` before `@click.pass_context`
- Slugify the name if provided
- Pass slug to `start_recording(config, slug=slug)`
- Include `"name"` and `"slug"` in state written to `state.json`

**`stop` command:**
- Read `name` and `slug` from `existing` (state.json) — both may be absent for unnamed sessions
- Write both to the metadata JSON alongside `wav_path` and `duration_seconds`
- No change to stem derivation — stem comes from `Path(output_path_str).stem` as today

### Modified: `meeting_notes/cli/commands/list.py`

**`_derive_title(meta, stem)`** — add one line at the top:

```python
def _derive_title(meta: dict, stem: str) -> str:
    name = meta.get("name")
    if name:
        return name
    # ... existing notes H1 / stem fallback ...
```

### Modified: `meeting_notes/cli/commands/summarize.py`

Notion title derivation currently uses `extract_title(notes, fallback_ts)`. Change to:

```python
name = session_metadata.get("name") if session_metadata else None
title = name or extract_title(notes, fallback_ts)
```

The `session_metadata` dict is already loaded in `summarize.py` (line 83). This is a two-line change.

### Unchanged: All other modules

`meet transcribe`, `meet doctor`, `meet init`, `services/transcription.py`, `services/llm.py`, `services/notion.py`, `core/config.py`, `core/state.py`, `core/health_check.py` — no changes required.

---

## Data Schema Changes

### state.json — new fields (optional, present only for named sessions)

```json
{
  "session_id": "...",
  "pid": 12345,
  "output_path": "/path/to/recordings/1-1-with-gabriel-20240322-143022.wav",
  "start_time": "2024-03-22T14:30:22+00:00",
  "name": "1:1 with Gabriel",
  "slug": "1-1-with-gabriel"
}
```

**New fields:** `name` (raw user input string), `slug` (pre-computed slug string)
**Both optional:** absent when `meet record` is run without a name argument

### Session metadata JSON — new fields (optional, present only for named sessions)

```json
{
  "name": "1:1 with Gabriel",
  "slug": "1-1-with-gabriel",
  "wav_path": "...",
  "duration_seconds": 3421,
  "transcript_path": "...",
  "srt_path": "...",
  "transcribed_at": "...",
  "word_count": 4832,
  "whisper_model": "...",
  "diarization_succeeded": false,
  "diarized_transcript_path": null,
  "speaker_turns": [],
  "notes_path": "...",
  "template": "1on1",
  "summarized_at": "...",
  "llm_model": "...",
  "notion_url": "https://notion.so/..."
}
```

**New fields:** `name`, `slug` — both optional strings
**All existing fields:** unchanged, preserved via read-merge-write pattern

---

## Backward Compatibility

**Existing sessions:** All existing session metadata JSONs lack `name` and `slug`. Every access point (`_derive_title`, Notion title derivation, `meet list`) uses `meta.get("name")` with a fallback — no migration needed.

**`--session STEM` flag:** Unchanged. The stem of a named recording (`1-1-with-gabriel-20240322-143022`) is still a valid, unambiguous identifier for `--session`.

**`resolve_latest_wav()`:** Unchanged. It sorts by `st_mtime`, not by filename pattern. Named recordings appear correctly in "latest" resolution.

---

## Updated File System Layout

```
~/.config/meeting-notes/
  config.json
  state.json                         # adds optional: name, slug

~/Documents/meeting-notes/           # or XDG_DATA_HOME
  recordings/
    1-1-with-gabriel-20240322-143022.wav   # named: slug-timestamp
    20240312-091500-a3f7b2c1.wav           # unnamed: timestamp-uuid8 (existing)
  transcripts/
    1-1-with-gabriel-20240322-143022.txt
    1-1-with-gabriel-20240322-143022.srt
    20240312-091500-a3f7b2c1.txt           # existing unnamed session unchanged
  notes/
    1-1-with-gabriel-20240322-143022-meeting.md
    1-1-with-gabriel-20240322-143022-1on1.md
  metadata/
    1-1-with-gabriel-20240322-143022.json  # adds: name, slug
    20240312-091500-a3f7b2c1.json          # unchanged
```

---

## Build Order for Phases

Dependencies flow in one direction: `storage.py` → `audio.py` → `record.py` → `stop` (in same file) → downstream commands. Tests must be written alongside each change.

| Phase | What to Build | Files Changed | Depends On |
|-------|--------------|---------------|------------|
| 1 | `slugify()` + `get_recording_path_with_slug()` in storage.py | `core/storage.py` | Nothing new |
| 1 | Tests for slugify (edge cases: colons, unicode, empty, whitespace) | `tests/test_storage.py` | Phase 1 storage |
| 2 | `start_recording(config, slug=None)` signature update | `services/audio.py` | Phase 1 storage |
| 2 | Tests for audio.py slug routing | `tests/test_audio.py` | Phase 2 audio |
| 3 | `meet record [NAME]` argument + state.json fields | `cli/commands/record.py` | Phase 2 audio |
| 3 | `meet stop` reads name/slug, writes to metadata JSON | `cli/commands/record.py` | Phase 3 record |
| 3 | Tests for record + stop with named and unnamed sessions | `tests/test_record_command.py` | Phase 3 commands |
| 4 | `_derive_title()` prefers `meta.get("name")` | `cli/commands/list.py` | Phase 3 metadata |
| 4 | Tests for list with named sessions | `tests/test_cli_list.py` | Phase 4 list |
| 5 | Notion title uses `meta.get("name")` over `extract_title()` | `cli/commands/summarize.py` | Phase 3 metadata |
| 5 | Tests for summarize Notion title with named sessions | `tests/test_summarize_command.py` | Phase 5 summarize |

**Rationale for ordering:**

- Phase 1 first: `slugify()` is a pure function with no dependencies — can be built and fully tested in isolation
- Phase 2 before Phase 3: `audio.py` is the next dependency in the chain; its signature change must be stable before `record.py` calls it
- Phase 3 (record + stop together): `stop` lives in the same file as `record`; they share `_get_state_path()` and `_get_config_path()`; separating them creates merge complexity
- Phase 4 and 5 are independent of each other: either can be built after Phase 3 completes; list is simpler so build it first
- Notion title change (Phase 5) is lowest risk — it is a two-line change gated behind existing Notion configuration

---

## Patterns to Follow

### Pattern: Read-merge-write for metadata

Already established and working. All metadata writes must read existing content first, merge, then write. Never overwrite. The `name` and `slug` fields written at `stop` time must survive through `transcribe` and `summarize` writes.

```python
existing = read_state(metadata_path) or {}
existing.update({"name": name, "slug": slug, ...})
write_state(metadata_path, existing)
```

### Pattern: Optional fields with `dict.get()` fallback

All consumers read `name` and `slug` with `.get()`. Never assume these fields exist — unnamed sessions will never have them, and existing sessions were created before this milestone.

### Pattern: Thin CLI commands, logic in core/services

`slugify()` belongs in `core/storage.py`, not in `cli/commands/record.py`. CLI commands should call pure functions from core, not implement logic inline.

---

## Anti-Patterns to Avoid

### Anti-Pattern: Separate `--name` flag instead of positional argument

`meet record --name "1:1 with Gabriel"` is more typing and less natural than `meet record "1:1 with Gabriel"`. The name is the primary optional input for this command. Use a Click `argument`, not an `option`.

**Exception:** If the project later adds `--template` or other record-time options, positional arguments can conflict. For now, a single optional argument is correct and Click handles it cleanly with `default=None, required=False`.

### Anti-Pattern: Computing slug in `record.py` and also in `stop.py`

Slug is computed once in `record.py`, stored in `state.json`, and read by `stop.py`. Never recompute it in `stop` — that would create inconsistency if slugify behavior changes between calls.

### Anti-Pattern: Modifying existing `get_recording_path()` signature

The existing function is used by tests and the audio service. Add a new sibling function rather than adding optional parameters to the existing one. This avoids breaking existing test fixtures.

### Anti-Pattern: Including slug in metadata filename without timestamp

`1-1-with-gabriel.json` would collide if the same meeting name is recorded twice. Always use the full stem (`slug-timestamp`) as the metadata file basename.

### Anti-Pattern: Changing how `meet transcribe --session` resolves sessions

The `--session` flag already accepts a stem. A named session's stem (`1-1-with-gabriel-20240322-143022`) is a valid stem. No changes to session resolution logic are needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Where to store name | HIGH | Code-verified: stop reads state.json; downstream reads metadata |
| Filename strategy | HIGH | Code-verified: stem-based resolution is already in transcribe + summarize |
| Slugify algorithm | HIGH | stdlib-only, no new deps, edge cases from PROJECT.md covered |
| Commands needing changes | HIGH | All command files read directly |
| Data flow | HIGH | Traced through all five commands in source |
| Backward compatibility | HIGH | `.get()` with fallback is the established pattern in list.py |
| Build order | HIGH | Dependency graph is explicit in source code |

---

*Researched: 2026-03-27 — v1.2 Named Recordings milestone*
