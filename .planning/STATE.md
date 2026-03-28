---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Named Recordings
status: Defining requirements
last_updated: "2026-03-27T00:00:00.000Z"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-27)

**Core value:** A developer can run `meet record`, stop it, and get structured notes in Notion — all without touching the internet or installing meeting bots.
**Current focus:** v1.2 — Named recordings

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-03-27 — Milestone v1.2 started

## Current Status

- [x] v1.0 MVP shipped 2026-03-24 (6 phases, 16 plans, 208 tests)
- [x] v1.1 SRT + Speaker Diarization shipped 2026-03-28 (1 phase, 5 plans)
- [ ] v1.2 Named Recordings — in progress

## Last Session

**Completed:** v1.2 milestone started — defining requirements
**Date:** 2026-03-27

## Decisions

- Used `setuptools.build_meta` backend (not `setuptools.backends._legacy`) — required for setuptools 82+
- ffmpeg device indices `:1` (BlackHole system audio) and `:2` (MacBook microphone) — never device names
- SIGTERM to process group first, wait 5s, then SIGKILL escalation for clean ffmpeg termination
- Atomic state.json via temp+replace (POSIX rename) for crash-safe session tracking
- HealthCheck ABC with abstractmethod — direct instantiation raises TypeError by design
- BlackHoleCheck checks device NAME at index (not just index reachability) per pitfall P1
- DiskSpaceCheck returns WARNING (not ERROR) below 5GB — non-fatal advisory
- meet init triggers 1-second avfoundation test recording to force macOS mic permission prompt (SETUP-02)
- [Phase 02]: Language auto-detect: omit language kwarg entirely when None — passing None causes mlx-whisper to default to en
- [Phase 02]: run_with_spinner uses threading.Thread for background mlx-whisper; Rich Live spinner renders in main thread
- [Phase 02]: Session stem derived from wav_path.stem not a stored UUID for correct --session round-trip
- [Phase 02]: WhisperModelCheck returns WARNING not ERROR when model not cached — model auto-downloads on first meet transcribe (D-08)
- [Phase 02]: No version pin on mlx-whisper in pyproject.toml — already installed and API is stable
- [Phase 02]: ensure_dirs() called first in transcribe() — prevents silent failure on fresh install before data dirs created
- [Phase 02]: OSError added to transcribe exception handler as defense-in-depth for Python 3.14 glob behavior
- [Phase 03]: OllamaRunningCheck and OllamaModelCheck both return ERROR severity per D-09 and D-10 — neither can auto-remediate
- [Phase 03-01]: requests>=2.28 added to pyproject.toml (not pinned — API is stable)
- [Phase 03-01]: chunk_transcript returns short text as-is (no strip); only strips after newline-split boundary
- [Phase 03]: [Phase 03-03]: Session resolution for transcripts mirrors transcribe.py pattern (latest .txt by mtime or exact stem)
- [Phase 03]: [Phase 03-03]: Map-reduce chunking triggered when estimate_tokens > 8000 (>32000 chars) per D-13
- [Phase 03]: [Phase 03-03]: Metadata uses read-merge-write pattern to preserve Phase 2 fields per D-08
- [Phase 04]: APIResponseError requires real constructor args (code, status, message, headers, raw_body_text) — MagicMock(spec=APIResponseError) cannot be raised, use real instances
- [Phase 04]: All heading levels (H1, H2, H3) convert to heading_2 blocks per RESEARCH.md guidance
- [Phase 04]: Notion push placed after local notes save — local save never fails due to Notion issues
- [Phase 04]: [Phase 04-02]: Both NotionTokenCheck and NotionDatabaseCheck return WARNING severity — Notion is optional for meet summarize to work
- [Phase 04]: [Phase 04-02]: notion_url stored in metadata JSON as full URL on success, null on skip/failure — Phase 5 meet list reads this field
- [Phase 05-01]: Shared Console in cli/ui.py uses force_terminal=sys.stdout.isatty() — single source of truth for all CLI output
- [Phase 05-01]: run_with_spinner quiet=True early-returns fn() directly — no threading overhead in quiet mode
- [Phase 05-01]: meet stop writes duration_seconds from start_time ISO string before clearing state — preserves timing across session
- [Phase 05-01]: PythonVersionCheck uses >=3.14 as WARNING not ERROR — Python 3.14 is untested but may work
- [Phase 05-01]: list_sessions import wrapped in try/except ImportError in main.py for forward-compat with Plan 02
- [Phase 05]: list_sessions registered directly in main.py (try/except ImportError guard removed — Plan 02 complete)
- [Phase 05]: [Phase 05-02]: Wide console (width=200) patched in tests to prevent Rich table truncation in CliRunner narrow terminal
- [Phase 06]: STATUS_ICONS moved to cli/ui.py for reuse by Plan 02 (meet init) without circular imports
- [Phase 06]: verbose_detail() returns None on base HealthCheck; subclasses opt in; OpenaiWhisperConflictCheck deliberately has no override (D-03)
- [Phase 06]: quiet wins over verbose (D-06): if quiet: verbose = False applied before output loop in doctor command
- [Phase 06]: fix_suggestion guard fixed to result.status != CheckStatus.OK (D-04) — never shown on OK results
- [Phase 06-03]: MIT License with year 2026 and "meeting-notes contributors" as copyright holder
- [Phase 06-03]: README uses device indices :1 (BlackHole) and :2 (MacBook Mic) throughout — never device names per AUDIO-06
- [Phase 06-03]: .gitignore adds defensive patterns for recordings/, transcripts/, notes/, .env even though XDG dirs normally outside repo
- [Phase 06]: Notion token validated via NotionClient.users.me() loop; APIResponseError re-prompts, generic Exception saves with warning
- [Phase 06]: Inline doctor in meet init uses HealthCheckSuite directly (no subprocess) per D-12
- [Phase 06]: APIResponseError test helper uses correct constructor: (code, status, message, headers, raw_body_text)
- [Phase 01-00]: Wave 0 stubs use @pytest.mark.skip(reason="Wave 0 stub — implementation pending") — consistent reason string across all 17 stubs
- [Phase 01-00]: test_checks.py is a new file for pyannote health check stubs (separate from test_health_check.py for v1.0 checks)
- [Phase 01-00]: Imports inside function bodies in test_checks.py to avoid collection failures before classes exist
- [Phase 01]: transcribe_audio() returns (text, segments) tuple — callers must unpack; breaking change to existing callers fixed in same plan
- [Phase 01]: generate_srt() accepts optional speaker_map dict keyed by 0-based segment index — ready for Plan 03 diarization
- [Phase 01]: SRT always written alongside .txt with no flag — per D-01; metadata baseline: diarization_succeeded=False, diarized_transcript_path=None, speaker_turns=[]
- [Phase 01-02]: HfApi imported at module level in checks.py and init.py so tests can patch via module path
- [Phase 01-02]: HuggingFaceTokenCheck returns WARNING (not ERROR) when token absent — diarization is optional, matches NotionTokenCheck pattern
- [Phase 01-02]: PyannoteCheck returns ERROR when pyannote.audio not importable — diarization cannot proceed without it (unlike WhisperModelCheck)
- [Phase 01-02]: _collect_hf_token() is wizard step 3.5 — after Notion, blank input skips (returns None), validated via HfApi().whoami()
- [Phase 01-02]: Field [7] added to update menu for HuggingFace token — consistent with existing 1-6 field numbering
- [Phase 01]: run_diarization() lazy-imports pyannote.audio.Pipeline — avoids import-time cost for users without pyannote
- [Phase 01]: diarized content overwrites plain .txt — diarized_transcript_path points to same file (RESEARCH.md Pitfall 5)
- [Phase 01]: assign_speakers_to_segments uses max-overlap: pyannote turn with greatest temporal overlap per Whisper segment
- [Phase 01-04]: torchaudio.list_audio_backends monkey-patch: pyannote.audio 3.x calls this at import time but removed in torchaudio>=2.9; patch adds missing function with ['soundfile'] backend
- [Phase 01-04]: pyannote.audio version pin relaxed from ==3.3.2 to >=3.3.2,<5 to avoid pip dependency conflict with torchaudio-resolved pyannote.core versions
- [Phase 01-04]: meet init --update flag uses early-exit routing to _update_specific_fields before interactive config-exists check

