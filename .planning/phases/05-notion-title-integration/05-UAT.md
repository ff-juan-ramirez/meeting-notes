---
status: testing
phase: 05-notion-title-integration
source: [05-01-SUMMARY.md]
started: 2026-03-28T00:00:00Z
updated: 2026-03-28T00:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: Named session uses recording_name as Notion page title
expected: |
  Run `meet summarize` on a session that was started with a name (e.g., `meet start "Weekly Sync"`).
  When the summary is pushed to Notion, the Notion page title should be "Weekly Sync" — the name
  you gave the recording — NOT an LLM-extracted heading from the transcript content.
awaiting: user response

## Tests

### 1. Named session uses recording_name as Notion page title
expected: Run `meet summarize` on a session that was started with a name (e.g., `meet start "Weekly Sync"`). When the summary is pushed to Notion, the Notion page title should be "Weekly Sync" — the name you gave the recording — NOT an LLM-extracted heading from the transcript content.
result: [pending]

### 2. Unnamed session falls through to extract_title
expected: Run `meet summarize` on a session that was started WITHOUT a name (e.g., `meet start` with no arguments). When the summary is pushed to Notion, the Notion page title should be the LLM-extracted heading from the transcript content — same behavior as before this phase.
result: [pending]

### 3. Pre-v1.2 session (no metadata) is unaffected
expected: If you have an old session recorded before v1.2 (no metadata file), running `meet summarize` on it should still work — it should fall through to extract_title for the Notion title, with no crash or error about missing metadata.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0

## Gaps

[none yet]
