# Phase 01: GUI Foundation - Research

**Researched:** 2026-03-30
**Domain:** PySide6 desktop GUI + Python service layer refactor
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** All implementation decisions deferred to Claude's discretion — the user confirmed
  `GUI-MILESTONE-PLAN.md` is the authoritative spec. Follow it faithfully.
- **D-02:** Use `meeting-notes-ui-mockups.pdf` as the visual/structural reference for layout
  and content. Exact pixel-perfect match not required; treat it as a structural guide.

### Claude's Discretion
All visual choices (color palette, dark/light theme, sidebar icon treatment, placeholder view
content) are Claude's to decide, guided by the mockup PDF and milestone plan. Recommended
defaults:
- Derive colors from the mockup PDF visually; default to a clean dark theme matching macOS
  native feel if mockup is ambiguous
- Sidebar: icons + text (standard macOS app nav pattern)
- Placeholder views: centered `QLabel` with screen name (minimal, avoids premature work)
- TMPL-06: Switch `meet summarize --template` validation to use `list_templates()` — no
  backward-compat concern since built-in names ("meeting", "minutes", "1on1") will still be
  in the list

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GUI-01 | `meet-gui` launches in < 2 seconds, no ML imports at startup | Lazy-import pattern inside `QThread.run()` verified in GUI-MILESTONE-PLAN.md; PySide6 startup is fast when heavy modules excluded |
| GUI-02 | All 6 screens reachable via sidebar | `QMainWindow` + `QStackedWidget` + sidebar `QListWidget` navigation pattern; direct code stubs in GUI-MILESTONE-PLAN.md |
| GUI-03 | All colors, fonts, QSS in `gui/theme.py` — no magic strings elsewhere | Single `app.setStyleSheet(APP_STYLESHEET)` call pattern; `COLORS`, `FONTS` dicts + factory functions in theme.py |
| GUI-04 | `pyside6>=6.7` installable via `pip install -e ".[gui]"` | `[project.optional-dependencies] gui = ["pyside6>=6.7"]` in pyproject.toml; verified 6.11.0 available and installs on Python 3.14 |
| GUI-05 | `meet` CLI remains fully functional after all changes | No existing CLI files are modified; pyproject.toml additive changes only |
| TMPL-01 | `list_templates()` returns built-in + user templates as `{name, path, builtin}` dicts | Full implementation stub in GUI-MILESTONE-PLAN.md; pattern uses `Path.glob("*.txt")` |
| TMPL-02 | `load_template()` checks user dir before built-ins | Updated implementation in GUI-MILESTONE-PLAN.md; user path checked first |
| TMPL-03 | `save_template(name, content)` writes to user dir; raises ValueError on built-in name collision | Full stub in GUI-MILESTONE-PLAN.md |
| TMPL-04 | `delete_template(name)` removes user template; raises ValueError for built-ins | Full stub in GUI-MILESTONE-PLAN.md |
| TMPL-05 | `duplicate_template(source, new)` duplicates any template to user dir | Implemented as `load_template()` + `save_template()` chain |
| TMPL-06 | `meet summarize --template` validates via `list_templates()` not hardcoded tuple | `summarize.py` imports `VALID_TEMPLATES` and uses `click.Choice([...])` — both must change to dynamic lookup |
</phase_requirements>

---

## Summary

Phase 01 delivers the application skeleton: `meet-gui` launches `MainWindow`, 6 sidebar screens
are navigable as placeholders, `gui/theme.py` centralizes all visual constants, and
`services/llm.py` gains full template CRUD. The GUI is purely additive — no existing
`core/`, `services/`, or `cli/` files are modified except `services/llm.py` (CRUD additions)
and `cli/commands/summarize.py` (TMPL-06 validation switch).

The technical path is completely specified in `GUI-MILESTONE-PLAN.md`. PySide6 6.11.0 is
confirmed installable on the project's Python 3.14 venv via an abi3 wheel. The startup-latency
requirement (GUI-01) is met by never importing `mlx_whisper`, `pyannote.audio`, or `torchaudio`
at module level in any GUI file — all heavy imports happen inside `QThread.run()`.

The TMPL-06 change in `summarize.py` is the most structurally sensitive point: the current
`click.Choice(["meeting", "minutes", "1on1"])` must become a dynamic validator, and the
`VALID_TEMPLATES` constant must be removed from the import. Existing tests for `load_template`
will need to be extended for the new CRUD functions.