## Performance Metrics

| Phase | Plan | Duration (s) | Tasks | Files |
|-------|------|-------------|-------|-------|
| Phase 01 | 00 | 120 | 2 | 6 |
| 01    | 02   | 244         | 2     | 20    |
| 01    | 03   | 225         | 2     | 7     |
| Phase 02 P01 | 3 | 2 tasks | 6 files |
| Phase 02 P02 | 78 | 2 tasks | 4 files |
| Phase 02 P03 | 124 | 1 tasks | 2 files |
| Phase 03 P02 | 84 | 2 tasks | 3 files |
| Phase 03 P01 | 141 | 2 tasks | 7 files |
| Phase 03 P03 | 127 | 2 tasks | 3 files |
| Phase 04 P01 | 147 | 2 tasks | 5 files |
| Phase 04 P02 | 270 | 2 tasks | 7 files |
| Phase 05 P01 | 352 | 2 tasks | 12 files |
| Phase 05 P02 | 232 | 1 tasks | 3 files |
| Phase 06 P01 | 163 | 2 tasks | 5 files |
| Phase 06 P03 | 900 | 2 tasks | 3 files |
| Phase 06 P02 | 329 | 1 tasks | 2 files |
| Phase 01 | 01 | 900 | 2 | 4 |
| Phase 01 | 02 | 720 | 2 | 6 |
| Phase 01 P03 | 900 | 2 tasks | 6 files |
| Phase 01 P04 | 480 | 2 tasks | 5 files |

## Roadmap Evolution

- Phase 1 added: SRT output and speaker diarization for transcription pipeline

## Key Context for Future Sessions

- Tech stack is fully validated and locked — do not suggest alternatives
- ffmpeg uses device INDICES (:1, :2), never device names
- WAV only — never .m4a
- mlx-whisper, not insanely-fast-whisper
- llama3.1:8b, not llama3.2
- LLM prompt must include strict grounding rule (no fabricated decisions/next steps)
- meet doctor architecture designed in Phase 1 — each subsequent phase adds its own checks
- Architecture: XDG Base Dir, pluggable health checks, process groups for ffmpeg, atomic state writes
- Package installed via `pip install -e .` in a fresh venv (Python 3.14)
- HealthCheck ABC pattern: subclass must implement check() -> CheckResult, register in HealthCheckSuite
