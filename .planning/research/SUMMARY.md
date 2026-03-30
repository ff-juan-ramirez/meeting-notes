# Project Research Summary

**Project:** meeting-notes CLI — v1.2 Named Recordings
**Domain:** Local meeting audio capture + transcription + LLM note generation CLI (macOS/Apple Silicon)
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

The v1.2 Named Recordings milestone is a tightly scoped additive feature on an already-working Python CLI tool. The core insight from all four research streams is the same: this feature touches a data pipeline where one command writes state that the next command reads, and every consumer of that data must be updated consistently or the name will silently disappear partway through the flow. The changes are individually small (one new stdlib function, two new JSON fields, four command files modified), but they must be implemented in the correct dependency order with tests at each layer to avoid silent data loss.

The recommended approach is zero new dependencies: slugification is achievable with Python stdlib `unicodedata` + `re`, and the existing Click 8.x `@click.argument(required=False)` pattern handles the optional positional argument cleanly. The filename strategy is `{slug}-{timestamp}-{uuid8}` — slug as human-readable prefix, existing timestamp+uuid suffix preserved for collision safety. The `name` field (raw user string) is stored in `state.json` at record time and propagated to the session metadata JSON at stop time, making it available to all downstream commands without further coordination.

The primary risk is silent failure: name not propagated from `state.json` to metadata, `meet list` not checking the `name` field before LLM-heading fallback, or Notion title continuing to use `extract_title()` without checking metadata first. All of these failures produce incorrect behavior with no error — the tool continues working but ignores the user's intent. The mitigation is consistent use of `meta.get("name")` with explicit fallback chains, integration tests that cover the full record → stop → list → summarize flow, and a dedicated backward-compatibility test fixture using pre-v1.2 metadata JSON.

## Key Findings

### Recommended Stack

The v1.2 milestone requires zero new dependencies. The existing stack (mlx-whisper, Ollama HTTP API, notion-client, Click 8.x, Rich 13.x) handles everything. Slugification uses Python stdlib `unicodedata.normalize` + `re.sub` — a 10-line function in `core/storage.py`. The `@click.argument("name", required=False, default=None)` pattern is native to Click 8.x and is the idiomatic choice when the argument is the command's primary subject rather than a modifier flag.

One note on the slug library decision: FEATURES.md initially suggested `python-slugify` (8.0.4), but STACK.md overrides this with a tested stdlib implementation, citing the `text-unidecode` GPL transitive dependency as a licensing concern. For the Latin/ASCII meeting names this tool will realistically encounter, the 10-line stdlib function produces identical output. If non-Latin Unicode coverage is needed later, `python-slugify[unidecode]` can replace the body of `slugify()` with no interface change.

**Core technologies:**
- `unicodedata` + `re` (stdlib): slugification — no new dependency, tested against all realistic edge cases
- `@click.argument(required=False)`: optional positional NAME argument — idiomatic, faster to type than `--name` flag
- `state.json` + session metadata JSON: name/slug persistence — existing read-merge-write pattern extended with two new optional fields
- `meta.get("name")`: name consumption — `.get()` with fallback is the established pattern throughout the codebase

### Expected Features

The feature scope for v1.2 is intentionally narrow. All table-stakes features are low-to-medium complexity and require changes to 5 files total. The "nice to have" differentiators are explicitly deferred to keep the milestone clean.

**Must have (table stakes):**
- `meet record [NAME]` optional positional argument — the only natural UX moment to name a session; must not break unnamed workflows
- `name` stored in `state.json` at record time — required for `meet stop` to receive the name (stop has no CLI context of its own)
- `name` stored in session metadata JSON at stop time — required for all downstream commands; must survive `clear_state()` in stop
- Slug-prefixed output filenames (`{slug}-{timestamp}-{uuid8}`) — makes recordings discoverable by name in the filesystem
- `meet list` shows stored name as title (before LLM-heading fallback) — primary UX payoff of the milestone
- Notion page title uses stored name (before `extract_title()` fallback) — ensures Notion reflects user intent, not LLM output
- Backward compatibility: unnamed sessions and pre-v1.2 metadata work identically to today

**Should have (competitive):**
- Separate Name column in `meet list` (distinct from derived Title) — shows user-intent vs. LLM output side-by-side; LOW complexity

**Defer (v2+):**
- `--session NAME` substring/fuzzy match — useful but not blocking; current `--session STEM` still works with the full slug-prefixed stem
- `meet rename SESSION NEW_NAME` — requires atomic multi-file rename across four directories; high complexity, low ROI for a personal tool
- Tagging/categories system — introduces query complexity; defeats flat-JSON-metadata simplicity

### Architecture Approach

The architecture change is additive and follows the established patterns of the existing codebase. A new `slugify()` function and `get_recording_path_with_slug()` are added to `core/storage.py` alongside the existing `get_recording_path()` (which is not modified). The `audio.py` service layer gains an optional `slug` parameter that routes to one of the two path functions. Four command files (`record.py`/`stop`, `list.py`, `summarize.py`) are updated to write or read the two new optional JSON fields. All other modules are untouched.