**Primary recommendation:** Follow `GUI-MILESTONE-PLAN.md` exactly as written. Implement in
the order specified: `pyproject.toml` → `theme.py` → `main_window.py` → `app.py` → template
CRUD in `llm.py` → TMPL-06 in `summarize.py`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.0 (>=6.7 constraint) | Qt6 Python bindings — widgets, threading, signals | Only Qt binding approved by project; abi3 wheel confirms Python 3.14 support |
| shiboken6 | 6.11.0 (auto-installed) | C++/Python bridge for PySide6 | Pulled in automatically; no direct use |
| PySide6_Essentials | 6.11.0 (auto-installed) | Core Qt modules (Widgets, Core, Gui) | Part of PySide6 meta-package |

### Supporting (no new deps needed beyond PySide6)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | Python 3.14 stdlib | Template file I/O for CRUD functions | All template path operations |
| dataclasses (stdlib) | Python 3.14 stdlib | Config dataclass already in use | No change needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PySide6 | PyQt6 | Same Qt API, different license (GPL vs LGPL). Project spec locks PySide6. |
| PySide6 | Tkinter | Far less capable; no serious consideration |

**Installation:**
```bash
pip install -e ".[gui]"
```

**Version verification (confirmed 2026-03-30):**
```
pyside6 6.11.0  (latest available)
shiboken6 6.11.0  (auto-pulled)
abi3 wheel: macosx_13_0_universal2 — compatible with Python 3.14 on macOS
```

---

## Architecture Patterns

### Recommended Project Structure (from GUI-MILESTONE-PLAN.md)
```
meeting_notes/
  gui/
    __init__.py
    app.py                  # QApplication entry, loads Config, launches MainWindow
    main_window.py          # QMainWindow — sidebar + QStackedWidget
    theme.py                # COLORS, FONTS, APP_STYLESHEET, factory functions
    widgets/                # Reusable atomic widgets (Phase 02+)
      badge.py
      session_row.py
      confirm_dialog.py
    views/                  # One QWidget per screen
      dashboard.py          # placeholder in Phase 01
      sessions.py           # placeholder in Phase 01
      record.py             # placeholder in Phase 01
      templates.py          # placeholder in Phase 01
      settings.py           # placeholder in Phase 01
      doctor.py             # placeholder in Phase 01
    workers/                # QThread subclasses (Phase 02+)
      record_worker.py
      transcribe_worker.py
      summarize_worker.py
      doctor_worker.py
```

### Pattern 1: MVP — Views Have Zero Business Logic
**What:** Views are dumb containers. Workers call service functions. MainWindow wires signals to slots.
**When to use:** Every view file, every worker file, no exceptions.
**Example (from GUI-MILESTONE-PLAN.md):**
```python
# Source: GUI-MILESTONE-PLAN.md — Workers section
class TranscribeWorker(QThread):
    progress = Signal(str)
    finished = Signal(str, int)
    failed   = Signal(str)

    def run(self):          # runs in worker thread
        try:
            from meeting_notes.services.transcription import transcribe_audio  # lazy import
            text, segments = transcribe_audio(self._wav_path, self._config)
            self.finished.emit(text.strip(), len(text.split()))
        except Exception as e:
            self.failed.emit(str(e))
```

### Pattern 2: Centralized Theme + QSS
**What:** All colors, font specs, and QSS in `theme.py`. One `app.setStyleSheet()` call.
**When to use:** Always. Never call `.setStyleSheet()` on individual widgets except for dynamic
state (e.g. recording pulse animation).
**Example (from GUI-MILESTONE-PLAN.md):**
```python
# Source: GUI-MILESTONE-PLAN.md — Styling System
COLORS = {
    "sidebar_bg":   "#1C1C1E",
    "accent":       "#0A84FF",
    "text_primary": "#1C1C1E",
    "green":        "#30D158",
    "red":          "#FF3B30",
    "yellow":       "#FF9F0A",
    "card_bg":      "#F9F9FB",
    "border":       "#E5E5EA",
    "input_bg":     "#F2F2F7",
}
FONTS = {
    "h1":    ("Helvetica Neue", 20, "bold"),
    "h2":    ("Helvetica Neue", 13, "bold"),
    "body":  ("Helvetica Neue", 11, "normal"),
    "mono":  ("Menlo", 10, "normal"),
    "small": ("Helvetica Neue",  9, "normal"),
}
```

