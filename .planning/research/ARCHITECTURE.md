# Architecture Research: meeting-notes

**Domain:** Local meeting audio capture + transcription + LLM note generation CLI
**Date:** 2026-03-22

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Click CLI Layer                         │
│  ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐         │
│  │  record  │ │  stop  │ │transcribe│ │summarize │ ...     │
│  └─────┬────┘ └───┬────┘ └─────┬────┘ └────┬─────┘         │
└────────┼──────────┼────────────┼────────────┼───────────────┘
         │          │            │            │
         ▼          ▼            ▼            ▼
┌──────────────────────────────────────────────────────────────┐
│                Services Layer (Business Logic)               │
│  ┌─────────┐ ┌───────────────┐ ┌────────┐ ┌────────────┐   │
│  │  audio  │ │ transcription │ │  llm   │ │  notion    │   │
│  └────┬────┘ └──────┬────────┘ └───┬────┘ └─────┬──────┘   │
└───────┼─────────────┼──────────────┼─────────────┼──────────┘
        │             │              │             │
        ▼             ▼              ▼             ▼
┌──────────────────────────────────────────────────────────────┐
│                   Core Layer (Infrastructure)                │
│  ┌────────────┐ ┌─────────┐ ┌────────┐ ┌────────────────┐  │
│  │  process   │ │ storage │ │ state  │ │     config     │  │
│  │  manager   │ │ manager │ │manager │ │                │  │
│  └────────────┘ └─────────┘ └────────┘ └────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            health_check (pluggable checks)            │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
        │             │              │
        ▼             ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│    ffmpeg    │ │  XDG     │ │ config.json  │
│  subprocess  │ │  dirs    │ │  state.json  │
└──────────────┘ └──────────┘ └──────────────┘
```

---

## Data Flow

```
1. meet record
   └─ StateManager.start_recording() → writes session_id to state.json
   └─ ProcessManager.start_ffmpeg() → spawns ffmpeg subprocess
       ffmpeg -f avfoundation -i ":1" -f avfoundation -i ":2"
             -filter_complex "[0:a][1:a]amix=inputs=2:normalize=0[aout]"
             -map "[aout]" -ar 16000 -ac 1 -c:a pcm_s16le -y {timestamp}-{uuid}.wav
   └─ Stores PID in state.json

2. meet stop (explicit or Ctrl+C)
   └─ RecordingSession._signal_handler() catches SIGINT
   └─ ProcessManager.stop_gracefully(pid) → SIGTERM to process group → wait 5s → SIGKILL
   └─ StateManager.stop_recording() → moves active_recording to last_recording

3. meet transcribe [--session SESSION]
   └─ StateManager.load() → resolves session or uses last_recording
   └─ TranscriptionService.transcribe(wav_path) → mlx_whisper.transcribe()
   └─ Writes to ~/.local/share/meeting-notes/transcripts/{uuid}.txt

4. meet summarize [--template meeting|minutes|1on1] [--session SESSION]
   └─ Loads transcript text
   └─ LLMService.generate(template, transcript) → POST localhost:11434/api/generate
   └─ Writes to ~/.local/share/meeting-notes/notes/{uuid}-{template}.md
   └─ NotionService.create_page() → notion-client creates page in database
```

---

## File System Layout

```
~/.config/meeting-notes/        # XDG_CONFIG_HOME — user config
  config.json                   # Notion token, device indices, preferences
  state.json                    # Active/last recording state (PID, paths)

~/.local/share/meeting-notes/   # XDG_DATA_HOME — persistent data
  recordings/
    2026-03-22-1030-{uuid}.wav  # Timestamped + session UUID
  transcripts/
    {uuid}.txt                  # Plain text transcripts
  notes/
    {uuid}-meeting.md           # Generated notes (by template)
    {uuid}-minutes.md
    {uuid}-1on1.md
  metadata/
    {uuid}.json                 # Per-session metadata (title, date, duration, notion_url)
