---
phase: 2
slug: local-transcription
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pytest.ini` or `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

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
| 2-01-01 | 01 | 1 | TRANS-01 | unit | `python -m pytest tests/test_transcription.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | TRANS-02 | unit | `python -m pytest tests/test_transcription.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | TRANS-03 | unit | `python -m pytest tests/test_transcription.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-04 | 01 | 1 | TRANS-04 | unit | `python -m pytest tests/test_transcription.py -x -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 2 | TRANS-05 | unit | `python -m pytest tests/test_transcription.py -x -q` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 2 | TRANS-05 | unit | `python -m pytest tests/test_health_check.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_transcription.py` — stubs for TRANS-01 through TRANS-05
- [ ] `tests/test_record_command.py` — extend with session resolution tests (if not covered)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rich spinner displays elapsed time during transcription | TRANS-02 | Requires real mlx-whisper call (minutes); threading behavior | Run `meet transcribe` on a real WAV, observe spinner updates |
| Memory pressure warning for >90 min recordings | TRANS-04 | Requires a large test WAV or mock | Use a WAV sized >165 MB or mock `wave.open` to return large frame count |
| `meet doctor --download-models` downloads model | TRANS-05 | Network operation; HuggingFace download | Run on system without cached model; observe download progress |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
