---
phase: 02-local-transcription
plan: 02
subsystem: health-checks
tags: [mlx-whisper, health-check, doctor, pyproject]

# Dependency graph
requires:
  - phase: 02-local-transcription
    plan: 01
    provides: MlxWhisperCheck/WhisperModelCheck depend on mlx-whisper service from plan 01
  - phase: 01-audio-capture-health-check-design
    provides: HealthCheck ABC, CheckResult, CheckStatus, HealthCheckSuite
provides:
  - MlxWhisperCheck: verifies mlx-whisper is importable
  - WhisperModelCheck: verifies whisper-large-v3-turbo model is cached (WARNING not ERROR when missing)
  - meet doctor now runs 5 checks including mlx-whisper import and model cache status
  - mlx-whisper declared as project dependency in pyproject.toml
affects: [05-integrated-cli]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - WhisperModelCheck returns WARNING (not ERROR) when model absent — non-blocking advisory per D-08
    - MlxWhisperCheck uses try/except ImportError with noqa F401 for side-effect-free import check
    - MODEL_CACHE_DIR module-level constant allows monkeypatching in tests

key-files:
  created: []
  modified:
    - meeting_notes/services/checks.py
    - meeting_notes/cli/commands/doctor.py
    - pyproject.toml
    - tests/test_health_check.py

key-decisions:
  - "WhisperModelCheck returns WARNING not ERROR when model not cached — model auto-downloads on first transcription (D-08)"
  - "No version pin on mlx-whisper in pyproject.toml — already installed and API is stable"
  - "MODEL_CACHE_DIR and HF_HUB_CACHE as module-level constants enable clean monkeypatching in tests"

requirements-completed: [TRANS-01, TRANS-05]

# Metrics
duration: 78s
completed: 2026-03-22
---

# Phase 2 Plan 02: Doctor Health Checks + mlx-whisper Dependency Summary

**Two new HealthCheck subclasses (MlxWhisperCheck, WhisperModelCheck) registered in `meet doctor`, mlx-whisper added to pyproject.toml, and 4 unit tests confirming import check and WARNING-not-ERROR model cache behavior**

## Performance

- **Duration:** 78s
- **Started:** 2026-03-22T21:07:56Z
- **Completed:** 2026-03-22T21:09:14Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- MlxWhisperCheck added: returns OK when mlx_whisper importable, ERROR with `pip install mlx-whisper` fix suggestion when not
- WhisperModelCheck added: returns OK when ~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo exists, WARNING (not ERROR) when absent per D-08
- Both checks registered in `meet doctor` — suite now runs 5 checks total
- mlx-whisper added to pyproject.toml dependencies (alphabetical, no version pin)
- 4 new unit tests; full 74-test suite passes

## Task Commits

Each task was committed atomically:

1. **Task 1: MlxWhisperCheck + WhisperModelCheck + tests** - `17465fb` (feat)
2. **Task 2: Register checks in doctor + add mlx-whisper to pyproject.toml** - `df142e1` (feat)

## Files Created/Modified

- `meeting_notes/services/checks.py` - Added Path import, HF_HUB_CACHE/MODEL_CACHE_DIR constants, MlxWhisperCheck and WhisperModelCheck classes
- `meeting_notes/cli/commands/doctor.py` - Added MlxWhisperCheck/WhisperModelCheck imports and two suite.register() calls
- `pyproject.toml` - Added "mlx-whisper" to dependencies list (alphabetical)
- `tests/test_health_check.py` - Added 4 tests: test_mlx_whisper_check_ok, test_mlx_whisper_check_error, test_whisper_model_check_ok, test_whisper_model_check_warning

## Decisions Made

- WhisperModelCheck returns WARNING not ERROR when model not cached — model auto-downloads on first `meet transcribe` invocation (D-08), so absence is advisory, not blocking
- No version pin on mlx-whisper — already installed in dev environment and API is stable
- MODULE_CACHE_DIR as module-level constant allows clean monkeypatching without needing to patch pathlib directly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — mlx-whisper was already installed. `pip install -e .` will pick up the new dependency declaration.

## Known Stubs

None.

## Next Phase Readiness

- Phase 2 fully complete: `meet transcribe` implemented (plan 01) + `meet doctor` extended with transcription prerequisites (plan 02)
- Phase 3 note generation can proceed: mlx-whisper validated by health check, transcript files available

---
*Phase: 02-local-transcription*
*Completed: 2026-03-22*
