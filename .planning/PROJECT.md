# meeting-notes

## What This Is

A 100% local CLI tool that captures audio from any video call (Zoom, Google Meet, Teams) without bots or browser extensions, transcribes it locally with Whisper, generates structured meeting notes using a local LLM, and saves them to Notion. No cloud, no third-party services, no data leaves the machine.

**Status:** v1.2 complete — Phase 07 complete (--title flag for meet summarize Notion page title override).

## Core Value

A developer can run `meet record`, stop it, and get structured notes in Notion — all without touching the internet or installing meeting bots.

## Requirements

### Validated (v1.0)

- ✓ Audio captured from system output and microphone simultaneously via ffmpeg + BlackHole 2ch, amix filter, WAV — v1.0
- ✓ `meet record` / `meet stop` with SIGTERM/SIGKILL lifecycle, atomic state.json, device-name validation — v1.0
- ✓ `meet doctor` validates BlackHole device (by name), ffmpeg device indices, disk space, Python version, openai-whisper conflict — v1.0
- ✓ `meet init` full interactive wizard: device detection, Notion token validation, reconfigure/update flow, test recording, inline doctor — v1.0
- ✓ Local mlx-whisper transcription with session resolution, Rich spinner, metadata persistence, short-transcript warning — v1.0
- ✓ `meet doctor` extended with MlxWhisperCheck (import) and WhisperModelCheck (cache, WARNING severity) — v1.0
- ✓ Ollama llama3.1:8b note generation with three templates (meeting/minutes/1on1), map-reduce for >8K tokens, 120s timeout, strict grounding prompt — v1.0
- ✓ `meet doctor` extended with OllamaRunningCheck and OllamaModelCheck (ERROR severity) — v1.0
- ✓ Notion auto-push: ≤1,900-char block splitting, exponential backoff on HTTP 429, notion_url in metadata — v1.0
- ✓ `meet doctor` extended with NotionTokenCheck and NotionDatabaseCheck (WARNING severity, optional) — v1.0
- ✓ Shared `cli/ui.py` console with TTY detection, `--quiet` flag, `--version`, all commands retrofitted — v1.0
- ✓ `meet list` with Rich table, `--status` filter, `--json` output, duration/title derivation — v1.0
- ✓ `meet doctor --verbose` with per-check `verbose_detail()` inline lines — v1.0
- ✓ Exportable git repo: pyproject.toml (PEP 621), README.md with Audio MIDI Setup walkthrough + ASCII diagram, MIT LICENSE, .gitignore — v1.0

### Validated (Phase 07 — 2026-03-29)

- ✓ `meet summarize --title "Custom Title"` overrides Notion page title at summarize time; priority chain: `--title` > `recording_name` > `extract_title()` fallback — Phase 07 (TITLE-01, TITLE-02, TITLE-03)
- ✓ Empty `--title ""` is treated as falsy — falls through to `recording_name` — Phase 07 (TITLE-03)
- ✓ `--title` value is runtime-only and never persisted to session metadata JSON — Phase 07 (D-05)

### Validated (Phase 06 — 2026-03-28)

- ✓ `meet list` table shows a "Session ID" column with the full file stem (untruncated) for each session — Phase 06 (SESSID-01)
- ✓ `meet list --json` output includes `session_id` field with value equal to the metadata file stem — Phase 06 (SESSID-02)
- ✓ `meet summarize --session` help text reflects v1.2 slug-prefixed stem format (e.g. `team-standup-20260322-143000-abc12345`) — Phase 06 (SESSID-03)

### Validated (Phase 05 — 2026-03-28)

- ✓ `meet summarize` uses `recording_name` as the Notion page title when available; unnamed/pre-v1.2 sessions fall back to `extract_title()` unchanged — Phase 05 (NOTION-01)

### Validated (Phase 04 — 2026-03-28)

- ✓ `meet list` displays `recording_name` as the session title when set; unnamed/pre-v1.2 sessions fall back to existing title derivation unchanged — Phase 04 (LIST-01, LIST-02)

### Validated (Phase 03 — 2026-03-28)