### Pattern 3: Data Loading in showEvent, Not __init__
**What:** Views load no data at construction time. Data loads in `showEvent` or on explicit refresh.
**When to use:** All views, especially those scanning the filesystem.
**Example:**
```python
# Source: GUI-MILESTONE-PLAN.md — Standard 7
def showEvent(self, event):
    super().showEvent(event)
    self._refresh_data()
```

### Pattern 4: Signals at Class Level, Slots Decorated
**What:** All signals defined as class-level `Signal(type)` attributes. All receivers use `@Slot(type)`.
**When to use:** Every QThread worker and every QWidget that emits signals.
**Example:**
```python
# Source: GUI-MILESTONE-PLAN.md — PySide6 Standard 1
class MyWorker(QThread):
    progress = Signal(str)
    finished = Signal(str, int)
    failed   = Signal(str)
```

### Pattern 5: QStackedWidget Navigation via Sidebar
**What:** `MainWindow` holds a `QListWidget` sidebar and a `QStackedWidget`. Sidebar item click
sets the stacked widget current index.
**When to use:** Phase 01 core pattern.
**Key points:**
- Sidebar items order: Dashboard(0), Sessions(1), Record(2), Templates(3), Settings(4), Health Check(5)
- `QListWidget.currentRowChanged` signal → `QStackedWidget.setCurrentIndex`
- Views created once, added in index order

### Pattern 6: Template CRUD — User Dir Precedence
**What:** `list_templates()` returns built-ins first, then user templates. `load_template()`
checks user dir before built-ins. `save_template()` rejects built-in name collisions.
**Key paths:**
```python
BUILTIN_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
USER_TEMPLATES_DIR    = get_config_dir() / "templates"
# ~/.config/meeting-notes/templates/
```

### Anti-Patterns to Avoid
- **Inline stylesheet strings:** Never `.setStyleSheet("color: red")` in view files. All strings in `theme.py`.
- **Blocking the main thread:** Never call filesystem, HTTP, or subprocess operations directly in view methods. Use workers.
- **Importing ML libs at module level in GUI:** `from mlx_whisper import ...` at top of any GUI file breaks GUI-01.
- **Importing Click or Rich in GUI path:** GUI and CLI paths must be fully separate import trees.
- **Fixed widget geometry:** Never `setGeometry(x, y, w, h)`. Use layout managers.
- **Lambda chains for complex logic:** Keep signal connections to simple slots or one-line lambdas only.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Background threading | Manual `threading.Thread` + queue | `QThread` subclass | Thread safety with Qt objects requires Qt's threading; `threading.Thread` cannot safely touch Qt widgets |
| Dialog confirmations | Custom modal widget | `QMessageBox.warning()` / `.information()` | Qt built-ins are macOS-native, accessible, and tested |
| Splitter panels | Manual widget resizing | `QSplitter` | Handles resize events, drag handles, min-size enforcement |
| Layout | Manual pixel arithmetic | `QHBoxLayout`, `QVBoxLayout`, `QGridLayout` | Required for HiDPI / Retina correct rendering |
| File open dialogs | Custom file picker | `QFileDialog.getExistingDirectory()` | Native macOS file picker |

**Key insight:** Qt already solves every common UI interaction pattern. The primary skill for
this phase is knowing which Qt class maps to which UI need — not building custom solutions.

---

## Common Pitfalls

### Pitfall 1: ML Imports at Startup Break GUI-01
**What goes wrong:** `import mlx_whisper` or `import pyannote.audio` at the top of any GUI
module causes 5-15 second cold-start delay loading model weights and CUDA/MPS initialization.
**Why it happens:** Python imports execute at load time; any `gui/` import chain that reaches
a ML module file causes the import.
**How to avoid:** All heavy imports go inside `QThread.run()` methods only. The `gui/app.py`
entry point must import only `PySide6`, `meeting_notes.gui.*`, `meeting_notes.core.config`,
and `meeting_notes.core.storage`.
**Warning signs:** Cold start taking > 2 seconds. Check `import time` profiling.

