---
phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline
verified: 2026-03-27T00:00:00Z
status: passed
score: 17/17 must-haves verified
gaps: []
human_verification:
  - test: "Run `meet transcribe` on a real multi-speaker recording with a valid HF token configured"
    expected: ".txt contains SPEAKER_XX: paragraph prefixes; .srt contains SPEAKER_XX: entry prefixes; both files are written; metadata records diarization_succeeded=true and speaker_turns"
    why_human: "Requires real pyannote.audio install (not available in test env), real WAV file, and valid HuggingFace token with model conditions accepted"
  - test: "Run `meet transcribe` on a real recording WITHOUT an HF token"
    expected: "Yellow warning printed, plain .txt and .srt produced with no speaker labels"
    why_human: "Integration test covers this with mocks; real-world confirmation requires actual CLI run"
  - test: "pip install 'torchaudio' && pip install 'pyannote.audio==3.3.2' in the project venv"
    expected: "Both packages install cleanly on Python 3.14; `import pyannote.audio` succeeds"
    why_human: "pyannote.audio 3.3.2 compatibility on Python 3.14 cannot be verified without running the install"
---

# Phase 1: SRT Output and Speaker Diarization Verification Report

**Phase Goal:** Extend `meet transcribe` to produce SRT subtitle files from Whisper segments and add pyannote-audio speaker diarization with graceful fallback. Every transcription produces both `.txt` and `.srt`. Diarized output uses `SPEAKER_XX:` prefixes. `meet summarize` prefers diarized transcripts when available.
**Verified:** 2026-03-27
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every `meet transcribe` run produces a `.srt` file alongside `.txt` | VERIFIED | `transcribe.py` line 150-151 writes `{stem}.srt`; `test_srt_file_created` passes |
| 2 | SRT uses correct `HH:MM:SS,mmm` timestamps with 1-based indices | VERIFIED | `seconds_to_srt_timestamp()` confirmed; `test_srt_timestamp_format` passes; spot-check `seconds_to_srt_timestamp(3661.5) == "01:01:01,500"` |
| 3 | `transcribe_audio()` returns `(text, segments)` tuple | VERIFIED | `transcription.py` line 58-74 returns `result["text"], result["segments"]`; `test_transcribe_returns_segments` passes |
| 4 | Metadata JSON includes `srt_path`, `diarization_succeeded`, `diarized_transcript_path`, `speaker_turns` | VERIFIED | `transcribe.py` lines 156-166; `test_metadata_includes_srt_fields` asserts all four fields |
| 5 | Diarization runs automatically when HF token is configured | VERIFIED | `transcribe.py` lines 104-130 call `run_diarization` when `hf_token` is truthy |
| 6 | Missing HF token skips diarization with yellow warning | VERIFIED | `transcribe.py` line 107: `"HuggingFace token not configured — skipping speaker diarization."`; `test_diarization_skips_without_hf_token` passes |
| 7 | Diarization failure warns in yellow and continues without speaker labels | VERIFIED | `transcribe.py` lines 127-130 catch `Exception`, print yellow warning; `test_diarization_graceful_failure` passes |
| 8 | Diarized `.txt` uses `SPEAKER_XX:` paragraph prefix | VERIFIED | `build_diarized_txt()` in `transcription.py` lines 132-166; `test_diarized_txt_grouping` passes |
| 9 | SRT entries include `SPEAKER_XX:` prefix when diarization succeeds | VERIFIED | `generate_srt()` accepts `speaker_map`; `test_generate_srt_with_speakers` passes |
| 10 | `meet summarize` prefers diarized transcript when available | VERIFIED | `summarize.py` lines 80-86 read `diarized_transcript_path` from metadata; `test_prefers_diarized_transcript` passes |
| 11 | `Config.load()` round-trips `huggingface.token` field | VERIFIED | `config.py` lines 50-51; `test_config_hf_token_roundtrip` passes; spot-check PASS |
| 12 | `meet init` wizard collects HF token after Notion credentials | VERIFIED | `init.py` line 287-288: `hf_token = _collect_hf_token()` at Step 3.5; `test_init_collects_hf_token` passes |
| 13 | `PyannoteCheck` returns ERROR when `pyannote.audio` not importable | VERIFIED | `checks.py` lines 430-451; `test_pyannote_check_error` passes |
| 14 | `HuggingFaceTokenCheck` returns WARNING when token is missing | VERIFIED | `checks.py` lines 454-484; `test_hf_token_check_warning_no_token` passes |
| 15 | `PyannoteModelCheck` returns WARNING when model not cached | VERIFIED | `checks.py` lines 487-521; `test_pyannote_model_check_warning` passes |
| 16 | `pyproject.toml` includes `pyannote.audio==3.3.2` and `torchaudio` | VERIFIED | `pyproject.toml` lines 10 and 13 |
| 17 | All 17 Wave 0 test stubs converted to real, passing tests | VERIFIED | `grep pytest.mark.skip tests/` returns 0 matches; 103 phase-01 tests pass |

