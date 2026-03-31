# Phase 02: Sessions & Dashboard - Research

**Researched:** 2026-03-30
**Domain:** PySide6 QThread workers, QSplitter two-panel layout, QTimer polling, session metadata rendering
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** While transcription or summarization is running, Transcribe and Summarize buttons both disable and gray out. A status label below the action buttons updates with `progress(str)` signal text (e.g., "Transcribing audio..."). All other buttons (Open Notion) also disable during the operation.

**D-02:** On worker completion (`finished` signal), the detail panel auto-refreshes from disk — reloads session metadata, updates button enabled states, and clears the status label. No manual refresh required. No explicit "Done" banner.

**D-03:** On worker failure (`failed` signal), show `QMessageBox.warning()` with the error string (existing pattern from milestone plan). Status label clears, buttons re-enable.

**D-04:** Sessions left panel empty state (no sessions at all): centered `QLabel` — "No sessions yet. Start a recording to get started." Filter bar still renders above it; the message replaces the list content area.

**D-05:** Sessions right panel when no session is selected: centered `QLabel` — "Select a session to view details." No action buttons shown in this state. This is also the initial state on first render.

**D-06:** Dashboard with zero sessions: stat counts show `0`; recent sessions list shows centered "No sessions yet." The dashboard still renders normally — it is not a blocking empty state.

**D-07:** Recording state displayed as a compact status pill (inline with "Start Recording" button): gray pill labeled "Idle" when not recording; red pill labeled "● Recording • 0:03:42" when active. Elapsed time derived from `start_time` in `state.json`, polled every 2 seconds via `QTimer`.

**D-08:** The recording pill and button row shows "Go to Record" when recording is active (replaces "Start Recording"). Clicking it navigates to the Record view (sidebar switch). The Record view owns the stop action — Dashboard does not invoke `StopWorker` directly.

**D-09:** When idle, the button is "Start Recording" and navigates to the Record view (sidebar switch to index 2). Consistent behavior in both states.

### Claude's Discretion

- Tab content in detail panel when file not yet available: placeholder text in the `QPlainTextEdit` (e.g., "Not yet transcribed.") with read-only mode
- Cross-view navigation architecture: `DashboardView` emits a typed signal; `MainWindow` connects it and calls `navigate_to(index)` + `SessionsView.select_session(session_id)`
- QSplitter proportions, filter pill visual treatment, pipeline step indicator (gray = not done, green fill = done)
- SessionRowWidget row content layout (date, duration, title, status dot) per mockup

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SESS-01 | User can see a scrollable list of all sessions with date, duration, title, and status indicator | `list_sessions()` helper from `list.py` (reused as module logic); `SessionRowWidget` in `widgets/session_row.py` |
| SESS-02 | User can filter sessions by status: All / Recorded / Transcribed / Summarized | In-memory filter over loaded sessions list; `_derive_status()` logic from `list.py` mirrors the logic needed |
| SESS-03 | User can select a session and see its details: title, date, duration, word count, speaker count, pipeline steps | `SessionDetailPanel` reads `read_state(metadata_path)` to populate; metadata JSON fields confirmed in `transcribe.py` |
| SESS-04 | User can see the pipeline step indicator (Recorded → Transcribed → Summarized → Notion) with green fill for completed steps | Derived from metadata fields: `wav_path`, `transcript_path`, `notes_path`, `notion_url`; color `#30D158` for done, `#E5E5EA` for pending |
| SESS-05 | User can open the Notion URL for a summarized session via a clickable link | `QDesktopServices.openUrl(QUrl(notion_url))` from `PySide6.QtGui` |
| SESS-06 | User can transcribe a session from the detail panel (enabled only if not yet transcribed); UI stays responsive | `TranscribeWorker(QThread)` calls `transcribe_audio(wav_path, config)` inside `run()`; signals: `progress(str)`, `finished(str, int)`, `failed(str)` |
| SESS-07 | User can summarize a session from the detail panel with template selector and title override; UI stays responsive | `SummarizeWorker(QThread)` calls `generate_notes()` + Notion push inside `run()`; template selector uses `list_templates()` |
| SESS-08 | User can read the transcript, notes, and SRT content in read-only tabs in the detail panel | `QTabWidget` with three `QPlainTextEdit` tabs set to `setReadOnly(True)`, styled with `QPlainTextEdit[style="mono"]` |
| DASH-01 | User can see aggregate stats: total sessions, transcribed count, summarized count, sessions this week | Scan metadata dir; compute from `_derive_status()` applied to all metadata files; "this week" = sessions with date within 7 days |
| DASH-02 | User can see the last 5 sessions sorted newest-first and click a row to open Sessions view with that session pre-selected | `list_sessions()` sorted-newest-first, take [:5]; row click emits `session_selected(session_id)` signal; `MainWindow` connects it |
| DASH-03 | User can see the active recording state (idle or recording + elapsed time) updated every 2 seconds via `QTimer` | `QTimer(2000)` calls `_refresh_recording_state()`; reads `state.json` via `read_state()`; checks `pid` liveness via `check_for_stale_session()` |
| DASH-04 | User can click "Start Recording" on the Dashboard to navigate to the Record view | Emit `navigate_requested(2)` signal from `DashboardView`; `MainWindow.navigate_to(index)` sets sidebar row + stack index |
</phase_requirements>