### Pitfall 2: Qt Objects Created in Worker Threads
**What goes wrong:** Creating `QLabel`, `QPushButton`, or any `QWidget` subclass inside a
`QThread.run()` call causes a crash ("QWidget: Must construct a QApplication before a
QWidget").
**Why it happens:** Qt requires all GUI objects to live on the main thread.
**How to avoid:** Workers emit signals with data (strings, ints, dicts). The main-thread
view slots create/update widgets from that data.

### Pitfall 3: Worker Reference Garbage-Collected Mid-Run
**What goes wrong:** A worker starts, the Python reference goes out of scope, the garbage
collector destroys it — the thread is killed silently.
**Why it happens:** `QThread` lifetime is not managed by Qt if no Python reference exists.
**How to avoid:** Always assign the worker to `self._worker = WorkerClass(...)` on the
parent widget. Call `self._worker.quit(); self._worker.wait()` in `closeEvent`.

### Pitfall 4: TMPL-06 — VALID_TEMPLATES Still Imported in summarize.py
**What goes wrong:** `summarize.py` currently imports `VALID_TEMPLATES` and uses
`click.Choice(["meeting", "minutes", "1on1"])` hardcoded. After adding `list_templates()`,
both the `VALID_TEMPLATES` import and the hardcoded `click.Choice` list must change.
**Why it happens:** The `click.Choice` list is evaluated at import time in Click's decorator.
For a dynamic list, a `callback=` validator or a dynamic `click.Choice` built from
`list_templates()` is needed.
**How to avoid:** Replace `type=click.Choice(["meeting", "minutes", "1on1"])` with a
`callback` that calls `list_templates()` at runtime, or build the Choice list lazily.
Recommended approach from CONTEXT.md D-01 discretion: use a runtime callback.

### Pitfall 5: click.Choice with Dynamic List at Import Time
**What goes wrong:** `click.Choice([t["name"] for t in list_templates()])` called at module
import time creates `USER_TEMPLATES_DIR` (a side effect) even when the CLI is not invoked.
**Why it happens:** Python decorators execute at import time.
**How to avoid:** Use `is_eager=False` with a `callback` validator that calls `list_templates()`
inside the function body. Example:
```python
@click.option("--template", default="meeting", help="Template name")
def summarize(ctx, template, session, title):
    valid = [t["name"] for t in list_templates()]
    if template not in valid:
        raise click.BadParameter(f"Invalid template '{template}'. Choose from: {', '.join(valid)}")
```
This evaluates `list_templates()` only when `meet summarize` is actually invoked.

### Pitfall 6: Missing `__init__.py` in `gui/` Subpackages
**What goes wrong:** Python can't find `meeting_notes.gui.views.dashboard` even though the
file exists — `ImportError: No module named 'meeting_notes.gui.views'`.
**Why it happens:** Each subdirectory (`widgets/`, `views/`, `workers/`) needs an
`__init__.py` to be a Python package.
**How to avoid:** Create empty `__init__.py` in `gui/`, `gui/widgets/`, `gui/views/`,
`gui/workers/`.

### Pitfall 7: HiDPI / Retina Attribute Deprecated in Qt 6.7+
**What goes wrong:** `app.setAttribute(Qt.AA_UseHighDpiPixmaps)` emits a deprecation
warning in PySide6 6.7+ because HiDPI is enabled by default in Qt 6.
**Why it happens:** Qt 6 enables high-DPI scaling automatically.
**How to avoid:** Keep the call (it is harmless and in the spec) but do not depend on it.
The spec from `GUI-MILESTONE-PLAN.md` includes it — follow the spec.

---

## Code Examples

Verified patterns from `GUI-MILESTONE-PLAN.md`:

### App Entry Point (gui/app.py)
```python
# Source: GUI-MILESTONE-PLAN.md — Entry Point & Packaging
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from meeting_notes.gui.main_window import MainWindow
from meeting_notes.gui.theme import APP_STYLESHEET
from meeting_notes.core.config import Config
from meeting_notes.core.storage import get_config_dir, ensure_dirs

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Meeting Notes")
    app.setApplicationDisplayName("Meeting Notes")
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setStyleSheet(APP_STYLESHEET)

    config_path = get_config_dir() / "config.json"
    config = Config.load(config_path)
    ensure_dirs(config.storage_path)

    window = MainWindow(config, config_path)
    window.setMinimumSize(900, 600)
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())
```

### Template CRUD Addition to services/llm.py
```python
# Source: GUI-MILESTONE-PLAN.md — Required Core Change
from meeting_notes.core.storage import get_config_dir

BUILTIN_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
USER_TEMPLATES_DIR    = get_config_dir() / "templates"

def list_templates() -> list[dict]:
    templates = []
    for p in sorted(BUILTIN_TEMPLATES_DIR.glob("*.txt")):
        templates.append({"name": p.stem, "path": p, "builtin": True})
    USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    for p in sorted(USER_TEMPLATES_DIR.glob("*.txt")):
        templates.append({"name": p.stem, "path": p, "builtin": False})
    return templates
```

### TMPL-06 — Dynamic Template Validation in summarize.py
```python
# Runtime validation instead of import-time click.Choice
@click.option("--template", default="meeting", help="Note template (default: meeting)")
def summarize(ctx, template, session, title):
    from meeting_notes.services.llm import list_templates
    valid_names = [t["name"] for t in list_templates()]
    if template not in valid_names:
        console.print(f"[red]Error:[/red] Invalid template '{template}'. Choose from: {', '.join(valid_names)}")
        sys.exit(1)
    # ... rest of command
```

### pyproject.toml Changes
```toml
# Source: GUI-MILESTONE-PLAN.md — Entry Point & Packaging
[project.scripts]
meet     = "meeting_notes.cli.main:main"
meet-gui = "meeting_notes.gui.app:main"   # new

[project.optional-dependencies]
gui = ["pyside6>=6.7"]
```

### Placeholder View (minimal, avoids premature work)
```python
# Source: CONTEXT.md — Claude's Discretion
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class DashboardView(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("Dashboard")
        layout.addWidget(label)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `VALID_TEMPLATES` tuple + `click.Choice` hardcoded | `list_templates()` dynamic lookup | Phase 01 (TMPL-06) | User-defined templates become valid choices in CLI |
| Single `load_template()` with built-ins only | `load_template()` checks user dir first | Phase 01 (TMPL-02) | User templates shadow built-ins by name |
| No GUI entry point | `meet-gui = "meeting_notes.gui.app:main"` | Phase 01 (GUI-04) | Optional GUI install path |

**Deprecated/outdated after Phase 01:**
- `VALID_TEMPLATES` tuple in `services/llm.py`: replaced by `list_templates()` call
- `click.Choice(["meeting", "minutes", "1on1"])` in `summarize.py`: replaced by runtime validator

---

## Open Questions

1. **click.Choice vs. runtime callback for TMPL-06**
   - What we know: `click.Choice` is evaluated at import time; `list_templates()` has a side
     effect (creates `USER_TEMPLATES_DIR`).
   - What's unclear: Whether the side effect of `mkdir` at import time is acceptable.
   - Recommendation: Use runtime validation inside the command body (see Pitfall 5 example).
     Avoids the side effect and is simpler to test.

2. **Sidebar icon treatment**
   - What we know: CONTEXT.md specifies "icons + text" and leaves icon choice to Claude.
   - What's unclear: Whether to use Qt's built-in `QStyle.StandardPixmap` icons or text-only.
   - Recommendation: Use text-only sidebar for Phase 01 (placeholder phase). Icon assets are
     out of scope until there is a mockup with specific icon choices.

3. **test_templates_contain_grounding_rule pre-existing failure**
   - What we know: `tests/test_llm_service.py::test_templates_contain_grounding_rule` fails
     against the current `meeting.txt` template (grounding string not present).
   - What's unclear: Whether this was a deliberate template change or a stale test.
   - Recommendation: Do not fix this pre-existing failure in Phase 01 — it is outside scope.
     Note it in the plan so the implementer is aware.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.14 | Project runtime | ✓ | 3.14.3 (venv) | — |
| pip | Package install | ✓ | 26.0 | — |
| PySide6 | GUI-01..GUI-05 | ✗ (not yet installed) | 6.11.0 available | — (must install) |
| shiboken6 | PySide6 dep | ✗ (auto with PySide6) | 6.11.0 | — |
| pathlib | TMPL-01..06 | ✓ | stdlib | — |
| pytest | Test suite | ✓ | installed in venv | — |

**Missing dependencies with no fallback:**
- `PySide6` — must be installed before any GUI code can run. Wave 0 task: add to
  `pyproject.toml` and run `pip install -e ".[gui]"`.

**Missing dependencies with fallback:**
- None.

**Pre-existing test failures (not introduced by Phase 01):**
- `tests/test_llm_service.py::test_templates_contain_grounding_rule` — template text mismatch
- `tests/test_storage.py::test_get_data_dir_default` — macOS XDG path mismatch
- `tests/test_transcription.py` (3 failures) — pyannote/torchaudio version issues

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed in .venv) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| Quick run command | `.venv/bin/python -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q` |
| Full suite command | `.venv/bin/python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GUI-01 | `meet-gui` imports no ML libs at startup | unit (import check) | `.venv/bin/python -m pytest tests/test_gui_app.py -x` | ❌ Wave 0 |
| GUI-02 | Sidebar navigates to all 6 views | unit (widget state) | `.venv/bin/python -m pytest tests/test_gui_main_window.py -x` | ❌ Wave 0 |
| GUI-03 | No QSS/color strings outside theme.py | unit (grep/import check) | `.venv/bin/python -m pytest tests/test_gui_theme.py -x` | ❌ Wave 0 |
| GUI-04 | `pip install -e ".[gui]"` adds meet-gui entry point | manual smoke | manual | — |
| GUI-05 | `meet` CLI works unchanged | integration | `.venv/bin/python -m pytest tests/test_summarize_command.py tests/test_record_command.py -x` | ✅ |
| TMPL-01 | `list_templates()` returns built-ins + user templates | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_list_templates -x` | ❌ Wave 0 |
| TMPL-02 | `load_template()` user dir takes precedence | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_load_template_user_precedence -x` | ❌ Wave 0 |
| TMPL-03 | `save_template()` writes file; raises on built-in collision | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_save_template -x` | ❌ Wave 0 |
| TMPL-04 | `delete_template()` removes user template; raises on built-in | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_delete_template -x` | ❌ Wave 0 |
| TMPL-05 | `duplicate_template()` copies any template to user dir | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_duplicate_template -x` | ❌ Wave 0 |
| TMPL-06 | `meet summarize --template custom` accepted if in user templates | integration | `.venv/bin/python -m pytest tests/test_summarize_command.py::test_summarize_dynamic_template -x` | ❌ Wave 0 |

**Note on GUI unit tests:** PySide6 widgets require a `QApplication` instance. Tests must
create one in a session-scoped fixture. Pattern:
```python
# conftest.py or test file fixture
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
```
Without this, all `QWidget` instantiations in tests will raise `RuntimeError: QWidget:
Must construct a QApplication before a QWidget`.

### Sampling Rate
- **Per task commit:** `.venv/bin/python -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q`
- **Per wave merge:** `.venv/bin/python -m pytest tests/ -q`
- **Phase gate:** Full suite green (excluding pre-existing failures) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_llm_service.py` — add TMPL-01..TMPL-06 test functions (extends existing file)
- [ ] `tests/test_summarize_command.py` — add TMPL-06 dynamic validation test
- [ ] `tests/test_gui_app.py` — GUI-01 startup import check (new file)
- [ ] `tests/test_gui_main_window.py` — GUI-02 sidebar navigation (new file)
- [ ] `tests/test_gui_theme.py` — GUI-03 no-magic-strings check (new file)
- [ ] `tests/conftest.py` — add `qt_app` session-scoped fixture for PySide6 tests

---

## Sources

### Primary (HIGH confidence)
- `GUI-MILESTONE-PLAN.md` (project file, read 2026-03-30) — complete architecture, code stubs,
  file structure, entry point, template CRUD, PySide6 standards
- `01-CONTEXT.md` (project file, read 2026-03-30) — locked decisions, canonical references,
  specific dimensions and font specs
- `meeting_notes/services/llm.py` (project file, read 2026-03-30) — exact current state of
  `load_template()`, `VALID_TEMPLATES`, import structure
- `meeting_notes/cli/commands/summarize.py` (project file, read 2026-03-30) — exact current
  state of `VALID_TEMPLATES` import and `click.Choice` usage (TMPL-06 target)
- `pyproject.toml` (project file, read 2026-03-30) — current dependencies, no gui group yet

### Secondary (MEDIUM confidence)
- `pip index versions pyside6` (verified 2026-03-30) — confirmed 6.11.0 is latest available
- `.venv/bin/pip install --dry-run "pyside6>=6.7"` (verified 2026-03-30) — confirmed
  abi3 wheel installs on Python 3.14, resolves to 6.11.0

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PySide6 version confirmed via pip dry-run on project venv
- Architecture: HIGH — GUI-MILESTONE-PLAN.md is the authoritative spec; fully read
- Template CRUD patterns: HIGH — exact code stubs in GUI-MILESTONE-PLAN.md, current code read
- TMPL-06 change: HIGH — current summarize.py read; exact imports and Change Points identified
- Pitfalls: HIGH — derived from direct code inspection plus PySide6 known patterns
- Test infrastructure: HIGH — existing test suite inspected, pytest confirmed installed

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (PySide6 minor releases; core architecture stable)
