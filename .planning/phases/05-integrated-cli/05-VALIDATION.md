---
phase: 5
slug: integrated-cli
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` (pytest section) |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | CLI-01..09 | unit | `python -m pytest tests/test_record_command.py -x -q` | ✅ | ⬜ pending |
| 5-01-02 | 01 | 1 | CLI-05, CLI-06 | unit | `python -m pytest tests/ -k "list" -x -q` | ❌ W0 | ⬜ pending |
| 5-01-03 | 01 | 1 | CLI-08, CLI-09 | unit | `python -m pytest tests/ -k "tty or quiet" -x -q` | ❌ W0 | ⬜ pending |
| 5-02-01 | 02 | 2 | CLI-07, CLI-08 | unit | `python -m pytest tests/ -k "ui or console" -x -q` | ❌ W0 | ⬜ pending |
| 5-02-02 | 02 | 2 | SETUP-05, SETUP-06 | unit | `python -m pytest tests/test_doctor_command.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cli_list.py` — stubs for CLI-05, CLI-06, CLI-08, CLI-09 (meet list command)
- [ ] `tests/test_cli_ui.py` — stubs for CLI-07, CLI-08 (shared console / TTY detection)

*Existing `tests/test_record_command.py` and `tests/test_doctor_command.py` cover remaining requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Spinner suppressed in `--quiet` mode | CLI-09 | Requires running CLI interactively and observing Rich output absence | Run `meet transcribe --quiet` and verify no spinner output appears |
| TTY detection suppresses Rich in piped output | CLI-08 | Requires piping stdout to file | Run `meet list \| cat` and verify no ANSI codes in output |
| End-to-end flow: record→stop→transcribe→summarize→list | CLI-01..05 | Integration test spanning processes and filesystem | Run full flow and verify `meet list` shows session with `summarized` status |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
