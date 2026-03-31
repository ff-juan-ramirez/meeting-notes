---
status: complete
phase: 01-gui-foundation
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md]
started: 2026-03-31T00:00:00Z
updated: 2026-03-31T00:01:00Z
---

## Current Test

[testing complete]

## Tests

### 1. CLI accepts user-created templates
expected: |
  Create a custom template file in ~/.config/meeting-notes/templates/ (e.g., standup.txt).
  Run: meet summarize --template standup <session>
  The command should NOT reject "standup" as an invalid template — it should proceed past validation
  (it may fail for other reasons like missing session, which is fine).
  Also: meet summarize --template meeting (built-in) still works as before.
result: pass

### 2. Invalid template name gives clear error
expected: |
  Run: meet summarize --template nonexistent
  The command should exit with an error message containing the invalid name and list available templates.
  It should NOT crash or show a Python traceback.
result: pass

### 3. meet-gui launches the window
expected: |
  Run: meet-gui
  A native macOS window should appear within 2 seconds with a dark sidebar on the left
  and a light content area on the right. No Python traceback in the terminal.
result: pass
note: requires venv active (.venv/bin/meet-gui or source .venv/bin/activate)

### 4. Sidebar shows all 6 nav items
expected: |
  In the open meet-gui window, the dark sidebar should list exactly 6 items:
  Dashboard, Sessions, Record, Templates, Settings, Health Check (in that order).
result: pass

### 5. Sidebar navigation switches views
expected: |
  Clicking each sidebar item should switch the content area to show that screen's name as a
  large centered heading (e.g., clicking "Sessions" shows "Sessions", clicking "Health Check"
  shows "Health Check"). All 6 items should work.
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