The data flow is strictly linear: `record` writes → `stop` reads state and writes metadata → all downstream commands read metadata. No circular dependencies, no new service abstractions needed.

**Major components:**
1. `core/storage.py` — new `slugify()` pure function + `get_recording_path_with_slug()` sibling; no changes to existing functions
2. `services/audio.py` — optional `slug` parameter routes to named or unnamed path generation
3. `cli/commands/record.py` (record + stop) — writes `name`/`slug` to state; stop propagates to metadata before clearing state
4. `cli/commands/list.py` — `_derive_title()` checks `meta.get("name")` before existing H1/stem fallback
5. `cli/commands/summarize.py` — Notion title uses `meta.get("name")` before `extract_title()` fallback

### Critical Pitfalls

1. **Filename collision on same-name recordings** — using slug alone (without timestamp+uuid suffix) means two recordings named "1:1 with Gabriel" silently overwrite each other. Prevention: always use `{slug}-{timestamp}-{uuid8}` and add a test recording two sessions with the same name back-to-back.

2. **Name lost between `record` and `stop`** — `meet stop` currently extracts only specific fields from `state.json`; a developer can add `name` to state but forget to propagate it in stop. Prevention: explicitly copy `name` from `existing` (state) to metadata dict in `stop`, before `clear_state()` is called; write a record→stop→metadata integration test.

3. **Backward compatibility on pre-v1.2 sessions** — all existing metadata JSONs have no `name` field; any code using `meta["name"]` (not `.get("name")`) will KeyError. Prevention: every consumer uses `meta.get("name")` with fallback; include a test fixture using a pre-v1.2 metadata JSON through every affected command.

4. **Slugification edge cases producing invalid/empty filenames** — naive slugify (space→hyphen only) passes `1:1 with Gabriel` through with a colon, which is filesystem-valid on macOS but breaks shell scripts. Unicode input, empty strings, and all-punctuation inputs must also be handled. Prevention: implement the full NFKD + ASCII + lowercase + regex pipeline with a `max_length` cap and `"untitled"` fallback; test with the edge-case matrix from PITFALLS.md.

5. **Notion title ignores session name** — `summarize.py` uses `extract_title()` driven by LLM-generated H1; without an explicit check of `meta.get("name")` first, the user's named session produces a Notion page titled "Meeting Notes" or similar. Prevention: two-line fix in `summarize.py`; test that `create_page` is called with `title=session_name` for named sessions.

## Implications for Roadmap

Based on the dependency graph established in ARCHITECTURE.md and the phase-to-pitfall mapping in PITFALLS.md, the build order is clear. The storage layer must be locked first because every other phase builds on its contracts. Then the audio service, then the record/stop command pair (which must stay together since they share state file logic), then the independent downstream consumers.

### Phase 1: Storage Foundation + Core Data Model

**Rationale:** `slugify()` and `get_recording_path_with_slug()` are pure functions with no external dependencies — they can be built and fully tested in isolation. All 5 critical pitfalls (collision safety, edge-case slugification, backward-compat schema, name propagation contract) have their prevention roots here. Nothing else can be built reliably until this layer is locked.

**Delivers:** A tested `slugify()` function covering all edge cases (colon, unicode, empty, all-spaces, 200-char, all-punctuation); a `get_recording_path_with_slug()` function that preserves the `{timestamp}-{uuid8}` suffix; schema decisions documented in code (optional `name`/`slug` fields, `.get()` access pattern).

**Addresses:** Slug-prefixed output filenames (FEATURES.md table stakes); collision-safe naming (PITFALLS.md P1, P2).

**Avoids:** Pitfalls P1 (collision), P2 (edge cases), P4 (backward compat — `.get()` pattern established at foundation).

### Phase 2: Audio Service + Record/Stop Command

**Rationale:** `audio.py` is the next dependency in the chain; its `start_recording(config, slug=None)` signature must be stable before `record.py` calls it. Record and stop must be built together because they share state-file helpers and the name-propagation handoff (`record` writes state, `stop` reads it and writes metadata) must be tested as a unit.

**Delivers:** `meet record [NAME]` accepts an optional name; slug is computed and stored in `state.json`; `meet stop` propagates `name` and `slug` to the session metadata JSON before clearing state. Full record→stop→metadata integration test confirms name survives the handoff.

**Addresses:** `meet record [NAME]` positional argument, name in state.json, name in session metadata JSON (FEATURES.md P1s).

**Avoids:** Pitfall P3 (name lost between record and stop), P4 (backward compat — unnamed sessions hit `slug=None` path and are unchanged).

### Phase 3: `meet list` Display

**Rationale:** `_derive_title()` change is a 3-line addition with no risk of breaking the audio/record pipeline. It can be implemented and verified independently after Phase 2 produces metadata with the `name` field. This is the primary visible UX payoff.

**Delivers:** `meet list` shows the human-readable name ("1:1 with Gabriel") as title for named sessions, falls back to existing LLM-heading/stem logic for unnamed and pre-v1.2 sessions. Backward-compat fixture test: pre-v1.2 metadata runs through `_derive_title()` without crash.

**Addresses:** `meet list` shows name as title, backward compatibility for unnamed sessions (FEATURES.md table stakes).

