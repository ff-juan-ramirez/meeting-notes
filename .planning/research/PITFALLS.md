# Pitfalls Research

**Domain:** Adding named recordings to an existing Python CLI meeting-notes tool
**Researched:** 2026-03-27
**Confidence:** HIGH — grounded in actual codebase (record.py, stop, transcribe.py, summarize.py, list.py, storage.py, state.py)

> This file covers pitfalls SPECIFIC TO the v1.2 Named Recordings milestone.
> It does not repeat v1.1 pitfalls (device indices, mlx-whisper memory, Notion rate-limiting, etc.) already in the prior PITFALLS.md.

---

## Critical Pitfalls

### Pitfall 1: Filename Collision — Two Recordings with the Same Name

**What goes wrong:**
Two recordings named "1:1 with Gabriel" both slugify to `1-1-with-gabriel`. The WAV, `.txt`, `.srt`, and `.json` metadata files for the second recording silently overwrite the first. The first session's data is permanently lost with no error, warning, or user prompt.

**Why it happens:**
`storage.py:get_recording_path()` currently generates `{timestamp}-{session_id}.wav`. The timestamp component makes collisions essentially impossible. When a name-based slug is prepended or replaces part of the filename, developers often place the slug BEFORE the timestamp, or worse, use the slug ALONE, losing the uniqueness guarantee.

Example of the unsafe pattern:
```python
# WRONG — collision-prone
filename = f"{slugify(name)}.wav"

# WRONG — still collision-prone if two recordings start in the same second
filename = f"{slugify(name)}-{timestamp}.wav"

# CORRECT — slug prefix, timestamp+uuid suffix preserved
filename = f"{slugify(name)}-{timestamp}-{session_id}.wav"
```

**How to avoid:**
Always preserve the `{timestamp}-{session_id}` suffix from the existing `get_recording_path()` logic. The slug is a human-readable prefix; uniqueness is guaranteed by the existing suffix. The function signature should become `get_recording_path(name: str | None = None)`, and when name is provided, prepend `{slug}-` to the existing filename pattern.

**Warning signs:**
- `get_recording_path()` is modified to accept a name but the existing timestamp+UUID suffix is removed or made optional
- Tests only test "first recording with name X" and never test "two recordings with name X back-to-back"
- The slug is used as the entire stem without a timestamp component

**Phase to address:** Phase 1 (storage layer — the slug-filename contract must be locked before any other phase builds on it)

---

### Pitfall 2: Slugification Edge Cases Produce Invalid or Ambiguous Filenames

**What goes wrong:**
The name entered by the user contains characters that either produce an empty slug, an unexpectedly short slug, or a slug identical to another name's slug. The tool either crashes (if the slug is used as a filename component directly), silently creates a confusingly-named file, or the name is lost entirely.

**Known edge cases against the target format "1:1 with Gabriel":**

| Input | Naive slug (replace spaces with `-`) | Correct slug |
|-------|--------------------------------------|--------------|
| `1:1 with Gabriel` | `1:1-with-gabriel` (colon kept, invalid on some FS) | `1-1-with-gabriel` |
| `Q1/Q2 planning` | `Q1/Q2-planning` (slash is path separator!) | `q1-q2-planning` |
| `Résumé review` | `Résumé-review` (non-ASCII) | `resume-review` (ASCII-folded) |
| `` (empty string) | `` (empty slug) | fallback to `untitled` |
| `   ` (all spaces) | `` (empty after strip) | fallback to `untitled` |
| `a` * 200 chars | 200-char slug (too long for filename stem) | truncated to 50 chars |
| `---` | `---` (all separators, visually useless) | fallback to `untitled` |
| `<>:"/\|?*` (Windows reserved chars) | multiple invalid chars | strip all non-alphanumeric/hyphen |
| `con` / `nul` / `prn` | Windows reserved names (irrelevant here but slug collision risk) | not a macOS issue, ignore |

**Why it happens:**
Developers implement slugification as a one-liner (`name.lower().replace(" ", "-")`) that handles the happy path but none of the edge cases. Colons, slashes, and unicode characters are not addressed. The function is rarely tested with adversarial inputs.

**How to avoid:**
Implement a single `slugify(name: str) -> str` function in `core/storage.py` (or `core/naming.py`) with the following contract, tested exhaustively:

```python
import re
import unicodedata

def slugify(name: str, max_length: int = 50) -> str:
    """Convert a human name to a safe filename slug.

    Rules (applied in order):
    1. Strip leading/trailing whitespace
    2. NFKD normalize, then encode as ASCII ignoring non-ASCII (accent folding)
    3. Lowercase
    4. Replace any run of non-alphanumeric characters with a single hyphen
    5. Strip leading/trailing hyphens
    6. Truncate to max_length
    7. If result is empty, return 'untitled'
    """
    name = name.strip()
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    name = name[:max_length]
    name = name.strip("-")  # truncation may leave trailing hyphen
    return name or "untitled"
```

**Warning signs:**
- Slugify function uses only `str.replace()` without regex or unicodedata
- No test covers `1:1` (colon), unicode input, empty string, all-spaces, very long strings, or all-punctuation inputs
- The function is defined inline in `record.py` rather than in a shared utility module

**Phase to address:** Phase 1 (core utility — slugify must be shared and tested before any command uses it)

---

### Pitfall 3: Name Lost Between `meet record` and `meet stop` — Metadata Never Sees It

**What goes wrong:**
`meet record` stores the name in `state.json`. `meet stop` reads `state.json`, computes the stem from `output_path` (not the name), and writes `metadata/{stem}.json`. If `meet stop` does not explicitly copy the `name` field from `state.json` to the metadata JSON, the name is silently lost and will never appear in `meet list`, `meet transcribe`, or Notion.

**Why it happens:**
Looking at the current `stop` command in `record.py` (lines 95–122): it reads `state.json` via `existing = read_state(state_path)`, extracts `output_path`, computes `stem`, reads or creates `metadata/{stem}.json`, adds `duration_seconds` and `wav_path`, then writes. A developer adding `name` to `state.json` in `meet record` will naturally forget to propagate it in `meet stop`, because `stop` only explicitly copies `output_path` and `start_time`. There is no general "copy all state fields to metadata" pattern — only specific fields are extracted.

**How to avoid:**
In `meet stop`, explicitly read `name` from `existing` (the state) and write it to the metadata dict:
```python
name = existing.get("name")  # None for unnamed sessions
if name is not None:
    meta["name"] = name
```
Do NOT use `existing.get("name", "")` — the distinction between `None` (no name) and `""` (empty name that should have been caught at input) is meaningful for backward compatibility.

Write a test that: (1) invokes `meet record "My Meeting"`, (2) invokes `meet stop`, (3) reads the metadata JSON and asserts `name == "My Meeting"`.

**Warning signs:**
- `meet list` shows the correct name for sessions recorded after the feature ships, but never for sessions that went through an actual record→stop→list flow (only tested by writing metadata directly in tests, not through the real command flow)
- `state.json` has `name` field but metadata JSON does not
- Tests for `stop` do not assert on the `name` field in the output metadata

**Phase to address:** Phase 1 (`meet record` + `meet stop` name propagation must be implemented and tested together as a unit)

---

### Pitfall 4: Backward Compatibility — Existing Sessions Have No Name Field

**What goes wrong:**
All sessions recorded before v1.2 have metadata JSON files without a `name` field. After shipping:
- `meet list` crashes or shows `None` in the Name column instead of graceful fallback
- `meet transcribe --session <old-stem>` fails because it tries to resolve by slug but the stem has no slug prefix
- `meet summarize --session <old-stem>` fails similarly
- `--json` output changes shape (new `name` field is `null` for old sessions), breaking any scripts that parse the output

**Why it happens:**
The feature is designed and tested only against new sessions. Old sessions are forgotten because the test suite creates fresh tmp_path fixtures and never simulates pre-existing metadata JSON without a `name` field.

**How to avoid:**

1. **`meet list`** — treat `name` as optional. When `name` is absent or `None`, fall back to the existing stem-based title derivation (`_derive_title()`). Never access `meta["name"]` without `.get("name")`.

2. **`meet transcribe --session` and `meet summarize --session`** — the `--session` argument is a stem, not a name. This contract MUST NOT CHANGE. Existing stems like `20260322-143000-abc12345` must continue to work. Named sessions have stems like `1-1-with-gabriel-20260327-103000-abc12345`; users pass the full stem. Do not attempt to resolve by slug alone.

3. **`--json` output** — include `"name": null` for old sessions rather than omitting the key. This is a stable schema: callers can do `session.get("name")` without crashing.