---

## Summary

Phase 02 replaces two placeholder views (`sessions.py` and `dashboard.py`) with fully functional screens. The work is self-contained within the `meeting_notes/gui/` tree: new files go into the empty `workers/` and `widgets/` directories that Phase 01 created; `main_window.py` gets one new navigation method; and the two placeholder views are completely rewritten.

The service layer (transcription, llm, notion, storage, state) is already complete and well-tested from the CLI phases. Workers call into it directly — no new service logic is needed. The data contract (metadata JSON shape) is fully understood from `transcribe.py` and `summarize.py`, and the helper logic for deriving status, title, date, and duration already exists in `cli/commands/list.py` and can be duplicated (or extracted) for GUI use.

The primary design challenge is worker lifecycle management: holding a reference to each worker, preventing double-starts, and ensuring the UI remains responsive. The secondary challenge is the cross-view navigation protocol (Dashboard → Sessions with a pre-selected session), which requires a typed signal chain through `MainWindow`.

**Primary recommendation:** Implement in four discrete units: (1) widgets (`session_row.py`, `badge.py`), (2) workers (`transcribe_worker.py`, `summarize_worker.py`), (3) `sessions.py` full view, (4) `dashboard.py` full view + `main_window.py` navigation wiring. Tests should use the existing `qt_app` session fixture from `conftest.py` and avoid any actual ML calls by monkeypatching the service imports inside worker `run()`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.0 (installed) | All Qt widgets, threading, timers | Locked in Phase 01; only Qt binding in project |
| PySide6.QtCore | 6.11.0 | `QThread`, `Signal`, `Slot`, `QTimer`, `Qt` | Threading + signal/slot system |
| PySide6.QtWidgets | 6.11.0 | `QSplitter`, `QTabWidget`, `QListWidget`, `QPlainTextEdit`, `QComboBox`, `QStackedWidget`, `QMessageBox` | All layout and interactive widgets used in spec |
| PySide6.QtGui | 6.11.0 | `QDesktopServices`, `QUrl` | Opening Notion URLs externally (SESS-05) |

### Supporting (existing project services consumed by workers)

| Module | Path | Purpose |
|--------|------|---------|
| `transcription.transcribe_audio` | `meeting_notes/services/transcription.py` | Called by `TranscribeWorker.run()` |
| `llm.generate_notes`, `llm.list_templates`, `llm.load_template` | `meeting_notes/services/llm.py` | Called by `SummarizeWorker.run()` |
| `notion.create_page` | `meeting_notes/services/notion.py` | Called by `SummarizeWorker.run()` for Notion push |
| `state.read_state` | `meeting_notes/core/state.py` | Dashboard polling (`state.json`), session metadata reads |
| `storage.get_data_dir`, `storage.get_config_dir` | `meeting_notes/core/storage.py` | Locating metadata dir, recordings dir |
| `theme.make_label`, `theme.make_button`, `theme.COLORS` | `meeting_notes/gui/theme.py` | All styled labels and buttons |

**No new pip dependencies required for this phase.** PySide6 and all service modules are already installed.

---

## Architecture Patterns

