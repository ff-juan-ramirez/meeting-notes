---
phase: 03-note-generation
plan: 03
subsystem: summarize-command
tags: [cli, ollama, summarize, map-reduce, tdd, rich-spinner]
dependency_graph:
  requires: [meeting_notes.services.llm, meeting_notes.services.transcription, meeting_notes.core.state, meeting_notes.core.storage]
  provides: [meet-summarize-command]
  affects: [04-notion-integration]
tech_stack:
  added: []
  patterns: [click-command, session-resolution, map-reduce-chunking, read-merge-write-metadata, rich-spinner-wrapper]
key_files:
  created:
    - meeting_notes/cli/commands/summarize.py
    - tests/test_summarize_command.py
  modified:
    - meeting_notes/cli/main.py
decisions:
  - Session resolution for transcripts mirrors transcribe.py pattern (latest .txt by mtime or exact stem)
  - Map-reduce path triggered when estimate_tokens > 8000 (>32000 chars) per D-13
  - Metadata uses read-merge-write pattern (read_state or {}, update, write_state) to preserve Phase 2 fields (D-08)
  - Notes overwrite silently per D-07 — no prompt, no error
  - run_with_spinner reused from transcription service for Rich spinner during LLM generation (D-16 / LLM-07)
metrics:
  duration_seconds: 127
  completed_date: "2026-03-23"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 3 Plan 3: meet summarize CLI Command Summary

**One-liner:** Click CLI command wiring transcript resolution, Ollama note generation, map-reduce chunking, Rich spinner, and metadata extension into a single `meet summarize` entrypoint.

## What Was Built

Created `meeting_notes/cli/commands/summarize.py` as the user-facing `meet summarize` command that turns transcripts into structured Markdown notes. The command mirrors the session resolution pattern from `transcribe.py`, calls Ollama via the LLM service (from Plan 01), and writes notes to `notes/{stem}-{template}.md`. For transcripts exceeding 8,000 tokens (32,000 chars), a map-reduce path chunks the transcript, summarizes each chunk, and merges via a second LLM call. Metadata is extended read-merge-write without erasing Phase 2 fields. Registered in `cli/main.py` as the sixth command. An 18-test suite covers all behavior paths.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create meet summarize CLI command | 64e77c4 | meeting_notes/cli/commands/summarize.py, meeting_notes/cli/main.py |
| 2 | Create comprehensive tests for meet summarize command | 7e2e08d | tests/test_summarize_command.py |

## Key Behaviors

- `meet summarize` resolves latest transcript by default; `--session STEM` resolves exact match
- `--template [meeting|minutes|1on1]` selects template (default: meeting)
- Notes saved to `notes/{stem}-{template}.md` (overwrites silently)
- Rich spinner shown via `run_with_spinner` for all LLM generation calls
- Transcripts >8,000 tokens use map-reduce: each chunk summarized independently, then merged
- `TimeoutError`, `ConnectionError`, `RuntimeError` all produce `[red]Error:[/red]` messages + exit 1
- Metadata `{stem}.json` extended with `notes_path`, `template`, `summarized_at`, `llm_model`; Phase 2 fields preserved
- Output: `Notes saved: {path} ({word_count} words)` + `Session: {stem}`

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None — all paths are fully wired. Ollama must be running locally at runtime, but that is an external dependency, not a code stub.

## Test Results

- `python3 -m pytest tests/test_summarize_command.py -x -q`: 18 passed
- `python3 -m pytest -x -q`: 114 passed (no regressions)

## Self-Check: PASSED
