---
phase: 3
slug: note-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` testpaths=["tests"] |
| **Quick run command** | `python3 -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q` |
| **Full suite command** | `python3 -m pytest -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q`
- **After every plan wave:** Run `python3 -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | LLM-01 | unit | `pytest tests/test_llm_service.py::test_generate_notes_calls_api -x` | ❌ Wave 0 | ⬜ pending |
| 3-01-02 | 01 | 0 | LLM-01 | unit | `pytest tests/test_llm_service.py::test_generate_notes_returns_response -x` | ❌ Wave 0 | ⬜ pending |
| 3-01-03 | 01 | 0 | LLM-03 | unit | `pytest tests/test_llm_service.py::test_templates_contain_grounding_rule -x` | ❌ Wave 0 | ⬜ pending |
| 3-01-04 | 01 | 0 | LLM-05 | unit | `pytest tests/test_llm_service.py::test_generate_notes_timeout -x` | ❌ Wave 0 | ⬜ pending |
| 3-01-05 | 01 | 0 | LLM-06 | unit | `pytest tests/test_llm_service.py::test_estimate_tokens -x` | ❌ Wave 0 | ⬜ pending |
| 3-01-06 | 01 | 0 | LLM-06 | unit | `pytest tests/test_llm_service.py::test_chunk_transcript -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-01 | 02 | 1 | LLM-02 | unit | `pytest tests/test_summarize_command.py::test_template_flag_meeting -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-02 | 02 | 1 | LLM-02 | unit | `pytest tests/test_summarize_command.py::test_template_flag_1on1 -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-03 | 02 | 1 | LLM-04 | unit | `pytest tests/test_summarize_command.py::test_notes_saved_correct_path -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-04 | 02 | 1 | LLM-05 | unit | `pytest tests/test_summarize_command.py::test_timeout_error_message -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-05 | 02 | 1 | LLM-06 | unit | `pytest tests/test_summarize_command.py::test_long_transcript_uses_chunking -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-06 | 02 | 1 | LLM-07 | unit | `pytest tests/test_summarize_command.py::test_spinner_shown -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-07 | 02 | 1 | D-05 | unit | `pytest tests/test_summarize_command.py::test_output_shows_path_and_word_count -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-08 | 02 | 1 | D-06 | unit | `pytest tests/test_summarize_command.py::test_session_stem_displayed -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-09 | 02 | 1 | D-07 | unit | `pytest tests/test_summarize_command.py::test_existing_notes_overwritten -x` | ❌ Wave 0 | ⬜ pending |
| 3-02-10 | 02 | 1 | D-08 | unit | `pytest tests/test_summarize_command.py::test_metadata_extended -x` | ❌ Wave 0 | ⬜ pending |
| 3-03-01 | 03 | 1 | D-09 | unit | `pytest tests/test_health_check.py::test_ollama_running_check_error -x` | ❌ Wave 0 | ⬜ pending |
| 3-03-02 | 03 | 1 | D-10 | unit | `pytest tests/test_health_check.py::test_ollama_model_check_error -x` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_llm_service.py` — stubs for LLM-01, LLM-03, LLM-05, LLM-06 (token estimation, chunking)
- [ ] `tests/test_summarize_command.py` — stubs for LLM-02, LLM-04, LLM-06 (integration), LLM-07, D-05 to D-08
- [ ] `tests/test_health_check.py` additional cases — OllamaRunningCheck and OllamaModelCheck (D-09, D-10)
- [ ] `requests>=2.28` added to `pyproject.toml` project dependencies

*Wave 0 creates all test stubs before implementation begins so feedback sampling works from task 1.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 1on1 template does not leak category definitions into output | D-03 | Model behavior depends on runtime LLM response | Run `meet summarize --template 1on1 --session <stem>`; verify output contains no lines like "Project Work: status, blockers..." |
| Map-reduce combine produces coherent notes (no duplicates) | LLM-06 | Requires long real transcript >8000 tokens | Provide a >32,000 char transcript; verify final notes have no duplicate action items |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