### Recommended File Structure (additions only)

```
meeting_notes/gui/
├── widgets/
│   ├── __init__.py          (exists, empty)
│   ├── session_row.py       (NEW — SessionRowWidget)
│   └── badge.py             (NEW — StatusPill)
├── workers/
│   ├── __init__.py          (exists, empty)
│   ├── transcribe_worker.py (NEW — TranscribeWorker)
│   └── summarize_worker.py  (NEW — SummarizeWorker)
├── views/
│   ├── sessions.py          (REPLACE placeholder)
│   └── dashboard.py         (REPLACE placeholder)
└── main_window.py           (EXTEND — add navigate_to() method)
```

### Pattern 1: Worker Signal Interface (from GUI-MILESTONE-PLAN.md)

```python
# Source: GUI-MILESTONE-PLAN.md §Workers — Threading Model
class TranscribeWorker(QThread):
    progress = Signal(str)            # status message for status label
    finished = Signal(str, int)       # stem, word_count (triggers panel auto-refresh)
    failed   = Signal(str)            # error message (triggers QMessageBox.warning)

    def __init__(self, wav_path: Path, config: Config) -> None:
        super().__init__()
        self._wav_path = wav_path
        self._config = config

    def run(self) -> None:
        try:
            from meeting_notes.services.transcription import transcribe_audio
            self.progress.emit("Transcribing audio...")
            text, segments = transcribe_audio(self._wav_path, self._config)
            self.finished.emit(self._wav_path.stem, len(text.split()))
        except Exception as e:
            self.failed.emit(str(e))
```

Signal type for `SummarizeWorker.finished` is `Signal(str)` (notion_url or empty string).

### Pattern 2: Worker Lifecycle Management

**Hold reference on parent, connect before start, cleanup on close.** This prevents premature GC and ensures clean shutdown.

```python
# In SessionsView or SessionDetailPanel
def _start_transcribe(self, wav_path: Path) -> None:
    self._worker = TranscribeWorker(wav_path, self._config)
    self._worker.progress.connect(self._on_progress)
    self._worker.finished.connect(self._on_transcribe_done)
    self._worker.failed.connect(self._on_worker_failed)
    self._worker.finished.connect(self._worker.deleteLater)
    self._set_buttons_enabled(False)
    self._worker.start()

def closeEvent(self, event) -> None:
    if self._worker and self._worker.isRunning():
        self._worker.quit()
        self._worker.wait()
    super().closeEvent(event)
```

**Double-start guard:** check `self._worker is None or not self._worker.isRunning()` before creating a new worker.

### Pattern 3: showEvent Data Refresh

```python
# Source: GUI-MILESTONE-PLAN.md §7 Data loading
def showEvent(self, event) -> None:
    super().showEvent(event)
    self._refresh_sessions()  # reload from disk every time view becomes visible
```

### Pattern 4: QTimer for Dashboard Polling (D-07)

```python
# In DashboardView.__init__ or _build_ui
self._poll_timer = QTimer(self)
self._poll_timer.setInterval(2000)
self._poll_timer.timeout.connect(self._refresh_recording_state)
# Start timer in showEvent, stop in hideEvent (optional optimization)
self._poll_timer.start()
```

Read `state.json` via `read_state(config_dir / "state.json")`. If result is not None and `pid` key exists and `check_for_stale_session(state)` returns True → recording is active. Derive elapsed time from `start_time` ISO string.

### Pattern 5: Cross-View Navigation (Claude's Discretion)

```python
# In DashboardView
class DashboardView(QWidget):
    navigate_requested = Signal(int)          # sidebar index to switch to
    session_selected   = Signal(str)          # session_id for Sessions pre-select

# In MainWindow._build_ui — connect after views are created
dashboard_view = self._views[0]
sessions_view  = self._views[1]
dashboard_view.navigate_requested.connect(self.navigate_to)
dashboard_view.session_selected.connect(sessions_view.select_session)

# In MainWindow
def navigate_to(self, index: int) -> None:
    self._sidebar.setCurrentRow(index)
    # _on_sidebar_changed fires automatically via currentRowChanged signal

# In SessionsView
def select_session(self, session_id: str) -> None:
    """Pre-select a session by ID after navigation from Dashboard."""
    # find item in list widget matching session_id and set it current
```

