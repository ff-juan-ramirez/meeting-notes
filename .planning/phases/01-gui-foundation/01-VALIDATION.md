---
phase: 01
slug: gui-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (installed in .venv) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q` |
| **Full suite command** | `.venv/bin/python -m pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q`
- **After every plan wave:** Run `.venv/bin/python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green (excluding pre-existing failures)
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-W0-01 | Wave 0 | 0 | GUI-01 | unit (import check) | `.venv/bin/python -m pytest tests/test_gui_app.py -x` | ❌ W0 | ⬜ pending |
| 01-W0-02 | Wave 0 | 0 | GUI-02 | unit (widget state) | `.venv/bin/python -m pytest tests/test_gui_main_window.py -x` | ❌ W0 | ⬜ pending |
| 01-W0-03 | Wave 0 | 0 | GUI-03 | unit (grep/import check) | `.venv/bin/python -m pytest tests/test_gui_theme.py -x` | ❌ W0 | ⬜ pending |
| 01-W0-04 | Wave 0 | 0 | TMPL-01..06 | unit | `.venv/bin/python -m pytest tests/test_llm_service.py -x` | ❌ W0 | ⬜ pending |
| 01-W0-05 | Wave 0 | 0 | TMPL-06 | integration | `.venv/bin/python -m pytest tests/test_summarize_command.py -x` | ❌ W0 | ⬜ pending |
| 01-GUI-01 | GUI | 1 | GUI-01 | unit | `.venv/bin/python -m pytest tests/test_gui_app.py -x` | ❌ W0 | ⬜ pending |
| 01-GUI-02 | GUI | 1 | GUI-02 | unit | `.venv/bin/python -m pytest tests/test_gui_main_window.py -x` | ❌ W0 | ⬜ pending |
| 01-GUI-03 | GUI | 1 | GUI-03 | unit | `.venv/bin/python -m pytest tests/test_gui_theme.py -x` | ❌ W0 | ⬜ pending |
| 01-GUI-04 | GUI | 2 | GUI-04 | manual smoke | manual | — | ⬜ pending |
| 01-GUI-05 | GUI | 2 | GUI-05 | integration | `.venv/bin/python -m pytest tests/test_summarize_command.py tests/test_record_command.py -x` | ✅ | ⬜ pending |
| 01-TMPL-01 | TMPL | 1 | TMPL-01 | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_list_templates -x` | ❌ W0 | ⬜ pending |
| 01-TMPL-02 | TMPL | 1 | TMPL-02 | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_load_template_user_precedence -x` | ❌ W0 | ⬜ pending |
| 01-TMPL-03 | TMPL | 1 | TMPL-03 | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_save_template -x` | ❌ W0 | ⬜ pending |
| 01-TMPL-04 | TMPL | 1 | TMPL-04 | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_delete_template -x` | ❌ W0 | ⬜ pending |
| 01-TMPL-05 | TMPL | 1 | TMPL-05 | unit | `.venv/bin/python -m pytest tests/test_llm_service.py::test_duplicate_template -x` | ❌ W0 | ⬜ pending |
| 01-TMPL-06 | TMPL | 1 | TMPL-06 | integration | `.venv/bin/python -m pytest tests/test_summarize_command.py::test_summarize_dynamic_template -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_gui_app.py` — GUI-01 startup import check (new file)
- [ ] `tests/test_gui_main_window.py` — GUI-02 sidebar navigation (new file)
- [ ] `tests/test_gui_theme.py` — GUI-03 no-magic-strings check (new file)
- [ ] `tests/test_llm_service.py` — add TMPL-01..TMPL-06 test functions (extends existing file)
- [ ] `tests/test_summarize_command.py` — add TMPL-06 dynamic validation test
- [ ] `tests/conftest.py` — add `qt_app` session-scoped fixture for PySide6 tests

**Note:** PySide6 widgets require a `QApplication` instance. All GUI tests must use the `qt_app` session fixture:
```python
@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
```

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `pip install -e ".[gui]"` adds `meet-gui` entry point | GUI-04 | Requires live pip install + shell PATH check | Run `pip install -e ".[gui]"` in a clean venv; verify `which meet-gui` resolves |

---

## Pre-Existing Test Failures (Out of Scope)

The following tests fail BEFORE Phase 01 and must NOT be counted against phase gate:
- `test_templates_contain_grounding_rule`
- `test_get_data_dir_default`
- 3 transcription tests (require network/model)

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