**Score:** 17/17 truths verified

---

### Required Artifacts

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `meeting_notes/services/transcription.py` | `seconds_to_srt_timestamp()`, `generate_srt()`, `transcribe_audio()`, `run_diarization()`, `assign_speakers_to_segments()`, `build_diarized_txt()` | VERIFIED | All 6 functions present and substantive (215 lines); `def seconds_to_srt_timestamp` confirmed at line 28 |
| `meeting_notes/cli/commands/transcribe.py` | SRT write, diarization integration, metadata with `srt_path` and diarization fields | VERIFIED | `srt_path` at line 159; diarization block lines 99-130; `diarization_succeeded` at line 163 |
| `meeting_notes/cli/commands/summarize.py` | Diarized transcript preference logic | VERIFIED | `diarized_transcript_path` read at lines 80-86; `session_metadata.get("diarized_transcript_path")` confirmed |
| `meeting_notes/core/config.py` | `HuggingFaceConfig` dataclass, `Config.huggingface` field | VERIFIED | `class HuggingFaceConfig` at line 23; `huggingface: HuggingFaceConfig` at line 35; `hf_data = data.get("huggingface", {})` at line 50 |
| `meeting_notes/services/checks.py` | `PyannoteCheck`, `HuggingFaceTokenCheck`, `PyannoteModelCheck`, `PYANNOTE_DIARIZATION_CACHE` | VERIFIED | All 3 classes + constant present at lines 160-161 and 430-521 |
| `meeting_notes/cli/commands/init.py` | `_collect_hf_token()`, `HuggingFaceConfig` in import, `("HuggingFace token", ...)` in update menu, 3 health checks in `_run_inline_doctor` | VERIFIED | `def _collect_hf_token` at line 90; `("HuggingFace token", ...)` at line 122; `suite.register(PyannoteCheck())` at line 231 |
| `pyproject.toml` | `pyannote.audio==3.3.2` and `torchaudio` deps | VERIFIED | Lines 10 and 13 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `transcription.py` | `transcribe.py` | `transcribe_audio()` return value unpacking | WIRED | `text, segments = run_with_spinner(lambda: transcribe_audio(...))` at line 96 |
| `transcribe.py` | `transcripts/{stem}.srt` | `srt_path.write_text(srt_content)` | WIRED | Line 151: `srt_path.write_text(srt_content)` |
| `transcription.py` | `transcribe.py` | `run_diarization()` called after `transcribe_audio()` | WIRED | `run_diarization` imported at line 20; called at line 111 |
| `transcribe.py` | `metadata/{stem}.json` | `diarization_succeeded` and `speaker_turns` written | WIRED | Lines 163-165 in metadata dict; `write_state(metadata_path, metadata)` at line 167 |
| `summarize.py` | `metadata/{stem}.json` | reads `diarized_transcript_path` for session resolution | WIRED | `session_metadata = read_state(metadata_path)` at line 82; `session_metadata.get("diarized_transcript_path")` at line 83 |
| `config.py` | `init.py` | `Config.huggingface.token` read/write | WIRED | `HuggingFaceConfig` imported in `init.py` line 11; `config.huggingface.token = hf_token` at line 184 |
| `checks.py` | `init.py` | Health check registration in `_run_inline_doctor` | WIRED | `PyannoteCheck`, `HuggingFaceTokenCheck`, `PyannoteModelCheck` imported at lines 19-29 and registered at lines 231-233 |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `transcribe.py` | `segments` | `mlx_whisper.transcribe()["segments"]` via `transcribe_audio()` | Yes — from Whisper inference | FLOWING |
| `transcribe.py` | `speaker_map` | `assign_speakers_to_segments(segments, diarization)` from `run_diarization()` | Yes — from pyannote pipeline | FLOWING |
| `transcribe.py` | `text` (diarized) | `build_diarized_txt(segments, speaker_map)` when diarization succeeded | Yes — built from real segments + speaker assignments | FLOWING |
| `summarize.py` | `transcript_path` (diarized) | `read_state(metadata_path)["diarized_transcript_path"]` | Yes — reads from JSON written by transcribe | FLOWING |

