# Feature Research: Named Recordings (v1.2)

**Domain:** Named sessions in a local CLI meeting-notes tool
**Researched:** 2026-03-27
**Confidence:** HIGH (direct codebase inspection — every claim verified against source)
**Scope:** Additive features for v1.2 only. Existing v1.0/v1.1 features are already built and in use.

---

## Context: What Already Exists

This section documents the exact current state derived from code inspection — not assumptions.

**Current session identity:** The WAV filename stem is `{YYYYMMDD-HHMMSS}-{8hex}` (e.g. `20260322-143000-abc12345`), generated in `get_recording_path()` in `core/storage.py` using `uuid4().hex[:8]`. This stem is the shared key across `recordings/`, `transcripts/`, `notes/`, and `metadata/`.

**Current title in `meet list`:** `_derive_title()` in `cli/commands/list.py` (lines 54–67) reads the notes file heading via `extract_title()` if a notes file exists, and falls back to the raw stem. There is no `"name"` field checked anywhere. Sessions without summarized notes always show the opaque stem.

**Current Notion title:** `summarize.py` line 151: `title = extract_title(notes, fallback_ts)` — entirely LLM-dependent. Falls back to a timestamp string (`"Meeting Notes — YYYY-MM-DD HH:MM"`). No user-provided name is involved.

**Current `meet record`:** `cli/commands/record.py` — the `record()` Click command has no arguments at all, only `ctx`. There is no name field in the state dict written to `state.json` (lines 52–58: only `session_id`, `pid`, `output_path`, `start_time`).

**Current `meet stop`:** Reads `state.json` for `pid`, `output_path`, `start_time`. Writes `duration_seconds` and `wav_path` to `metadata/{stem}.json`. Does not propagate any name because none exists in state.

**Current `start_recording()`:** `services/audio.py` line 34: `output_path = get_recording_path(config.storage_path)`. The slug must be threaded through here — the path is computed inside `start_recording`, so the name must reach that function.

**Current `get_recording_path()`:** `core/storage.py` lines 34–37: takes only `storage_path`, generates its own timestamp and UUID. Must be extended to accept an optional slug prefix.

---

## Feature Landscape

### Table Stakes (Users Must Have These for the Milestone to Be Useful)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `meet record [NAME]` optional positional argument | Record-time is the only natural moment to name a session; all later outputs are derived from the filename stem chosen at this moment | LOW | Click `@click.argument("name", default=None, required=False)`; no existing workflows break when name is omitted |
| Name stored in `state.json` during recording | `meet stop` reads `state.json` to build metadata; the handoff only works if name is in state | LOW | Add `"name": name` to the dict in `record.py` lines 52–58; `None` when no name given |
| Name stored in `metadata/{stem}.json` at `meet stop` | The name must be durable for all downstream commands (`meet list`, `meet summarize`) to use | LOW | `stop.py` already does a read-merge-write on metadata; add `meta["name"] = existing.get("name")` from state — but only when non-None |
| Slug-prefixed output filenames when name is given | Files should be discoverable by name at the filesystem level, not by opaque UUID; this is the primary filesystem payoff | MEDIUM | `get_recording_path()` must accept optional `slug: str \| None`; prefix as `{slug}-{timestamp}-{8hex}.wav`; slug generated once in `record.py` via `python-slugify` before calling `start_recording()` |
| `start_recording()` accepts and threads through the slug | The path is computed inside `start_recording()`, so the slug cannot be computed there — it must be passed in | LOW | Add `slug: str \| None = None` parameter to `start_recording()`; pass it through to `get_recording_path()` |
| `meet list` shows stored name as title when present | The primary UX payoff — "1:1 with Gabriel" instead of `20260322-143000-abc12345` | LOW | `_derive_title()` in `list.py`: check `meta.get("name")` first; existing fallback chain (`notes heading → stem`) unchanged |
| Notion page title uses stored name when present | The Notion page should reflect the user's intent, not an LLM guess | LOW | `summarize.py` line 150–151: read `session_metadata.get("name")` before calling `extract_title()`; if name exists, use it as title directly; only fall back to LLM heading when name is absent |
| Backward compatibility: all unnamed sessions unchanged | 208 tests pass today; none of them provide a name; all must continue to pass | LOW | Every code path treats `name=None` and `slug=None` as no-op; `get_recording_path()` without slug produces identical output to current |

### Differentiators (Nice-to-Haves, Build Only If Time Allows)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Separate "Name" column in `meet list` Rich table | Makes it visually explicit that the displayed title is user-provided, not LLM-derived | LOW | One additional column in the Rich table; only populated when `meta.get("name")` is set; fits within current table structure |
| `--session NAME` substring match in `meet transcribe` / `meet summarize` | Users can reference sessions by human name instead of memorizing stems | MEDIUM | Requires modifying session resolution in both `transcribe.py` and `summarize.py`; risk of ambiguity when multiple sessions share a name prefix; must handle "multiple matches" gracefully |