**Avoids:** Pitfall P7 (`meet list` ignoring name field), P4 (pre-v1.2 fixture test).

### Phase 4: Notion Title Integration

**Rationale:** The lowest-risk change in the milestone — two lines in `summarize.py`. Gated behind existing Notion configuration, so it only affects users who have Notion set up. Placed last because it has the least impact on the core feature flow and can be verified independently.

**Delivers:** `meet summarize` on a named session produces a Notion page titled with the user-provided name rather than the LLM-generated H1. Unnamed and pre-v1.2 sessions continue to use `extract_title()` as before.

**Addresses:** Notion page title uses stored name (FEATURES.md table stakes).

**Avoids:** Pitfall P6 (Notion title ignoring session name).

### Phase Ordering Rationale

- **Storage first:** `slugify()` and `get_recording_path_with_slug()` are the root dependency for every other phase. Testing them in isolation reduces debugging surface area when building the command layer.
- **Record+stop together:** These two commands in the same file share `_get_state_path()` and `_get_config_path()`; separating them into different phases creates merge complexity. The name-propagation contract (record writes, stop reads) must be tested end-to-end as a unit.
- **List before Notion:** Both are independent after Phase 2, but `meet list` is the higher-frequency user interaction and the most visible UX win. Notion title is a low-touch, low-risk change that can come last.
- **No phase requires research during planning:** All four phases have well-established patterns in the existing codebase (read-merge-write metadata, `.get()` fallback, stem-based resolution). The build order is dictated entirely by the dependency graph, which is explicit in source code.

### Research Flags

Phases with standard patterns (no phase-level research needed):
- **Phase 1 (Storage):** Pure functions with no external dependencies; stdlib patterns are well-established.
- **Phase 2 (Record/Stop):** Follows existing Click argument and state.json patterns already in the codebase.
- **Phase 3 (List):** Three-line addition to an existing function; pattern is established in `_derive_title()` itself.
- **Phase 4 (Notion):** Two-line addition; pattern is established in `summarize.py` where `session_metadata` is already loaded.

No phases require `/gsd:research-phase` during planning. All implementation decisions have been resolved at the research stage.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Stdlib slugify tested locally against all PROJECT.md edge cases; Click `required=False` confirmed in official docs and issue tracker; zero new dependencies validated |
| Features | HIGH | Based on direct codebase inspection of all affected command files; scope is narrow and well-bounded |
| Architecture | HIGH | All five commands read directly; dependency graph traced through source; data flow verified end-to-end |
| Pitfalls | HIGH | Grounded in actual code paths (record.py lines cited); failure modes are concrete, not speculative |

**Overall confidence:** HIGH

### Gaps to Address

- **Slug resolution for `--session` flag (P5):** PITFALLS.md documents a UX gap where `meet transcribe --session 1-1-with-gabriel` fails because `resolve_wav_by_stem()` does an exact match. FEATURES.md classifies `--session NAME` substring match as a P3 "should have" deferred to after the core milestone. The roadmapper should decide whether to include glob-prefix resolution in the v1.2 scope or defer it. If included, it belongs in Phase 2 alongside the record/stop work (the resolver is a shared utility). If deferred, document the limitation in the milestone notes.
- **Empty/whitespace name validation:** PITFALLS.md flags that `meet record "   "` silently producing an `untitled` session is a poor UX. The roadmapper should decide whether Phase 2 includes explicit CLI-level validation (warn and exit, or warn and continue as unnamed). This is a small addition to `record.py` but affects the test suite.
- **`meet list --json` schema stability:** PITFALLS.md recommends that old sessions output `"name": null` (key present, value null) rather than omitting the key. This is a schema contract decision that should be explicit in Phase 3 acceptance criteria.

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `meeting_notes/cli/commands/record.py`, `stop`, `transcribe.py`, `summarize.py`, `list.py`, `core/storage.py`, `core/state.py`, `services/audio.py`, `services/notion.py` — all architecture and pitfall findings are grounded in actual source
- [Click Arguments documentation](https://click.palletsprojects.com/en/stable/arguments/) — `required=False` pattern for optional positional arguments
- [pallets/click issue #94](https://github.com/pallets/click/issues/94) and [#3045](https://github.com/pallets/click/issues/3045) — optional positional argument support confirmed
- Local Python 3.14 test — stdlib slugify verified against PROJECT.md examples and 6 edge cases
- Python `unicodedata` stdlib documentation — NFKD normalization for accent folding

### Secondary (MEDIUM confidence)
- [python-slugify on PyPI](https://pypi.org/project/python-slugify/) — v8.0.4 dependency tree and licensing; confirmed `text-unidecode` GPL transitive dep
- [unicode-slugify Snyk health analysis](https://snyk.io/advisor/python/unicode-slugify) — inactive, not recommended
- tmux `new-session -s NAME` and git worktree naming conventions — positional-name-at-creation UX pattern

### Tertiary (LOW confidence)
- macOS HFS+/APFS colon-in-filename behavior — colons are technically allowed via POSIX API but create shell confusion; confirmed in PITFALLS.md but not independently verified against APFS docs

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
