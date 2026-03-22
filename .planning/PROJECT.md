# meeting-notes

## What This Is

A 100% local CLI tool that captures audio from any video call (Zoom, Google Meet, Teams) without bots or browser extensions, transcribes it locally with Whisper, generates structured meeting notes using a local LLM, and saves them to Notion. No cloud, no third-party services, no data leaves the machine.

## Core Value

A developer can run `meet record`, stop it, and get structured notes in Notion — all without touching the internet or installing meeting bots.

## Requirements

### Validated

- [x] Audio is captured from system output and microphone simultaneously via ffmpeg + BlackHole 2ch, mixed with amix, saved as WAV — Validated in Phase 01: audio-capture-health-check-design
- [x] CLI exposes `meet record`, `meet stop`, `meet doctor`, `meet init` commands — Validated in Phase 01: audio-capture-health-check-design
- [x] `meet doctor` validates BlackHole device, ffmpeg device indices, disk space — Validated in Phase 01: audio-capture-health-check-design
- [x] `meet init` wizard guides first-time setup (device indices, config) — Validated in Phase 01: audio-capture-health-check-design

### Validated

- [x] Transcription runs locally using mlx-whisper with mlx-community/whisper-large-v3-turbo — Validated in Phase 02: local-transcription
- [x] CLI exposes `meet transcribe` command with session resolution, metadata, and spinner — Validated in Phase 02: local-transcription
- [x] `meet doctor` extended with mlx-whisper import check and model cache check — Validated in Phase 02: local-transcription

### Active

- [ ] Notes are generated locally using Ollama llama3.1:8b with three templates: meeting, minutes, 1on1
- [ ] Notes are saved to Notion via notion-client Python SDK
- [ ] CLI exposes commands: `meet summarize`, `meet list`
- [ ] `meet doctor` extended: Ollama running + llama3.1:8b pulled, Notion token set
- [ ] Project is exportable as a git repo for others to clone and use

### Out of Scope

- Cloud transcription (OpenAI Whisper API, AssemblyAI, etc.) — privacy requirement, 100% local
- Browser extensions or meeting bots — no injection into call software
- Windows or Linux support — macOS + Apple Silicon only (BlackHole, MLX, avfoundation)
- Real-time transcription during recording — transcription runs post-recording
- Speaker diarization — not required for v1
- GUI — CLI-only

## Context

- macOS + Apple Silicon (M-series) only
- BlackHole 2ch virtual audio driver routes system audio; must be set as Multi-Output Device alongside speakers in Audio MIDI Setup
- ffmpeg captures two avfoundation devices by index (not name — names are unreliable): index 1 = BlackHole 2ch (system audio), index 2 = MacBook Pro Microphone (user voice)
- mlx-whisper runs natively on Apple Silicon via MLX framework; insanely-fast-whisper breaks on Python 3.14 + Apple Silicon due to CUDA dependency
- Ollama serves llama3.1:8b locally; llama3.2 is too small for quality meeting summarization
- LLM prompt must prevent hallucination: "Base your notes ONLY on what is said in the transcript. Only include decisions and next steps if EXPLICITLY mentioned."
- Whisper auto-detects language — no need to specify it

## Constraints

- **Tech Stack**: Python + Click + Rich for CLI — already decided
- **Audio**: ffmpeg with avfoundation, amix filter, two devices by index — not Aggregate Device (unreliable)
- **Audio Format**: WAV only (-ar 16000 -ac 1 -c:a pcm_s16le) — mlx-whisper cannot process .m4a
- **Transcription**: mlx-whisper + mlx-community/whisper-large-v3-turbo — not insanely-fast-whisper
- **LLM**: Ollama llama3.1:8b — not llama3.2 (too small)
- **Notion SDK**: notion-client Python SDK
- **Platform**: macOS + Apple Silicon only

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ffmpeg device index over device name | Device names are unreliable across macOS versions and audio setups | — Pending |
| WAV over m4a for recording | mlx-whisper cannot process .m4a files | — Pending |
| amix filter over Aggregate Device | Aggregate Device is unreliable; amix mixes two separate avfoundation captures cleanly | — Pending |
| mlx-whisper over insanely-fast-whisper | insanely-fast-whisper breaks on Python 3.14 + Apple Silicon (CUDA dependency) | — Pending |
| llama3.1:8b over llama3.2 | llama3.2 is too small for quality meeting summarization | — Pending |
| meet doctor designed in Phase 1 | All later phases depend on prerequisites it validates; architecture decisions affect every phase | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-22 — Phase 02 complete (local transcription via mlx-whisper, `meet transcribe` command, doctor health checks)*
