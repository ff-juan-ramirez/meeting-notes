---
phase: 03-note-generation
plan: 01
subsystem: llm-service
tags: [llm, ollama, templates, requests, tdd]
dependency_graph:
  requires: []
  provides: [meeting_notes.services.llm, meeting_notes.templates]
  affects: [03-02-summarize-command]
tech_stack:
  added: [requests>=2.28]
  patterns: [pure-functions, module-level-constants, ollama-http-api]
key_files:
  created:
    - meeting_notes/services/llm.py
    - meeting_notes/templates/__init__.py
    - meeting_notes/templates/meeting.txt
    - meeting_notes/templates/minutes.txt
    - meeting_notes/templates/1on1.txt
    - tests/test_llm_service.py
  modified:
    - pyproject.toml
decisions:
  - requests>=2.28 added (not pinned to exact version — API is stable)
  - chunk_transcript returns text as-is for short inputs (no strip), strips only after newline-split
metrics:
  duration_seconds: 110
  completed_date: "2026-03-22"
  tasks_completed: 2
  files_created: 6
  files_modified: 1
---

# Phase 3 Plan 1: LLM Service and Prompt Templates Summary

**One-liner:** Ollama HTTP wrapper with three grounding-rule prompt templates and 15-test TDD coverage using mocked requests.

## What Was Built

Created `meeting_notes/services/llm.py` as a pure-function module (no Click/Rich) that wraps the Ollama HTTP API for local LLM note generation. Three prompt template files were added covering meeting, formal minutes, and 1-on-1 formats. All templates include the strict grounding rule per D-04. A 15-test unit test suite covers all public functions with full HTTP mocking.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create prompt template files and LLM service module | 7fcc5af | meeting_notes/services/llm.py, 3 template .txt files, pyproject.toml |
| 2 | Create unit tests for LLM service | 1d9d17a | tests/test_llm_service.py |

## Key Functions Exported

- `generate_notes(prompt, timeout=120)` — POST to Ollama, raises TimeoutError/ConnectionError/RuntimeError
- `estimate_tokens(text)` — returns `len(text) // 4`
- `chunk_transcript(text)` — splits into ~6000-token chunks on newline boundaries
- `load_template(name)` — loads .txt template from `meeting_notes/templates/`, raises ValueError on invalid name
- `build_prompt(template_text, transcript)` — substitutes `{transcript}` placeholder
- Constants: `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `VALID_TEMPLATES`

## Template Sections

| Template | Sections |
|----------|---------|
| meeting.txt | Summary, Decisions, Action Items |
| minutes.txt | Attendees, Agenda, Discussion, Decisions, Action Items |
| 1on1.txt | Project Work, Technical Overview, Team Collaboration, Feedback, Personal notes |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_chunk_transcript_short assertion**
- **Found during:** Task 2 TDD GREEN phase
- **Issue:** Test compared `chunks[0] == text.strip()` but `chunk_transcript` does not strip input when text is short (only strips on split boundaries). The assertion failed because `text.strip()` removed the trailing space but `chunks[0]` preserved it.
- **Fix:** Changed assertion to `chunks[0] == text` (short path returns as-is)
- **Files modified:** tests/test_llm_service.py
- **Commit:** 1d9d17a

## Known Stubs

None — all functions are fully implemented. The LLM call requires Ollama running locally but that is an external runtime dependency, not a code stub.

## Test Results

- `python3 -m pytest tests/test_llm_service.py -x -q`: 15 passed
- `python3 -m pytest -x -q`: 91 passed (no regressions)

## Self-Check: PASSED
