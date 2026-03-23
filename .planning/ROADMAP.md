# Roadmap: meeting-notes

**Created:** 2026-03-22
**Goal:** A fully working local CLI tool for meeting capture, transcription, LLM note generation, and Notion export — installable from a git repo.

---

## Phase 1: Audio Capture + Health Check Design

**Goal:** Capture meeting audio reliably from two devices using ffmpeg. Design the meet doctor health check architecture that all later phases will build on.

**Why first:** Audio capture is the only truly hardware-dependent phase. Everything else depends on having a valid WAV file. The meet doctor design must happen here because it validates all prerequisites that later phases introduce — architecture decisions here affect every phase.

**Requirements covered:** AUDIO-01 to AUDIO-06, SETUP-01 to SETUP-04 (design + partial impl)

**Plans:** 3/3 plans executed

Plans:
- [x] 01-01-PLAN.md — Project scaffold, core infrastructure (config, storage, state), Wave 0 test stubs
- [x] 01-02-PLAN.md — Audio capture pipeline (process manager, audio service, record/stop commands)
- [x] 01-03-PLAN.md — Health check architecture, Phase 1 checks, meet doctor and meet init commands

**Pitfalls to address in this phase:**
- P1: Validate device at index 1 IS BlackHole (not just any device)
- P2: Add explicit `aresample=16000` before amix in ffmpeg command
- P3: Use SIGTERM (not SIGKILL) for clean WAV header write
- P4: Test recording in `meet init` to trigger mic permission prompt early

**Deliverables:**
- `meet record` starts a real recording (two devices, amix, WAV)
- `meet stop` gracefully terminates ffmpeg
- `meet init` configures the tool from scratch
- `meet doctor` validates Phase 1 prerequisites

---

## Phase 2: Local Transcription

**Goal:** Transcribe a WAV recording to text using mlx-whisper running on Apple Silicon.

**Requirements covered:** TRANS-01 to TRANS-05

**Plans:** 2/3 plans executed

Plans:
- [x] 02-01-PLAN.md — Transcription service + meet transcribe CLI command
- [x] 02-02-PLAN.md — Phase 2 health checks (MlxWhisperCheck, WhisperModelCheck) + pyproject.toml update
- [ ] 02-03-PLAN.md — Gap closure: fix silent exit on fresh system (ensure_dirs + OSError handler)

**Pitfalls to address:**
- P6: `meet doctor` warns if model not cached; shows download command
- P7: Warn user if recording is >90 minutes (memory pressure risk)
- P8: Post-transcription check for empty/short output
- P9: Allow `"whisper": {"language": null}` in config (null = auto, string = forced)

**Deliverables:**
- `meet transcribe` produces a text file from the WAV
- `meet doctor` validates mlx-whisper and model availability

---

## Phase 3: Note Generation

**Goal:** Generate structured meeting notes from a transcript using Ollama llama3.1:8b with three templates.

**Requirements covered:** LLM-01 to LLM-07

**Plans:** 2/3 plans executed

Plans:
- [x] 03-01-PLAN.md — LLM service module, three prompt templates (meeting/minutes/1on1), unit tests, requests dependency
- [x] 03-02-PLAN.md — Ollama health checks (OllamaRunningCheck, OllamaModelCheck), meet doctor registration, tests
- [ ] 03-03-PLAN.md — meet summarize CLI command with session resolution, map-reduce chunking, metadata extension, tests

**Pitfalls to address:**
- P10: `meet doctor` checks Ollama is running; shows `ollama serve` fix
- P11: Map-reduce chunking for transcripts >8K tokens
- P12: 120s timeout on all Ollama HTTP requests
- P13: Log model version in session metadata JSON

**Deliverables:**
- `meet summarize` produces structured notes in three template formats
- Notes saved as local Markdown files
- `meet doctor` validates Ollama availability

---

## Phase 4: Notion Integration

**Goal:** Save generated notes to a Notion page automatically.

**Requirements covered:** NOTION-01 to NOTION-07

**Plans:** 2 plans

Plans:
- [ ] 04-01-PLAN.md — Notion service module (create_page, extract_title, markdown_to_blocks, text splitting, retry logic) + NotionConfig + tests
- [ ] 04-02-PLAN.md — Integrate Notion push into summarize command + NotionTokenCheck/NotionDatabaseCheck health checks + doctor registration + tests

**Pitfalls to address:**
- P14: Split all text into ≤1,900-char blocks before sending to Notion
- P15: Retry with exponential backoff on HTTP 429
- P16: `meet doctor` validates database has required properties
- P17: Full transcript stored locally only; Notion page gets structured notes + local path reference