### Pattern 6: Session Data Loading (reuse list.py logic)

The GUI needs the same derivation logic as `cli/commands/list.py`:

| Function | Where it lives | GUI strategy |
|----------|----------------|--------------|
| `_derive_status(meta)` | `list.py` | Duplicate inline in sessions view or extract to `core/storage.py` as a shared helper |
| `_derive_title(meta, stem)` | `list.py` | Duplicate; avoid importing CLI module from GUI |
| `_derive_date(meta)` | `list.py` | Duplicate |
| `_format_duration(seconds)` | `list.py` | Duplicate |
| Scan+sort metadata files | `list.py` | Copy the sorted `metadata_dir.glob("*.json")` + `_sort_key` pattern |

**Recommendation:** Keep the logic as private helpers inside `sessions.py` (not shared with CLI). This avoids circular imports and keeps GUI self-contained. The functions are small and stable.

### Pattern 7: Pipeline Step Indicator

Four steps: Recorded, Transcribed, Summarized, Notion. Each step is filled green (`#30D158`) when its file/URL exists:

| Step | Condition for "done" |
|------|----------------------|
| Recorded | `meta.get("wav_path")` and `Path(wav_path).exists()` |
| Transcribed | `meta.get("transcript_path")` and `Path(transcript_path).exists()` |
| Summarized | `meta.get("notes_path")` and `Path(notes_path).exists()` |
| Notion | `meta.get("notion_url")` is not None and not empty |

Implementation: four `QFrame` instances with fixed size (e.g. 24×24px circle via `border-radius: 12px`) in an `QHBoxLayout` row. Use `setStyleSheet` per-frame to toggle between green-filled and border-only. Connect frames with `QLabel` arrows or simple `QLabel("→")` separators.

### Anti-Patterns to Avoid

- **Importing ML modules at class level in workers:** `import mlx_whisper` must be inside `run()` only — checked by `test_gui_app_no_ml_imports`
- **Loading session data in `__init__`:** violates lazy-loading rule; use `showEvent` instead
- **Calling `.setStyleSheet()` on entire view for dynamic state:** only per-widget for dynamic state (pipeline step indicator, status pill color); all base styles stay in `APP_STYLESHEET`
- **Lambda chains for complex slot logic:** use named `@Slot()` methods instead
- **Not holding worker reference:** `self._worker = TranscribeWorker(...)` — if not stored, Python may GC the worker mid-run
- **Blocking the main thread in `_refresh_sessions`:** reading metadata files should be fast (small JSON), but beware large metadata dirs; keep reads synchronous for now (acceptable for typical session counts < 1000)
- **Using `QListWidget.addItem()` directly for `SessionRowWidget`:** use `QListWidget` + `setItemWidget()` with a `QListWidgetItem` of custom `sizeHint` — or use a `QScrollArea` + `QVBoxLayout` for simpler row composition

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Opening URLs in browser | Custom subprocess call | `QDesktopServices.openUrl(QUrl(url))` | Cross-platform, handles macOS `open` correctly, single import |
| Thread-safe UI updates from worker thread | Direct widget.setText() from QThread | Signal/slot (Qt queues cross-thread calls automatically) | Qt guarantees cross-thread safety only through signal/slot mechanism |
| Timer-based polling | `threading.Timer` or `time.sleep` loop | `QTimer` | Runs on the Qt event loop; `threading.Timer` would require mutex for UI updates |
| File dialog (not needed this phase) | Custom path picker | `QFileDialog` | — |
| Elapsed time formatting | Custom formatter | `divmod(seconds, 60)` is fine — no library needed | Simple arithmetic |

---

## Common Pitfalls

### Pitfall 1: ML Import at Module Level Breaks Startup Test
**What goes wrong:** `import mlx_whisper` (or pyannote, torchaudio) at the top of `transcribe_worker.py` causes `test_gui_app_no_ml_imports` to fail — the test reloads `gui.app` and checks `sys.modules`.
**Why it happens:** Python caches module-level imports in `sys.modules` the moment the file is imported.
**How to avoid:** All heavy imports must be inside the `run()` method body: `from meeting_notes.services.transcription import transcribe_audio`.
**Warning signs:** `test_gui_app_no_ml_imports` failing after adding a new worker.

