# Phase 03: Record - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-01
**Phase:** 03-record
**Areas discussed:** Post-stop navigation, Recent recordings list, Stop failure recovery

---

## Post-stop Navigation

| Option | Description | Selected |
|--------|-------------|----------|
| Stay on Record (Idle) | View resets to Idle, title clears, recent list refreshes. User can immediately start another recording. | ✓ |
| Auto-navigate to Sessions | Switch to Sessions view with new session pre-selected, ready for transcription. | |

**User's choice:** Stay on Record (Idle)
**Notes:** Title field should clear on every return to Idle (confirmed in follow-up).

---

## Recent Recordings List

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse SessionRowWidget | Same widget from Phase 02 — title, date, duration, status dots. Already built. | ✓ |
| Simple read-only rows | Lightweight plain labels — title + date only. | |

**User's choice:** Reuse SessionRowWidget
**Notes:** Rows are read-only (no navigation action) until Phase 05 cross-view wiring.

---

## Stop Failure Recovery

| Option | Description | Selected |
|--------|-------------|----------|
| Return to Recording state | QMessageBox.warning + stay in Recording state; user can retry stop or restart. | ✓ |
| Go to Idle + warn | QMessageBox.warning + transition to Idle; simpler but may lose partial WAV. | |

**User's choice:** Return to Recording state
**Notes:** Process may still be running — correct to keep Stop button available.

---

## Claude's Discretion

- QPropertyAnimation pulse implementation details (duration, opacity range)
- Device index display format (milestone plan shows inline label)
- QTimer interval (1 second per milestone plan)
- Stopping state UI (all buttons disabled, status label visible)
- Instance var naming for pid/output_path storage between workers
- FakeRecordWorker / FakeStopWorker test structure

## Deferred Ideas

- Clicking a recent SessionRowWidget → navigate to Sessions view with session pre-selected
  (Phase 05 cross-view navigation)
