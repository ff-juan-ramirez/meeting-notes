# Features Research: meeting-notes

**Domain:** Local meeting transcription + note generation CLI
**Date:** 2026-03-22

---

## 1. Recording Management

### Table Stakes (Must Have)
- `meet record` / `meet stop` basic workflow
- Mix microphone (user voice) + system audio (participants) into single WAV
- State persists to disk (auto-save on crash — don't lose in-progress recording metadata)
- Basic metadata per recording: timestamp, file path, duration
- Status messages on start: show which devices are active

### Differentiators (Nice to Have)
- Resume interrupted recording (append to same file; requires checkpointing last timestamp)
- Pause/resume within a single session (state machine in CLI)
- Silence detection warning: if both audio channels aren't producing signal after 5s, warn

### Anti-Features (Deliberately Exclude)
- Real-time transcription during recording — complexity, doesn't match async batch workflow
- Background daemon — explicit record/stop is simpler and more transparent
- Audio format negotiation — WAV-only per constraint

---

## 2. Output Formats

### Table Stakes (Must Have)
- Three structured note templates:
  - **meeting** (default): Context, Key Points, Decisions Made, Next Steps
  - **minutes**: Attendees, Topics, Discussion, Action Items (formal)
  - **1on1**: Updates, Highlights, Blockers, Feedback, Follow-ups
- Markdown output stored locally
- Notion page creation (automated)
- LLM-generated title per recording

### Differentiators (Nice to Have)
- JSON output (`--format json`) for piping to other tools
- Template customization: users define custom templates in config
- Transcript embedded as collapsible section in Notion page

### Anti-Features (Deliberately Exclude)
- DOCX/PDF export — scope creep; users can export from Notion
- Google Docs integration — focus on Notion
- Audio attachments in Notion — local audio stays local

---

## 3. CLI UX Patterns

### Table Stakes (Must Have)
- Rich progress bars for transcription and summarization (not silent waiting)
- Spinners during long operations
- Clear error messages: missing device, Ollama not running, invalid Notion token
- `--quiet` flag suppresses progress output for scripting
- Config file: `~/.config/meeting-notes/config.json`
- `meet --help` and per-command help with examples
- Sensible defaults: `--template meeting`, configurable output directory

### Differentiators (Nice to Have)
- Shell completion (zsh/bash): `meet [TAB]`
- `--json` output on `meet list` for piping to jq
- `--dry-run` flag for transcription/summarization
- `meet history` (alias for `meet list`)

### Anti-Features (Deliberately Exclude)
- Interactive REPL mode — doesn't match Unix philosophy
- TUI dashboard — scope creep; keep it CLI
- Telemetry/analytics — privacy-first project, no tracking
- Auto-update system — managed via brew/pip

---

## 4. Notion Integration Patterns

### Table Stakes (Must Have)
- One Notion page per `meet summarize` run
- Database properties: Title, Date, Duration, Template Type, Status (Draft/Final)
- Note body: template sections as Notion blocks
- LLM-generated title
- Backlink to local WAV + transcript file path

### Differentiators (Nice to Have)
- Participant extraction: LLM identifies names, stored as multi-select property
- Notion database vs. plain page: user configures which parent to target
- `meet list` shows Notion URL when a page exists

### Anti-Features (Deliberately Exclude)
- Real-time sync — batch is simpler
- Sync back from Notion — high complexity, v2 candidate
- Audio embedding in Notion — privacy concern

---

## 5. `meet list` Feature

### Table Stakes (Must Have)
Per-row metadata:
- Date (YYYY-MM-DD HH:MM)
- Duration (m:ss)
- Auto-generated title (from transcript) or filename
- Status: `not-transcribed` | `transcribed` | `summarized`
- Sort newest-first by default
- `--status` filter
- `--json` output for scripting

### Differentiators (Nice to Have)
- `--since` / `--until` date range filter
- `--search KEYWORD` searches transcript content
- Show Notion URL if page was created
- `--format detailed` shows word count of transcript

### Anti-Features (Deliberately Exclude)
- Database backend (SQLite) — JSON metadata file is sufficient for v1
- Full-text search index — grep on files is sufficient
- Sentiment analysis per meeting — high complexity, low ROI

---

## 6. `meet doctor` Health Check Patterns

### Table Stakes (Must Have)

| Check | What it Validates |
|-------|-------------------|
| BlackHole installed | `brew list blackhole-2ch` or device present in `ffmpeg -f avfoundation -list_devices` |
| ffmpeg device indices | Index `:1` (BlackHole) and `:2` (Mic) are reachable |
| Ollama running | HTTP GET `localhost:11434` returns 200 |
| llama3.1:8b pulled | Model listed in `ollama list` output |
| mlx-whisper installed | `import mlx_whisper` succeeds |
| Whisper model available | Model files present in cache |
| Notion token set | `NOTION_TOKEN` env var is non-empty |
| Notion token valid | Can fetch current user via API |
| Disk space | Warn if < 5GB free |

### Differentiators (Nice to Have)
- `--verbose` flag: shows versions, file sizes, model locations
- Fix suggestions on failure: "Install BlackHole: `brew install blackhole-2ch`"
- `meet doctor --fix` attempts auto-fixes (model download, etc.)

### Anti-Features (Deliberately Exclude)
- Network connectivity check — 100% local tool
- GPU availability check — MLX handles Apple Silicon automatically

---

## Summary

| Category | v1 Scope | v2 Candidates |
|----------|----------|---------------|
| Recording | record/stop, mix, metadata | resume interrupted, pause/resume |
| Output | 3 templates, Markdown, Notion | JSON export, custom templates |
| CLI UX | Rich progress, errors, config | shell completion, dry-run |
| Notion | page creation, properties, title | participant extraction, bulk ops |
| List | list with status, JSON output | search, date filter, Notion URL |
| Doctor | all prerequisite checks | verbose, fix suggestions, repair mode |

---
*Researched: 2026-03-22*