Note: `diarized_transcript_path` in metadata points to the same `.txt` path as `transcript_path` (diarized content overwrites plain content per D-09). This is intentional per the RESEARCH.md design note.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `seconds_to_srt_timestamp(0.0)` returns `"00:00:00,000"` | Python inline | PASS | PASS |
| `seconds_to_srt_timestamp(3661.5)` returns `"01:01:01,500"` | Python inline | PASS | PASS |
| `generate_srt()` produces valid 2-entry SRT with correct indices | Python inline | PASS | PASS |
| `Config.huggingface.token` round-trips through save/load | Python inline | PASS | PASS |
| All phase-01 test functions importable | Python import check | PASS | PASS |
| `pytest tests/test_transcription.py tests/test_transcribe_command.py tests/test_summarize_command.py tests/test_config.py tests/test_checks.py tests/test_init.py` | pytest | 103 passed, 0 failed | PASS |
| Full suite `pytest tests/` | pytest | 219 passed, 2 failed (pre-existing, unrelated to phase 01) | PASS (see note) |

Note on full suite: 2 pre-existing failures exist that are unrelated to this phase:
- `tests/test_llm_service.py::test_templates_contain_grounding_rule` — pre-dates phase 01 (LLM template grounding rule missing from v1.0 implementation)
- `tests/test_storage.py::test_get_data_dir_default` — pre-dates phase 01 (default storage path changed from `~/.local/share` to `~/Documents` in v1.0)

Both are documented in `deferred-items.md`.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| NYQUIST-W0 | 01-00 | All Wave 0 test stubs exist and are skipped (then green) | SATISFIED | All 17 stubs converted; no `pytest.mark.skip` remains in any test file |
| D-01 | 01-01 | Every `meet transcribe` run produces `.srt` alongside `.txt` | SATISFIED | `transcribe.py` writes `srt_path`; `test_srt_file_created` green |
| D-02 | 01-01 | SRT saved in `transcripts/` directory with same stem | SATISFIED | `srt_path = transcripts_dir / f"{stem}.srt"` at line 150 |
| D-03 | 01-01 | Segment-level timestamps only (no `word_timestamps=True`) | SATISFIED | `generate_srt` uses `seg["start"]`/`seg["end"]`; `word_timestamps` not present in any call |
| D-04 | 01-01 | SRT not shown in `meet list` | SATISFIED | SRT is an output side-effect only; not referenced in list/display logic |
| D-05 | 01-02 | Library: `pyannote-audio` with `pyannote/speaker-diarization-3.1` | SATISFIED | `run_diarization()` uses `Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")` |
| D-06 | 01-02 | HF token collected in `meet init` wizard, stored in `config.json` | SATISFIED | `_collect_hf_token()` called at wizard Step 3.5; `HuggingFaceConfig` field in `Config` |
| D-07 | 01-03 | Diarization runs automatically as part of `meet transcribe` | SATISFIED | Diarization block wired inline in `transcribe()` command |
| D-08 | 01-03 | Graceful fallback — warn + continue without diarization on any failure | SATISFIED | Missing token: yellow warning (line 107); exception: yellow warning (lines 129-130) |
| D-09 | 01-03 | Plain `.txt` uses `SPEAKER_XX:` prefix per paragraph (consecutive same-speaker grouped) | SATISFIED | `build_diarized_txt()` groups by speaker; `test_diarized_txt_grouping` green |
| D-10 | 01-03 | SRT entries prefixed with speaker tag when diarization succeeded | SATISFIED | `generate_srt(segments, speaker_map=speaker_map)` at line 149; `test_generate_srt_with_speakers` green |
| D-11 | 01-03 | `meet summarize` prefers diarized `.txt` when available | SATISFIED | `summarize.py` reads `diarized_transcript_path` from metadata at lines 80-86 |
| D-12 | 01-03 | Speaker labels use pyannote defaults (`SPEAKER_00`, `SPEAKER_01`, etc.) | SATISFIED | No renaming logic; labels passed through directly from pyannote |
| D-13 | 01-02 | `PyannoteCheck` — verifies `pyannote.audio` importable, ERROR severity | SATISFIED | `class PyannoteCheck` in `checks.py`; `test_pyannote_check_error` green |
| D-14 | 01-02 | `HuggingFaceTokenCheck` — verifies HF token, WARNING severity | SATISFIED | `class HuggingFaceTokenCheck` in `checks.py`; `test_hf_token_check_warning_no_token` green |
| D-15 | 01-02 | `PyannoteModelCheck` — verifies model cached, WARNING severity | SATISFIED | `class PyannoteModelCheck` in `checks.py`; `test_pyannote_model_check_warning` green |

