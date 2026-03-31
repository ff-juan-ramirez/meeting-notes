---
phase: 01-gui-foundation
plan: 01
subsystem: template-service
tags: [templates, crud, llm-service, cli, tdd]
dependency_graph:
  requires: []
  provides: [template-crud-api, dynamic-template-validation]
  affects: [meeting_notes/services/llm.py, meeting_notes/cli/commands/summarize.py]
tech_stack:
  added: []
  patterns: [user-templates-dir, builtin-precedence, runtime-validation]
key_files:
  created: []
  modified:
    - meeting_notes/services/llm.py
    - meeting_notes/cli/commands/summarize.py
    - tests/test_llm_service.py
    - tests/test_summarize_command.py
decisions:
  - keep-valid-templates-for-compat-then-remove
  - runtime-import-list-templates-avoids-import-time-side-effects
  - user-templates-dir-created-on-list-templates-call
metrics:
  duration_seconds: 204
  completed_date: "2026-03-31"
  tasks: 2
  files_modified: 4
---

# Phase 01 Plan 01: Template CRUD Service Layer Summary

**One-liner:** Template CRUD (list/load/save/delete/duplicate) added to `llm.py` with user templates shadowing built-ins; `meet summarize --template` now validates at runtime via `list_templates()` instead of a hardcoded `click.Choice`.

## What Was Built

Template CRUD functions enabling user-created custom templates stored in `~/.config/meeting-notes/templates/`. Built-in templates (meeting, minutes, 1on1) continue to work unchanged. User templates shadow built-ins of the same name. The CLI's `--template` option now validates against all available templates at runtime instead of a compile-time `click.Choice(["meeting", "minutes", "1on1"])`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Template CRUD functions in llm.py + unit tests (TDD) | 9dc9a04 | meeting_notes/services/llm.py, tests/test_llm_service.py |
| 2 | Dynamic template validation in summarize.py | 9dcb271 | meeting_notes/cli/commands/summarize.py, tests/test_summarize_command.py |

## Key Changes

**`meeting_notes/services/llm.py`:**
- Added `BUILTIN_TEMPLATES_DIR` and `USER_TEMPLATES_DIR` constants (replaces `TEMPLATES_DIR`)
- Added `list_templates() -> list[dict]` — returns all built-in + user templates with `{name, path, builtin}` dicts
- Updated `load_template()` — checks user path before built-in path; raises `ValueError("Template not found: ...")` instead of `"Invalid template: ..."`
- Added `save_template(name, content) -> Path` — writes to user dir, guards against built-in name collisions
- Added `delete_template(name) -> None` — guards against deleting built-ins, raises `FileNotFoundError` for missing user templates
- Added `duplicate_template(source_name, new_name) -> Path` — copies any template to a new user template
- Removed `VALID_TEMPLATES` constant entirely

**`meeting_notes/cli/commands/summarize.py`:**
- Removed `VALID_TEMPLATES` import
- Removed `type=click.Choice(...)` from `--template` option
- Added runtime validation inside `summarize()` function body via `list_templates()` (imported inside function to avoid import-time side effects)

**`tests/test_llm_service.py`:**
- Added `user_templates_dir` fixture that monkeypatches `USER_TEMPLATES_DIR` to a temp dir
- Added 11 new tests covering all CRUD functions and user template precedence
- Updated `test_load_template_invalid` to match new error message (`"Template not found"`)

**`tests/test_summarize_command.py`:**
- Added `test_summarize_invalid_template` — invalid template exits 1 with "Invalid template"
- Added `test_summarize_dynamic_template` — user-created template is accepted without error

## Decisions Made

1. **Keep `VALID_TEMPLATES` for Task 1 backward compat, remove in Task 2** — Plan specified keeping it as a bridge constant so `summarize.py` import wouldn't break between tasks. Removed atomically in Task 2 along with the `summarize.py` import change.

2. **Import `list_templates` inside function body (not at module level)** — Per Pitfall 5 in RESEARCH.md: `list_templates()` triggers `get_config_dir()` + `mkdir` at call time. Importing at module level would cause side effects when the module is imported. Importing inside the function body avoids this.

3. **`USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)` inside `list_templates()`** — The user templates directory is created lazily on first `list_templates()` call. This is acceptable because `list_templates()` is always called from the CLI before any template operations.

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

```
.venv/bin/python -m pytest tests/test_llm_service.py tests/test_summarize_command.py -q -k "not test_templates_contain_grounding_rule"
50 passed, 1 deselected in 7.73s
```

The deselected test (`test_templates_contain_grounding_rule`) is a pre-existing failure — the built-in templates do not contain the literal grounding rule string. This is documented in the plan as a known pre-existing failure.

## Known Stubs

None — all template CRUD functions are fully wired. User templates stored in `~/.config/meeting-notes/templates/` are discovered by `list_templates()` and accepted by `meet summarize --template`.

## Self-Check: PASSED
