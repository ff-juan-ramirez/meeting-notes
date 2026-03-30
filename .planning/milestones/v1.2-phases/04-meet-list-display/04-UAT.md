---
status: complete
phase: 04-meet-list-display
source: [04-01-SUMMARY.md]
started: 2026-03-28T00:00:00Z
updated: 2026-03-28T00:01:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Named session shows recording_name as title
expected: When you run `meet list` and a session was recorded with a name (e.g. `meet record "1:1 with Gabriel"`), the Title column in the table shows "1:1 with Gabriel" — not the filename stem or LLM heading.
result: pass

### 2. Unnamed sessions still show previous title
expected: When you run `meet list` and a session has no recording name (recorded with plain `meet record`), the Title column still shows the LLM-derived heading or filename stem — exactly as it did before v1.2. No regression.
result: pass

### 3. JSON output includes recording_name field and correct title
expected: When you run `meet list --json` on a named session, the JSON object contains both a `recording_name` field (the raw name) and a `title` field whose value matches the recording name.
result: pass

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
