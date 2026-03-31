# Requirements: meeting-notes v2.0

**Defined:** 2026-03-30
**Core Value:** A developer can run `meet record`, stop it, and get structured notes in Notion — all without touching the internet or installing meeting bots.

## v2.0 Requirements

### Foundation & Entry Point

- [x] **GUI-01**: User can launch `meet-gui` and see the main window in < 2 seconds (no ML imports at startup)
- [x] **GUI-02**: User can navigate between all 6 screens via the sidebar (Dashboard, Sessions, Record, Templates, Settings, Health Check)
- [x] **GUI-03**: All visual constants (colors, fonts, QSS) are centralized in `gui/theme.py` — no magic strings in other files
- [x] **GUI-04**: `pyside6>=6.7` is installable as an optional dep: `pip install -e ".[gui]"` — base `pip install -e .` installs CLI only
- [x] **GUI-05**: The `meet` CLI entry point remains unchanged and fully functional after all GUI changes

### Template Service (Core Change)

- [x] **TMPL-01**: `list_templates()` returns all built-in and user-created templates as `{name, path, builtin}` dicts
- [x] **TMPL-02**: `load_template()` checks user templates dir (`~/.config/meeting-notes/templates/`) before built-ins — user templates take precedence
- [x] **TMPL-03**: `save_template(name, content)` writes a `.txt` file to the user templates dir; raises `ValueError` if name collides with a built-in
- [x] **TMPL-04**: `delete_template(name)` removes a user template; raises `ValueError` for built-in names
- [x] **TMPL-05**: `duplicate_template(source_name, new_name)` duplicates any template (built-in or user) to a new user template
- [x] **TMPL-06**: `meet summarize` CLI validates template name via `list_templates()` instead of the hardcoded tuple

### Sessions View

- [ ] **SESS-01**: User can see a scrollable list of all sessions with date, duration, title, and status indicator
- [ ] **SESS-02**: User can filter sessions by status: All / Recorded / Transcribed / Summarized
- [ ] **SESS-03**: User can select a session and see its details: title, date, duration, word count, speaker count, pipeline steps
- [ ] **SESS-04**: User can see the pipeline step indicator (Recorded → Transcribed → Summarized → Notion) with green fill for completed steps
- [ ] **SESS-05**: User can open the Notion URL for a summarized session via a clickable link (`QDesktopServices.openUrl`)
- [ ] **SESS-06**: User can transcribe a session from the detail panel (enabled only if not yet transcribed); UI stays responsive during transcription
- [ ] **SESS-07**: User can summarize a session from the detail panel with template selector and title override; UI stays responsive during summarization
- [ ] **SESS-08**: User can read the transcript, notes, and SRT content in read-only tabs in the detail panel

### Dashboard View

- [ ] **DASH-01**: User can see aggregate stats: total sessions, transcribed count, summarized count, sessions this week
- [ ] **DASH-02**: User can see the last 5 sessions sorted newest-first and click a row to open Sessions view with that session pre-selected
- [ ] **DASH-03**: User can see the active recording state (idle or recording + elapsed time) updated every 2 seconds via `QTimer`
- [ ] **DASH-04**: User can click "Start Recording" on the Dashboard to navigate to the Record view

### Record View

- [ ] **REC-01**: User can start a recording with an optional title (Idle state → Recording state)
- [ ] **REC-02**: User can see elapsed time updating every second while recording (Recording state)
- [ ] **REC-03**: User can stop the recording (Recording state → Stopping state → Idle state)
- [ ] **REC-04**: User can see device info (system device index + mic device index) in the Idle state
- [ ] **REC-05**: Recording creates a WAV file using the existing `meet record` / `meet stop` service layer

### Templates View

- [ ] **TPLV-01**: User can see all templates (built-in and custom) with name and a badge indicating type
- [ ] **TPLV-02**: User can view a built-in template in read-only mode with a "Duplicate" button and yellow warning banner
- [ ] **TPLV-03**: User can create a new custom template with name, description, and prompt body
- [ ] **TPLV-04**: User can edit an existing custom template and save changes
- [ ] **TPLV-05**: User can delete a custom template after a confirmation dialog
- [ ] **TPLV-06**: Template name is validated against `^[a-z0-9][a-z0-9-]*$` with inline error display

### Settings View

- [ ] **SETT-01**: User can edit all config fields: system audio device index, mic device index, Whisper language, Notion token, Notion parent page ID, HuggingFace token, storage path
- [ ] **SETT-02**: User can save settings and see a success confirmation
- [ ] **SETT-03**: User can reset settings to defaults after a confirmation dialog
- [ ] **SETT-04**: Notion token and HuggingFace token fields use password echo mode with a show/hide toggle button

