# Milestones

## v1.1 SRT Output and Speaker Diarization (Shipped: 2026-03-28)

**Phases completed:** 1 phase, 5 plans
**Timeline:** 2026-03-27 → 2026-03-28 (1 day)
**Files changed:** 28 files, +2,436 / -55 lines

**Key accomplishments:**

1. SRT subtitle generation: `seconds_to_srt_timestamp()` + `generate_srt()` — every `meet transcribe` writes `.srt` alongside `.txt`
2. `transcribe_audio()` refactored to return `(text, segments)` tuple — all callers updated
3. `HuggingFaceConfig` in `Config` + HF token step 3.5 in `meet init` wizard
4. Three new health checks: `PyannoteCheck` (ERROR), `HuggingFaceTokenCheck` (WARNING), `PyannoteModelCheck` (WARNING) — wired into `meet doctor`
5. Speaker diarization via pyannote.audio: `run_diarization()` + `assign_speakers_to_segments()` + `SPEAKER_XX:` labels in `.txt` and `.srt`, graceful fallback when pyannote unavailable
6. `meet summarize` prefers diarized transcript when `diarized_transcript_path` is set in metadata
7. `meet init --update` flag for non-interactive field updates; torchaudio≥2.9 compatibility via `torchaudio.list_audio_backends` monkey-patch

**Archive:**

- `.planning/milestones/v1.1-ROADMAP.md` — phase details

---

## v1.0 MVP (Shipped: 2026-03-24)

**Phases completed:** 6 phases, 16 plans
**Timeline:** 2026-03-22 → 2026-03-23 (2 days)

**Key accomplishments:**

1. ffmpeg two-device amix audio capture pipeline with SIGTERM/SIGKILL lifecycle, atomic state.json, and BlackHole device-name validation — `meet record` / `meet stop`
2. Local mlx-whisper transcription with session resolution, Rich spinner, metadata persistence, and short-transcript warning — `meet transcribe`
3. Ollama llama3.1:8b note generation with three grounding-rule templates (meeting/minutes/1on1) and map-reduce chunking for >8K-token transcripts — `meet summarize`
4. Notion auto-push with ≤1,900-char block splitting, exponential backoff on HTTP 429, and `notion_url` stored in session metadata
5. Full CLI polish: shared `cli/ui.py` console with TTY detection and `--quiet` flag, `meet list` with Rich table + `--status` filter + `--json` output
6. Exportable repo: full interactive `meet init` wizard with device detection + Notion validation + inline doctor, `meet doctor --verbose` with per-check detail lines, README with Audio MIDI Setup ASCII diagram

**Known gaps:**

- AUDIO-05 checkbox was never ticked in REQUIREMENTS.md (checkbox oversight — path is implemented in storage module)

**Archive:**

- `.planning/milestones/v1.0-ROADMAP.md` — full phase details
- `.planning/milestones/v1.0-REQUIREMENTS.md` — all 40 v1 requirements

---
