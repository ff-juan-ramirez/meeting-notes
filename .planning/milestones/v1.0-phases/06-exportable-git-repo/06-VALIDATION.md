---
phase: 6
slug: exportable-git-repo
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` (pytest config inline) |
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
| 6-01-01 | 6.1 | 0 | PKG-01 | unit | `python -m pytest tests/test_doctor_command.py -x -q` | ✅ | ⬜ pending |
| 6-01-02 | 6.1 | 1 | PKG-01 | unit | `python -m pytest tests/test_doctor_command.py -x -q` | ✅ | ⬜ pending |
| 6-02-01 | 6.2 | 0 | SETUP-01 | unit | `python -m pytest tests/test_init.py -x -q` | ❌ W0 | ⬜ pending |
| 6-02-02 | 6.2 | 1 | SETUP-02 | unit | `python -m pytest tests/test_init.py -x -q` | ❌ W0 | ⬜ pending |
| 6-03-01 | 6.3 | 2 | PKG-02 | manual | inspect `pyproject.toml`, `README.md`, `.gitignore` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_init.py` — stubs for SETUP-01 to SETUP-06: first-time vs reconfigure branching, device selection, Notion token validation, config write, inline doctor call
- [ ] `tests/test_doctor_command.py` — extend existing tests: verbose flag output, all phase health checks present, exit codes

*Existing doctor test file exists — Wave 0 extends it; init test file must be created.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Audio device detection shows real device indices | SETUP-02 | Requires live soundcard/BlackHole hardware | Run `meet init`, verify device list shows ffmpeg device indices |
| Test recording triggers macOS mic permission dialog | SETUP-04 | OS permission dialog cannot be automated | Fresh install: run `meet init`, confirm dialog appears |
| `meet doctor --verbose` shows model file sizes | PKG-01 | Requires mlx model cache downloaded | Run `meet doctor --verbose`, confirm sizes shown |
| Clone → `pip install .` → `meet init` → `meet record` succeeds | PKG-03 | Full E2E first-time setup | Follow README quick-start on clean environment |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
