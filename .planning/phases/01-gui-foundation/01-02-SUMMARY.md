---
phase: 01-gui-foundation
plan: 02
subsystem: gui
tags: [pyside6, gui, theme, navigation, sidebar, qstackedwidget]
dependency_graph:
  requires: [meeting_notes/core/config.py, meeting_notes/core/storage.py]
  provides: [meet-gui entry point, GUI package skeleton, centralized theme, MainWindow with sidebar navigation]
  affects: [pyproject.toml, tests/conftest.py]
tech_stack:
  added: [PySide6>=6.7]
  patterns: [QSS stylesheet via APP_STYLESHEET, QListWidget sidebar + QStackedWidget navigation, factory functions make_label/make_button]
key_files:
  created:
    - meeting_notes/gui/__init__.py
    - meeting_notes/gui/theme.py
    - meeting_notes/gui/app.py
    - meeting_notes/gui/main_window.py
    - meeting_notes/gui/views/__init__.py
    - meeting_notes/gui/views/dashboard.py
    - meeting_notes/gui/views/sessions.py
    - meeting_notes/gui/views/record.py
    - meeting_notes/gui/views/templates.py
    - meeting_notes/gui/views/settings.py
    - meeting_notes/gui/views/doctor.py
    - meeting_notes/gui/widgets/__init__.py
    - meeting_notes/gui/workers/__init__.py
    - tests/test_gui_app.py
    - tests/test_gui_main_window.py
    - tests/test_gui_theme.py
  modified:
    - pyproject.toml
    - tests/conftest.py
decisions:
  - "PySide6 >= 6.7 added as optional dependency under [gui] extras — pip install -e '.[gui]' for GUI, pip install -e . for CLI-only"
  - "APP_STYLESHEET applied once via app.setStyleSheet in app.py — no per-widget QSS except factory functions"
  - "QListWidget.setFixedWidth(180) sets both minimumWidth and maximumWidth — test uses both assertions"
  - "GUI startup chain imports only PySide6, gui.*, core.config, core.storage — no ML modules (GUI-01)"
metrics:
  duration_seconds: ~420
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_created: 16
  files_modified: 2
---

# Phase 01 Plan 02: GUI Foundation Skeleton Summary

**One-liner:** PySide6 GUI package with centralized dark-sidebar QSS theme, 6-view MainWindow sidebar navigation, and `meet-gui` entry point via optional `[gui]` dep.

## What Was Built

### Task 1: Package structure, theme.py, placeholder views (commit 95a0139)

- Created `meeting_notes/gui/` package with `__init__.py` files for `gui`, `views`, `widgets`, `workers`
- Updated `pyproject.toml` to add `meet-gui = "meeting_notes.gui.app:main"` script and `gui = ["pyside6>=6.7"]` optional dep
- Implemented `gui/theme.py` as the single source of truth for all visual constants:
  - `COLORS` dict with 10 named colors (sidebar_bg, accent, text_primary, green, red, yellow, card_bg, border, input_bg, surface)
  - `FONTS` dict with 5 roles (h1, h2, body, mono, small) — all sizes in pt
  - `APP_STYLESHEET` QSS string covering QMainWindow, sidebar, buttons (primary/danger), card frame, QLineEdit, QPlainTextEdit
  - `make_label(text, role, color_key)` factory returning styled QLabel
  - `make_button(text, style)` factory returning QPushButton with QSS property set
- Created 6 placeholder views (DashboardView, SessionsView, RecordView, TemplatesView, SettingsView, DoctorView) — each centered QLabel with h1 heading, no color hex codes or font strings

### Task 2: MainWindow, app.py, GUI tests (commit daa363b)

- Implemented `gui/main_window.py`:
  - `SIDEBAR_ITEMS` list with exact 6 labels in spec order
  - `MainWindow(QMainWindow)` with `_sidebar` (QListWidget, objectName="sidebar", fixedWidth=180) and `_stack` (QStackedWidget)
  - `currentRowChanged` connected to `_on_sidebar_changed` slot
  - Default selection `setCurrentRow(0)` (Dashboard)
- Implemented `gui/app.py`:
  - `main()` sets QApplication name, AA_UseHighDpiPixmaps, APP_STYLESHEET
  - Loads Config from XDG config dir, calls ensure_dirs
  - Creates MainWindow with minimumSize(900, 600), resize(1100, 700), window.show()
  - No ML module imports anywhere in import chain
- Added `qt_app` session-scoped fixture to `tests/conftest.py`
- Created `tests/test_gui_app.py` — tests GUI-01 (no ML import at startup) + callable main()
- Created `tests/test_gui_main_window.py` — tests GUI-02 (sidebar count=6, stack count=6, default=0, navigation, labels, width)
- Created `tests/test_gui_theme.py` — tests GUI-03 (COLORS/FONTS/APP_STYLESHEET exports, no hex in views, no font strings in views, make_label/make_button factories)

## Test Results

- 15 new GUI tests: all pass
- 46 existing CLI tests (test_summarize_command.py, test_record_command.py): all pass (GUI-05)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PySide6 QListWidget has no `fixedWidth()` method**
- **Found during:** Task 2, running test_gui_main_window.py
- **Issue:** Plan specified test using `main_window._sidebar.fixedWidth()` — PySide6 QListWidget does not expose this method; `setFixedWidth(n)` sets both minimumWidth and maximumWidth
- **Fix:** Updated `test_main_window_sidebar_width` to assert `minimumWidth() == 180 and maximumWidth() == 180`
- **Files modified:** tests/test_gui_main_window.py
- **Commit:** daa363b

## Known Stubs

All 6 views are intentional placeholder stubs — each renders only a centered h1 QLabel with the screen name. This is by design for Phase 01. Subsequent phases (02-04) replace these placeholders with functional content:

| File | Stub type | Reason | Resolved in |
|------|-----------|--------|-------------|
| views/dashboard.py | Placeholder QLabel | Phase 01 skeleton only | Phase 02 |
| views/sessions.py | Placeholder QLabel | Phase 01 skeleton only | Phase 02 |
| views/record.py | Placeholder QLabel | Phase 01 skeleton only | Phase 03 |
| views/templates.py | Placeholder QLabel | Phase 01 skeleton only | Phase 04 |
| views/settings.py | Placeholder QLabel | Phase 01 skeleton only | Phase 04 |
| views/doctor.py | Placeholder QLabel | Phase 01 skeleton only | Phase 04 |

These stubs do NOT prevent the plan's goal from being achieved — the plan's objective is the navigation shell (GUI-01..05), not the functional views.

## Requirements Addressed

- GUI-01: No ML imports at startup — verified by test_gui_app_no_ml_imports
- GUI-02: 6-view sidebar navigation — verified by test_gui_main_window.py
- GUI-03: All visual constants in theme.py — verified by test_no_color_hex_in_views + test_no_font_family_in_views
- GUI-04: pip install -e ".[gui]" — optional dep wired in pyproject.toml, PySide6 installed
- GUI-05: CLI unchanged — 46 CLI tests pass after GUI changes

## Self-Check: PASSED