### Pitfall 2: Worker Garbage-Collected Mid-Run
**What goes wrong:** Worker thread is silently killed; no finished/failed signal emitted.
**Why it happens:** Python GC runs if no strong reference holds the worker object.
**How to avoid:** Always assign `self._worker = SomeWorker(...)` on the owning widget before `.start()`. Never create a worker in a local variable only.
**Warning signs:** Transcription/summarization button grays out but never re-enables.

### Pitfall 3: Double-Start on Rapid Button Clicks
**What goes wrong:** User clicks Transcribe twice; two `TranscribeWorker` instances start on the same WAV file.
**How to avoid:** Disable buttons as D-01 specifies. Additionally guard: `if self._worker and self._worker.isRunning(): return`.

### Pitfall 4: `QTimer` Continues After View Hidden
**What goes wrong:** Dashboard timer continues ticking when user navigates away; emits signal that triggers `read_state()` 30 times a minute unnecessarily.
**How to avoid:** Either keep the timer always running (acceptable — `read_state` is fast) or stop in `hideEvent` / restart in `showEvent`.

### Pitfall 5: `read_state()` Returns None for Missing Metadata
**What goes wrong:** A `.json` metadata file may not exist for a session that only has a WAV (pre-Phase 01 session or aborted recording).
**How to avoid:** Always use `meta = read_state(path) or {}` pattern (already used in `list.py`).

### Pitfall 6: `notion_url` is `null` in JSON (not missing key)
**What goes wrong:** `meta.get("notion_url")` returns `None` for sessions that attempted Notion push but had it fail — `notion_url` is explicitly written as `null` in metadata. A truthiness check `if meta.get("notion_url"):` handles both missing key and null correctly.
**How to avoid:** Use `if meta.get("notion_url"):` for the Notion step "done" condition — not `if "notion_url" in meta:`.

### Pitfall 7: `setItemWidget` Requires Matching `sizeHint`
**What goes wrong:** `SessionRowWidget` appears collapsed/invisible in `QListWidget`.
**Why it happens:** `QListWidgetItem.setSizeHint()` must match the widget's preferred height; Qt doesn't auto-size custom item widgets.
**How to avoid:** After `list_widget.setItemWidget(item, row_widget)`, call `item.setSizeHint(row_widget.sizeHint())`.

### Pitfall 8: Cross-Thread `finished` Signal Carries Wrong Session
**What goes wrong:** User selects session A, clicks Transcribe. Before it finishes, selects session B. When worker finishes, `_on_transcribe_done` refreshes the currently shown panel (session B).
**How to avoid:** Store the session_id in the worker (`self._stem = wav_path.stem`). Emit `finished(stem, word_count)`. In `_on_transcribe_done(stem, word_count)` check if `stem == self._current_session_id` before refreshing. If not matching, just skip — the list will refresh on next `showEvent`.

---

## Code Examples

### TranscribeWorker (worker file)

```python
# Source: GUI-MILESTONE-PLAN.md §Workers + verified pattern
from pathlib import Path
from PySide6.QtCore import QThread, Signal, Slot
from meeting_notes.core.config import Config


class TranscribeWorker(QThread):
    progress = Signal(str)
    finished = Signal(str, int)  # stem, word_count
    failed   = Signal(str)

    def __init__(self, wav_path: Path, config: Config) -> None:
        super().__init__()
        self._wav_path = wav_path
        self._config   = config

    def run(self) -> None:
        try:
            from meeting_notes.services.transcription import transcribe_audio
            self.progress.emit("Transcribing audio...")
            text, segments = transcribe_audio(self._wav_path, self._config)
            self.finished.emit(self._wav_path.stem, len(text.split()))
        except Exception as exc:
            self.failed.emit(str(exc))
```

### SummarizeWorker (worker file)