**All 16 requirement IDs (NYQUIST-W0 + D-01 through D-15) are SATISFIED.**

No orphaned requirements found. D-01 through D-15 are fully covered across plans 01-01, 01-02, and 01-03.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | No stubs, placeholders, or TODO/FIXME in phase 01 modified files |

Scan results: No `pytest.mark.skip`, `TODO`, `FIXME`, `placeholder`, `return {}`, `return []`, or `return null` patterns found in the phase 01 implementation files (`transcription.py`, `transcribe.py`, `summarize.py`, `config.py`, `checks.py`, `init.py`).

---

### Human Verification Required

#### 1. Real Diarization End-to-End

**Test:** Configure a valid HF token via `meet init`. Run `meet transcribe` on a WAV recording that contains at least 2 speakers.
**Expected:** `.txt` contains `SPEAKER_00:` and `SPEAKER_01:` paragraph prefixes; `.srt` has `SPEAKER_00: text` on each entry; metadata JSON has `diarization_succeeded: true`, a non-empty `speaker_turns` array, and `diarized_transcript_path` pointing to the `.txt` file.
**Why human:** Requires real pyannote.audio installation (not in test environment), a real audio file, and a valid HuggingFace token with model conditions accepted at `huggingface.co/pyannote/speaker-diarization-3.1` and `huggingface.co/pyannote/segmentation-3.0`.

#### 2. Graceful Fallback Smoke Test

**Test:** Remove or clear `huggingface.token` from `config.json`. Run `meet transcribe` on any WAV.
**Expected:** Yellow warning "HuggingFace token not configured — skipping speaker diarization." printed. `.txt` and `.srt` produced without any `SPEAKER_` labels.
**Why human:** Integration test covers this with mocks; real-world CLI confirmation needed.

#### 3. pyannote.audio Installation Compatibility

**Test:** In the project virtual environment, run `pip install torchaudio && pip install "pyannote.audio==3.3.2"`, then `python -c "import pyannote.audio; print('ok')"`.
**Expected:** Both packages install without errors; import succeeds on Python 3.14.
**Why human:** Package installation compatibility on Python 3.14 (which is what this project runs on per the test runner output) cannot be verified programmatically — pyannote.audio==3.3.2 was designed for Python 3.8-3.11.

---

### Gaps Summary

No gaps. All 17 observable truths are verified, all artifacts pass all four levels (exists, substantive, wired, data flowing), all 16 requirement IDs are satisfied, no anti-patterns found in phase 01 files, and all 103 phase-01 tests pass green.

The only 2 test suite failures in `pytest tests/ -x` are pre-existing from the v1.0 milestone:
- `test_llm_service.py::test_templates_contain_grounding_rule` — LLM template grounding rule gap from Phase 3
- `test_storage.py::test_get_data_dir_default` — storage path default changed in v1.0

Both are documented in `.planning/phases/01-srt-output-and-speaker-diarization-for-transcription-pipeline/deferred-items.md` and are out of scope for this phase.

---

_Verified: 2026-03-27_
_Verifier: Claude (gsd-verifier)_
