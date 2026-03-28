---
phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline
plan: 01
subsystem: transcription
tags: [mlx-whisper, srt, subtitles, timestamps, segments]

# Dependency graph
requires:
  - phase: v1.0-phase-02-local-transcription
    provides: "transcription.py with mlx_whisper wrapper, transcribe CLI command, result dict with segments"
provides:
  - "seconds_to_srt_timestamp() — float seconds to HH:MM:SS,mmm"
  - "generate_srt() — SRT file content from mlx_whisper segments with optional speaker_map"
  - "transcribe_audio() returns (text, segments) tuple instead of plain str"
  - "meet transcribe writes .srt alongside .txt in transcripts/"
  - "metadata JSON includes srt_path, diarization_succeeded, diarized_transcript_path, speaker_turns"
affects:
  - "01-03: diarization plan uses generate_srt() with speaker_map"
  - "01-02: config/checks plan depends on updated transcribe command"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SRT generation: pure formatting of mlx_whisper result segments list"
    - "transcribe_audio() returns tuple — callers unpack (text, segments)"
    - "Metadata JSON extended with diarization fields set to False/None/[] baseline"

key-files:
  created: []
  modified:
    - "meeting_notes/services/transcription.py"
    - "meeting_notes/cli/commands/transcribe.py"
    - "tests/test_transcription.py"
    - "tests/test_transcribe_command.py"

key-decisions:
  - "transcribe_audio() returns (text, segments) tuple — callers must unpack; breaking change to existing callers fixed in same plan"
  - "generate_srt() accepts optional speaker_map dict keyed by 0-based segment index — ready for Plan 03 diarization"
  - "SRT always written alongside .txt with no flag — per D-01"
  - "Metadata baseline: diarization_succeeded=False, diarized_transcript_path=None, speaker_turns=[] — Plan 03 will populate these"

patterns-established:
  - "SRT timestamp format: HH:MM:SS,mmm via seconds_to_srt_timestamp()"
  - "SRT indices are 1-based, text is stripped of leading/trailing whitespace"
  - "speaker_map keys are 0-based segment indices; values are speaker label strings (e.g. SPEAKER_00)"

requirements-completed: [D-01, D-02, D-03, D-04]

# Metrics
duration: 15min
completed: 2026-03-27
---

# Phase 01 Plan 01: SRT Output Summary

**SRT subtitle generation added to transcription pipeline: seconds_to_srt_timestamp() + generate_srt() in transcription.py, transcribe_audio() returns (text, segments) tuple, and meet transcribe writes .srt alongside .txt with diarization-ready metadata**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-27T00:00:00Z
- **Completed:** 2026-03-27T00:15:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `seconds_to_srt_timestamp()` converting float seconds to `HH:MM:SS,mmm` SRT format
- Added `generate_srt()` building valid SRT content from mlx_whisper segments with optional speaker_map parameter (ready for Plan 03 diarization)
- Changed `transcribe_audio()` return type from `str` to `tuple[str, list[dict]]`; updated all callers and mocks
- Wired SRT file output into `meet transcribe` — writes `transcripts/{stem}.srt` alongside existing `.txt`
- Extended metadata JSON with `srt_path`, `diarization_succeeded`, `diarized_transcript_path`, `speaker_turns` baseline fields

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SRT functions to transcription.py and update transcribe_audio() return type** - `5e2de25` (feat)
2. **Task 2: Wire SRT output into transcribe CLI command and update metadata** - `3d45be2` (feat)

## Files Created/Modified

- `meeting_notes/services/transcription.py` - Added `seconds_to_srt_timestamp()`, `generate_srt()`, changed `transcribe_audio()` return to `(text, segments)` tuple
- `meeting_notes/cli/commands/transcribe.py` - Import `generate_srt`, unpack tuple, write SRT file, extend metadata dict
- `tests/test_transcription.py` - Updated 4 existing mocks for new return type; added 4 new tests (srt_timestamp_format, generate_srt, generate_srt_with_speakers, transcribe_returns_segments)
- `tests/test_transcribe_command.py` - Updated 7 existing mocks for `"segments": []`; added test_srt_file_created and test_metadata_includes_srt_fields

## Decisions Made

- `generate_srt()` accepts `speaker_map: dict[int, str] | None = None` keyed by 0-based segment index — same parameter Plan 03 will use for diarization labels, avoiding a future breaking change
- All existing tests updated for `(text, segments)` return type in the same commit as the implementation change (no intermediate broken state in history)
- Metadata diarization fields set to baseline values (`False`, `None`, `[]`) so Plan 03 can simply overwrite them when diarization succeeds

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pre-existing test mocks missing "segments" key**
- **Found during:** Task 1 (updating transcribe_audio return type)
- **Issue:** 4 existing tests in test_transcription.py and 7 in test_transcribe_command.py mocked mlx_whisper returning `{"text": "..."}` without a `"segments"` key. Once `transcribe_audio()` accesses `result["segments"]`, all these tests would fail with KeyError.
- **Fix:** Updated all affected mocks to include `"segments": []` in the same commits as the implementation changes.
- **Files modified:** tests/test_transcription.py, tests/test_transcribe_command.py
- **Verification:** Full test suite passes with 33/33 for the affected files
- **Committed in:** `5e2de25` (Task 1) and `3d45be2` (Task 2)

**2. [Rule 0 - Pre-existing, out of scope] Wave 0 test stubs not present in worktree**
- **Found during:** Task 1 planning
- **Issue:** Plan 01-01 was designed to "remove @pytest.mark.skip" from stubs added by Plan 01-00. Those stubs were not present in the worktree branch (only on dev branch).
- **Fix:** Wrote tests directly without the stub/unskip dance. Functionally identical outcome.
- **Impact:** No scope change — same tests, same coverage, same behavior.

---

**Total deviations:** 1 auto-fixed (blocking mock update), 1 workflow adaptation (stub absence)
**Impact on plan:** All fixes necessary for correctness. No scope creep.

## Issues Encountered

Pre-existing test failures (out of scope, not caused by plan 01-01 changes):
- `tests/test_init.py::test_first_time_init_runs_full_wizard` — wizard prompt ordering issue
- `tests/test_storage.py::test_get_data_dir_default` — expects XDG path but default changed to `~/Documents/meeting-notes`
- `tests/test_llm_service.py::test_templates_contain_grounding_rule` — pre-existing LLM template mismatch

These existed before this plan and are unrelated to SRT changes.

## Known Stubs

None — all SRT functionality is fully wired. `diarization_succeeded`, `diarized_transcript_path`, and `speaker_turns` are set to baseline values (`False`, `None`, `[]`) intentionally — Plan 03 will populate them when diarization runs.

## Next Phase Readiness

- Plan 01-02 (config + health checks) can proceed — no dependency on SRT output
- Plan 01-03 (diarization) has the foundation it needs: `generate_srt()` with `speaker_map` parameter, `transcribe_audio()` returning segments, and metadata fields ready to receive diarization results
- All 33 target tests pass; 3 pre-existing unrelated failures noted above

## Self-Check: PASSED

All files exist, all commits verified, all key patterns confirmed in source files.

---
*Phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline*
*Completed: 2026-03-27*