### Anti-Features (Explicitly Exclude from v1.2)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| `meet rename SESSION NEW_NAME` | Correct a name given at record time | Requires atomically renaming files across four directories (`recordings/`, `transcripts/`, `notes/`, `metadata/`) plus updating cross-references in metadata JSON; one filesystem failure mid-rename corrupts the session | Accept that names are set at record time; sessions are cheap to redo |
| Tagging or category system | Group meetings by project, person, or topic | Introduces a new data dimension requiring query logic; defeats the simplicity of flat JSON metadata; correct long-term answer is `meet list --search KEYWORD` (a v2 candidate already documented) | Defer to v2 `--search` flag |
| `NAME` as required argument (not optional) | Consistent filename format | Breaks every existing script and workflow that calls `meet record` with no args; violates the principle of least surprise | Optional arg with `default=None` |
| `--name NAME` as a named flag instead of positional | Explicit flag is "cleaner" | `meet record "1:1 with Gabriel"` reads more naturally; positional-at-creation is the pattern in tmux (`new -s name`), git worktree, screen sessions | Positional arg |
| Slug as sole identifier (removing timestamp+UUID suffix) | Shorter, cleaner filenames | Two recordings of "Eng standup" on different days produce a collision; both sessions destroyed | Slug as prefix, timestamp+UUID as suffix — always |
| Custom slug normalization rules | Exact character mapping fidelity | `python-slugify` handles all Unicode and punctuation correctly; custom rules add maintenance burden with no user benefit | Accept `python-slugify` defaults (separator=`-`, max_length=40) |
| Propagating name back into Notion after rename | Cross-tool sync | Notion has no concept of "update by external ID"; implementing a Notion page update would require storing and using the page ID; the current tool is append-only toward Notion | Users update Notion pages directly if needed |

---

## Name vs. Slug: The Core Design Decision

**Two distinct things, never conflated:**

- **`name`** (human-readable): stored verbatim in `metadata/{stem}.json` as `"name"`. Examples: `"1:1 with Gabriel"`, `"Q1 Roadmap Review"`. This is what users see in `meet list` and what becomes the Notion page title.
- **`slug`** (filesystem artifact): derived once at record-time via `python-slugify`. Used exclusively as the filename prefix. Example: `1-1-with-gabriel`. Never displayed to users directly.

**Why compute slug at record time, not derived from name later?** The slug is baked into the filename. If it were re-derived later from the stored name, any change to slugify behavior or settings would create a mismatch between the stored filename and the derived slug. Compute once, embed in stem, never re-derive.

**Why keep timestamp+UUID suffix?** Two reasons: (1) collision prevention — two "Eng standup" recordings must not overwrite each other; (2) sort-by-mtime behavior in `meet list` is preserved because the timestamp is embedded in the stem.

**Slug generation specifics:** `python-slugify` 8.x, `separator="-"`, `max_length=40`. The 40-character cap ensures the full stem (`{40-char-slug}-{15-char-timestamp}-{8-char-uuid}` = 65 chars + `.wav` = 69 chars) stays well under the 255-byte macOS filename limit.

---

## Feature Dependencies

```
[meet record NAME argument]
    └──generates──> [slug via python-slugify]
    |                   └──passed to──> [start_recording(slug=slug)]
    |                                       └──passed to──> [get_recording_path(slug=slug)]
    |                                                           └──produces──> [{slug}-{timestamp}-{8hex}.wav stem]
    |                                                                              └──propagates to──> [transcripts/{stem}.txt]
    |                                                                              └──propagates to──> [transcripts/{stem}.srt]
    |                                                                              └──propagates to──> [notes/{stem}-{template}.md]
    |                                                                              └──propagates to──> [metadata/{stem}.json]
    |
    └──writes──> ["name" in state.json]
                     └──read by meet stop──> ["name" in metadata/{stem}.json]
                                                 └──read by meet list──> [title column shows name]
                                                 └──read by meet summarize──> [Notion page title = name]
```

### Dependency Notes

- **Slug must be computed in `record.py`, not in `start_recording()`:** `start_recording()` is an audio service function; slug is a CLI concern. The slug is computed before the call, passed as an argument.
- **`start_recording()` signature change:** Adding `slug: str | None = None` is backward-compatible — all existing callers (and tests) that pass no slug argument continue to work.
- **`get_recording_path()` signature change:** Adding `slug: str | None = None` is backward-compatible. When `slug=None`, output is identical to today.
- **Name flows via `state.json`:** The `record.py` → `stop.py` handoff is exclusively through `state.json`. Name must be written there at record time or `meet stop` cannot access it.
- **All downstream commands inherit the stem:** `meet transcribe --session` and `meet summarize --session` use the stem for file lookups. Named stems are longer but otherwise identical in behavior.
- **`python-slugify` is a new dependency:** Must be added to `pyproject.toml` `[project.dependencies]`. No known conflicts with the current dependency set.

---

## Backward Compatibility

**Filename stems:** Old sessions use `{YYYYMMDD-HHMMSS}-{8hex}`. New named sessions use `{slug}-{YYYYMMDD-HHMMSS}-{8hex}`. Both are unique, both sort correctly, both work as `--session` values — the resolution is exact filename match and nothing changes there.

