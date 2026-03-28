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

<details>
<summary>🚧 v1.2 Named Recordings (Phases 02-05) — IN PROGRESS</summary>

- [ ] Phase 02: Storage foundation — `slugify()` pure function + `get_recording_path_with_slug()` (SLUG-01, SLUG-02, RECORD-05)
  **Plans:** 1 plan
  Plans:
  - [ ] 02-01-PLAN.md — TDD slugify() and get_recording_path_with_slug() pure functions
- [ ] Phase 03: Record/Stop command — `meet record [NAME]` argument, name/slug in state.json and metadata JSON (RECORD-01–04)
- [ ] Phase 04: `meet list` display — title derived from `recording_name` before LLM-heading fallback (LIST-01, LIST-02)
- [ ] Phase 05: Notion title integration — page title uses `recording_name` before `extract_title()` fallback (NOTION-01)

</details>

---

## Progress

| Phase | Milestone | Plans | Status   | Completed  |
|-------|-----------|-------|----------|------------|
| 1-6. v1.0 MVP phases | v1.0 | 16/16 | Complete | 2026-03-24 |
| 01. SRT + Speaker Diarization | v1.1 | 5/5 | Complete | 2026-03-28 |
| 02. Storage Foundation | v1.2 | 0/1 | Complete    | 2026-03-28 |
| 03. Record/Stop Command | v1.2 | 0/? | Pending | — |
| 04. meet list Display | v1.2 | 0/? | Pending | — |
| 05. Notion Title | v1.2 | 0/? | Pending | — |

---
