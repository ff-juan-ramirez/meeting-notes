# Phase 03: Record - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the `RecordView` placeholder (`gui/views/record.py`) with a fully functional
Idle/Recording/Stopping state machine. Deliver `RecordWorker` and `StopWorker` QThread
classes that wrap the existing `start_recording` / `stop_recording` service layer.
Elapsed time updates every second while recording. Device info (system + mic indices)
visible in Idle state. Last 2 sessions shown as `SessionRowWidget` rows in Idle state.

Requirements covered: REC-01, REC-02, REC-03, REC-04, REC-05.

No changes to the CLI (`meet record` / `meet stop`) — service layer is shared, not replaced.

</domain>

<decisions>
## Implementation Decisions

### Post-stop Navigation
- **D-01:** After `StopWorker.stopped` fires (WAV saved), the view resets to Idle state and
  stays on the Record screen. Title field clears. Recent list refreshes to include the new
  session. User can immediately start another recording without navigating away.

### Title Field
- **D-02:** Title field clears on every return to Idle — both after a successful stop and on
  initial load. No title preservation across sessions.

### Recent Recordings List
- **D-03:** The "last 2 recordings" section in Idle state reuses `SessionRowWidget` from
  Phase 02 (`gui/widgets/session_row.py`). Consistent with Sessions view — shows title,
  date, duration, and status dots. Read-only: clicking a row does nothing in this context
  (no navigation to Sessions from here — that belongs in Phase 05 cross-view wiring).

### Stop Failure Recovery
- **D-04:** If `StopWorker.failed` fires, show `QMessageBox.warning()` with the error string
  and return the view to **Recording state** (not Idle). The ffmpeg process may still be
  running — the user retains the Stop button and can try again or restart the app.

### Worker Error (RecordWorker failure)
- **D-05:** If `RecordWorker.failed` fires (ffmpeg couldn't start), show
  `QMessageBox.warning()` with the error string and return to Idle state. Established
  Phase 02 error pattern.

### Claude's Discretion
- QPropertyAnimation opacity pulse on the record button in Recording state (per milestone
  plan) — implementation details (duration, opacity range) left to Claude
- Whether device indices are shown as `QLabel` or `QSpinBox` — read-only display in Idle
  state; milestone plan shows "System: :1 | Mic: :2" inline label format
- `QTimer` interval for elapsed time: 1 second (per milestone plan)
- Stopping state: disable all buttons, show "Stopping and saving..." status label
- `RecordWorker` stores `(pid, output_path)` returned by `started` signal in view-level
  instance vars (`self._pid`, `self._output_path`) for use by `StopWorker`
- Test structure: `FakeRecordWorker` / `FakeStopWorker` classes (not MagicMock), following
  Phase 02 FakeWorker pattern

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Primary Design Spec
- `GUI-MILESTONE-PLAN.md` — Screen 3 (Record) spec: state descriptions, worker signal
  interfaces, `RecordWorker` / `StopWorker` constructor signatures, animation notes,
  recent recordings layout

### Visual Reference
- `meeting-notes-ui-mockups.pdf` — page 3 (Record screen); use as structural guide for
  state layouts

### Design Contract (carries forward)
- `.planning/phases/01-gui-foundation/01-UI-SPEC.md` — spacing scale, typography, color
  palette, component patterns; all tokens carry forward

### Requirements
- `.planning/REQUIREMENTS.md` §Record View — REC-01 through REC-05 (acceptance criteria)

### Existing Code to Extend
- `meeting_notes/gui/views/record.py` — placeholder to replace
- `meeting_notes/gui/workers/` — add `record_worker.py`, `stop_worker.py`
- `meeting_notes/gui/widgets/session_row.py` — `SessionRowWidget` to reuse in recent list
- `meeting_notes/gui/main_window.py` — no changes needed (navigation handled by D-01)
- `meeting_notes/gui/theme.py` — read before implementing; no new tokens expected
- `meeting_notes/services/audio.py` — `start_recording(config, output_path=None)` and
  `stop_recording(proc)` — the service layer RecordWorker/StopWorker will call
- `meeting_notes/core/state.py` — `write_state`, `read_state`, `clear_state` — workers
  use the same state lifecycle as the CLI commands
- `meeting_notes/core/storage.py` — `list_sessions()`, `read_session_metadata()` for
  refreshing the recent recordings list; `get_recording_path_with_slug()` / `slugify()`
  for named recordings
- `meeting_notes/cli/commands/record.py` — reference for the state lifecycle and
  recording_name / recording_slug propagation logic (mirror in workers)

### Prior Phase Patterns to Follow
- `.planning/phases/02-sessions-dashboard/02-CONTEXT.md` — worker signal handling patterns,
  FakeWorker test approach, button disable during work, QMessageBox.warning for errors

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SessionRowWidget` (`gui/widgets/session_row.py`) — use directly in recent recordings list
- `theme.make_label(text, role, color_key)` / `theme.make_button(text, style)` — all UI
  elements
- `theme.COLORS` — red (#FF3B30) for recording state; green (#30D158) for done indicators
- `start_recording(config, output_path=None)` → `(Popen, Path)` — RecordWorker calls this
- `stop_recording(proc)` → None — StopWorker calls this
- `slugify(name)` / `get_recording_path_with_slug(name, storage_path)` — for named sessions

### Established Patterns
- Workers receive all deps at construction; import ML/service modules inside `run()` only
- Signals at class level: `Signal(type)`; receivers: `@Slot(type)`
- `showEvent` → data refresh (trigger recent recordings reload)
- `QMessageBox.warning(self, "Error", msg)` for all worker failures
- `blockSignals(True/False)` around list repopulation
- `processEvents()` after `worker.wait()` in tests

### Integration Points
- `workers/` directory exists (`__init__.py` only) — add `record_worker.py`, `stop_worker.py`
- Phase 02 Dashboard uses `state.json` to detect active recording — RecordWorker must
  write state in the same format as the CLI `meet record` command
- Phase 05 will add cross-view navigation (clicking a recent row → Sessions); D-03 notes
  the rows are read-only until then

</code_context>

<specifics>
## Specific Ideas

- Device info in Idle state: `"System: :{system_device_index} | Mic: :{mic_device_index}"`
  as a single `QLabel` below the record button, derived from `config.audio.*`
- Elapsed time format: `H:MM:SS` (consistent with Dashboard recording pill from Phase 02)
- Worker constructor signatures from milestone plan:
  - `RecordWorker(config: Config, name: str | None)` → `started(pid, output_path)`, `failed(str)`
  - `StopWorker(pid: int, output_path: str, config: Config)` → `stopped(output_path)`, `failed(str)`

</specifics>

<deferred>
## Deferred Ideas

- Clicking a recent SessionRowWidget row → navigate to Sessions view with that session
  pre-selected. Deferred to Phase 05 (cross-view navigation wiring).

</deferred>

---

*Phase: 03-record*
*Context gathered: 2026-04-01*