```

**Why XDG:** Backup tools understand `.local/share`; caches are ignored; config lives separately from data.

---

## Config File Structure

```json
{
  "version": 1,
  "notion": {
    "token": "secret_...",
    "database_id": "uuid-of-target-page-or-database"
  },
  "audio": {
    "system_device_index": 1,
    "microphone_device_index": 2
  },
  "llm": {
    "model": "llama3.1:8b",
    "ollama_endpoint": "http://127.0.0.1:11434",
    "timeout_seconds": 120
  },
  "storage": {
    "data_dir": null
  }
}
```

**Why JSON over .env:** Type safety, nested structure, easy to validate, supports migrations via `version` field.

---

## Module Structure

```
meeting_notes/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py                  # Click group entry point
│   ├── commands/
│   │   ├── record.py            # meet record + meet stop
│   │   ├── transcribe.py        # meet transcribe
│   │   ├── summarize.py         # meet summarize
│   │   ├── list.py              # meet list
│   │   ├── init.py              # meet init wizard
│   │   └── doctor.py            # meet doctor
│   └── ui.py                    # Rich helpers: spinners, tables, panels
│
├── core/
│   ├── config.py                # Config loading + dataclass
│   ├── state.py                 # State file (active/last recording)
│   ├── storage.py               # XDG paths + directory management
│   ├── process_manager.py       # ffmpeg subprocess + signal handling
│   └── health_check.py          # Pluggable prerequisite validation
│
├── services/
│   ├── audio.py                 # ffmpeg orchestration
│   ├── transcription.py         # mlx-whisper wrapper
│   ├── llm.py                   # Ollama HTTP API wrapper
│   └── notion.py                # notion-client wrapper
│
└── templates/
    ├── meeting.txt              # LLM prompt template: full meeting notes
    ├── minutes.txt              # LLM prompt template: formal minutes
    └── 1on1.txt                 # LLM prompt template: 1-on-1
```

---

## meet doctor — Pluggable Health Check Architecture

Each phase adds its own checks by implementing `HealthCheck`:

```python
class HealthCheck(ABC):
    @abstractmethod
    def check(self) -> CheckResult:  # status: ok | warning | error
        pass

# Phase 1 adds:
BlackHoleCheck, FFmpegDeviceCheck, DiskSpaceCheck

# Phase 2 adds:
MlxWhisperCheck, WhisperModelCheck

# Phase 3 adds:
OllamaRunningCheck, OllamaModelCheck

# Phase 4 adds:
NotionTokenCheck, NotionDatabaseCheck

# Phase 6 integrates all checks into meet doctor
```

This means `meet doctor` in Phase 1 only validates audio prerequisites. By Phase 6, it validates everything.

---

## Signal Handling for `meet stop`

```python
# RecordingSession (services/audio.py)
signal.signal(signal.SIGINT, self._signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, self._signal_handler)  # kill

def stop_gracefully(pid, timeout=5):
    os.killpg(os.getpgid(pid), signal.SIGTERM)  # entire process group
    psutil.wait_procs([psutil.Process(pid)], timeout=timeout)
    # fallback to SIGKILL after timeout
```

**Critical:** Use `start_new_session=True` when spawning ffmpeg so it runs in its own process group. This ensures `os.killpg()` terminates both ffmpeg and any children.

---

## State File (Atomic Writes)

```python
# Atomic write pattern: temp file + rename (POSIX-safe)
temp_file = state_path.with_suffix('.tmp')
temp_file.write_text(json.dumps(state))
temp_file.replace(state_path)  # atomic on POSIX
```

State file holds: `session_id`, `pid`, `started_at`, `output_path` — enough to recover from a crash.

---

## Build Order (Dependencies)

| Phase | Components | Depends On |
|-------|-----------|------------|
| 1 | config, storage, state, health_check, process_manager | nothing |
| 1 | services/audio | core/* |
| 1 | cli/commands/record, stop | services/audio, core/* |
| 1 | cli/commands/init, doctor | core/health_check |
| 2 | services/transcription | core/storage |
| 2 | cli/commands/transcribe | services/transcription |
| 3 | templates/*.txt, services/llm | core/config |
| 3 | cli/commands/summarize | services/llm, services/transcription |
| 4 | services/notion | core/config |
| 4 | cli/commands/summarize (notion) | services/notion |
| 5 | cli/commands/list | core/storage, metadata/*.json |

---

## Key Decisions

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| XDG Base Directory spec | Industry standard, multi-machine sync, backup tools understand it | Slightly verbose paths |
| State file over lock file | Rich context (session_id, timestamps), easier recovery | Must use atomic writes |
| `start_new_session=True` for ffmpeg | Enables clean `os.killpg()` termination | POSIX-only (fine; macOS-only tool) |
| Pluggable health checks | Each phase adds checks without touching Phase 1 | Small upfront abstraction |
| JSON config over .env | Type safety, nested config, version migrations | Requires JSON parsing |
| Session UUID + timestamp | Prevents collisions, enables recovery, sortable filenames | Slightly longer filenames |
| HTTP API for Ollama | No first-party Python SDK; HTTP is stable | Manual request construction |
| Separate services from CLI | Testable, reusable, decoupled | One extra indirection layer |

---
*Researched: 2026-03-22*