**Deliverables:**
- `meet summarize` creates a Notion page with the structured notes
- Notion URL stored in session metadata and shown in CLI output
- `meet doctor` validates Notion token and target database

---

## Phase 5: Integrated CLI

**Goal:** Wire all commands into a cohesive CLI with full UX polish.

**Requirements covered:** CLI-01 to CLI-09

### Plans

**5.1 — CLI wiring + meet list**
- Implement `cli/main.py`: Click group registering all commands; `--version` flag; global `--quiet` flag
- Implement `cli/commands/list.py`: `meet list` — scan `metadata/*.json`, display Rich table (date, duration, title, status, Notion URL); `--status` filter; `--json` output without ANSI codes
- Implement session metadata JSON (`metadata/{uuid}.json`): date, duration, wav path, transcript path, notes path, notion_url, template, model_version

**5.2 — UX polish**
- Implement `cli/ui.py`: shared Rich console; spinners, progress bars, panels, error formatting; TTY detection (`sys.stdout.isatty()`) — suppress Rich formatting in non-TTY contexts
- Ensure `--json` on `meet list` produces clean JSON (no ANSI codes regardless of TTY)
- Add consistent error messages across all commands: missing config, missing recording, Ollama down, Notion error

**Pitfalls to address:**
- P18: TTY detection in `cli/ui.py`; `--quiet` flag globally available

**Deliverables:**
- All 5 commands work end-to-end in sequence: `meet record` → `meet stop` → `meet transcribe` → `meet summarize` → `meet list`
- Full UX polish (spinners, progress, errors, TTY-safe output)

---

## Phase 6: Exportable Git Repo

**Goal:** Package the project as a clean, cloneable git repo. Implement `meet doctor` in full — integrating all per-phase health checks. Implement `meet init` wizard completely.

**Requirements covered:** PKG-01 to PKG-03, SETUP-01 to SETUP-06 (full implementation)

### Plans

**6.1 — Full meet doctor**
- Integrate ALL phase health checks into `meet doctor`: Phase 1 (BlackHole, ffmpeg, disk), Phase 2 (mlx-whisper, model cache), Phase 3 (Ollama, model), Phase 4 (Notion token, database properties), Phase 5 (Python version, no openai-whisper conflict)
- Add `--verbose` flag: show versions, file sizes, model locations
- Each failed check shows specific fix suggestion (e.g., "Install BlackHole: `brew install blackhole-2ch`")
- Exit code 1 on any ERROR; exit code 0 on all OK (warnings allowed)

**6.2 — Full meet init wizard**
- Interactive wizard: detect audio devices and present choices, test each device index, collect Notion token + database ID, write config.json, trigger test recording for mic permissions, run `meet doctor` at end to verify setup
- Handle first-time vs. reconfigure flows

**6.3 — Project packaging**
- Finalize `pyproject.toml`: all dependencies pinned, `python_requires = ">=3.11,<3.14"`, entry point `meet`
- Write `README.md`: prerequisites (BlackHole, Audio MIDI Setup config, Ollama, Notion), installation (`pip install .` or `pip install -e .`), quick-start guide, all commands with examples
- Add `.gitignore`: `__pycache__`, `*.pyc`, `.env`, `recordings/`, `transcripts/`, `notes/` (user data stays local)
- Final git cleanup: meaningful commit history, no secrets in repo

**Pitfalls to address:**
- P19: `pyproject.toml` with `python_requires`; doctor checks Python version
- P20: Doctor checks for `openai-whisper` conflict

**Deliverables:**
- Anyone can clone the repo, run `pip install .`, run `meet init`, and use the tool
- `meet doctor` gives a complete system health report across all components
- Clean git history, full README, no user data in repo

---

## Summary

| Phase | What Gets Built | Key Risk |
|-------|----------------|----------|
| 1 | Audio capture + health check architecture | Hardware dependency (BlackHole, devices) |
| 2 | Local transcription (mlx-whisper) | Model download, memory pressure on long recordings |
| 3 | Note generation (Ollama llama3.1:8b) | Context window limits, LLM timeout |
| 4 | Notion integration | API rate limits, block size limits |
| 5 | Integrated CLI + meet list | UX polish, TTY detection |
| 6 | Exportable repo + full meet doctor + meet init | Packaging, first-time setup UX |

---
*Roadmap created: 2026-03-22*
*Last updated: 2026-03-22 after Phase 4 planning*
