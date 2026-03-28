---
phase: 1
slug: srt-output-and-speaker-diarization-for-transcription-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (configured in pyproject.toml) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` testpaths = ["tests"] |
| **Quick run command** | `pytest tests/test_transcription.py tests/test_transcribe_command.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds (all mocked; no real audio/model calls) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_transcription.py tests/test_transcribe_command.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | SRT timestamp format | unit | `pytest tests/test_transcription.py::test_srt_timestamp_format -x` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 0 | generate_srt() valid SRT | unit | `pytest tests/test_transcription.py::test_generate_srt -x` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 0 | generate_srt() speaker prefix | unit | `pytest tests/test_transcription.py::test_generate_srt_with_speakers -x` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 0 | transcribe_audio() returns tuple | unit | `pytest tests/test_transcription.py::test_transcribe_returns_segments -x` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | meet transcribe writes .srt | integration | `pytest tests/test_transcribe_command.py::test_srt_file_created -x` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 1 | metadata includes srt_path | integration | `pytest tests/test_transcribe_command.py::test_metadata_includes_srt_fields -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 0 | assign_speakers_to_segments() overlap | unit | `pytest tests/test_transcription.py::test_speaker_segment_merge -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 0 | build_diarized_txt() groups speakers | unit | `pytest tests/test_transcription.py::test_diarized_txt_grouping -x` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 0 | Config hf_token round-trip | unit | `pytest tests/test_config.py::test_config_hf_token_roundtrip -x` | ❌ W0 | ⬜ pending |
| 1-02-04 | 02 | 1 | diarization skips without HF token | integration | `pytest tests/test_transcribe_command.py::test_diarization_skips_without_hf_token -x` | ❌ W0 | ⬜ pending |
| 1-02-05 | 02 | 1 | diarization graceful failure | integration | `pytest tests/test_transcribe_command.py::test_diarization_graceful_failure -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 0 | PyannoteCheck ERROR when not importable | unit | `pytest tests/test_checks.py::test_pyannote_check_error -x` | ❌ W0 (new file) | ⬜ pending |
| 1-03-02 | 03 | 0 | HuggingFaceTokenCheck WARNING no token | unit | `pytest tests/test_checks.py::test_hf_token_check_warning_no_token -x` | ❌ W0 (new file) | ⬜ pending |
| 1-03-03 | 03 | 0 | PyannoteModelCheck WARNING not cached | unit | `pytest tests/test_checks.py::test_pyannote_model_check_warning -x` | ❌ W0 (new file) | ⬜ pending |
| 1-04-01 | 04 | 0 | meet init collects HF token | integration | `pytest tests/test_init.py::test_init_collects_hf_token -x` | ❌ W0 | ⬜ pending |
| 1-04-02 | 04 | 0 | _update_specific_fields includes HF token | integration | `pytest tests/test_init.py::test_update_includes_hf_token -x` | ❌ W0 | ⬜ pending |
| 1-05-01 | 05 | 0 | summarize prefers diarized transcript | integration | `pytest tests/test_summarize_command.py::test_prefers_diarized_transcript -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_checks.py` — new file; stubs for PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck tests
- [ ] `tests/test_transcription.py` — extend with stubs: test_srt_timestamp_format, test_generate_srt, test_generate_srt_with_speakers, test_speaker_segment_merge, test_diarized_txt_grouping, test_transcribe_returns_segments
- [ ] `tests/test_transcribe_command.py` — extend with stubs: test_srt_file_created, test_metadata_includes_srt_fields, test_diarization_skips_without_hf_token, test_diarization_graceful_failure
- [ ] `tests/test_config.py` — extend with stub: test_config_hf_token_roundtrip
- [ ] `tests/test_init.py` — extend with stubs: test_init_collects_hf_token, test_update_includes_hf_token
- [ ] `tests/test_summarize_command.py` — extend with stub: test_prefers_diarized_transcript

*Existing infrastructure: pytest configured, conftest.py has tmp_path fixtures, CliRunner pattern established — all reusable. No new framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| pyannote.audio 3.3.2 installs on Python 3.14 | P4 (Python 3.14 compat) | Cannot mock install process | Run `pip install torchaudio && pip install "pyannote.audio==3.3.2"` in project venv; verify `import pyannote.audio` succeeds |
| Diarization produces correct speaker labels on real audio | D-05, D-09, D-10 | Requires real audio + HF model | Run `meet transcribe` on a known recording with multiple speakers; inspect .txt and .srt for speaker prefixes |
| HuggingFace gated model conditions acceptance | P3 | Requires browser + HF account | Visit huggingface.co/pyannote/speaker-diarization-3.1 and huggingface.co/pyannote/segmentation-3.0; accept conditions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
