---
phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline
plan: "03"
subsystem: transcription, diarization
tags: [pyannote, speaker-diarization, transcription, summarize, hf-token, graceful-fallback]
one_liner: "pyannote speaker diarization wired into transcribe pipeline with graceful fallback, SPEAKER_XX labels in .txt and .srt, and diarized transcript preference in meet summarize"

dependency_graph:
  requires: ["01-01", "01-02"]
  provides:
    - "run_diarization() — pyannote Pipeline wrapper in transcription.py"
    - "assign_speakers_to_segments() — max-overlap segment-to-speaker assignment"
    - "build_diarized_txt() — SPEAKER_XX: paragraph grouping for .txt output"
    - "Diarized .txt and .srt written by meet transcribe when HF token configured"
    - "meet summarize prefers diarized_transcript_path from metadata (D-11)"
  affects:
    - "meeting_notes/services/transcription.py"
    - "meeting_notes/cli/commands/transcribe.py"
    - "meeting_notes/cli/commands/summarize.py"

tech-stack:
  added: []
  patterns:
    - "Lazy import of pyannote.audio.Pipeline inside run_diarization() — avoids import-time cost"
    - "Graceful diarization fallback: missing HF token → yellow warning → plain output"
    - "Exception catch on diarization: any failure → yellow warning → plain output"
    - "assign_speakers_to_segments: max temporal overlap wins (ties broken by iteration order)"
    - "build_diarized_txt: consecutive same-speaker segments grouped into paragraphs"
    - "metadata records diarization_succeeded, speaker_turns, diarized_transcript_path"
    - "summarize.py reads metadata before reading transcript — prefers diarized path (D-11)"

key-files:
  created: []
  modified:
    - "meeting_notes/services/transcription.py"
    - "meeting_notes/cli/commands/transcribe.py"
    - "meeting_notes/cli/commands/summarize.py"
    - "tests/test_transcription.py"
    - "tests/test_transcribe_command.py"
    - "tests/test_summarize_command.py"

key-decisions:
  - "run_diarization() lazy-imports pyannote.audio.Pipeline to avoid import-time cost for users without pyannote installed"
  - "assign_speakers_to_segments uses max-overlap: for each Whisper segment, the pyannote turn with greatest temporal overlap wins"
  - "build_diarized_txt groups consecutive same-speaker segments into paragraphs with SPEAKER_XX: header (D-09)"
  - "diarized content overwrites plain .txt — diarized_transcript_path points to same file (per RESEARCH.md Pitfall 5)"
  - "diarization_succeeded and diarized_transcript_path set in metadata so summarize can detect diarized content"
  - "summarize diarized preference is technically no-op in current design (same .txt path) but future-proofs for separate paths"

# Metrics
duration_seconds: 900
tasks_completed: 2
files_changed: 6
tests_added: 5
completed_date: "2026-03-27"
---

# Phase 01 Plan 03: Diarization Integration Summary

**pyannote speaker diarization wired into transcribe pipeline with graceful fallback, SPEAKER_XX labels in .txt and .srt, and diarized transcript preference in meet summarize**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-03-27
- **Tasks:** 2
- **Files modified:** 6
- **Tests added:** 5 (2 transcription unit, 2 transcribe command, 1 summarize command)

## Accomplishments

**Task 1: Diarization functions + transcribe command integration**

Added 3 new functions to `meeting_notes/services/transcription.py`:
- `run_diarization(wav_path, hf_token)` — lazy-imports `pyannote.audio.Pipeline`, calls `Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")`, returns annotation object
- `assign_speakers_to_segments(segments, diarization)` — assigns each Whisper segment the pyannote speaker with maximum temporal overlap; returns `{segment_index: "SPEAKER_XX"}`
- `build_diarized_txt(segments, speaker_map)` — groups consecutive same-speaker segments into paragraph blocks with `SPEAKER_XX:` header per D-09

Wired into `meet transcribe`:
- Checks `config.huggingface.token` — if None, prints yellow warning, skips diarization
- If token present: runs diarization via spinner, catches any exception → yellow warning, continues with plain output
- When successful: rewrites `text` using `build_diarized_txt()`, saves diarized `.txt` and speaker-labeled `.srt`
- Metadata records: `diarization_succeeded`, `diarized_transcript_path`, `speaker_turns`

**Task 2: Diarized transcript preference in meet summarize**