```python
# Source: GUI-MILESTONE-PLAN.md §Workers
from PySide6.QtCore import QThread, Signal
from meeting_notes.core.config import Config


class SummarizeWorker(QThread):
    progress = Signal(str)
    finished = Signal(str)   # notion_url or "" on skip
    failed   = Signal(str)

    def __init__(self, stem: str, template: str,
                 title: str | None, config: Config) -> None:
        super().__init__()
        self._stem     = stem
        self._template = template
        self._title    = title
        self._config   = config

    def run(self) -> None:
        try:
            from meeting_notes.services.llm import load_template, build_prompt, generate_notes, estimate_tokens, MAX_TOKENS_BEFORE_CHUNKING, chunk_transcript
            from meeting_notes.core.storage import get_data_dir, get_config_dir
            from meeting_notes.core.state import read_state, write_state
            from datetime import datetime, timezone
            from meeting_notes.services.llm import OLLAMA_MODEL

            self.progress.emit("Loading transcript...")
            transcripts_dir = get_data_dir(self._config.storage_path) / "transcripts"
            transcript_path = transcripts_dir / f"{self._stem}.txt"
            transcript_text = transcript_path.read_text().strip()

            template_text = load_template(self._template)
            self.progress.emit("Generating notes...")
            # Single-pass (chunking omitted for brevity — replicate CLI logic)
            prompt = build_prompt(template_text, transcript_text)
            notes = generate_notes(prompt)

            notes_dir = get_data_dir(self._config.storage_path) / "notes"
            notes_path = notes_dir / f"{self._stem}-{self._template}.md"
            notes_path.write_text(notes)

            # Metadata update + Notion push (mirrors summarize.py)
            ...

            self.finished.emit(notion_url or "")
        except Exception as exc:
            self.failed.emit(str(exc))
```

**Note:** The full `SummarizeWorker.run()` body mirrors `cli/commands/summarize.py` logic — read transcript, build prompt, generate notes, save file, update metadata, push to Notion if configured. Copy the exact logic from `summarize.py` lines 86–179 rather than reimplementing.

### QTimer Recording Poll

```python
# In DashboardView
from PySide6.QtCore import QTimer
from meeting_notes.core.state import read_state, check_for_stale_session
from meeting_notes.core.storage import get_config_dir

def _refresh_recording_state(self) -> None:
    state_path = get_config_dir() / "state.json"
    state = read_state(state_path)
    if state and check_for_stale_session(state):
        start_time_str = state.get("start_time", "")
        # derive elapsed seconds from ISO start_time
        from datetime import datetime, timezone
        start = datetime.fromisoformat(start_time_str)
        elapsed = int((datetime.now(timezone.utc) - start).total_seconds())
        mins, secs = divmod(elapsed, 60)
        hours, mins = divmod(mins, 60)
        elapsed_str = f"{hours}:{mins:02d}:{secs:02d}"
        self._set_recording_active(elapsed_str)
    else:
        self._set_recording_idle()
```

### QDesktopServices for Notion URL

```python
# Source: PySide6 docs — QDesktopServices
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

def _open_notion(self) -> None:
    url = self._current_session.get("notion_url", "")
    if url:
        QDesktopServices.openUrl(QUrl(url))
```

### StatusPill Widget (badge.py)

