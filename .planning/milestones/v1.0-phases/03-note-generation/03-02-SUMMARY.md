---
phase: 03-note-generation
plan: "02"
subsystem: health-checks
tags: [ollama, health-check, doctor, tdd]
dependency_graph:
  requires: []
  provides: [OllamaRunningCheck, OllamaModelCheck]
  affects: [meet-doctor]
tech_stack:
  added: [requests]
  patterns: [HealthCheck ABC subclass, subprocess.run for CLI, requests.get with timeout]
key_files:
  created: []
  modified:
    - meeting_notes/services/checks.py
    - meeting_notes/cli/commands/doctor.py
    - tests/test_health_check.py
decisions:
  - OllamaRunningCheck returns ERROR (not WARNING) per D-09 — Ollama cannot auto-start
  - OllamaModelCheck returns ERROR (not WARNING) per D-10 — models cannot auto-download
  - requests library used for HTTP check to localhost:11434 (timeout=5s)
  - subprocess.run used for ollama list CLI check (timeout=10s)
metrics:
  duration_seconds: 84
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_modified: 3
---

# Phase 3 Plan 02: Ollama Health Checks Summary

**One-liner:** Added OllamaRunningCheck and OllamaModelCheck to checks.py and registered both in meet doctor, with full TDD test coverage using monkeypatching.

## What Was Built

Two new health check classes added to `meeting_notes/services/checks.py`:

- **OllamaRunningCheck** (`name = "Ollama Service"`): Makes a GET request to `http://localhost:11434` with a 5-second timeout. Returns OK on HTTP 200, ERROR with "Run: ollama serve" fix on ConnectionError or any other exception.
- **OllamaModelCheck** (`name = "Ollama Model (llama3.1:8b)"`): Runs `ollama list` via subprocess. Returns OK when "llama3.1:8b" appears in stdout, ERROR with "Run: ollama pull llama3.1:8b" when missing, ERROR with ollama.com install link on FileNotFoundError.

Both classes were registered in `meet doctor` (7 total checks now) and covered by 5 new tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add OllamaRunningCheck and OllamaModelCheck | 5c39df9 | meeting_notes/services/checks.py |
| 2 | Register Ollama checks in doctor.py and add tests | de3eb55 | meeting_notes/cli/commands/doctor.py, tests/test_health_check.py |

## Verification Results

- `python3 -c "from meeting_notes.services.checks import OllamaRunningCheck, OllamaModelCheck; print('imports OK')"` — passed
- `python3 -c "from meeting_notes.cli.commands.doctor import doctor; print('doctor imports OK')"` — passed
- `python3 -m pytest tests/test_health_check.py -x -q` — 18 passed
- `python3 -m pytest -x -q` — 81 passed (no regressions)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- `meeting_notes/services/checks.py` contains OllamaRunningCheck and OllamaModelCheck
- `meeting_notes/cli/commands/doctor.py` imports and registers both checks
- `tests/test_health_check.py` contains all 5 new Ollama test functions
- Commits 5c39df9 and de3eb55 exist in git log
