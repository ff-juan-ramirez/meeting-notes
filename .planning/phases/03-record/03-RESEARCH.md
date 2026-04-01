# Phase 03: Record - Research

**Researched:** 2026-04-01
**Domain:** PySide6 QThread workers, state machine views, QPropertyAnimation, QTimer, service layer integration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** After `StopWorker.stopped` fires (WAV saved), view resets to Idle and stays on the Record screen. Title field clears. Recent list refreshes to include the new session. User can immediately start another recording without navigating away.
- **D-02:** Title field clears on every return to Idle — both after a successful stop and on initial load. No title preservation across sessions.
- **D-03:** The "last 2 recordings" section in Idle state reuses `SessionRowWidget` from Phase 02 (`gui/widgets/session_row.py`). Consistent with Sessions view — shows title, date, duration, and status dots. Read-only: clicking a row does nothing in this context (no navigation to Sessions from here — that belongs in Phase 05 cross-view wiring).
- **D-04:** If `StopWorker.failed` fires, show `QMessageBox.warning()` with the error string and return the view to **Recording state** (not Idle). The ffmpeg process may still be running — the user retains the Stop button and can try again or restart the app.
- **D-05:** If `RecordWorker.failed` fires (ffmpeg couldn't start), show `QMessageBox.warning()` with the error string and return to Idle state. Established Phase 02 error pattern.

### Claude's Discretion

- QPropertyAnimation opacity pulse on the record button in Recording state — implementation details (duration, opacity range) left to Claude
- Whether device indices are shown as `QLabel` or `QSpinBox` — read-only display in Idle state; milestone plan shows "System: :1 | Mic: :2" inline label format
- `QTimer` interval for elapsed time: 1 second (per milestone plan)
- Stopping state: disable all buttons, show "Stopping and saving..." status label
- `RecordWorker` stores `(pid, output_path)` returned by `started` signal in view-level instance vars (`self._pid`, `self._output_path`) for use by `StopWorker`
- Test structure: `FakeRecordWorker` / `FakeStopWorker` classes (not MagicMock), following Phase 02 FakeWorker pattern

### Deferred Ideas (OUT OF SCOPE)

- Clicking a recent SessionRowWidget row to navigate to Sessions view with that session pre-selected. Deferred to Phase 05 (cross-view navigation wiring).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REC-01 | User can start a recording with an optional title (Idle state → Recording state) | RecordWorker pattern, state machine wiring via started signal |
| REC-02 | User can see elapsed time updating every second while recording (Recording state) | QTimer(1000) + elapsed calculation from start_time |
| REC-03 | User can stop the recording (Recording state → Stopping state → Idle state) | StopWorker pattern, state transitions via stopped signal |
| REC-04 | User can see device info (system device index + mic device index) in the Idle state | config.audio.system_device_index / microphone_device_index |
| REC-05 | Recording creates a WAV file using the existing `meet record` / `meet stop` service layer | audio.start_recording() / audio.stop_recording() wrapped in workers |
</phase_requirements>

---

## Summary

Phase 03 replaces the `RecordView` placeholder with a fully functional three-state (Idle/Recording/Stopping) view backed by two new QThread workers: `RecordWorker` and `StopWorker`. Both workers wrap the existing `start_recording` / `stop_recording` service layer from `meeting_notes/services/audio.py` without modifying it. The state machine is entirely signal-driven — button clicks only start workers, and state transitions happen exclusively when worker signals fire.

The implementation follows patterns established in Phase 02 exactly: workers receive all dependencies at construction, import service modules inside `run()`, define signals at class level, and use FakeWorker classes (not MagicMock) for testing. The `showEvent` pattern restores active recording state from `state.json` on every view show, matching Dashboard behavior. The one new UI element — a circular record button with QPropertyAnimation opacity pulse — requires a single new QSS rule added to `theme.py`.

All state lifecycle operations (write_state, read_state, clear_state) must mirror the CLI `meet record` / `meet stop` commands exactly so the Dashboard's polling of `state.json` continues to work correctly.

**Primary recommendation:** Build workers first (Wave 1), then the state machine view (Wave 2), then tests (Wave 3). The service layer requires zero changes.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | >=6.7 | Qt widgets, QThread, Signal/Slot, QPropertyAnimation, QTimer | Project-locked in pyproject.toml [gui] extras |
| Python stdlib | >=3.11 | datetime, os, uuid4, subprocess | Already in use throughout codebase |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `meeting_notes.services.audio` | project | `start_recording(config, output_path=None)` → `(Popen, Path)`, `stop_recording(proc)` | Called inside worker `run()` methods only |
| `meeting_notes.core.state` | project | `write_state`, `read_state`, `clear_state` | State lifecycle in workers + showEvent restoration |
| `meeting_notes.core.storage` | project | `list_sessions()`, `get_recording_path_with_slug()`, `slugify()`, `get_data_dir()`, `get_config_dir()` | Path resolution, recent session list |
| `meeting_notes.gui.widgets.session_row` | project | `SessionRowWidget` | Recent recordings list (2 rows, read-only) |
| `meeting_notes.gui.theme` | project | `make_label()`, `make_button()`, `COLORS`, `APP_STYLESHEET` | All UI construction |
| `meeting_notes.core.config` | project | `Config` dataclass — `config.audio.system_device_index`, `config.audio.microphone_device_index` | Device info display + worker construction |

### No New Dependencies

This phase adds zero new pip dependencies. All tools are already installed.

---

## Architecture Patterns

### Recommended Project Structure

```
meeting_notes/gui/workers/
├── __init__.py          (exists)
├── transcribe_worker.py (exists — reference pattern)
├── summarize_worker.py  (exists — reference pattern)
├── record_worker.py     (NEW)
└── stop_worker.py       (NEW)

meeting_notes/gui/views/
└── record.py            (REPLACE placeholder)

meeting_notes/gui/
└── theme.py             (ADD record-circle QSS rule only)

tests/
└── test_gui_record.py   (NEW — REC-01 through REC-05)
```

### Pattern 1: Worker Signal Interface

Workers follow the exact same pattern as `TranscribeWorker` and `SummarizeWorker`. Signals defined at class level, all service imports deferred to `run()`.

```python
# Source: meeting_notes/gui/workers/transcribe_worker.py (verified in codebase)
class RecordWorker(QThread):
    started = Signal(int, str)   # pid, output_path
    failed = Signal(str)         # error message

    def __init__(self, config: Config, name: str | None) -> None:
        super().__init__()
        self._config = config
        self._name = name

    def run(self) -> None:
        try:
            from meeting_notes.services.audio import start_recording
            from meeting_notes.core.storage import (
                get_recording_path_with_slug, get_config_dir, get_data_dir
            )
            from meeting_notes.core.state import write_state, read_state, clear_state
            from meeting_notes.core.storage import slugify
            from datetime import datetime, timezone
            from uuid import uuid4
            # ... (mirrors cli/commands/record.py state lifecycle)
            self.started.emit(proc.pid, str(output_path))
        except Exception as exc:
            self.failed.emit(str(exc))
```

```python
class StopWorker(QThread):
    stopped = Signal(str)   # output_path
    failed = Signal(str)    # error message

    def __init__(self, pid: int, output_path: str, config: Config) -> None:
        super().__init__()
        self._pid = pid
        self._output_path = output_path
        self._config = config

    def run(self) -> None:
        try:
            import subprocess
            from meeting_notes.services.audio import stop_recording
            from meeting_notes.core.state import read_state, write_state, clear_state
            from meeting_notes.core.storage import get_config_dir, get_data_dir
            from datetime import datetime, timezone
            from pathlib import Path
            # ... (mirrors cli/commands/record.py stop logic)
            self.stopped.emit(self._output_path)
        except Exception as exc:
            self.failed.emit(str(exc))
```

### Pattern 2: State Machine View

The view maintains `_state` ("idle" | "recording" | "stopping") and transitions only via worker signals. All button clicks merely start workers.

```python
# Source: pattern from gui/views/sessions.py + CONTEXT.md D-01 through D-05
class RecordView(QWidget):
    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._pid: int | None = None
        self._output_path: str | None = None
        self._record_worker: RecordWorker | None = None
        self._stop_worker: StopWorker | None = None
        self._elapsed_timer: QTimer | None = None
        self._start_time: datetime | None = None
        self._animation: QPropertyAnimation | None = None
        self._build_ui()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._restore_or_idle()

    def _restore_or_idle(self) -> None:
        """Check state.json; restore Recording state or enter Idle."""
        from meeting_notes.core.state import read_state
        from meeting_notes.core.storage import get_config_dir
        state = read_state(get_config_dir() / "state.json")
        if state and state.get("pid") and state.get("output_path"):
            self._pid = state["pid"]
            self._output_path = state["output_path"]
            start_time_str = state.get("start_time")
            if start_time_str:
                from datetime import datetime, timezone
                self._start_time = datetime.fromisoformat(start_time_str)
            self._enter_recording_state()
        else:
            self._enter_idle_state()
```

### Pattern 3: State Lifecycle (mirrors CLI exactly)

`RecordWorker.run()` must write `state.json` in the exact same format as `cli/commands/record.py`. This is critical for Dashboard compatibility.

```python
# Source: meeting_notes/cli/commands/record.py lines 61-71 (verified in codebase)
state = {
    "session_id": session_id,       # uuid4().hex
    "pid": proc.pid,
    "output_path": str(output_path),
    "start_time": datetime.now(timezone.utc).isoformat(),
}
if recording_name:
    state["recording_name"] = recording_name
    state["recording_slug"] = recording_slug
write_state(state_path, state)
```

`StopWorker.run()` must write metadata JSON and clear state in the same format as `cli/commands/record.py stop`:

```python
# Source: meeting_notes/cli/commands/record.py lines 116-146 (verified in codebase)
meta["duration_seconds"] = duration_seconds      # computed from start_time
meta["wav_path"] = str(Path(output_path_str).resolve())
if recording_name:
    meta["recording_name"] = recording_name
    meta["recording_slug"] = recording_slug
write_state(metadata_path, meta)
clear_state(state_path)
```

### Pattern 4: QPropertyAnimation Opacity Pulse

```python
# Source: 03-UI-SPEC.md Animation Contract (verified)
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect

# Attach opacity effect to button for QPropertyAnimation to target
effect = QGraphicsOpacityEffect(self._record_btn)
self._record_btn.setGraphicsEffect(effect)

self._animation = QPropertyAnimation(effect, b"opacity")
self._animation.setDuration(1200)
self._animation.setStartValue(1.0)
self._animation.setEndValue(0.4)
self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
self._animation.setLoopCount(-1)   # infinite

# Start: self._animation.start()
# Stop:  self._animation.stop(); effect.setOpacity(1.0)
```

**Critical implementation note:** `QPropertyAnimation` cannot animate `windowOpacity` directly on a child widget — it only works on `QWindow`. To animate opacity on a `QPushButton` inside a layout, the correct approach is attaching `QGraphicsOpacityEffect` to the button and animating the effect's `opacity` property. The UI-SPEC says "windowOpacity via QPropertyAnimation on the button's opacity" — interpret this as the effect's `opacity` property.

### Pattern 5: Elapsed Time QTimer

```python
# QTimer fires every 1000ms; elapsed derived from stored start_time
self._elapsed_timer = QTimer(self)
self._elapsed_timer.setInterval(1000)
self._elapsed_timer.timeout.connect(self._update_elapsed)

def _update_elapsed(self) -> None:
    if self._start_time is None:
        return
    from datetime import datetime, timezone
    elapsed = int((datetime.now(timezone.utc) - self._start_time).total_seconds())
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    self._elapsed_label.setText(f"{hours}:{minutes:02d}:{seconds:02d}")
```

### Pattern 6: FakeWorker Test Pattern

```python
# Source: established in Phase 02 (STATE.md entry: "FakeWorker class (not MagicMock)")
class FakeRecordWorker(QThread):
    started = Signal(int, str)
    failed = Signal(str)

    def __init__(self, config, name, *, emit_started=True, pid=12345,
                 output_path="/tmp/test.wav"):
        super().__init__()
        self._emit_started = emit_started
        self._pid = pid
        self._output_path = output_path

    def run(self) -> None:
        if self._emit_started:
            self.started.emit(self._pid, self._output_path)
        else:
            self.failed.emit("Recording failed: test error")
```

### Pattern 7: showEvent Recent List Refresh

```python
# Source: Phase 02 pattern (gui/views/sessions.py showEvent)
def _refresh_recent(self) -> None:
    """Load 2 most recent sessions sorted by start_time descending."""
    from meeting_notes.core.storage import get_data_dir
    from meeting_notes.core.state import read_state
    # ... scan metadata dir, sort by start_time, take [:2]
    # Use same _derive_title / _derive_status helpers as sessions.py
    # Clear and repopulate list with SessionRowWidget instances
```

### Anti-Patterns to Avoid

- **Transitioning state from button click handler directly:** Buttons only call `worker.start()`. State transitions ONLY happen in `@Slot` handlers connected to worker signals.
- **Importing service modules at the top of worker files:** All `from meeting_notes.services.audio import ...` must be inside `run()`.
- **Using MagicMock for worker tests:** PySide6 Signal type checking rejects MagicMock. Always use concrete FakeWorker QThread subclasses.
- **Animating `windowOpacity` on a child widget:** Use `QGraphicsOpacityEffect` + animate the effect's `opacity` property.
- **Writing state.json in a different format than the CLI:** Dashboard polls state.json; any schema difference breaks the recording indicator.
- **Storing `subprocess.Popen` object across thread boundary:** The CLI stop command reconstructs a minimal Popen object from the stored PID — `StopWorker` must do the same.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Opus pulse animation | Custom paint loop | `QPropertyAnimation` + `QGraphicsOpacityEffect` | Qt handles frame timing, easing curves, and loop count |
| Elapsed time display | Manual time math | `QTimer(1000)` + datetime arithmetic | Timer drift is negligible at 1s intervals; stdlib datetime handles UTC correctly |
| Thread-safe signal delivery | Mutex + callbacks | Qt signal/slot cross-thread queued connections | Qt's event loop guarantees delivery order; no manual locking needed |
| Session list sorting/slicing | Custom comparator | `sorted(..., key=lambda m: m.get("start_time",""), reverse=True)[:2]` | Already established in dashboard.py |
| WAV duration for recent rows | Re-implement wav reader | Reuse `_wav_duration()` pattern from `sessions.py` / `dashboard.py` | Pattern already exists — copy (not import) per established convention |

**Key insight:** Cross-view helper duplication (like `_wav_duration`, `_derive_status`, `_derive_title`) is intentional in this codebase — views are designed as self-contained units without cross-imports between view files.

---

## Common Pitfalls

### Pitfall 1: QPropertyAnimation on windowOpacity vs. QGraphicsOpacityEffect
**What goes wrong:** Calling `QPropertyAnimation(button, b"windowOpacity")` has no effect on a child widget inside a layout — `windowOpacity` is a `QWindow` property, not a `QWidget` property.
**Why it happens:** Confusing window-level opacity with widget-level opacity.
**How to avoid:** Attach `QGraphicsOpacityEffect` to the button, then animate `effect.opacity` via `QPropertyAnimation(effect, b"opacity")`.
**Warning signs:** Animation starts with no visible pulse on the button.

### Pitfall 2: State JSON Schema Drift
**What goes wrong:** If RecordWorker writes state.json with a different key structure than the CLI, the Dashboard's `_check_recording_state()` polls it and fails to detect active recording from the GUI.
**Why it happens:** Workers reimplement the state write logic independently.
**How to avoid:** Copy the state dict construction verbatim from `cli/commands/record.py` lines 61-71. Include `session_id`, `pid`, `output_path`, `start_time`, and optionally `recording_name`/`recording_slug`.
**Warning signs:** Dashboard shows "Idle" while GUI Record view shows "Recording".

### Pitfall 3: Popen Reconstruction for StopWorker
**What goes wrong:** StopWorker cannot hold a `subprocess.Popen` object constructed in RecordWorker across thread boundaries (and shouldn't store Qt objects in workers). The CLI uses `subprocess.Popen.__new__(subprocess.Popen)` with manual `.pid` assignment.
**Why it happens:** `stop_recording(proc)` expects a Popen object, but only the PID is serializable.
**How to avoid:** In StopWorker.run(), reconstruct the Popen object: `proc = subprocess.Popen.__new__(subprocess.Popen); proc.pid = self._pid; proc.returncode = None`, then call `stop_recording(proc)`. This is exactly what `cli/commands/record.py` does.
**Warning signs:** `stop_recording()` raises AttributeError on missing pid.

### Pitfall 4: processEvents() Required After worker.wait() in Tests
**What goes wrong:** Cross-thread signal delivery is queued in Qt's event loop. After `worker.wait()` in tests, the signal may be queued but not yet delivered to slots.
**Why it happens:** Qt signal delivery requires event loop processing.
**How to avoid:** Always call `QApplication.instance().processEvents()` after `worker.wait()` in tests.
**Warning signs:** Signal result lists are empty after worker.wait() completes.
**Source:** STATE.md: "[Phase 02]: processEvents() required after worker.wait() — Qt cross-thread signals are queued and need event loop processing"

### Pitfall 5: StopWorker.failed Returns to Recording State (not Idle)
**What goes wrong:** Treating stop failure like record failure — both returning to Idle.
**Why it happens:** Intuitive but wrong. If stop fails, ffmpeg may still be running.
**How to avoid:** D-04 is a locked decision: `StopWorker.failed` → `QMessageBox.warning()` → restore Recording state (re-enable Stop button, restart elapsed timer if needed).
**Warning signs:** After a stop failure, user loses the Stop button and cannot try again.

### Pitfall 6: Title Field Not Cleared on Every Idle Entry
**What goes wrong:** Title persists after a successful stop, or after an error recovery.
**Why it happens:** Only clearing title in `__init__`.
**How to avoid:** D-02 is locked: call `self._title_field.clear()` in `_enter_idle_state()`, which is called both on first show and after successful stop.

### Pitfall 7: blockSignals Not Used When Rebuilding Recent List
**What goes wrong:** Spurious signals fire while clearing and repopulating the recent recordings list widget.
**Why it happens:** QListWidget emits `currentRowChanged` during clear/repopulate.
**How to avoid:** Wrap list repopulation with `self._recent_list.blockSignals(True)` / `blockSignals(False)` — established Phase 02 pattern.
**Source:** STATE.md: "[Phase 02]: blockSignals(True/False) around QListWidget clear/repopulate"

---

## Code Examples

### RecordWorker.run() — State Write Mirrors CLI

```python
# Source: meeting_notes/cli/commands/record.py (verified in codebase)
def run(self) -> None:
    try:
        from meeting_notes.services.audio import start_recording
        from meeting_notes.core.storage import (
            get_config_dir, get_recording_path_with_slug, slugify
        )
        from meeting_notes.core.state import (
            write_state, read_state, clear_state, check_for_stale_session
        )
        from datetime import datetime, timezone
        from uuid import uuid4

        state_path = get_config_dir() / "state.json"
        existing = read_state(state_path)
        if existing and check_for_stale_session(existing):
            self.failed.emit("Another recording is already active.")
            return
        elif existing:
            clear_state(state_path)   # stale PID — safe to clear

        recording_name = self._name.strip() if self._name else None
        recording_slug = slugify(recording_name) if recording_name else None

        if recording_name:
            from meeting_notes.core.storage import get_recording_path_with_slug
            output_path_pre = get_recording_path_with_slug(recording_name, self._config.storage_path)
            proc, output_path = start_recording(self._config, output_path=output_path_pre)
        else:
            proc, output_path = start_recording(self._config)

        state = {
            "session_id": uuid4().hex,
            "pid": proc.pid,
            "output_path": str(output_path),
            "start_time": datetime.now(timezone.utc).isoformat(),
        }
        if recording_name:
            state["recording_name"] = recording_name
            state["recording_slug"] = recording_slug
        write_state(state_path, state)

        self.started.emit(proc.pid, str(output_path))
    except Exception as exc:
        self.failed.emit(str(exc))
```

### StopWorker.run() — Metadata Write + State Clear Mirrors CLI

```python
# Source: meeting_notes/cli/commands/record.py stop function (verified in codebase)
def run(self) -> None:
    try:
        import subprocess
        from meeting_notes.services.audio import stop_recording
        from meeting_notes.core.storage import get_config_dir, get_data_dir
        from meeting_notes.core.state import read_state, write_state, clear_state
        from datetime import datetime, timezone
        from pathlib import Path

        # Reconstruct Popen from stored PID (same technique as CLI stop)
        proc = subprocess.Popen.__new__(subprocess.Popen)
        proc.pid = self._pid
        proc.returncode = None
        stop_recording(proc)

        # Write metadata
        stem = Path(self._output_path).stem
        data_dir = get_data_dir(self._config.storage_path)
        metadata_dir = data_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = metadata_dir / f"{stem}.json"

        state_path = get_config_dir() / "state.json"
        existing_state = read_state(state_path) or {}

        meta = read_state(metadata_path) or {}
        start_time_str = existing_state.get("start_time")
        if start_time_str:
            start = datetime.fromisoformat(start_time_str)
            now = datetime.now(timezone.utc)
            meta["duration_seconds"] = int((now - start).total_seconds())
        meta["wav_path"] = str(Path(self._output_path).resolve())

        recording_name = existing_state.get("recording_name")
        recording_slug = existing_state.get("recording_slug")
        if recording_name:
            meta["recording_name"] = recording_name
        if recording_slug:
            meta["recording_slug"] = recording_slug

        write_state(metadata_path, meta)
        clear_state(state_path)

        self.stopped.emit(self._output_path)
    except Exception as exc:
        self.failed.emit(str(exc))
```

### QSS Addition for Circular Record Button

```python
# Source: 03-UI-SPEC.md Component Inventory (verified)
# Add to APP_STYLESHEET in theme.py
"""
QPushButton[style="record-circle"] {
    background: #FF3B30;
    color: white;
    border-radius: 40px;
    font-weight: bold;
    border: none;
    min-width: 80px;  max-width: 80px;
    min-height: 80px; max-height: 80px;
}

QPushButton[style="record-circle"]:disabled {
    background: #E5E5EA;
    color: #8E8E93;
}
"""
```

### Device Info Label Construction

```python
# Source: CONTEXT.md specifics + 03-UI-SPEC.md Idle State Layout (verified)
device_info_text = (
    f"System: :{self._config.audio.system_device_index} "
    f"| Mic: :{self._config.audio.microphone_device_index}"
)
self._device_info_label = make_label(device_info_text, role="body")
```

### Slot Decorators and Signal Connection (locked by project style)

```python
# Source: GUI-MILESTONE-PLAN.md PySide6 Standards §1 + STATE.md (verified)
from PySide6.QtCore import Slot, Signal

@Slot(int, str)
def _on_record_started(self, pid: int, output_path: str) -> None:
    self._pid = pid
    self._output_path = output_path
    self._enter_recording_state()

@Slot(str)
def _on_record_failed(self, msg: str) -> None:
    QMessageBox.warning(self, "Recording Failed",
        f"Could not start recording: {msg}. Check your audio device configuration.")
    self._enter_idle_state()

@Slot(str)
def _on_stop_done(self, output_path: str) -> None:
    self._enter_idle_state()   # clears title, refreshes recent list (D-01, D-02)

@Slot(str)
def _on_stop_failed(self, msg: str) -> None:
    QMessageBox.warning(self, "Stop Failed",
        f"Could not save the recording: {msg}. "
        "The recording may still be active — try stopping again or restart the app.")
    self._enter_recording_state()   # D-04: return to Recording, not Idle
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Button click directly mutates state | Signal-driven state machine only | Phase 02 established | Prevents race conditions when worker takes time |
| Magic strings for QSS | `setProperty("style", "primary")` + class-level APP_STYLESHEET | Phase 01 established | Single source of truth in theme.py |
| MagicMock for Qt workers | FakeWorker QThread subclasses | Phase 02 established | Avoids PySide6 Signal type mismatches |

---

## Open Questions

1. **Does `list_sessions()` exist in storage.py?**
   - What we know: `CONTEXT.md` references `list_sessions()` from `core/storage` for refreshing recent recordings. `storage.py` was fully read and does not contain `list_sessions()`.
   - What's unclear: The function may be in a different module (sessions service?), or the view may need to implement its own scan of the metadata directory directly (as `dashboard.py` and `sessions.py` do).
   - Recommendation: The planner should note that the recent list population must be implemented by scanning `get_data_dir(config.storage_path) / "metadata"` directly, matching the pattern used in `dashboard.py` — no `list_sessions()` import needed. This is consistent with the established "views are self-contained" pattern.

2. **Does the `storage.py` module contain `list_sessions()`?**
   - What we know: `storage.py` contains `get_config_dir`, `get_data_dir`, `ensure_dirs`, `slugify`, `get_recording_path`, `get_recording_path_with_slug`. No `list_sessions()`.
   - What's unclear: `CONTEXT.md` references `list_sessions()` and `read_session_metadata()` from `core/storage`. These may not exist yet or may live elsewhere.
   - Recommendation: Wave 0 or Wave 1 plan should confirm whether these functions exist. If not, the recent list can be built by scanning the metadata directory directly (established pattern in `sessions.py`).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All | ✓ | 3.14 | — |
| PySide6 | GUI workers + view | ✗ (in test env) | not installed in test venv | GUI tests require `pip install -e ".[gui]"` |
| ffmpeg | start_recording service | assumed ✓ (existing CLI works) | system install | — |

**PySide6 availability note:** All GUI tests fail in the current test environment with `ModuleNotFoundError: No module named 'PySide6'`. This is an environment configuration issue, not a code issue — the same pattern exists for all existing GUI tests (test_gui_workers.py, test_gui_theme.py, etc.). The plan must account for this by scoping tests to run with `pip install -e ".[gui]"` active.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none (uses default discovery) |
| Quick run command | `python3 -m pytest tests/test_gui_record.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q --ignore=tests/test_gui_sessions.py` |

**Note:** `tests/test_gui_sessions.py` currently causes a collection error (ModuleNotFoundError for a missing module). The plan must not break other tests, but should not depend on test_gui_sessions.py passing.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REC-01 | RecordWorker.started fires with (pid, output_path) when start_recording succeeds | unit | `python3 -m pytest tests/test_gui_record.py::test_record_worker_started_signal -x` | ❌ Wave 0 |
| REC-01 | RecordWorker.failed fires when start_recording raises | unit | `python3 -m pytest tests/test_gui_record.py::test_record_worker_failed_signal -x` | ❌ Wave 0 |
| REC-01 | RecordView transitions to Recording state after started signal | unit | `python3 -m pytest tests/test_gui_record.py::test_record_view_starts_recording -x` | ❌ Wave 0 |
| REC-02 | Elapsed time label updates format H:MM:SS | unit | `python3 -m pytest tests/test_gui_record.py::test_elapsed_time_format -x` | ❌ Wave 0 |
| REC-03 | StopWorker.stopped fires after stop_recording succeeds | unit | `python3 -m pytest tests/test_gui_record.py::test_stop_worker_stopped_signal -x` | ❌ Wave 0 |
| REC-03 | View returns to Idle after StopWorker.stopped (D-01) | unit | `python3 -m pytest tests/test_gui_record.py::test_record_view_stops_recording -x` | ❌ Wave 0 |
| REC-03 | View returns to Recording after StopWorker.failed (D-04) | unit | `python3 -m pytest tests/test_gui_record.py::test_stop_failure_returns_to_recording -x` | ❌ Wave 0 |
| REC-04 | Device info label shows correct format "System: :1 | Mic: :2" | unit | `python3 -m pytest tests/test_gui_record.py::test_device_info_label -x` | ❌ Wave 0 |
| REC-05 | RecordWorker writes state.json in CLI-compatible format | unit | `python3 -m pytest tests/test_gui_record.py::test_record_worker_writes_state -x` | ❌ Wave 0 |
| REC-05 | StopWorker writes metadata JSON and clears state | unit | `python3 -m pytest tests/test_gui_record.py::test_stop_worker_writes_metadata -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/test_gui_record.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q --ignore=tests/test_gui_sessions.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_gui_record.py` — covers REC-01 through REC-05 with FakeRecordWorker / FakeStopWorker

---

## Sources

### Primary (HIGH confidence)

- `meeting_notes/cli/commands/record.py` — state lifecycle (write_state format, Popen reconstruction, metadata write pattern) — read in full
- `meeting_notes/services/audio.py` — `start_recording` / `stop_recording` API signatures — read in full
- `meeting_notes/core/state.py` — `write_state`, `read_state`, `clear_state`, `check_for_stale_session` — read in full
- `meeting_notes/core/storage.py` — all path helpers, slugify, get_recording_path_with_slug — read in full
- `meeting_notes/gui/workers/transcribe_worker.py` — canonical worker pattern — read in full
- `meeting_notes/gui/workers/summarize_worker.py` — canonical worker pattern with metadata write — read in full
- `meeting_notes/gui/widgets/session_row.py` — `SessionRowWidget` constructor and sizing — read in full
- `meeting_notes/gui/theme.py` — COLORS, FONTS, make_label, make_button, APP_STYLESHEET — read in full
- `meeting_notes/gui/views/record.py` — current placeholder — read in full
- `meeting_notes/core/config.py` — Config dataclass, `config.audio.system_device_index` / `microphone_device_index` — read in full
- `.planning/phases/03-record/03-CONTEXT.md` — all locked decisions D-01 through D-05
- `.planning/phases/03-record/03-UI-SPEC.md` — full visual/interaction contract
- `GUI-MILESTONE-PLAN.md` — Screen 3 spec, worker table, PySide6 standards
- `tests/test_gui_workers.py` — FakeWorker test pattern precedent, processEvents() usage
- `tests/conftest.py` — qt_app fixture, session scope QApplication

### Secondary (MEDIUM confidence)

- `meeting_notes/gui/views/sessions.py` — showEvent, _derive_status, _derive_title, blockSignals pattern
- `meeting_notes/gui/views/dashboard.py` — state.json polling, SessionRowWidget usage pattern
- `.planning/STATE.md` — Phase 02 decisions relevant to GUI worker patterns

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies verified by reading actual source files
- Architecture: HIGH — worker/view patterns verified from existing codebase implementation
- Pitfalls: HIGH — verified from STATE.md decisions + code reading (not speculation)
- Test infrastructure: HIGH — test files and conftest.py read directly; PySide6 absence confirmed by test run

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable PySide6 API, no fast-moving dependencies)