- ✓ `meet record [NAME]` accepts optional name argument; slug computed via `slugify()` and stored as `recording_slug` in `state.json` alongside `recording_name` — Phase 03 (RECORD-01, RECORD-02)
- ✓ Named session uses `get_recording_path_with_slug()` for WAV output path; unnamed sessions unchanged — Phase 03 (RECORD-03)
- ✓ `meet stop` propagates `recording_name` and `recording_slug` from `state.json` to session metadata JSON — Phase 03 (RECORD-04)

### Validated (Phase 02 — 2026-03-28)

- ✓ `slugify(text)` pure function in `core/storage.py`: NFKD normalization, ASCII-safe, lowercase, colon→hyphen, 80-char max, `"untitled"` fallback — Phase 02 (SLUG-01, SLUG-02)
- ✓ `get_recording_path_with_slug(name)` produces `{slug}-{timestamp}-{uuid8}.wav` path; unnamed sessions use existing `get_recording_path()` unchanged — Phase 02 (RECORD-05)
- ✓ Zero new dependencies for slugification (stdlib `unicodedata` + `re` only) — Phase 02

### Validated (Phase 01 — 2026-03-27)

- ✓ SRT subtitle output: `generate_srt()` + `seconds_to_srt_timestamp()`, every transcription writes `.srt` alongside `.txt` — Phase 01
- ✓ `transcribe_audio()` returns `(text, segments)` tuple; all callers updated — Phase 01
- ✓ Speaker diarization via pyannote.audio: `run_diarization()`, `assign_speakers_to_segments()`, `build_diarized_txt()` with graceful fallback — Phase 01
- ✓ `HuggingFaceConfig` in `Config`, HF token collected in `meet init` wizard step 3.5 — Phase 01
- ✓ Three new health checks: `PyannoteCheck` (ERROR), `HuggingFaceTokenCheck` (WARNING), `PyannoteModelCheck` (WARNING) — Phase 01
- ✓ `meet summarize` prefers diarized transcript when `diarized_transcript_path` is set in metadata — Phase 01

### Active (v2.0 candidates)

- [ ] Shell completion scripts (zsh/bash) via `meet --install-completion`
- [ ] `meet list --search KEYWORD` — searches transcript content
- [ ] Custom user-defined note templates via config file
- [ ] Participant extraction — LLM identifies speaker names, stored as Notion property
- [ ] Resume interrupted recording (append to same WAV; requires checkpoint)
- [ ] `meet doctor --fix` attempts automatic repairs (model download, schema validation)

### Out of Scope

- Cloud transcription (OpenAI Whisper API, AssemblyAI, etc.) — privacy requirement, 100% local
- Browser extensions or meeting bots — no injection into call software
- Windows or Linux support — macOS + Apple Silicon only (BlackHole, MLX, avfoundation)
- Real-time transcription during recording — transcription runs post-recording
- Speaker diarization — ~~not required for v1, high complexity~~ shipped in Phase 01
- GUI — CLI-only by design
- SQLite database for metadata — JSON files sufficient
- Sync back from Notion — high complexity, v2+ candidate
- Audio attachments in Notion — local audio stays local (privacy)

## Context

- macOS + Apple Silicon (M-series) only
- BlackHole 2ch virtual audio driver routes system audio; must be set as Multi-Output Device alongside speakers in Audio MIDI Setup
- ffmpeg captures two avfoundation devices by index (not name — names are unreliable): index 1 = BlackHole 2ch (system audio), index 2 = MacBook Pro Microphone (user voice)
- mlx-whisper runs natively on Apple Silicon via MLX framework; insanely-fast-whisper breaks on Python 3.14 + Apple Silicon due to CUDA dependency
- Ollama serves llama3.1:8b locally; llama3.2 is too small for quality meeting summarization
- LLM prompt must prevent hallucination: "Base your notes ONLY on what is said in the transcript. Only include decisions and next steps if EXPLICITLY mentioned."
- Whisper auto-detects language — omit language kwarg entirely when None (passing None defaults to English)
- Package installed via `pip install -e .` in a fresh venv (Python ≥3.11, <3.14 recommended; 3.14 untested)
- 208 tests passing at v1.0 ship

## Constraints

