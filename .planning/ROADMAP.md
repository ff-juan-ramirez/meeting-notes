# Roadmap: meeting-notes

**Goal:** A fully working local CLI tool for meeting capture, transcription, LLM note generation, and Notion export — installable from a git repo.

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-24)
- ✅ **v1.1 SRT + Diarization** — Phase 01 (shipped 2026-03-28)
- 🚧 **v1.2 Named Recordings** — Phases 02-05 (in progress)

---

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-6) — SHIPPED 2026-03-24</summary>

- [x] Phase 1: Audio Capture + Health Check Design (3/3 plans) — completed 2026-03-22
- [x] Phase 2: Local Transcription (3/3 plans) — completed 2026-03-22
- [x] Phase 3: Note Generation (3/3 plans) — completed 2026-03-22
- [x] Phase 4: Notion Integration (2/2 plans) — completed 2026-03-23
- [x] Phase 5: Integrated CLI (2/2 plans) — completed 2026-03-23
- [x] Phase 6: Exportable Git Repo (3/3 plans) — completed 2026-03-23

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>✅ v1.1 SRT Output and Speaker Diarization (Phase 01) — SHIPPED 2026-03-28</summary>

- [x] Phase 01: SRT output and speaker diarization for transcription pipeline (5/5 plans) — completed 2026-03-28

Full details: `.planning/milestones/v1.1-ROADMAP.md`

</details>

## v1.2: Named Recordings — IN PROGRESS

- [x] Phase 02: Storage foundation — completed 2026-03-28 (1/1 plans)
- [ ] Phase 03: Record/Stop command — pending (1 plan)
- [ ] Phase 04: meet list display — pending
- [ ] Phase 05: Notion title integration — pending

### Phase 02: Storage Foundation

**Goal:** Implement `slugify()` pure function and `get_recording_path_with_slug()` in `core/storage.py` using TDD. Zero new dependencies.
**Requirements covered:** SLUG-01, SLUG-02, RECORD-05
**Status:** ✅ Complete (2026-03-28)
**Plans:** 1/1 plans

Plans:
- [x] 02-01-PLAN.md — TDD slugify() and get_recording_path_with_slug() pure functions

### Phase 03: Record/Stop Command

**Goal:** Wire `meet record [NAME]` optional argument, store `recording_name`/`recording_slug` in `state.json` at record time, and propagate both fields to session metadata JSON in `meet stop`.
**Requirements covered:** RECORD-01, RECORD-02, RECORD-03, RECORD-04
**Plans:** 1 plan

Plans:
- [ ] 03-01-PLAN.md — Wire NAME arg through record/stop lifecycle with state and metadata propagation

### Phase 04: meet list Display

**Goal:** Update `meet list` to derive session title from `meta.get("recording_name")` before the existing LLM-heading / stem fallback. Unnamed and pre-v1.2 sessions must display exactly as they do today.
**Requirements covered:** LIST-01, LIST-02

### Phase 05: Notion Title Integration

**Goal:** Update `meet summarize` to use `meta.get("recording_name")` as the Notion page title before `extract_title()` fallback. Unnamed and pre-v1.2 sessions are unaffected.
**Requirements covered:** NOTION-01

---

## Progress

| Phase | Milestone | Plans | Status   | Completed  |
|-------|-----------|-------|----------|------------|
| 1-6. v1.0 MVP phases | v1.0 | 16/16 | Complete | 2026-03-24 |
| 01. SRT + Speaker Diarization | v1.1 | 5/5 | Complete | 2026-03-28 |
| 02. Storage Foundation | v1.2 | 1/1 | Complete    | 2026-03-28 |
| 03. Record/Stop Command | v1.2 | 0/1 | Pending | — |
| 04. meet list Display | v1.2 | 0/? | Pending | — |
| 05. Notion Title | v1.2 | 0/? | Pending | — |

---