```python
# Idle pill: gray QFrame + "Idle" QLabel
# Recording pill: red QFrame + "● Recording • H:MM:SS" QLabel
# Uses setStyleSheet() on the QFrame for dynamic color — exception to no-inline rule
# because color is determined at runtime, not compile time

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from meeting_notes.gui.theme import COLORS, FONTS

class StatusPill(QFrame):
    def set_idle(self) -> None:
        self.setStyleSheet(f"background: {COLORS['border']}; border-radius: 10px; padding: 2px 8px;")
        self._label.setText("Idle")

    def set_recording(self, elapsed: str) -> None:
        self.setStyleSheet(f"background: {COLORS['red']}; border-radius: 10px; padding: 2px 8px;")
        self._label.setText(f"● Recording \u2022 {elapsed}")
        self._label.setStyleSheet("color: white;")
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| PySide2 / PyQt5 | PySide6 6.7+ | `Signal`/`Slot` same API; `exec_()` → `exec()` |
| `QThread.run()` with module-level imports | Lazy imports inside `run()` | Keeps startup < 2s — enforced by test |
| Manual `QListWidget.addItem(text)` | `QListWidget` + `setItemWidget()` for rich rows | Enables custom `SessionRowWidget` layout |

---

## Open Questions

1. **`SummarizeWorker` map-reduce path**
   - What we know: CLI `summarize.py` has full map-reduce logic for transcripts > 8000 tokens
   - What's unclear: Should `SummarizeWorker` implement the same chunking? The worker's `run()` body needs to replicate or call the map-reduce path.
   - Recommendation: Yes — copy the `_map_reduce_summarize` logic into `SummarizeWorker.run()` or call a shared helper. Emit `progress("Summarizing chunk 1/3...")` during map phase. This is implementation detail for the planner to specify.

2. **`SessionRowWidget` vs plain `QListWidget` items for Dashboard recent sessions**
   - What we know: Sessions list uses `SessionRowWidget` with custom layout. Dashboard recent sessions is a simpler 5-row list.
   - Recommendation: Dashboard recent sessions can reuse `SessionRowWidget` for consistency, or use plain `QListWidgetItem` with display text. The planner should decide; the research supports both.

3. **`speaker_count` field in metadata**
   - What we know: Metadata has `speaker_turns` list (from `transcribe.py`). `word_count` field is explicit. `speaker_count` is not stored explicitly.
   - Recommendation: Derive `speaker_count` at render time: `len(set(t["speaker"] for t in meta.get("speaker_turns", [])))`. This is zero for sessions without diarization.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PySide6 | All GUI widgets | ✓ | 6.11.0 | None — required |
| PySide6.QtCore (QThread, Signal, QTimer) | Workers, Dashboard polling | ✓ | 6.11.0 | — |
| PySide6.QtGui (QDesktopServices) | SESS-05 Notion URL | ✓ | 6.11.0 | — |
| mlx_whisper (via worker) | TranscribeWorker | available in venv | — | Not needed at import time |
| meeting_notes services | Workers | ✓ | — | — |
| pytest + PySide6 | Test suite | ✓ | pytest 9.0.2 | — |

**No missing blocking dependencies.**

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (inferred; no pytest.ini found) |
| Quick run command | `.venv/bin/python -m pytest tests/test_gui_sessions.py tests/test_gui_dashboard.py tests/test_gui_workers.py -x -q` |
| Full suite command | `.venv/bin/python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SESS-01 | SessionsView shows scrollable list | unit/widget | `.venv/bin/python -m pytest tests/test_gui_sessions.py::test_sessions_list_populated -x` | Wave 0 |
| SESS-02 | Filter bar filters by status | unit/widget | `.venv/bin/python -m pytest tests/test_gui_sessions.py::test_sessions_filter_status -x` | Wave 0 |
| SESS-03 | Detail panel shows metadata fields | unit/widget | `.venv/bin/python -m pytest tests/test_gui_sessions.py::test_detail_panel_loads_session -x` | Wave 0 |
| SESS-04 | Pipeline indicator fills green on done steps | unit/widget | `.venv/bin/python -m pytest tests/test_gui_sessions.py::test_pipeline_indicator_steps -x` | Wave 0 |
| SESS-05 | Open Notion URL via QDesktopServices | unit (mock) | `.venv/bin/python -m pytest tests/test_gui_sessions.py::test_open_notion_url -x` | Wave 0 |
| SESS-06 | TranscribeWorker emits correct signals | unit (mock service) | `.venv/bin/python -m pytest tests/test_gui_workers.py::test_transcribe_worker_signals -x` | Wave 0 |
| SESS-07 | SummarizeWorker emits correct signals | unit (mock service) | `.venv/bin/python -m pytest tests/test_gui_workers.py::test_summarize_worker_signals -x` | Wave 0 |
| SESS-08 | Tab bar shows transcript/notes/SRT content | unit/widget | `.venv/bin/python -m pytest tests/test_gui_sessions.py::test_detail_tabs_content -x` | Wave 0 |
| DASH-01 | Dashboard shows correct stat counts | unit/widget | `.venv/bin/python -m pytest tests/test_gui_dashboard.py::test_dashboard_stats -x` | Wave 0 |
| DASH-02 | Last 5 sessions rendered; row click navigates | unit/widget | `.venv/bin/python -m pytest tests/test_gui_dashboard.py::test_dashboard_recent_sessions -x` | Wave 0 |
| DASH-03 | QTimer polls state.json; pill updates | unit (mock state) | `.venv/bin/python -m pytest tests/test_gui_dashboard.py::test_dashboard_recording_indicator -x` | Wave 0 |
| DASH-04 | "Start Recording" navigates to Record view | unit/widget | `.venv/bin/python -m pytest tests/test_gui_dashboard.py::test_dashboard_navigate_to_record -x` | Wave 0 |