- **Tech Stack**: Python + Click + Rich for CLI — validated and locked
- **Audio**: ffmpeg with avfoundation, amix filter, two devices by index — not Aggregate Device (unreliable)
- **Audio Format**: WAV only (-ar 16000 -ac 1 -c:a pcm_s16le) — mlx-whisper cannot process .m4a
- **Transcription**: mlx-whisper + mlx-community/whisper-large-v3-turbo — not insanely-fast-whisper
- **LLM**: Ollama llama3.1:8b — not llama3.2 (too small)
- **Notion SDK**: notion-client Python SDK
- **Platform**: macOS + Apple Silicon only

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ffmpeg device index over device name | Device names are unreliable across macOS versions and audio setups | ✓ Good — no device-name bugs reported |
| WAV over m4a for recording | mlx-whisper cannot process .m4a files | ✓ Good — no format issues |
| amix filter over Aggregate Device | Aggregate Device is unreliable; amix mixes two separate avfoundation captures cleanly | ✓ Good — clean two-channel mix |
| mlx-whisper over insanely-fast-whisper | insanely-fast-whisper breaks on Python 3.14 + Apple Silicon (CUDA dependency) | ✓ Good — no compatibility issues |
| llama3.1:8b over llama3.2 | llama3.2 is too small for quality meeting summarization | ✓ Good — note quality validated |
| meet doctor designed in Phase 1 | All later phases depend on prerequisites it validates; architecture decisions affect every phase | ✓ Good — pluggable ABC scaled cleanly to 9 checks |
| SIGTERM → wait 5s → SIGKILL escalation | Clean WAV header write on graceful shutdown | ✓ Good — no corrupt WAV files |
| Atomic state.json via temp+replace | POSIX rename is crash-safe; prevents corrupt state | ✓ Good — no state corruption observed |
| WhisperModelCheck as WARNING (not ERROR) | Model auto-downloads on first `meet transcribe` — non-fatal | ✓ Good — smooth first-run experience |
| NotionTokenCheck/DatabaseCheck as WARNING | Notion is optional; `meet summarize` works without it (local-only mode) | ✓ Good — tool works offline |
| Shared cli/ui.py console | Single TTY detection source; `--quiet` suppresses all Rich output consistently | ✓ Good — clean piped output |
| setuptools.build_meta backend | Required for setuptools 82+ (legacy backend removed) | ✓ Good — no packaging issues |
| Language kwarg omitted (not None) for auto-detect | Passing None to mlx-whisper defaults to English, not auto-detect | ✓ Good — multilingual transcription works |
| `transcribe_audio()` returns `(text, segments)` tuple | SRT generation requires segment timestamps; callers fixed in same plan | ✓ Good — clean API boundary |
| SRT always written alongside `.txt`, no opt-out flag | Every transcription should have subtitle output; simplicity wins | ✓ Good — no flag confusion |
| `HuggingFaceTokenCheck` as WARNING (not ERROR) | Diarization is optional; matches NotionTokenCheck pattern | ✓ Good — graceful degradation |
| `PyannoteCheck` as ERROR (not WARNING) | Diarization cannot proceed without pyannote.audio importable | ✓ Good — clear failure signal |
| `run_diarization()` lazy-imports pyannote.audio.Pipeline | Avoids import-time cost for users without pyannote installed | ✓ Good — startup not affected |
| torchaudio.list_audio_backends monkey-patch | pyannote.audio 3.x calls this at import time; removed in torchaudio≥2.9 | ✓ Good — fixed silent import failure |
| pyannote.audio pin relaxed to `>=3.3.2,<5` | `==3.3.2` caused pip conflicts with torchaudio-resolved pyannote.core | ✓ Good — installs cleanly |

## Current Milestone: v1.2 Named Recordings

**Goal:** Allow `meet record` to accept an optional name that propagates to all output files, metadata, and downstream tools.

**Target features:**
- `meet record [NAME]` — optional name argument at record time
- Name stored in session metadata (state.json and session JSON)
- Output files slugified from name (e.g. "1:1 with Gabriel" → `1-1-with-gabriel-<timestamp>.wav/.txt/.srt`)
- `meet list` displays the recording name/title
- Notion page title uses the recording name

## Evolution

**Last updated:** 2026-03-27 — v1.2 milestone started (Named recordings)

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
*Last updated: 2026-03-28 — Phase 06 complete (Session ID column in meet list, session_id in --json output, summarize --session help updated)*