4. **Migration** — do NOT retroactively add `name: null` to all existing metadata JSON files. Absence of the key and presence of `null` must both be handled identically throughout the codebase.

**Warning signs:**
- Any code that uses `meta["name"]` instead of `meta.get("name")`
- Tests that only create new sessions and never load pre-existing metadata without a `name` field
- `meet list --json` output has `name` for new sessions but omits the key for old sessions (inconsistent schema)
- `resolve_wav_by_stem` or `resolve_transcript_by_stem` is modified to accept a human name instead of a stem

**Phase to address:** Phase 1 (implement), with a specific backward-compat test fixture representing a pre-v1.2 metadata file

---

### Pitfall 5: `meet transcribe` and `meet summarize` Stem Resolution Breaks for Named Sessions

**What goes wrong:**
`meet transcribe --session 1-1-with-gabriel` fails because no WAV file named `1-1-with-gabriel.wav` exists. The actual WAV is named `1-1-with-gabriel-20260327-103000-abc12345.wav`. The user is forced to copy-paste the full stem, which defeats the purpose of a human name.

**Why it happens:**
`resolve_wav_by_stem()` does an exact match (`recordings_dir / f"{stem}.wav"`). This was fine when stems were generated UUIDs. A developer adds named recordings and forgets to update the resolution logic, leaving users with a confusing experience: they named the session but still have to use the UUID stem to access it.

**How to avoid:**
Update `resolve_wav_by_stem()` to support prefix matching when an exact match fails:

```python
def resolve_wav_by_stem(recordings_dir: Path, stem: str) -> Path:
    # Exact match first (backward compat + named sessions with full stem)
    candidate = recordings_dir / f"{stem}.wav"
    if candidate.exists():
        return candidate
    # Prefix match: find WAVs whose stem starts with slug-of-stem
    matches = list(recordings_dir.glob(f"{stem}-*.wav"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Ambiguous — most recent
        return sorted(matches, key=lambda p: p.stat().st_mtime)[-1]
    raise FileNotFoundError(f"No recording found for session: {stem}")
```

Apply the same pattern to `resolve_transcript_by_stem()` in `summarize.py`.

**Warning signs:**
- `meet transcribe --session 1-1-with-gabriel` returns "No recording found for session: 1-1-with-gabriel" even though a WAV with that prefix exists
- Tests for `--session` only use exact stems and never test a slug prefix that requires glob matching
- The slug prefix matching is implemented in `transcribe.py` but not in `summarize.py` (or vice versa), creating asymmetric behavior

**Phase to address:** Phase 2 (`meet transcribe --session` with slug prefix) and Phase 3 (`meet summarize --session` with slug prefix), though the shared helper logic should be extracted in Phase 1

---

### Pitfall 6: Notion Title Priority Conflict — Name vs. LLM-Generated H1

**What goes wrong:**
`meet summarize` uses `extract_title()` to derive the Notion page title from the notes markdown (first H1, fallback to first non-empty line, fallback to timestamp). If a session has a user-provided name (`"1:1 with Gabriel"`), the Notion page title may still end up as whatever the LLM generated as its H1 heading — which could be "Meeting Notes" or "Discussion Summary". The user's intent (name the recording after the meeting) is lost.

**Why it happens:**
`extract_title()` in `notion.py` is content-driven, not metadata-driven. The `summarize` command does not read the `name` field from session metadata before calling `extract_title()`. Developers add the `name` field to metadata but forget to thread it through to the Notion title logic.

The current code in `summarize.py` (lines 150–151):
```python
fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
title = extract_title(notes, fallback_ts)
```

There is no opportunity for the session name to influence `title` here.

**How to avoid:**
Read the session name from metadata before computing the title. Use the name as the FIRST priority, ahead of the LLM-generated H1:

```python
session_name = (session_metadata or {}).get("name")  # already loaded above
fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
title = session_name or extract_title(notes, fallback_ts)
```

This respects user intent: if they named the session, that name is the Notion page title.

**Warning signs:**
- `meet summarize` test stubs out `extract_title()` but never asserts on the `title` passed to `create_page()` when `session_metadata` contains a `name`
- A session named "1:1 with Gabriel" produces a Notion page titled "Meeting Notes — 2026-03-27 10:30"
- `session_metadata` is loaded for `diarized_transcript_path` (already done in the code) but not for `name`

**Phase to address:** Phase 3 (`meet summarize` — Notion title update), same phase that implements the Notion push enhancement

---

