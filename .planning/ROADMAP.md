# Roadmap: meeting-notes

**Goal:** A fully working local CLI tool for meeting capture, transcription, LLM note generation, and Notion export — installable from a git repo. v2.0 adds a native PySide6 desktop GUI that wraps all CLI functionality.

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-24)
- ✅ **v1.1 SRT + Diarization** — Phase 01 (shipped 2026-03-28)
- ✅ **v1.2 Named Recordings** — Phases 02-07 (shipped 2026-03-29)
- 🔄 **v2.0 Native Desktop GUI** — Phases 01-05 (in progress)

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
<summary>✅ v1.2 Named Recordings (Phases 02-07) — SHIPPED 2026-03-29</summary>

- [x] Phase 02: Storage Foundation (1/1 plans) — completed 2026-03-28
- [x] Phase 03: Record/Stop Command (1/1 plans) — completed 2026-03-28
- [x] Phase 04: meet list Display (1/1 plans) — completed 2026-03-28
- [x] Phase 05: Notion Title Integration (1/1 plans) — completed 2026-03-28
- [x] Phase 06: Session ID Column + meet list wiring (1/1 plans) — completed 2026-03-28
- [x] Phase 07: --title flag for Notion page title override (1/1 plans) — completed 2026-03-29

Full details: `.planning/milestones/v1.2-ROADMAP.md`

</details>

### v2.0 Native Desktop GUI

- [x] **Phase 01: GUI Foundation** — MainWindow, sidebar, theme system, template service CRUD, `meet-gui` entry point (completed 2026-03-31)
- [ ] **Phase 02: Sessions & Dashboard** — Session list, detail panel, transcribe/summarize workers, dashboard stats
- [ ] **Phase 03: Record** — RecordWorker, StopWorker, Idle/Recording/Stopping state machine
- [ ] **Phase 04: Templates, Settings & Health Check** — Templates CRUD view, Settings view, DoctorWorker + Doctor view
- [ ] **Phase 05: Polish & Packaging** — Cross-view navigation, error paths, PyInstaller `.app`, DMG installer

---

## Phase Details

### Phase 01: GUI Foundation
**Goal**: The application skeleton launches and navigation works — all 6 screens are reachable via the sidebar, the theme is centralized, and the template service layer supports full CRUD
**Depends on**: Nothing (first v2.0 phase)
**Requirements**: GUI-01, GUI-02, GUI-03, GUI-04, GUI-05, TMPL-01, TMPL-02, TMPL-03, TMPL-04, TMPL-05, TMPL-06
**Success Criteria** (what must be TRUE):
  1. User can run `meet-gui` and see the main window appear in under 2 seconds with no ML import delay
  2. User can click each of the 6 sidebar items (Dashboard, Sessions, Record, Templates, Settings, Health Check) and the view switches correctly
  3. User can run `meet` CLI after the GUI changes and all existing CLI commands work unchanged
  4. Developer can `pip install -e ".[gui]"` to get PySide6, or `pip install -e .` to get CLI only
  5. All colors, fonts, and QSS strings are in `gui/theme.py` — no magic strings in view or widget files
**Plans**: TBD
**UI hint**: yes

### Phase 02: Sessions & Dashboard
**Goal**: Users can browse all past sessions, view details, trigger transcription and summarization from the UI, and see aggregate stats on a dashboard
**Depends on**: Phase 01
**Requirements**: SESS-01, SESS-02, SESS-03, SESS-04, SESS-05, SESS-06, SESS-07, SESS-08, DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. User can open the Sessions view and see a scrollable list of all past sessions with date, duration, title, and status
  2. User can filter the session list by status (All / Recorded / Transcribed / Summarized) and the list updates immediately
  3. User can select a session and transcribe or summarize it from the detail panel while the UI remains responsive (no freeze)
  4. User can see the pipeline step indicator (Recorded → Transcribed → Summarized → Notion) with green fill for completed steps and click the Notion link to open the page in a browser
  5. User can open the Dashboard and see total session counts, sessions this week, the active recording state, and the 5 most recent sessions
