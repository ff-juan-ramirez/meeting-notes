---
phase: 02-sessions-dashboard
plan: "02"
subsystem: gui/workers
tags: [gui, workers, qthread, transcription, summarization]
dependency_graph:
  requires:
    - Phase 01 gui-foundation (QThread, Signal infrastructure via PySide6)
    - meeting_notes/services/transcription.py (transcribe_audio)
    - meeting_notes/services/llm.py (generate_notes, chunk_transcript, etc.)
    - meeting_notes/services/notion.py (create_page, extract_title)
    - meeting_notes/core/state.py (read_state, write_state)
    - meeting_notes/core/storage.py (get_data_dir)
  provides:
    - TranscribeWorker(QThread) — Plan 03 SessionDetailPanel uses this
    - SummarizeWorker(QThread) — Plan 03 SessionDetailPanel uses this
  affects: []
tech_stack:
  added: []
  patterns:
    - "QThread subclass with class-level Signal declarations"
    - "Lazy service imports inside run() to prevent ML modules at startup"
    - "read-merge-write metadata pattern (mirrors CLI commands)"
key_files:
  created:
    - meeting_notes/gui/workers/transcribe_worker.py
    - meeting_notes/gui/workers/summarize_worker.py
  modified: []
decisions:
  - "Lazy imports inside run(): all service/ML imports deferred to avoid loading mlx_whisper, pyannote, torchaudio at GUI startup"
  - "TranscribeWorker writes transcript .txt and updates metadata JSON — mirrors cli/commands/transcribe.py read-merge-write pattern"
  - "SummarizeWorker includes _map_reduce() for long transcripts (>8000 tokens, per D-13), consistent with CLI path"
  - "Notion failure in SummarizeWorker is non-fatal (bare except: pass) — notes always saved locally first"
  - "Config interface uses config.whisper.language (WhisperConfig nested dataclass) not flat whisper_language attr — plan's interface description was for an older Config shape"
metrics:
  duration_seconds: 103
  completed_date: "2026-03-31"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 02 Plan 02: Background Workers Summary

**One-liner:** TranscribeWorker and SummarizeWorker QThread classes with lazy ML imports that call the existing service layer from the GUI thread.

## What Was Built

Two `QThread` worker classes that offload heavy ML operations from the Qt main thread:

- **`meeting_notes/gui/workers/transcribe_worker.py`** — `TranscribeWorker(QThread)` with `progress(str)`, `finished(str, int)`, `failed(str)` signals. Calls `transcribe_audio()` inside `run()`, writes transcript `.txt`, and updates session metadata JSON.

- **`meeting_notes/gui/workers/summarize_worker.py`** — `SummarizeWorker(QThread)` with `progress(str)`, `finished(str)`, `failed(str)` signals. Mirrors `cli/commands/summarize.py`: single-pass or map-reduce LLM path, writes notes `.md`, updates metadata JSON, optionally pushes to Notion.

## Verification Results

Both workers imported cleanly with no ML modules loaded at import time:

```
from meeting_notes.gui.workers.transcribe_worker import TranscribeWorker  # OK
from meeting_notes.gui.workers.summarize_worker import SummarizeWorker    # OK
```

Test suite: 144 passed, 1 pre-existing failure in `test_templates_contain_grounding_rule` (unrelated to this plan — logged to deferred-items).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Config interface mismatch in plan's `<interfaces>` block**
- **Found during:** Task 1 implementation
- **Issue:** Plan's `<interfaces>` block showed `Config` with flat `whisper_language: str | None` attribute. Actual `Config` uses nested `config.whisper.language` via `WhisperConfig` dataclass. The transcription service itself uses `config.whisper.language` in `transcribe_audio()`.
- **Fix:** Workers reference `config.whisper.language` correctly via the actual nested structure. No code change needed — the service layer handles this internally, and workers pass the whole `Config` object.
- **Files modified:** None (design-time correction, not code fix)

## Known Stubs

None — both workers are fully implemented with no placeholder data or hardcoded empty values.

## Self-Check: PASSED

- `meeting_notes/gui/workers/transcribe_worker.py` exists: FOUND
- `meeting_notes/gui/workers/summarize_worker.py` exists: FOUND
- Commit `bbf6f78` (TranscribeWorker): FOUND
- Commit `5b8dd18` (SummarizeWorker): FOUND
