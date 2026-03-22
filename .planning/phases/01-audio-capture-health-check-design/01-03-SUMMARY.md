---
phase: 01-audio-capture-health-check-design
plan: 03
subsystem: health-check
tags: [health-check, cli, abc, tdd, doctor, init]
dependency_graph:
  requires: ["01-01", "01-02"]
  provides: ["health-check-abc", "meet-doctor", "meet-init"]
  affects: ["all-future-phases"]
tech_stack:
  added: []
  patterns:
    - "Pluggable health check architecture via ABC + HealthCheckSuite registry"
    - "TDD red-green cycle: tests committed before implementation"
    - "Click CliRunner for command integration tests"
    - "monkeypatch for subprocess and shutil in health check tests"
key_files:
  created:
    - meeting_notes/core/health_check.py
    - meeting_notes/services/checks.py
    - meeting_notes/cli/commands/doctor.py
    - meeting_notes/cli/commands/init.py
  modified:
    - meeting_notes/cli/main.py
    - tests/test_health_check.py
    - tests/test_doctor_command.py
decisions:
  - "HealthCheck ABC with abstractmethod prevents direct instantiation by design"
  - "BlackHoleCheck checks device NAME at index (not just index reachability) per pitfall P1 in research"
  - "DiskSpaceCheck returns WARNING (not ERROR) below 5GB — non-fatal advisory"
  - "meet init triggers 1s test recording via avfoundation to force macOS mic permission prompt (SETUP-02)"
metrics:
  duration_seconds: 225
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_created: 4
  files_modified: 3
---

# Phase 01 Plan 03: Health Check Architecture + meet doctor / meet init Summary

**One-liner:** Pluggable health check ABC (HealthCheck/HealthCheckSuite) with BlackHoleCheck, FFmpegDeviceCheck, DiskSpaceCheck, and meet doctor/init CLI commands.

## What Was Built

### Core Architecture (`meeting_notes/core/health_check.py`)

- `CheckStatus` enum: OK / WARNING / ERROR
- `CheckResult` dataclass: status, message, fix_suggestion (optional)
- `HealthCheck` ABC: abstract `check()` method — direct instantiation raises TypeError
- `HealthCheckSuite`: registry with `register()`, `run_all()` (returns `list[tuple[HealthCheck, CheckResult]]`), `has_errors()`

### Phase 1 Checks (`meeting_notes/services/checks.py`)

- `BlackHoleCheck`: parses ffmpeg avfoundation stderr, checks device NAME at index for "BlackHole" — not just index reachability
- `FFmpegDeviceCheck`: verifies microphone device exists at given index in parsed device list
- `DiskSpaceCheck`: `shutil.disk_usage("/")` — OK if >5GB, WARNING if ≤5GB

### CLI Commands

- `meet doctor`: loads config, creates suite with 3 checks, prints Rich-formatted results with status icons (✓ / ! / ✗), exits 1 on any ERROR
- `meet init`: lists ffmpeg devices, prompts for indices, writes config.json, triggers 1-second avfoundation test recording to prompt macOS mic permissions
- `meeting_notes/cli/main.py`: registered doctor and init commands

### Tests

- `tests/test_health_check.py`: 9 tests — ABC enforcement, dataclass, suite behavior, all 3 checks with monkeypatched subprocess/shutil
- `tests/test_doctor_command.py`: 3 tests — all-pass exit 0, error exit 1, ok exit 0 using Click CliRunner

## Decisions Made

1. HealthCheck ABC with `@abstractmethod` — correct Python pattern; TypeError on direct instantiation is the expected Python behavior
2. BlackHoleCheck checks device NAME (not just index existence) — per pitfall P1 in research: must verify "BlackHole" is in the device name
3. DiskSpaceCheck returns WARNING not ERROR — low disk is advisory, not a hard blocker
4. meet init triggers 1-second test recording — forces macOS mic permission dialog per SETUP-02

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None — all Phase 1 checks are fully implemented and wired to the CLI. meet doctor and meet init are complete.

## Test Results

```
tests/test_health_check.py    9 passed
tests/test_doctor_command.py  3 passed
Full suite (tests/)          45 passed
```

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| TDD RED | b86c3a9 | test(01-03): add failing tests for health check ABC and Phase 1 checks |
| TDD GREEN (Task 1) | bd6f26e | feat(01-03): implement HealthCheck ABC, HealthCheckSuite, and Phase 1 checks |
| Task 2 | e420b4b | feat(01-03): implement meet doctor and meet init CLI commands |

## Self-Check: PASSED

All files created and all commits verified present.
