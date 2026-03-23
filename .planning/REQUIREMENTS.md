# Requirements: meeting-notes

**Defined:** 2026-03-22
**Core Value:** A developer can run `meet record`, stop it, and get structured notes in Notion — all without touching the internet or installing meeting bots.

---

## v1 Requirements

### Audio Capture

- [x] **AUDIO-01**: `meet record` captures system audio (BlackHole, device index 1) and microphone (device index 2) simultaneously using ffmpeg avfoundation with amix filter, saved as WAV (16kHz, mono, pcm_s16le)
- [x] **AUDIO-02**: `meet stop` gracefully terminates the ffmpeg subprocess (SIGTERM → wait 5s → SIGKILL) and finalizes the WAV file with a valid header
- [x] **AUDIO-03**: Recording state (session ID, PID, output path, start time) is persisted to `~/.config/meeting-notes/state.json` atomically; survives a CLI crash
- [x] **AUDIO-04**: `meet record` fails with a clear error message if already recording (prevents duplicate sessions)
- [ ] **AUDIO-05**: Audio output is saved to `~/.local/share/meeting-notes/recordings/{timestamp}-{uuid}.wav`
- [x] **AUDIO-06**: ffmpeg uses explicit device indices (`:1`, `:2`) — never device names

### Transcription

- [x] **TRANS-01**: `meet transcribe` runs mlx-whisper (mlx-community/whisper-large-v3-turbo) on the last or specified recording and produces a plain text transcript
- [x] **TRANS-02**: Transcript is saved to `~/.local/share/meeting-notes/transcripts/{uuid}.txt`
- [x] **TRANS-03**: `meet transcribe` shows a Rich progress indicator (spinner or progress bar) while running — does not appear frozen
- [x] **TRANS-04**: If transcript is empty or fewer than 50 words, warn the user ("Transcript may be empty — check audio routing")
- [x] **TRANS-05**: Whisper language detection is automatic (no hardcoded language); user can pin language via config

### Note Generation

- [x] **LLM-01**: `meet summarize` generates structured notes from the transcript using Ollama llama3.1:8b via HTTP API (localhost:11434/api/generate)
- [x] **LLM-02**: Three templates are supported: `meeting` (default), `minutes`, `1on1` — selected via `--template` flag
- [x] **LLM-03**: LLM prompt enforces strict grounding: "Base your notes ONLY on what is said in the transcript. Only include decisions and next steps if EXPLICITLY mentioned."
- [x] **LLM-04**: Notes are saved to `~/.local/share/meeting-notes/notes/{uuid}-{template}.md`
- [x] **LLM-05**: All Ollama HTTP requests have a configurable timeout (default: 120s); timeout shows an actionable error message
- [x] **LLM-06**: If transcript exceeds 8,000 tokens, it is chunked, each chunk summarized, then summaries are combined ("map-reduce")
- [x] **LLM-07**: `meet summarize` shows a Rich spinner while waiting for LLM response

### Notion Integration

- [x] **NOTION-01**: `meet summarize` (or `meet summarize --save`) creates a Notion page with the structured notes after generation
- [x] **NOTION-02**: Notion page title is LLM-generated from the transcript summary
- [x] **NOTION-03**: Page content uses template structure as Notion blocks (heading + bullet blocks per section)
- [x] **NOTION-04**: Long text sections are split into ≤1,900-character Notion blocks to avoid API limits
- [x] **NOTION-05**: All Notion API calls include retry logic with exponential backoff on HTTP 429 (rate limiting)
- [x] **NOTION-06**: Notion token and target database/page ID are stored in `~/.config/meeting-notes/config.json`
- [x] **NOTION-07**: `meet summarize` stores the created Notion page URL in the session metadata JSON

### CLI Commands

