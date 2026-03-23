---
phase: 4
slug: notion-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | NOTION-01 | unit | `pytest tests/test_notion.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | NOTION-04 | unit | `pytest tests/test_notion.py::test_text_splitting -x -q` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 1 | NOTION-05 | unit | `pytest tests/test_notion.py::test_retry_backoff -x -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 2 | NOTION-02 | integration | `pytest tests/test_summarize.py -x -q` | ✅ | ⬜ pending |
| 4-02-02 | 02 | 2 | NOTION-03 | unit | `pytest tests/test_summarize.py::test_notion_url_stored -x -q` | ✅ | ⬜ pending |
| 4-02-03 | 02 | 2 | NOTION-06 | unit | `pytest tests/test_health_check.py -x -q` | ✅ | ⬜ pending |
| 4-02-04 | 02 | 2 | NOTION-07 | unit | `pytest tests/test_health_check.py::test_notion_checks -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_notion.py` — stubs for NOTION-01, NOTION-04, NOTION-05 (new file, no notion service yet)
- [ ] `tests/conftest.py` — add `mock_notion_client` fixture (notion-client mock)

*Existing `tests/test_health_check.py` and `tests/test_summarize.py` cover Wave 2 tasks but need new test cases added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notion page appears in workspace | NOTION-02 | Requires live Notion API token and parent page | Run `meet summarize <audio>` with `NOTION_TOKEN` set; verify page created under parent |
| Spinner displays during API call | NOTION-03 | Terminal UI rendering not captured by pytest | Run `meet summarize <audio>` and observe "Saving to Notion..." spinner |
| Warning panel on failure | NOTION-06 | Requires controlled network failure or invalid token | Set invalid token in config.json; run `meet summarize`; verify yellow warning panel with local path |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
