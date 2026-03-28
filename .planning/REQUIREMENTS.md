# Requirements: meeting-notes v1.2 Named Recordings

**Defined:** 2026-03-28
**Core Value:** A developer can run `meet record`, stop it, and get structured notes in Notion — all without touching the internet or installing meeting bots.

## v1.2 Requirements

### Recording

- [x] **RECORD-01**: `meet record [NAME]` accepts an optional positional NAME argument; unnamed invocation is unchanged
- [x] **RECORD-02**: NAME is stored verbatim in `state.json` at record time (field: `recording_name`)
- [x] **RECORD-03**: Slug is computed from NAME at record time (`{slug}-{timestamp}-{uuid8}`) and stored as `recording_slug` in `state.json`
- [x] **RECORD-04**: `meet stop` propagates `recording_name` and `recording_slug` from `state.json` to the session metadata JSON before clearing state
- [x] **RECORD-05**: Named output files use `{slug}-{timestamp}-{uuid8}` stem (WAV, TXT, SRT); unnamed sessions retain existing `{timestamp}-{uuid8}` stem — no collision possible

### Slugification

- [x] **SLUG-01**: `slugify(text)` is a pure function in `core/storage.py`; handles colons (`1:1` → `1-1`), Unicode accents, slashes, whitespace runs, leading/trailing hyphens, max 80 chars, and all-punctuation/empty input (fallback: `"untitled"`)
- [x] **SLUG-02**: Slugification uses Python stdlib only (`unicodedata` + `re`) — zero new dependencies

### List Display

- [ ] **LIST-01**: `meet list` derives the session title from `meta.get("recording_name")` before the existing LLM-heading / stem fallback
- [ ] **LIST-02**: Unnamed sessions and pre-v1.2 sessions (no `recording_name` field) display exactly as they do today — no regressions

### Notion

- [ ] **NOTION-01**: `meet summarize` uses `meta.get("recording_name")` as the Notion page title before `extract_title()` fallback; unnamed and pre-v1.2 sessions are unaffected

## v2 Requirements

### Session Resolution

- **SESSRES-01**: `meet transcribe --session NAME` and `meet summarize --session NAME` accept a human-readable name (slug-prefix glob match) in addition to the exact stem — deferred because exact stem still works with the full slug-prefixed stem

### List

- **LIST-03**: Dedicated "Name" column in `meet list` output showing user-provided name distinct from derived title — deferred; low ROI for narrow table width

## Out of Scope

| Feature | Reason |
|---------|--------|
| `meet rename SESSION NEW_NAME` | Multi-directory atomic rename, high complexity, low ROI for a personal tool |
| Tagging / categories | Introduces query complexity; defeats flat-JSON-metadata simplicity |
| NAME as required argument | Breaks every existing `meet record` invocation — anti-feature |
| `python-slugify` dependency | Text-unidecode GPL transitive dep; stdlib covers all realistic Latin/ASCII meeting names |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SLUG-01 | Phase 02 | Complete |
| SLUG-02 | Phase 02 | Complete |
| RECORD-05 | Phase 02 | Complete |
| RECORD-01 | Phase 03 | Complete |
| RECORD-02 | Phase 03 | Complete |
| RECORD-03 | Phase 03 | Complete |
| RECORD-04 | Phase 03 | Complete |
| LIST-01 | Phase 04 | Pending |
| LIST-02 | Phase 04 | Pending |
| NOTION-01 | Phase 05 | Pending |

**Coverage:**
- v1.2 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-28 after initial definition*