### Pitfall 7: `meet list` Title Column Ignores the `name` Field

**What goes wrong:**
`meet list` derives titles via `_derive_title()`, which reads from `notes_path` (LLM-generated H1) or falls back to the session stem. Even after named recordings are implemented, `meet list` shows `1-1-with-gabriel-20260327-103000-abc12345` in the Title column instead of `1:1 with Gabriel`, because `_derive_title()` does not read the `name` field from metadata.

**Why it happens:**
`_derive_title()` was written before the `name` field existed. Developers update `record.py` and `stop` to write the name, but forget to update `list.py`. The behavior difference between named and unnamed sessions in `meet list` is only visible by running the full flow, not through unit tests that mock metadata directly.

**How to avoid:**
Update `_derive_title()` to check `meta.get("name")` first:

```python
def _derive_title(meta: dict, stem: str) -> str:
    # User-provided name takes priority (v1.2+)
    name = meta.get("name")
    if name:
        return name
    # LLM-generated title from notes
    notes_path = meta.get("notes_path")
    if notes_path and Path(notes_path).exists():
        try:
            notes_text = Path(notes_path).read_text()
            return extract_title(notes_text, stem)
        except Exception:
            return stem
    return stem
```

**Warning signs:**
- `meet list` shows the stem (e.g. `1-1-with-gabriel-20260327-103000`) instead of the human name
- Test for `_derive_title()` with a metadata dict containing `name` is missing
- The `name` column in `meet list --json` output contains the stem rather than the human name

**Phase to address:** Phase 4 (`meet list` display), but the `name` field in metadata must be written in Phase 1 before Phase 4 can read it

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Slugify inline in `record.py` as a lambda | Faster to implement | Not reusable in tests or other commands; different commands slugify differently | Never — extract to `core/storage.py` or `core/naming.py` |
| Use slug alone as filename (no timestamp suffix) | Human-readable filenames | Silent data loss on collision; loses guaranteed uniqueness | Never |
| Copy `name` to metadata only in `transcribe`, not `stop` | Less code in `stop` | Sessions that are never transcribed have no name in metadata; `meet list` can't display it | Never — name must be persisted at `stop` time |
| Resolve `--session` by exact stem only (no prefix) | Zero code change to resolver | Users must paste full UUID stem, not slug; defeats purpose of named recordings | Never — implement prefix matching |
| `meet list` title from stem when name exists in metadata | No change to list.py | Users see `1-1-with-gabriel-20260327-...` instead of `1:1 with Gabriel` | Never — check `name` field first |
| Accept empty string as a valid name | Simpler validation | Empty slug → `untitled` → collision with all other unnamed sessions | Never — validate non-empty at CLI argument level |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Notion page title | Using `extract_title(notes, fallback)` regardless of session name | Check `session_metadata.get("name")` first; use it as title if present |
| `meet list --json` schema | Adding `name` only for named sessions (key absent for old sessions) | Always include `"name": meta.get("name")` — value is `null` for old sessions, consistent schema |
| `meet transcribe --session` | Requiring full stem `1-1-with-gabriel-20260327-103000-abc12345` | Support slug prefix matching via `glob(f"{stem}-*.wav")` |
| `meet summarize --session` | Different resolution logic than `transcribe` | Extract shared resolver to avoid drift between commands |
| `state.json` cleanup | `clear_state()` in `stop` destroys `name` before it reaches metadata | Always copy `name` from state to metadata BEFORE calling `clear_state()` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `meet list` slug resolution on every list call | None at current scale (~100 sessions) | Not a trap at this scale; JSON scan is O(n) and n is small | Never becomes an issue for a local single-user tool |
| Glob pattern matching in resolver (`f"{stem}-*.wav"`) | Could match unrelated files if stem is very short (e.g. `a-`) | Enforce minimum slug length (5 chars) or use full timestamp format in glob | Only if very short names are allowed; e.g. `meet record "hi"` → slug `hi` → glob `hi-*.wav` matches `hike-20260327-...wav` |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Name only shown in `meet list` after summarization | User records "1:1 with Gabriel", runs `meet list`, sees the stem instead of the name — name only appears after LLM summarization generates an H1 | Read `name` from metadata first; don't require summarization to show a human title |
| User types `meet transcribe --session "1:1 with Gabriel"` (with spaces, quotes, colons) | Shell quotes are handled by the shell, but the stem resolution fails because the session was stored as `1-1-with-gabriel-...` | `--session` documentation must say "use the slug prefix" not "the original name"; or auto-slugify the `--session` argument before resolving |
| Long name produces extremely long filename | `meet record "Q1 2026 Engineering All-Hands Planning Session with Product and Design Teams"` → 80-char slug prefix in filename | Truncate slug to 50 chars in `slugify()` |
| Name contains only special characters | `meet record "???"` → slug is empty → falls back to `untitled` silently | Warn the user: "Name produced an empty slug. Saving as untitled." |

