---
status: partial
phase: 02-sessions-dashboard
source: [02-VERIFICATION.md]
started: 2026-03-31T21:00:00Z
updated: 2026-03-31T21:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Dashboard visual layout
expected: 4 stat cards appear (Total Sessions, Transcribed, Summarized, This Week), StatusPill shows 'Idle', 'Start Recording' button is visible
result: [pending]

### 2. Start Recording navigation (DASH-04)
expected: Clicking 'Start Recording' on Dashboard navigates to the Record view (sidebar selection changes)
result: [pending]

### 3. Sessions two-panel layout (SESS-03, SESS-04, SESS-08)
expected: Detail panel populates with title, date, duration, word count, pipeline step circles, Transcribe/Summarize/Open Notion buttons, and 3 content tabs
result: [pending]

### 4. Filter dropdown behavior (SESS-02)
expected: Session list filters to show only sessions with that status; empty state label appears if none match
result: [pending]

### 5. Notion URL opens browser (SESS-05)
expected: Browser opens the Notion page URL when clicking 'Open in Notion' on a session with a Notion URL
result: [pending]

### 6. Live recording state update (DASH-03)
expected: StatusPill changes from 'Idle' to '● Recording • H:MM:SS' within 2 seconds of starting `meet record`
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