**`meet list` title derivation:** Current chain: `notes heading → stem`. New chain: `stored name → notes heading → stem`. Sessions without `"name"` in metadata return the same result as today.

**`meet summarize` Notion title:** Current: `extract_title(notes, fallback_ts)`. New: `session_metadata.get("name") or extract_title(notes, fallback_ts)`. Sessions without `"name"` in metadata produce identical Notion titles to today.

**Metadata JSON:** Old session files simply have no `"name"` key. All new code reads `meta.get("name")` which returns `None` — fallback paths activate, behavior is identical to today.

**Tests:** All 208 existing tests call `record()` without a name argument. The optional positional arg with `default=None` means every test continues to exercise the no-name code path unchanged.

---

## MVP Definition (v1.2)

### Build in v1.2 (All Table Stakes)

- [ ] `meet record [NAME]` — optional positional Click argument
- [ ] Name stored in `state.json` at record time (key: `"name"`)
- [ ] Name stored in `metadata/{stem}.json` at `meet stop`
- [ ] `get_recording_path()` accepts `slug: str | None = None` parameter
- [ ] `start_recording()` accepts and threads `slug` to `get_recording_path()`
- [ ] `record.py` computes slug via `python-slugify` before calling `start_recording()`
- [ ] `meet list` `_derive_title()` checks `meta.get("name")` before existing fallbacks
- [ ] `meet summarize` uses `session_metadata.get("name")` as Notion title when present
- [ ] `python-slugify` added to `pyproject.toml` dependencies
- [ ] All 208 existing tests continue to pass

### Defer to v2.0

- [ ] `meet rename` — post-hoc rename (high complexity, multi-directory atomic rename required)
- [ ] `--session NAME` substring/fuzzy match — useful but not needed for core value
- [ ] Tagging or categories — over-engineering for a personal CLI tool

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `meet record [NAME]` positional arg | HIGH | LOW | P1 |
| Name in `state.json` | HIGH | LOW | P1 |
| Name in `metadata/{stem}.json` | HIGH | LOW | P1 |
| `get_recording_path()` slug parameter | HIGH | LOW | P1 |
| `start_recording()` slug threading | HIGH | LOW | P1 |
| Slug-prefixed output filenames | HIGH | MEDIUM | P1 |
| `meet list` shows name as title | HIGH | LOW | P1 |
| Notion title uses stored name | HIGH | LOW | P1 |
| Backward compat: unnamed sessions unchanged | HIGH | LOW | P1 |
| Separate Name column in `meet list` | LOW | LOW | P2 |
| `--session NAME` substring match | MEDIUM | MEDIUM | P3 |
| `meet rename` | LOW | HIGH | Defer |
| Tagging system | LOW | HIGH | Defer |

---

## Touch Map: Files That Must Change

This is derived from dependency analysis — not speculation.

| File | Change Required | Risk |
|------|----------------|------|
| `core/storage.py` | Add `slug: str \| None = None` to `get_recording_path()`; prepend slug to filename when provided | LOW — purely additive |
| `services/audio.py` | Add `slug: str \| None = None` to `start_recording()`; pass to `get_recording_path()` | LOW — one parameter added |
| `cli/commands/record.py` | Add positional arg; compute slug; pass to `start_recording()`; store `"name"` in state dict | LOW — isolated to this file |
| `cli/commands/stop.py` (`stop` command) | Read `"name"` from `existing` state dict; write to metadata when non-None | LOW — one additional field in merge |
| `cli/commands/list.py` | Update `_derive_title()` to check `meta.get("name")` first | LOW — one additional condition |
| `cli/commands/summarize.py` | Read `session_metadata.get("name")`; use as Notion title when present | LOW — one additional condition before existing title logic |
| `pyproject.toml` | Add `python-slugify>=8.0.0` to `[project.dependencies]` | LOW — stable library, no known conflicts |

Files that do NOT need changes: `transcribe.py`, `notion.py`, `state.py`, `health_check.py`, `checks.py`, `llm.py`, `transcription.py`, `ui.py`, `main.py`, all template files.

---

## Sources

- Direct inspection: `meeting_notes/cli/commands/record.py` — confirmed no name arg exists
- Direct inspection: `meeting_notes/cli/commands/stop.py` — confirmed state dict fields written to metadata
- Direct inspection: `meeting_notes/core/storage.py` — confirmed `get_recording_path()` signature and stem format
- Direct inspection: `meeting_notes/services/audio.py` — confirmed `start_recording()` calls `get_recording_path(config.storage_path)`
- Direct inspection: `meeting_notes/cli/commands/list.py` — confirmed `_derive_title()` chain (notes heading → stem, no name key)
- Direct inspection: `meeting_notes/cli/commands/summarize.py` — confirmed Notion title via `extract_title(notes, fallback_ts)`, no name key
- [python-slugify on PyPI](https://pypi.org/project/python-slugify/) — v8.0.4, handles Unicode, pure Python, stable
- tmux `new-session -s NAME` — positional name at creation time precedent
- git worktree naming convention — human name separate from machine identifier precedent

---
*Feature research for: Named recordings in meeting-notes CLI (v1.2)*
*Researched: 2026-03-27*
