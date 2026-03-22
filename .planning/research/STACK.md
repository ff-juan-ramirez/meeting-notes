# Stack Research: meeting-notes

**Domain:** Local meeting audio capture + transcription + LLM note generation CLI on macOS/Apple Silicon
**Date:** 2026-03-22

---

## Recommended Stack

### Audio Capture

| Component | Choice | Version | Confidence |
|-----------|--------|---------|------------|
| Audio driver | BlackHole 2ch | latest (brew) | ✓ High |
| Capture tool | ffmpeg (avfoundation) | 6.x+ | ✓ High |
| Device selection | Index numbers only (`:1`, `:2`) | — | ✓ Validated |
| Mix strategy | `amix=inputs=2:normalize=0` | — | ✓ Validated |
| Output format | WAV, 16kHz, mono, pcm_s16le | — | ✓ Required |

**Why NOT Aggregate Device:** macOS Aggregate Devices add latency and are unreliable for capture; the two-input amix approach is deterministic.

### Transcription

| Component | Choice | Version | Confidence |
|-----------|--------|---------|------------|
| Framework | mlx-whisper | ≥0.4.0 | ✓ High |
| Model | mlx-community/whisper-large-v3-turbo | latest | ✓ High |
| Python | 3.11 or 3.12 | — | ✓ High |

**Why NOT insanely-fast-whisper:** Has CUDA dependency that breaks on Python 3.14 + Apple Silicon. MLX is native to Apple Silicon Neural Engine.
**Why NOT whisper-small/base:** Quality insufficient for meeting notes. turbo variant balances speed and accuracy well.
**Python version:** Avoid 3.14 (too new, breakage risk with ML deps). 3.11/3.12 are safest for the full dependency tree.

### LLM

| Component | Choice | Notes |
|-----------|--------|-------|
| Server | Ollama | Must be running before CLI use |
| Model | llama3.1:8b | Minimum quality for meeting summarization |
| Integration | HTTP API (`localhost:11434/api/generate`) | More stable than SDK |

**Why HTTP API over Ollama Python SDK:** Ollama doesn't have a first-party Python SDK. Third-party SDKs lag Ollama server updates. Direct HTTP is stable and dependency-free.
**Why NOT llama3.2:** Too small (1b/3b variants) — produces shallow summaries. llama3.1:8b is the minimum viable model.

### Notion Integration

| Component | Choice | Version |
|-----------|--------|---------|
| SDK | notion-client | ≥2.2.x |

**Rate limit:** 3 request units/second. Add `time.sleep(0.34)` between bulk API calls.
**Page creation pattern:** `notion.pages.create(parent={"database_id": ...}, properties={...}, children=[...])` — or plain page with `parent={"page_id": ...}`.

### CLI Framework

| Component | Choice | Version | Notes |
|-----------|--------|---------|-------|
| CLI | Click | ≥8.1 | Handles Ctrl+C via context managers |
| Terminal UI | Rich | ≥13.x | Progress, panels, live display |
| Config | python-dotenv or ~/.config/meeting-notes/config.json | — | XDG Base Dir preferred |

**Signal handling pattern for ffmpeg subprocess:**
```python
import signal, subprocess

proc = subprocess.Popen(["ffmpeg", ...])
def handle_sigint(sig, frame):
    proc.send_signal(signal.SIGINT)  # graceful ffmpeg stop
    proc.wait()
signal.signal(signal.SIGINT, handle_sigint)
```

### Python Packaging

| Choice | Rationale |
|--------|-----------|
| `pyproject.toml` (PEP 621) | 2025 standard; works with pip, uv, poetry |
| Entry point: `[project.scripts]` | `meet = "meeting_notes.cli:main"` |
| Dependency manager | `uv` (fast) or `pip` in venv |

### What NOT to Use

| Tool | Reason |
|------|--------|
| insanely-fast-whisper | CUDA dependency, breaks on Apple Silicon + Python 3.14 |
| llama3.2 | Too small for meeting summarization quality |
| m4a audio format | mlx-whisper cannot process it |
| ffmpeg device names | Unreliable across macOS versions |
| Aggregate Device | Unreliable for capture; amix is better |
| OpenAI Whisper API | Violates 100% local requirement |
| Any cloud LLM | Violates 100% local requirement |

---

## Installation Notes

1. `brew install blackhole-2ch ffmpeg` — ffmpeg must be built with avfoundation
2. `pip install mlx-whisper` — downloads model on first `mlx_whisper.transcribe()` call (~1.5GB for large-v3-turbo)
3. `ollama pull llama3.1:8b` — must be done before first use (~4.7GB)
4. `pip install notion-client click rich python-dotenv` — no conflicts with mlx-whisper

---
*Researched: 2026-03-22*