**Testing ML workers:** Use `monkeypatch` to replace the lazy-imported service function inside `run()`. Since the import is inside `run()`, patch at the module level: `monkeypatch.setattr("meeting_notes.services.transcription.transcribe_audio", mock_fn)`.

### Sampling Rate

- **Per task commit:** `.venv/bin/python -m pytest tests/test_gui_sessions.py tests/test_gui_dashboard.py tests/test_gui_workers.py -x -q`
- **Per wave merge:** `.venv/bin/python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_gui_sessions.py` — covers SESS-01 through SESS-08
- [ ] `tests/test_gui_dashboard.py` — covers DASH-01 through DASH-04
- [ ] `tests/test_gui_workers.py` — covers TranscribeWorker and SummarizeWorker signal behavior

Existing `conftest.py` `qt_app` fixture is sufficient — no new fixture infrastructure needed.

---

## Project Constraints (from CLAUDE.md)

No `CLAUDE.md` found in project root. Constraints are sourced from `GUI-MILESTONE-PLAN.md` (canonical spec) and `STATE.md` (project decisions):

- PySide6 only — no other Qt bindings
- All heavy ML imports (`mlx_whisper`, `pyannote.audio`, `torchaudio`) must be inside worker `run()` methods — enforced by `test_gui_app_no_ml_imports`
- MVP pattern: Views have zero business logic; Workers call service layer directly; no Qt widget imports in workers
- All signals defined at class level using `Signal(type)`; all receivers decorated with `@Slot(type)`
- No magic strings for colors, fonts, or spacing outside `theme.py`
- No blocking calls on the main Qt thread
- `meet` CLI entry point must remain unchanged
- Config loaded once at startup, passed as reference
- `QMessageBox.warning()` for all worker error surface
- `showEvent` triggers data refresh (not `__init__`)

---

## Sources

### Primary (HIGH confidence)

- `GUI-MILESTONE-PLAN.md` — Worker signal interfaces, threading rules, screen specs, PySide6 standards
- `.planning/phases/01-gui-foundation/01-UI-SPEC.md` — Spacing scale, typography, color palette, QSS component inventory
- `meeting_notes/gui/theme.py` — Verified COLORS dict, FONTS dict, APP_STYLESHEET, factory functions (already implemented)
- `meeting_notes/gui/main_window.py` — Existing navigation mechanism confirmed
- `meeting_notes/cli/commands/list.py` — Session data derivation helpers (status, title, date, duration) confirmed working
- `meeting_notes/cli/commands/transcribe.py` — Metadata JSON shape: `wav_path`, `transcript_path`, `srt_path`, `transcribed_at`, `word_count`, `speaker_turns`, `diarization_succeeded`
- `meeting_notes/cli/commands/summarize.py` — Metadata JSON shape: `notes_path`, `template`, `summarized_at`, `llm_model`, `notion_url`
- `meeting_notes/core/state.py` — `read_state`, `check_for_stale_session` confirmed
- `meeting_notes/core/config.py` — Config dataclass fields confirmed

### Secondary (MEDIUM confidence)

- PySide6 6.11.0 confirmed installed in `.venv` — all widgets used in spec (`QSplitter`, `QTabWidget`, `QListWidget`, `QPlainTextEdit`, `QComboBox`, `QTimer`, `QDesktopServices`) are available in this version
- `tests/conftest.py` — `qt_app` session fixture confirmed; pattern for new GUI tests established

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PySide6 6.11.0 verified in venv; all service modules read directly
- Architecture: HIGH — patterns from GUI-MILESTONE-PLAN.md + decisions locked in CONTEXT.md
- Pitfalls: HIGH — derived from code inspection of existing workers pattern + known PySide6 threading rules
- Data contract: HIGH — metadata JSON shape confirmed by reading `transcribe.py` and `summarize.py`

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable stack; PySide6 API changes rarely)
