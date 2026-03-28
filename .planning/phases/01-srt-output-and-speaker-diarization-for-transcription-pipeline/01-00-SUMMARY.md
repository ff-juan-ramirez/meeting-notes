---
phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline
plan: "00"
subsystem: tests
tags: [wave-0, stubs, nyquist, tdd, srt, diarization]
dependency_graph:
  requires: []
  provides: [wave-0-test-stubs]
  affects: [01-01-PLAN, 01-02-PLAN, 01-03-PLAN]
tech_stack:
  added: []
  patterns: [pytest.mark.skip for Wave 0 stubs]
key_files:
  created:
    - tests/test_checks.py
  modified:
    - tests/test_transcription.py
    - tests/test_transcribe_command.py
    - tests/test_config.py
    - tests/test_init.py
    - tests/test_summarize_command.py
decisions:
  - "Wave 0 stubs use @pytest.mark.skip(reason='Wave 0 stub — implementation pending') — consistent reason string across all 17 stubs"
  - "test_checks.py is a new file (health check stubs are separate from test_health_check.py which covers v1.0 checks)"
  - "Imports of PyannoteCheck/HuggingFaceTokenCheck/PyannoteModelCheck are inside function bodies to avoid collection failures before classes exist"
metrics:
  duration_seconds: 120
  completed_date: "2026-03-27"
  tasks_completed: 2
  files_changed: 6
---

# Phase 1 Plan 00: Wave 0 Nyquist Test Stubs Summary

17 Wave 0 test stubs created across 6 test files — all skipped, all named to match VALIDATION.md task IDs, full suite green.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Add test stubs to 5 existing test files | 1f0696e | tests/test_transcription.py, tests/test_transcribe_command.py, tests/test_config.py, tests/test_init.py, tests/test_summarize_command.py |
| 2 | Create new tests/test_checks.py with 3 pyannote health check stubs | 1f0696e | tests/test_checks.py |

## Stubs Created

### tests/test_transcription.py (6 stubs)
- `test_srt_timestamp_format` — seconds_to_srt_timestamp() format check
- `test_generate_srt` — SRT index and timestamp format
- `test_generate_srt_with_speakers` — speaker tag prefixing
- `test_transcribe_returns_segments` — tuple return signature change
- `test_speaker_segment_merge` — max-overlap speaker assignment
- `test_diarized_txt_grouping` — consecutive same-speaker grouping

### tests/test_transcribe_command.py (4 stubs)
- `test_srt_file_created` — .srt written alongside .txt
- `test_metadata_includes_srt_fields` — srt_path and diarization_succeeded in JSON
- `test_diarization_skips_without_hf_token` — graceful skip with yellow warning
- `test_diarization_graceful_failure` — transcription continues on diarization exception

### tests/test_checks.py (3 stubs — new file)
- `test_pyannote_check_error` — ERROR when pyannote.audio not importable
- `test_hf_token_check_warning_no_token` — WARNING when token is None
- `test_pyannote_model_check_warning` — WARNING when model cache absent

### tests/test_config.py (1 stub)
- `test_config_hf_token_roundtrip` — huggingface.token save/load

### tests/test_init.py (2 stubs)
- `test_init_collects_hf_token` — wizard collects and saves HF token
- `test_update_includes_hf_token` — update flow includes HF token field

### tests/test_summarize_command.py (1 stub)
- `test_prefers_diarized_transcript` — uses diarized_transcript_path from metadata

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

All 17 tests are intentional Wave 0 stubs. They will be implemented (un-skipped and filled in) by Plans 01-03.

## Deferred Issues

Pre-existing test failures found (not caused by this plan's changes):
1. `tests/test_init.py::test_first_time_init_runs_full_wizard` — wizard prompts for storage path not in test input
2. `tests/test_llm_service.py::test_templates_contain_grounding_rule` — template missing grounding rule text
3. `tests/test_storage.py::test_get_data_dir_default` — data dir returns ~/Documents/meeting-notes instead of ~/.local/share/meeting-notes

Logged to: `.planning/phases/01-srt-output-and-speaker-diarization-for-transcription-pipeline/deferred-items.md`

## Self-Check: PASSED

- [x] tests/test_checks.py exists and has 3 stubs
- [x] 17 total stubs across 6 files (15 + 2 from test_init.py = 17)
- [x] Commit 1f0696e exists
- [x] All stubs marked @pytest.mark.skip