- [x] **CLI-01**: `meet record` starts a recording session
- [x] **CLI-02**: `meet stop` stops the active recording session
- [x] **CLI-03**: `meet transcribe [--session UUID]` transcribes the last or specified recording
- [x] **CLI-04**: `meet summarize [--template meeting|minutes|1on1] [--session UUID]` generates notes and saves to Notion
- [ ] **CLI-05**: `meet list` displays all recordings with: date, duration, title (or filename), status (not-transcribed / transcribed / summarized), and Notion URL if available
- [ ] **CLI-06**: `meet list` supports `--status` filter and `--json` output flag
- [x] **CLI-07**: All commands display Rich-formatted output with color, spinners, and progress bars
- [x] **CLI-08**: Rich output is suppressed when stdout is not a TTY (piped output is clean)
- [x] **CLI-09**: `--quiet` flag suppresses all progress output for scripting

### Setup & Health Check

- [x] **SETUP-01**: `meet init` wizard collects: Notion token, target database/page ID, audio device indices (with detection help), and writes `config.json`
- [x] **SETUP-02**: `meet init` triggers a short test recording (~1s) to force the macOS microphone permission prompt before the first real meeting
- [x] **SETUP-03**: `meet doctor` checks all prerequisites and reports pass/fail per component with actionable fix suggestions
- [x] **SETUP-04**: `meet doctor` checks: BlackHole device at index 1 is confirmed BlackHole (not just "any device"), ffmpeg device index 2 is reachable, Ollama running + llama3.1:8b pulled, mlx-whisper installed + model cached locally, Notion token set + valid, disk space >5GB
- [x] **SETUP-05**: `meet doctor` checks Python version (>=3.11, <3.14) and warns if `openai-whisper` is installed alongside `mlx-whisper`
- [x] **SETUP-06**: `meet doctor` exits with code 1 if any check fails (ERROR level), code 0 if all pass or only warnings

### Packaging & Distribution

- [ ] **PKG-01**: Project uses `pyproject.toml` (PEP 621) with entry point `meet = "meeting_notes.cli.main:main"`
- [ ] **PKG-02**: Project is a clean git repo with `README.md`, `pyproject.toml`, `.gitignore`
- [ ] **PKG-03**: `README.md` includes prerequisites (BlackHole, Audio MIDI Setup, Ollama, Notion integration setup) and usage examples

---

## v2 Requirements

### Enhanced Recording
- **AUDIO-V2-01**: Resume interrupted recording (append to same WAV file; requires checkpoint)
- **AUDIO-V2-02**: Pause/resume within a single session
- **AUDIO-V2-03**: Silence detection warning (warn if audio channel is silent for >10s)

### Enhanced Notes
- **LLM-V2-01**: Custom user-defined note templates via config file
- **LLM-V2-02**: Participant extraction — LLM identifies speaker names, stored as Notion property

### Enhanced CLI
- **CLI-V2-01**: Shell completion scripts (zsh/bash) via `meet --install-completion`
- **CLI-V2-02**: `meet list --search KEYWORD` — searches transcript content

### Enhanced Notion
- **NOTION-V2-01**: `meet doctor --fix` attempts automatic repairs (model download, schema validation)
- **NOTION-V2-02**: Database schema auto-creation in `meet init` (creates required properties)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cloud transcription (Whisper API, AssemblyAI) | Privacy requirement — 100% local |
| Browser extensions or meeting bots | No injection into call software |
| Windows or Linux support | BlackHole + MLX + avfoundation are macOS/Apple Silicon only |
| Real-time transcription during recording | Complexity; async batch model is correct for this use case |
| Speaker diarization | Not required for v1; high complexity |
| GUI or TUI dashboard | CLI-only by design |
| Google Docs integration | Notion is the designated output; duplicating adds scope |
| Audio attachments in Notion | Local audio stays local (privacy) |
| SQLite database for metadata | JSON metadata files are sufficient for v1 |
| Sync back from Notion | High complexity; v2+ candidate |
| Auto-update system | Managed via pip/brew |
| Telemetry or analytics | Privacy-first project |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDIO-01 to AUDIO-06 | Phase 1 | Pending |
| SETUP-01 to SETUP-06 | Phase 1 (design) + Phase 6 (full impl) | Pending |
| TRANS-01 to TRANS-05 | Phase 2 | Pending |
| LLM-01 to LLM-07 | Phase 3 | Pending |
| NOTION-01 to NOTION-07 | Phase 4 | Pending |
| CLI-01 to CLI-09 | Phase 5 | Pending |
| PKG-01 to PKG-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after initial definition*