---

## "Looks Done But Isn't" Checklist

- [ ] **Name in `meet list`:** Verify that sessions recorded before v1.2 (no `name` field in metadata) still show a title — not `None` or blank
- [ ] **Name propagation through full flow:** Run `meet record "1:1 with Gabriel"` → `meet stop` → read metadata JSON → confirm `"name": "1:1 with Gabriel"` is present
- [ ] **Collision safety:** Record two sessions with the same name back-to-back (within the same second) and confirm both WAV files exist with distinct filenames
- [ ] **Slug resolution in `meet transcribe`:** Run `meet transcribe --session 1-1-with-gabriel` (slug prefix, not full stem) and confirm it resolves correctly
- [ ] **Notion title uses name:** After `meet summarize` on a named session, confirm the Notion page title is the user-provided name, not the LLM's H1
- [ ] **Empty/whitespace name rejected:** `meet record "   "` should error or warn — not silently create an `untitled` session
- [ ] **`meet list --json` schema stability:** Confirm old sessions have `"name": null` (key present, value null) not missing key entirely
- [ ] **SRT and `.txt` files use same slug-prefixed stem:** Confirm `1-1-with-gabriel-{timestamp}.txt`, `.srt`, and `.json` all share the same stem as the WAV

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Filename collision (two sessions overwrite) | HIGH | No automatic recovery — data is gone. Restore from backup if available. Prevention is the only option. |
| Name lost between `record` and `stop` | MEDIUM | Manually add `"name": "..."` to the metadata JSON file. `meet list` will pick it up on next run. |
| Backward compat crash on old sessions | LOW | Add `.get("name")` guard at the crash site; re-run failed command. |
| Notion title wrong (LLM H1 used instead of name) | LOW | Manually rename the Notion page. Future sessions unaffected once fix is shipped. |
| Slug too permissive (colon in filename) | MEDIUM | Rename affected files manually; fix `slugify()` and re-record. Old files with invalid chars work on macOS but break portability. |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| P1: Filename collision | Phase 1 — `storage.py` slug+timestamp filename contract | Test: two records with same name → two distinct WAV files exist |
| P2: Slugification edge cases | Phase 1 — `slugify()` utility with exhaustive tests | Test matrix: colon, slash, unicode, empty, all-spaces, 200-char, all-punctuation |
| P3: Name lost between record and stop | Phase 1 — `meet stop` copies `name` from state to metadata | Test: record→stop→read metadata → name present |
| P4: Backward compat (no name field) | Phase 1 — all readers use `.get("name")` | Test fixture: pre-v1.2 metadata JSON without `name` field runs through all commands without crash |
| P5: Stem resolution breaks for named sessions | Phase 2+3 — resolver uses glob prefix matching | Test: `--session 1-1-with-gabriel` resolves without full stem |
| P6: Notion title ignores session name | Phase 3 — `meet summarize` reads name from metadata before `extract_title()` | Test: summarize with named session → `create_page` called with `title=session_name` |
| P7: `meet list` ignores name field | Phase 4 — `_derive_title()` checks `name` first | Test: `meet list` with named session metadata → name shown in Title column |

---

## Sources

- Direct code analysis: `meeting_notes/cli/commands/record.py`, `stop`, `transcribe.py`, `summarize.py`, `list.py`
- Direct code analysis: `meeting_notes/core/storage.py`, `meeting_notes/core/state.py`, `meeting_notes/services/notion.py`
- Python `unicodedata` module documentation — NFKD normalization for accent folding
- macOS filesystem behavior — HFS+/APFS allow colons in filenames via POSIX API but the shell interprets them; colons in filenames create confusion in shell scripts even if technically allowed
- Existing PITFALLS.md (v1.1) — not duplicated here

---
*Pitfalls research for: Named recordings added to existing Python CLI meeting-notes tool (v1.2)*
*Researched: 2026-03-27*
