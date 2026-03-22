---
phase: 1
slug: audio-capture-health-check-design
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml (Wave 0 installs) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

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
| 1-01-01 | 01 | 1 | SETUP-01 | unit | `pytest tests/test_config.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | SETUP-01 | unit | `pytest tests/test_storage.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | SETUP-01 | unit | `pytest tests/test_state.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 2 | AUDIO-01 | unit | `pytest tests/test_process_manager.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 2 | AUDIO-02 | unit | `pytest tests/test_audio.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 2 | AUDIO-03 | integration | `pytest tests/test_record_command.py -x -q` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 3 | SETUP-02 | unit | `pytest tests/test_health_check.py -x -q` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 3 | SETUP-03 | integration | `pytest tests/test_doctor_command.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (tmp_path, mock config, mock state)
- [ ] `tests/test_config.py` — stubs for config load/save (SETUP-01)
- [ ] `tests/test_storage.py` — stubs for XDG path creation (SETUP-01)
- [ ] `tests/test_state.py` — stubs for atomic state read/write (SETUP-01)
- [ ] `tests/test_process_manager.py` — stubs for subprocess lifecycle (AUDIO-01)
- [ ] `tests/test_audio.py` — stubs for ffmpeg command building (AUDIO-02)
- [ ] `tests/test_record_command.py` — stubs for record/stop CLI commands (AUDIO-03)
- [ ] `tests/test_health_check.py` — stubs for health check base classes (SETUP-02)
- [ ] `tests/test_doctor_command.py` — stubs for meet doctor output (SETUP-03)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| BlackHole device at index 1 confirmed | AUDIO-05 | Requires real hardware | Run `ffmpeg -f avfoundation -list_devices true -i ""` and verify index 1 shows BlackHole |
| `meet record` starts actual WAV recording | AUDIO-01 | Requires real audio devices | Run `meet record`, let run 5s, run `meet stop`, verify WAV file exists and has audio |
| `meet init` triggers macOS mic permission prompt | SETUP-04 | Requires macOS permission dialog | Run `meet init` on fresh system and confirm dialog appears |
| `meet doctor` exits 1 on error check | SETUP-03 | Requires real device state | Unplug/disable BlackHole, run `meet doctor`, verify exit code 1 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
