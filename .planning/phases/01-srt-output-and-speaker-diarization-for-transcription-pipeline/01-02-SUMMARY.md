---
phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline
plan: "02"
subsystem: config, health-checks, init-wizard, deps
tags: [config, huggingface, pyannote, health-checks, init-wizard, diarization-infra]
one_liner: "HuggingFaceConfig dataclass + 3 pyannote health checks + HF token wizard step + pyannote.audio==3.3.2 deps"
dependency_graph:
  requires: [01-00]
  provides: [HuggingFaceConfig, PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck, init-hf-wizard]
  affects: [meeting_notes/core/config.py, meeting_notes/services/checks.py, meeting_notes/cli/commands/init.py, pyproject.toml]
tech_stack:
  added: [huggingface_hub, pyannote.audio==3.3.2, torchaudio]
  patterns: [HealthCheck ABC subclass, dataclass config field, TDD RED-GREEN]
key_files:
  created: [tests/test_checks.py]
  modified:
    - meeting_notes/core/config.py
    - meeting_notes/services/checks.py
    - meeting_notes/cli/commands/init.py
    - pyproject.toml
    - tests/test_config.py
    - tests/test_init.py
decisions:
  - "HfApi imported at module level in both checks.py and init.py so tests can patch meeting_notes.services.checks.HfApi and meeting_notes.cli.commands.init.HfApi"
  - "HuggingFaceTokenCheck validates via HfApi().whoami() at check time — WARNING not ERROR when token absent (Notion pattern)"
  - "PyannoteCheck returns ERROR (not WARNING) when pyannote.audio not importable — matches MlxWhisperCheck severity"
  - "PyannoteModelCheck returns WARNING — model auto-downloads on first meet transcribe (WhisperModelCheck pattern)"
  - "_collect_hf_token() placed as step 3.5 in wizard (after Notion, before config save) — token optional, blank=skip"
  - "Field [7] added to update menu for HuggingFace token — consistent with existing 1-6 field numbering"
metrics:
  duration_seconds: ~720
  tasks_completed: 2
  files_changed: 6
  tests_added: 25
  completed_date: "2026-03-27"
---

# Phase 1 Plan 02: HuggingFace Config, Pyannote Health Checks, Init Wizard Summary

## What Was Built

Infrastructure for speaker diarization without touching the transcription pipeline. Sets up all the prerequisites that Plan 03 (diarization) will depend on.

**HuggingFaceConfig** — new dataclass in `config.py` with `token: str | None = None` field. `Config.load()` and `Config.save()` round-trip the `huggingface` JSON section. `Config` now has `huggingface: HuggingFaceConfig = field(default_factory=HuggingFaceConfig)`.

**3 new health checks** in `checks.py`:
- `PyannoteCheck` — ERROR when pyannote.audio not importable (install gate for diarization)
- `HuggingFaceTokenCheck(token)` — WARNING when token absent or validation fails, OK when HfApi().whoami() succeeds
- `PyannoteModelCheck` — WARNING when `PYANNOTE_DIARIZATION_CACHE` not on disk, OK when cached

**Constants added** — `PYANNOTE_DIARIZATION_CACHE` and `PYANNOTE_SEGMENTATION_CACHE` next to existing `MODEL_CACHE_DIR`.

**Init wizard** — `_collect_hf_token()` is step 3.5 after Notion credentials. Blank entry skips (returns None). Valid token is verified via `HfApi().whoami()`. The update menu now shows field `[7] HuggingFace token`. `_run_inline_doctor()` registers all 3 new checks.

**pyproject.toml** — `pyannote.audio==3.3.2` and `torchaudio` added to dependencies.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing test_init.py failures caused by cb3a91a commit**
- **Found during:** Task 1 (full test run)
- **Issue:** `cb3a91a change default folders to store recordings` added a storage path prompt to `init()` but did not update test inputs. 9 tests were consuming the storage path prompt with the Notion token, causing Abort.
- **Fix:** Added `\n` to each test's input string for the storage path prompt (blank = default). This fix was required to maintain the test baseline before adding the HF token step.
- **Files modified:** `tests/test_init.py`
- **Commit:** 093d3fd (part of Task 1 commit)

**2. [Rule 1 - Bug] Updated test inputs again for new HF token wizard step**
- **Found during:** Task 2 (init tests after adding _collect_hf_token)
- **Issue:** Adding the HF token prompt to the full wizard required another `\n` at the end of all wizard test inputs.
- **Fix:** Added trailing `\n` (blank = skip HF token) to 9 existing tests + 3 new HF token tests added.
- **Files modified:** `tests/test_init.py`
- **Commit:** 3d54645

## Self-Check: PASSED

- meeting_notes/core/config.py: FOUND
- meeting_notes/services/checks.py: FOUND
- meeting_notes/cli/commands/init.py: FOUND
- tests/test_checks.py: FOUND
- Commit 093d3fd: FOUND
- Commit 3d54645: FOUND
