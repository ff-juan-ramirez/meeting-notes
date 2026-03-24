---
phase: 02-local-transcription
plan: 01
subsystem: transcription
tags: [mlx-whisper, cli, rich, threading, click, config]

# Dependency graph
requires:
  - phase: 01-audio-capture-health-check-design
    provides: core modules (config, storage, state), CLI command pattern, service module pattern
provides:
  - meet transcribe CLI command with --session and auto-latest WAV resolution
  - services/transcription.py: transcribe_audio, estimate_wav_duration_seconds, run_with_spinner
  - WhisperConfig dataclass added to Config with backward-compatible loading
  - Transcript files saved to transcripts/{stem}.txt
  - Metadata JSON written to metadata/{stem}.json with Phase 2 fields
  - Rich spinner with elapsed time via threading during transcription
affects: [03-note-generation, 05-integrated-cli]

# Tech tracking
tech-stack:
  added: [mlx-whisper (mlx-community/whisper-large-v3-turbo)]
  patterns:
    - Language auto-detect by omitting language kwarg (not passing None)
    - Run blocking call in background threading.Thread; render Rich Live spinner in main thread
    - WAV duration from file size formula (no ffprobe dependency)
    - WhisperConfig mirrors AudioConfig pattern in Config dataclass

key-files:
  created:
    - meeting_notes/services/transcription.py
    - meeting_notes/cli/commands/transcribe.py
    - tests/test_transcription.py
    - tests/test_transcribe_command.py
  modified:
    - meeting_notes/core/config.py
    - meeting_notes/cli/main.py

key-decisions:
  - "Language auto-detect requires omitting language key entirely from decode_opts — passing language=None causes mlx-whisper to default to 'en'"
  - "run_with_spinner uses threading.Thread for background transcription; Rich Live renders elapsed time in main thread"
  - "WAV duration estimated from file size (BYTES_PER_SECOND=32000, WAV_HEADER_BYTES=44) — no ffprobe dependency"
  - "Session stem derived from wav_path.stem (not a stored UUID) to ensure --session round-trip works"
  - "metadata/{stem}.json overwritten fresh on re-transcription — no read-modify-write"

patterns-established:
  - "Transcription service pattern: pure functions in services/transcription.py, no Click/Rich imports"
  - "CLI command follows record.py structure: module-level Console, helper functions at module level"
  - "Config extension: WhisperConfig dataclass before Config, backward-compatible via data.get('whisper', {})"

requirements-completed: [TRANS-01, TRANS-02, TRANS-03, TRANS-04, TRANS-05]

# Metrics
duration: 3min
completed: 2026-03-22
---

# Phase 2 Plan 01: Local Transcription Summary

**mlx-whisper transcription service and `meet transcribe` CLI command with spinner, session resolution, transcript/metadata persistence, and 25 new unit tests**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-22T21:02:02Z
- **Completed:** 2026-03-22T21:05:32Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- WhisperConfig dataclass added to Config with backward-compatible JSON loading (handles missing whisper key, null language, and string language)
- Transcription service created with language auto-detect handling (omit kwarg when None), WAV duration estimate, and threading-based Rich spinner
- `meet transcribe` command: resolves latest WAV by mtime or exact --session stem, saves transcript and metadata, warns on short transcripts (<50 words) and long recordings (>90 min)
- 25 unit tests (13 service + 12 CLI) covering all behaviors; full 70-test suite passes

## Task Commits

Each task was committed atomically:

1. **Task 1: Config extension + transcription service + tests** - `46d2464` (feat)
2. **Task 2: CLI transcribe command + session resolution + metadata + tests** - `420da29` (feat)

## Files Created/Modified

- `meeting_notes/core/config.py` - Added WhisperConfig dataclass and whisper field to Config with backward-compatible load()
- `meeting_notes/services/transcription.py` - New: transcribe_audio (language kwarg handling), estimate_wav_duration_seconds (size-based), run_with_spinner (threading + Rich Live)
- `meeting_notes/cli/commands/transcribe.py` - New: meet transcribe command, resolve_latest_wav, resolve_wav_by_stem
- `meeting_notes/cli/main.py` - Registered transcribe command
- `tests/test_transcription.py` - New: 13 unit tests for service and config
- `tests/test_transcribe_command.py` - New: 12 unit tests for CLI command

## Decisions Made

- Language auto-detect requires omitting `language` key from `decode_opts` entirely — passing `language=None` causes mlx-whisper to default to `"en"` per its source implementation
- `run_with_spinner` runs transcription in a `threading.Thread` (daemon=True); main thread renders Rich `Live` display with elapsed time update every 0.1s
- WAV duration estimated from `(file_size - 44) / 32000` — no ffprobe subprocess needed
- Session stem from `wav_path.stem` not any stored UUID, ensuring `--session` round-trip works correctly
- Metadata overwritten fresh on re-transcription per D-03 decision

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `meet transcribe` fully functional for Phase 3 note generation
- Session stem output from `meet transcribe` can be passed to `--session` in Phase 3 `meet summarize`
- Metadata JSON in `metadata/{stem}.json` ready for Phase 3 to read and extend with note fields

---
*Phase: 02-local-transcription*
*Completed: 2026-03-22*
