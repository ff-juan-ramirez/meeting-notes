# Phase 02: Sessions & Dashboard - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the two placeholder views with fully functional screens: a session browser (scrollable list with filter bar + detail panel with transcribe/summarize workers) and a dashboard (aggregate stats, active recording indicator, recent sessions list). Requirements covered: SESS-01 through SESS-08, DASH-01 through DASH-04.

New widgets introduced: `SessionRowWidget`, `SessionDetailPanel`, `StatusPill`. New workers: `TranscribeWorker`, `SummarizeWorker`.

</domain>

<decisions>
## Implementation Decisions

### Worker Progress UX
- **D-01:** While transcription or summarization is running, the Transcribe and Summarize buttons both disable and gray out. A status label below the action buttons updates with `progress(str)` signal text (e.g., "Transcribing audio..."). All other buttons (Open Notion) also disable during the operation.
- **D-02:** On worker completion (`finished` signal), the detail panel auto-refreshes from disk — reloads session metadata, updates button enabled states, and clears the status label. No manual refresh required. No explicit "Done" banner.
- **D-03:** On worker failure (`failed` signal), show `QMessageBox.warning()` with the error string (existing pattern from milestone plan). Status label clears, buttons re-enable.

### Empty States
- **D-04:** Sessions left panel empty state (no sessions at all): centered `QLabel` — "No sessions yet. Start a recording to get started." Filter bar still renders above it; the message replaces the list content area.
- **D-05:** Sessions right panel when no session is selected: centered `QLabel` — "Select a session to view details." No action buttons shown in this state. This is also the initial state on first render.
- **D-06:** Dashboard with zero sessions: stat counts show `0`; recent sessions list shows centered "No sessions yet." The dashboard still renders normally — it is not a blocking empty state.

### Dashboard Recording Indicator
- **D-07:** Recording state displayed as a compact status pill (inline with "Start Recording" button): gray pill labeled "Idle" when not recording; red pill labeled "● Recording • 0:03:42" when active. Elapsed time derived from `start_time` in `state.json`, polled every 2 seconds via `QTimer`.
- **D-08:** The recording pill and button row shows "Go to Record" when recording is active (replaces "Start Recording"). Clicking it navigates to the Record view (sidebar switch). The Record view owns the stop action — Dashboard does not invoke `StopWorker` directly.
- **D-09:** When idle, the button is "Start Recording" and navigates to the Record view (sidebar switch to index 2). Consistent behavior in both states.

### Claude's Discretion
All other visual and architectural choices deferred to Claude, guided by `GUI-MILESTONE-PLAN.md` and `meeting-notes-ui-mockups.pdf`:
- Tab content in detail panel when file not yet available: placeholder text in the `QPlainTextEdit` (e.g., "Not yet transcribed.") with read-only mode
- Cross-view navigation architecture: `DashboardView` emits a typed signal; `MainWindow` connects it and calls `navigate_to(index)` + `SessionsView.select_session(session_id)`
- QSplitter proportions, filter pill visual treatment, pipeline step indicator (gray = not done, green fill = done)
- SessionRowWidget row content layout (date, duration, title, status dot) per mockup

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Primary Design Spec
- `GUI-MILESTONE-PLAN.md` — screen specs for Sessions (§"Screen 2") and Dashboard (§"Screen 1"), worker signal interfaces, threading rules, PySide6 standards

### Visual Reference
- `meeting-notes-ui-mockups.pdf` — use page 1 (Dashboard) and page 2 (Sessions) as structural guide for layout and content

### Design Contract (carries forward from Phase 01)
- `.planning/phases/01-gui-foundation/01-UI-SPEC.md` — spacing scale, typography, color palette, component patterns; all tokens carry forward unchanged

### Requirements
- `.planning/REQUIREMENTS.md` §Sessions View — SESS-01 through SESS-08 (acceptance criteria)
- `.planning/REQUIREMENTS.md` §Dashboard View — DASH-01 through DASH-04 (acceptance criteria)

### Existing Code to Extend
- `meeting_notes/gui/views/sessions.py` — placeholder to replace
- `meeting_notes/gui/views/dashboard.py` — placeholder to replace
- `meeting_notes/gui/main_window.py` — add inter-view navigation method
- `meeting_notes/gui/widgets/` — add `session_row.py` (SessionRowWidget), `badge.py` (StatusPill)
- `meeting_notes/gui/workers/` — add `transcribe_worker.py`, `summarize_worker.py`
- `meeting_notes/gui/theme.py` — read before implementing; do not add new tokens unless needed
- `meeting_notes/services/transcription.py` — called by TranscribeWorker
- `meeting_notes/services/llm.py` — called by SummarizeWorker (`list_templates`, `load_template`)
- `meeting_notes/core/state.py` — read `state.json` for active recording detection on Dashboard
- `meeting_notes/core/storage.py` — `list_sessions()`, `read_session_metadata()` for session data

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `theme.make_label(text, role, color_key)` — use for all text labels
- `theme.make_button(text, style)` — use for all action buttons ("primary", "danger")
- `theme.COLORS` — status colors: green (#30D158) = done, red (#FF3B30) = recording/danger, yellow (#FF9F0A) = warning
- `QFrame[style="card"]` QSS — reuse for detail panel sections (already in APP_STYLESHEET)
- `MainWindow._stack` + `_sidebar.setCurrentRow(index)` — existing navigation mechanism

### Established Patterns
- Views receive `config` at construction; no data loaded in `__init__`
- `showEvent` triggers data refresh (established in milestone plan, carried forward)
- All signals defined at class level using `Signal(type)`; receivers decorated with `@Slot(type)`
- Workers import ML modules inside `run()` only — never at class or module level
- `QMessageBox.warning()` for error surface (milestone plan standard)

### Integration Points
- `MainWindow._on_sidebar_changed` already connects sidebar → stack switch; extend with inter-view navigation method
- `workers/` directory exists but is empty (`__init__.py` only) — add `transcribe_worker.py` and `summarize_worker.py`
- `widgets/` directory exists but is empty (`__init__.py` only) — add `session_row.py` and `badge.py`

</code_context>

<specifics>
## Specific Ideas

- Status pill for Dashboard recording indicator: gray `QFrame` with `QLabel` "Idle" when not recording; red `QFrame` with `QLabel` "● Recording • H:MM:SS" when active. Update via QTimer(2000).
- "Go to Record" when recording is active; "Start Recording" when idle — same widget position, button label changes.
- Detail panel status label: placed below action buttons row, hidden when idle, visible with progress text when worker runs.
- Tab bar for transcript/notes/SRT: `QTabWidget` with three `QPlainTextEdit` tabs set to `ReadOnly=True`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-sessions-dashboard*
*Context gathered: 2026-03-30*
