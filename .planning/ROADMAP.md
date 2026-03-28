# Roadmap: meeting-notes

**Goal:** A fully working local CLI tool for meeting capture, transcription, LLM note generation, and Notion export — installable from a git repo.

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-24)

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

---

## Progress

| Phase | Milestone | Plans | Status   | Completed  |
|-------|-----------|-------|----------|------------|
| 1. Audio Capture + Health Check Design | v1.0 | 5/5 | Gap closure | — |
| 2. Local Transcription | v1.0 | 3/3 | Complete | 2026-03-22 |
| 3. Note Generation | v1.0 | 3/3 | Complete | 2026-03-22 |
| 4. Notion Integration | v1.0 | 2/2 | Complete | 2026-03-23 |
| 5. Integrated CLI | v1.0 | 2/2 | Complete | 2026-03-23 |
| 6. Exportable Git Repo | v1.0 | 3/3 | Complete | 2026-03-23 |

### Phase 1: SRT output and speaker diarization for transcription pipeline

**Goal:** Extend `meet transcribe` to produce SRT subtitle files from Whisper segments and add pyannote-audio speaker diarization with graceful fallback. Every transcription produces both `.txt` and `.srt`. Diarized output uses `SPEAKER_XX:` prefixes. `meet summarize` prefers diarized transcripts when available.
**Requirements**: D-01 through D-15 (SRT output, speaker diarization, diarized format, health checks)
**Depends on:** v1.0 MVP
**Plans:** 5 plans (4 complete + 1 gap closure)

Plans:
- [x] 01-00-PLAN.md — Wave 0: Nyquist test stubs for all phase tests (1/4 complete, 2026-03-27)
- [x] 01-01-PLAN.md — SRT generation + transcribe_audio tuple return + CLI wiring
- [x] 01-02-PLAN.md — HuggingFaceConfig + init wizard + pyannote health checks + deps
- [x] 01-03-PLAN.md — Speaker diarization integration + summarize diarized preference
- [x] 01-04-PLAN.md — Gap closure: doctor pyannote checks + init --update flag + pip reinstall

---
*v1.0 shipped 2026-03-24 — see `.planning/MILESTONES.md` for details*
*Next milestone phases will be added here via `/gsd:new-milestone`*