Added 7 lines to `summarize.py` before reading transcript text:
- Reads metadata for the session
- If `diarized_transcript_path` is set and file exists → uses that path as `transcript_path`
- Ensures summarize always uses the best available content (D-11)
- Implemented `test_prefers_diarized_transcript` (was Wave 0 stub with `@pytest.mark.skip`)

## Task Commits

1. **Task 1: Add diarization functions and wire into transcribe command** - `0e043bd` (feat)
2. **Task 2: Add diarized transcript preference to meet summarize** - `ff79820` (feat)

## Files Created/Modified

- `meeting_notes/services/transcription.py` — Added `run_diarization()`, `assign_speakers_to_segments()`, `build_diarized_txt()`; added `Optional` import
- `meeting_notes/cli/commands/transcribe.py` — Added diarization block (imports + token check + try/except + text/srt rewrite); updated metadata
- `meeting_notes/cli/commands/summarize.py` — Added metadata read + diarized_transcript_path preference block (D-11)
- `tests/test_transcription.py` — Added `test_speaker_segment_merge`, `test_diarized_txt_grouping`
- `tests/test_transcribe_command.py` — Added `test_diarization_skips_without_hf_token`, `test_diarization_graceful_failure`
- `tests/test_summarize_command.py` — Replaced `@pytest.mark.skip` stub with full `test_prefers_diarized_transcript`

## Deviations from Plan

### Auto-fixed Issues

**1. [Workflow adaptation] Wave 0 stub pattern for test_transcription.py and test_transcribe_command.py**
- **Found during:** Task 1
- **Issue:** Plan 01-03 instructed "remove @pytest.mark.skip" from test stubs in test_transcription.py and test_transcribe_command.py. As noted in Plan 01-01 SUMMARY, Wave 0 stubs were not present in this worktree branch — those stubs only existed on `dev` branch.
- **Fix:** Wrote the 4 tests directly (without stub/unskip dance). Functionally identical outcome.
- **Impact:** No scope change — same 4 tests written, same coverage, same behavior.
- **Committed in:** `0e043bd`

**2. [Rule 3 - Blocking] Merged dev branch before execution**
- **Found during:** Pre-execution
- **Issue:** This worktree was based on `cb3a91a` (before plans 01-01 and 01-02 were merged to dev). Plans 01-01 (SRT) and 01-02 (HuggingFaceConfig) are dependencies of Plan 01-03.
- **Fix:** Ran `git merge dev` to fast-forward the worktree branch to include all prerequisite work.
- **Impact:** Required to proceed — without the merge, `generate_srt()`, `transcribe_audio()` tuple return, and `HuggingFaceConfig` were all missing.
- **Committed in:** Fast-forward merge (no additional commit)

## Pre-existing Issues (Out of Scope)

These existed before this plan and are unrelated to diarization changes:
- `tests/test_llm_service.py::test_templates_contain_grounding_rule` — LLM template grounding rule mismatch
- `tests/test_storage.py::test_get_data_dir_default` — XDG path vs Documents path (from `cb3a91a` commit changing default storage)
- `tests/test_init.py::test_first_time_init_runs_full_wizard` — wizard prompt ordering issue

## Known Stubs

None — all diarization functionality is fully wired:
- `run_diarization()` calls real pyannote pipeline (lazy import)
- `assign_speakers_to_segments()` real max-overlap algorithm
- `build_diarized_txt()` real paragraph grouping
- `diarized_transcript_path` in metadata is real path when diarization succeeds
- `test_prefers_diarized_transcript` is a real test with assertions

## Self-Check: PASSED

Files exist:
- meeting_notes/services/transcription.py: FOUND — contains `def run_diarization`, `def assign_speakers_to_segments`, `def build_diarized_txt`, `Pipeline.from_pretrained`, `use_auth_token=hf_token`
- meeting_notes/cli/commands/transcribe.py: FOUND — contains `run_diarization`, `HuggingFace token not configured`, `diarization_succeeded = True`, `diarized_transcript_path`
- meeting_notes/cli/commands/summarize.py: FOUND — contains `diarized_transcript_path`, `session_metadata.get("diarized_transcript_path")`
- tests/test_summarize_command.py: FOUND — `test_prefers_diarized_transcript` has NO `@pytest.mark.skip`

Commits exist:
- 0e043bd: FOUND
- ff79820: FOUND

Test results: 63/63 passing across test_transcription.py + test_transcribe_command.py + test_summarize_command.py

## Self-Check: PASSED

All files exist, all commits verified, all key patterns confirmed in source files.

---
*Phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline*
*Completed: 2026-03-27*