**Plans**: 4 plans

Plans:
- [ ] 02-01-PLAN.md -- Test stubs, theme QSS extensions, SessionRowWidget and StatusPill widgets
- [ ] 02-02-PLAN.md -- TranscribeWorker and SummarizeWorker QThread classes
- [ ] 02-03-PLAN.md -- Sessions view full implementation + green tests
- [ ] 02-04-PLAN.md -- Dashboard view, MainWindow navigation wiring, green tests + visual checkpoint

**UI hint**: yes

### Phase 03: Record
**Goal**: Users can start and stop recordings from the GUI using the same underlying service layer as the CLI, with real-time elapsed time display and a clear state machine
**Depends on**: Phase 01
**Requirements**: REC-01, REC-02, REC-03, REC-04, REC-05
**Success Criteria** (what must be TRUE):
  1. User can enter an optional title, click the record button, and see the view transition from Idle to Recording state
  2. User can see elapsed time increment every second while recording is active
  3. User can click Stop and see the view transition through Stopping state before returning to Idle, with the new WAV file visible in Sessions
  4. User can see the configured system device index and mic device index displayed in the Idle state
**Plans**: TBD
**UI hint**: yes

### Phase 04: Templates, Settings & Health Check
**Goal**: Users can manage custom templates, edit all configuration fields, and run health checks with streaming results — all from the GUI
**Depends on**: Phase 01
**Requirements**: TPLV-01, TPLV-02, TPLV-03, TPLV-04, TPLV-05, TPLV-06, SETT-01, SETT-02, SETT-03, SETT-04, DOCT-01, DOCT-02, DOCT-03
**Success Criteria** (what must be TRUE):
  1. User can view all templates in the Templates view with a badge distinguishing built-in from custom, and built-ins show a read-only warning banner with a Duplicate button
  2. User can create, edit, and delete a custom template — name validation rejects names that do not match `^[a-z0-9][a-z0-9-]*$` with an inline error
  3. User can edit every config field in the Settings view, save changes with a success confirmation, or reset to defaults after a confirmation dialog
  4. User can see Notion token and HuggingFace token fields in password echo mode with a show/hide toggle
  5. User can click "Run All Checks" in the Health Check view and watch check result cards appear one by one as each check completes, with colored borders and fix suggestions
**Plans**: TBD
**UI hint**: yes

### Phase 05: Polish & Packaging
**Goal**: The application is shippable — cross-view navigation works end-to-end, error paths surface clean messages, and the app bundles into a self-contained `.app` + DMG installer
**Depends on**: Phase 02, Phase 03, Phase 04
**Requirements**: PKG-01, PKG-02, PKG-03
**Success Criteria** (what must be TRUE):
  1. User can click a session row on the Dashboard and arrive at the Sessions view with that session pre-selected
  2. User can run `pyinstaller build_gui.spec` and get a working `Meeting Notes.app` that launches without a Python installation
  3. User can run `create-dmg` against the built `.app` and receive a distributable `.dmg` file
**Plans**: TBD

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1-6. v1.0 MVP phases | v1.0 | 16/16 | Complete | 2026-03-24 |
| 01. SRT + Speaker Diarization | v1.1 | 1/2 | Complete    | 2026-03-31 |
| 02-07. Named Recordings | v1.2 | 6/6 | Complete | 2026-03-29 |
| 01. GUI Foundation | v2.0 | 0/? | Not started | - |
| 02. Sessions & Dashboard | v2.0 | 0/4 | Planning complete | - |
| 03. Record | v2.0 | 0/? | Not started | - |
| 04. Templates, Settings & Health Check | v2.0 | 0/? | Not started | - |
| 05. Polish & Packaging | v2.0 | 0/? | Not started | - |