### Health Check View

- [ ] **DOCT-01**: User can run all health checks from the Doctor view and see results stream in as cards (one per check)
- [ ] **DOCT-02**: Each check result card shows: colored left border (green/yellow/red), status icon, check name, message, and fix suggestion if applicable
- [ ] **DOCT-03**: User can re-run a single health check from its card

### Packaging

- [ ] **PKG-01**: `pyinstaller build_gui.spec` produces a working `Meeting Notes.app` bundle (self-contained, no Python installation required)
- [ ] **PKG-02**: `create-dmg` produces a `.dmg` installer from `Meeting Notes.app`
- [ ] **PKG-03**: The built `.app` launches `meet-gui` and all 6 screens function correctly

## Future Requirements (v3.0+)

### CLI Enhancements

- **CLI-01**: Shell completion scripts (zsh/bash) via `meet --install-completion`
- **CLI-02**: `meet list --search KEYWORD` searches transcript content
- **CLI-03**: `meet doctor --fix` attempts automatic repairs (model download, schema validation)

### Advanced Features

- **ADV-01**: Participant extraction — LLM identifies speaker names from diarized transcript, stored as Notion property
- **ADV-02**: Resume interrupted recording (append to same WAV; requires checkpoint mechanism)
- **ADV-03**: `QSystemTrayIcon` for recording status in macOS menu bar

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cloud transcription (OpenAI Whisper API, AssemblyAI) | Privacy requirement — 100% local |
| Browser extensions or meeting bots | No injection into call software |
| Windows or Linux support | macOS + Apple Silicon only (BlackHole, MLX, avfoundation) |
| Real-time transcription during recording | Transcription runs post-recording |
| GUI for `meet init` wizard | CLI wizard is sufficient; Settings view covers config editing |
| SQLite database for metadata | JSON files sufficient |
| Sync back from Notion | High complexity, v3+ candidate |
| Audio attachments in Notion | Local audio stays local (privacy) |
| Replacing the existing CLI | GUI is additive; `meet` CLI must remain unchanged |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GUI-01 | Phase 01 | Complete |
| GUI-02 | Phase 01 | Complete |
| GUI-03 | Phase 01 | Complete |
| GUI-04 | Phase 01 | Complete |
| GUI-05 | Phase 01 | Complete |
| TMPL-01 | Phase 01 | Complete |
| TMPL-02 | Phase 01 | Complete |
| TMPL-03 | Phase 01 | Complete |
| TMPL-04 | Phase 01 | Complete |
| TMPL-05 | Phase 01 | Complete |
| TMPL-06 | Phase 01 | Complete |
| SESS-01 | Phase 02 | Pending |
| SESS-02 | Phase 02 | Pending |
| SESS-03 | Phase 02 | Pending |
| SESS-04 | Phase 02 | Pending |
| SESS-05 | Phase 02 | Pending |
| SESS-06 | Phase 02 | Pending |
| SESS-07 | Phase 02 | Pending |
| SESS-08 | Phase 02 | Pending |
| DASH-01 | Phase 02 | Pending |
| DASH-02 | Phase 02 | Pending |
| DASH-03 | Phase 02 | Pending |
| DASH-04 | Phase 02 | Pending |
| REC-01 | Phase 03 | Pending |
| REC-02 | Phase 03 | Pending |
| REC-03 | Phase 03 | Pending |
| REC-04 | Phase 03 | Pending |
| REC-05 | Phase 03 | Pending |
| TPLV-01 | Phase 04 | Pending |
| TPLV-02 | Phase 04 | Pending |
| TPLV-03 | Phase 04 | Pending |
| TPLV-04 | Phase 04 | Pending |
| TPLV-05 | Phase 04 | Pending |
| TPLV-06 | Phase 04 | Pending |
| SETT-01 | Phase 04 | Pending |
| SETT-02 | Phase 04 | Pending |
| SETT-03 | Phase 04 | Pending |
| SETT-04 | Phase 04 | Pending |
| DOCT-01 | Phase 04 | Pending |
| DOCT-02 | Phase 04 | Pending |
| DOCT-03 | Phase 04 | Pending |
| PKG-01 | Phase 05 | Pending |
| PKG-02 | Phase 05 | Pending |
| PKG-03 | Phase 05 | Pending |

**Coverage:**
- v2.0 requirements: 44 total
- Mapped to phases: 44
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 — traceability filled by roadmapper*
