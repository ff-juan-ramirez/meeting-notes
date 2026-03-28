---
phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline
plan: "04"
subsystem: doctor, init, checks, transcription
tags: [gap-closure, pyannote, doctor, init, health-checks, torchaudio, monkey-patch]
one_liner: "Wired 3 pyannote health checks into meet doctor, added --update CLI flag to meet init, and fixed pyannote.audio import for torchaudio>=2.9 via monkey-patch"

dependency_graph:
  requires: ["01-02", "01-03"]
  provides:
    - "PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck registered in doctor command"
    - "meet init --update CLI flag routing to _update_specific_fields flow"
    - "torchaudio.list_audio_backends compatibility patch for pyannote.audio 3.x"
  affects:
    - "meeting_notes/cli/commands/doctor.py"
    - "meeting_notes/cli/commands/init.py"
    - "meeting_notes/services/checks.py"
    - "meeting_notes/services/transcription.py"
    - "pyproject.toml"

tech_stack:
  added: []
  patterns:
    - "Monkey-patch torchaudio.list_audio_backends before pyannote.audio import to support torchaudio>=2.9"
    - "Click --update is_flag=True for direct CLI field update without interactive prompt"

key_files:
  created: []
  modified:
    - meeting_notes/cli/commands/doctor.py
    - meeting_notes/cli/commands/init.py
    - meeting_notes/services/checks.py
    - meeting_notes/services/transcription.py
    - pyproject.toml

decisions:
  - "torchaudio.list_audio_backends monkey-patch: pyannote.audio 3.x calls this function at import time but it was removed in torchaudio>=2.9 (the only versions available for Python 3.14). Patch adds missing function with ['soundfile'] backend before each lazy import."
  - "pyannote.audio version pin relaxed from ==3.3.2 to >=3.3.2,<5: strict pin conflicted with pip installing 3.4.0 due to torchaudio/pyannote.core dependencies. Both versions need the same monkey-patch."
  - "--update flag implementation: early-exit at top of init() body, before existing config-exists check, routes to _update_specific_fields + _run_test_recording + _run_inline_doctor flow."

metrics:
  duration_seconds: 480
  completed_date: "2026-03-28"
  tasks_completed: 2
  files_modified: 5
---

# Phase 01 Plan 04: Gap Closure — Pyannote Doctor Wiring, Init --update Flag, Pyannote Import Fix Summary

Wired 3 pyannote health checks into `meet doctor`, added `--update` CLI flag to `meet init`, and fixed `pyannote.audio` import incompatibility with `torchaudio>=2.9` via a targeted monkey-patch.

## What Was Built

### Task 1: Register pyannote checks in doctor.py and add --update flag to init.py

**doctor.py changes:**
- Added `HuggingFaceTokenCheck`, `PyannoteCheck`, `PyannoteModelCheck` to import block
- Added 3 `suite.register()` calls after `NotionDatabaseCheck`: `PyannoteCheck()`, `HuggingFaceTokenCheck(config.huggingface.token)`, `PyannoteModelCheck()`
- `meet doctor` now shows all 3 pyannote health checks in output (UAT Test 5 unblocked)

**init.py changes:**
- Added `@click.option('--update', is_flag=True, default=False)` decorator to `init` command
- Added `update: bool` parameter to `init()` function signature
- Added early-exit guard: when `--update` is passed, loads config and routes to `_update_specific_fields()` + `_run_test_recording()` + `_run_inline_doctor()` (UAT Test 4 unblocked)

**Commit:** `d6b7d53`

### Task 2: Reinstall editable package + fix pyannote.audio import (with auto-fix deviation)

- Ran `pip install -e .` from main repo to reinstall editable package against current `pyproject.toml`
- Discovered `pyannote.audio` still failed to import: `AttributeError: module 'torchaudio' has no attribute 'list_audio_backends'`
- Root cause: pyannote.audio 3.x calls `torchaudio.list_audio_backends()` at import time; function was removed in torchaudio>=2.9 (minimum version available for Python 3.14 on macOS)
- Auto-fix (Rule 1 - Bug): added monkey-patch in `PyannoteCheck.check()` and `run_diarization()` before lazy pyannote import
- Relaxed `pyannote.audio` pin from `==3.3.2` to `>=3.3.2,<5` in `pyproject.toml` to resolve pip dependency conflict

**Commits:** `31ef46b` (monkey-patch), `5489de8` (version pin)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pyannote.audio AttributeError on torchaudio>=2.9**
- **Found during:** Task 2 (reinstall verification)
- **Issue:** `pyannote.audio 3.x` calls `torchaudio.list_audio_backends()` at import time; this function was removed in `torchaudio>=2.9`. The `PyannoteCheck.check()` only caught `ImportError`, not `AttributeError`. The `run_diarization()` function also had no protection.
- **Fix:** Added `if not hasattr(torchaudio, 'list_audio_backends'): torchaudio.list_audio_backends = lambda: ['soundfile']` before each lazy `pyannote.audio` import in both `checks.py` and `transcription.py`.
- **Files modified:** `meeting_notes/services/checks.py`, `meeting_notes/services/transcription.py`
- **Commit:** `31ef46b`

**2. [Rule 1 - Bug] Relaxed pyannote.audio version pin to resolve pip conflict**
- **Found during:** Task 2 (pip install)
- **Issue:** `pyproject.toml` pinned `pyannote.audio==3.3.2` but pip resolved to 3.4.0 due to `pyannote.core` version conflict with 3.3.2. Strict pin caused pip dependency conflict warning.
- **Fix:** Changed pin from `==3.3.2` to `>=3.3.2,<5`. Both versions need the same monkey-patch.
- **Files modified:** `pyproject.toml`
- **Commit:** `5489de8`

### Pre-existing Issue (Not Fixed — Out of Scope)

`test_llm_service.py::test_templates_contain_grounding_rule` was already failing before this plan's changes (confirmed by stash test). The meeting template doesn't include the expected grounding rule text. This is out of scope for plan 01-04 which focuses on pyannote wiring and doctor/init gaps.

## Known Stubs

None — all plan goals fully implemented and verified.

## Verification Results

1. `grep -q "suite.register(PyannoteCheck"` doctor.py — PASS
2. `grep -q "suite.register(HuggingFaceTokenCheck"` doctor.py — PASS
3. `grep -q "suite.register(PyannoteModelCheck"` doctor.py — PASS
4. `grep -q "\-\-update"` init.py — PASS
5. `python -c "import torchaudio; torchaudio.list_audio_backends = lambda: ['soundfile']; import pyannote.audio"` — PASS
6. `pytest tests/test_doctor_command.py tests/test_init.py tests/test_checks.py -x -q` — 51 passed

## UAT Gap Closure

| UAT Test | Issue | Status After Plan 04 |
|----------|-------|---------------------|
| 4 | `meet init --update` not found | CLOSED: `--update` flag added to Click decorator |
| 5 | `meet doctor` missing pyannote checks | CLOSED: 3 pyannote checks registered in doctor.py |
| 8 | `pyannote.audio` not importable | CLOSED: torchaudio monkey-patch + pip reinstall |

## Self-Check: PASSED

All files verified present:
- FOUND: meeting_notes/cli/commands/doctor.py
- FOUND: meeting_notes/cli/commands/init.py
- FOUND: meeting_notes/services/checks.py
- FOUND: .planning/phases/.../01-04-SUMMARY.md

All commits verified:
- FOUND: d6b7d53 (feat: pyannote checks in doctor + --update flag)
- FOUND: 31ef46b (fix: torchaudio monkey-patch)
- FOUND: 5489de8 (chore: version pin relaxation)
