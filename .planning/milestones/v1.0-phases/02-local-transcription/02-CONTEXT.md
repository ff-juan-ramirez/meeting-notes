# Phase 2: Local Transcription - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Transcribe a WAV recording to text using mlx-whisper running on Apple Silicon. Produces a plain-text transcript file and partial session metadata. Adds mlx-whisper health checks to `meet doctor`.

New capabilities (speaker diarization, streaming, cloud transcription) belong in other phases.

</domain>

<decisions>
## Implementation Decisions

### Session Resolution

- **D-01:** `meet transcribe` with no `--session` flag resolves to the most recently modified `.wav` file in `recordings/`. Fails clearly if directory is empty.
- **D-02:** `--session` accepts the full WAV filename stem (e.g. `20260322-143000-abc12345`). Exact match only — no prefix/substring matching.
- **D-03:** If a transcript already exists for the session, overwrite silently (no prompt, no error).
- **D-04:** After successful transcription, display the WAV filename stem so the user can pass it to `--session` in later commands.

### Transcript Format

- **D-05:** Save plain text only to `transcripts/{stem}.txt` — just the concatenated transcript text from `mlx_whisper.transcribe()["text"]`. No timestamps, no segments file.
- **D-06:** Transcript filename uses the same stem as the WAV file (e.g. `20260322-143000-abc12345.txt`). Consistent naming across `recordings/` and `transcripts/`.

### Model Not Cached Behavior

- **D-07:** If `whisper-large-v3-turbo` is not cached in `~/.cache/huggingface/hub/`, `meet transcribe` auto-downloads it — mlx-whisper handles the download automatically. Show a `Downloading model...` Rich spinner so the user isn't surprised by the wait.
- **D-08:** `WhisperModelCheck` in `meet doctor` returns **WARNING** (not ERROR) when model is not cached — non-fatal since transcription will auto-download. Show: `WARNING  Whisper model not cached — will download on first use (run: meet transcribe)`.
- **D-09:** When model IS cached, `WhisperModelCheck` shows: `OK  Whisper model cached at ~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo`.

### Session Metadata

- **D-10:** Phase 2 writes a partial `metadata/{stem}.json` on successful transcription. Subsequent phases append their own fields to the same file.
- **D-11:** Fields written by Phase 2:
  - `wav_path` — absolute path to the WAV file
  - `transcript_path` — absolute path to the `.txt` file
  - `transcribed_at` — ISO 8601 timestamp of when transcription completed
  - `word_count` — word count of the transcript text (for the <50 word warning display)
  - `whisper_model` — model identifier string (e.g. `mlx-community/whisper-large-v3-turbo`)

### Locked from Roadmap (not re-discussed)

- **D-12:** mlx-whisper call: `mlx_whisper.transcribe(path, path_or_hf_repo="mlx-community/whisper-large-v3-turbo")`
- **D-13:** Warn user if transcript word count < 50 (empty/short recording check)
- **D-14:** Warn user if WAV file duration > 90 minutes (memory pressure risk on Apple Silicon)
- **D-15:** Config supports `"whisper": {"language": null}` — null = auto-detect, string = forced language
- **D-16:** Rich spinner with elapsed time during transcription (no silent wait)
- **D-17:** Two health checks: `MlxWhisperCheck` (import succeeds) and `WhisperModelCheck` (model cached). Both registered with `meet doctor`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Architecture
- `.planning/ROADMAP.md` §Phase 2 — Plan specs (2.1, 2.2) and pitfalls P6–P9
- `.planning/PROJECT.md` — Tech stack constraints and out-of-scope items

### Existing Code Patterns
- `meeting_notes/services/audio.py` — Model for `services/transcription.py` structure
- `meeting_notes/core/health_check.py` — HealthCheck ABC that new checks must subclass
- `meeting_notes/services/checks.py` — Where new Phase 2 checks get registered
- `meeting_notes/core/storage.py` — XDG dir helpers; `transcripts/` and `metadata/` already wired
- `meeting_notes/core/state.py` — Atomic JSON write pattern for metadata writes
- `meeting_notes/cli/commands/record.py` — Model for `cli/commands/transcribe.py` structure

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/storage.py`: `get_data_dir()` returns XDG data dir — use for `recordings/`, `transcripts/`, `metadata/` paths. `ensure_dirs()` already creates all three.
- `core/state.py`: `write_state(path, dict)` / `read_state(path)` — use this atomic write pattern for metadata JSON files.
- `core/health_check.py`: `HealthCheck` ABC with `check() -> CheckResult` abstractmethod — subclass for both `MlxWhisperCheck` and `WhisperModelCheck`.
- `services/checks.py`: Existing health checks registered here — add Phase 2 checks to the same module.
- Rich `Console` already instantiated in existing commands — follow same pattern in `transcribe.py`.

### Established Patterns
- Commands use `click.command()` + `Console()` at module level — follow in `transcribe.py`.
- State/config paths retrieved via `get_config_dir()` — config.json lives there; whisper language setting read from there.
- Health checks return `CheckResult` with severity (OK / WARNING / ERROR) and message string.
- DiskSpaceCheck returns WARNING (not ERROR) — consistent with D-08 for WhisperModelCheck.

### Integration Points
- `cli/main.py` — register `transcribe` command here (same pattern as `record`, `stop`, `doctor`, `init`)
- `services/checks.py` — register `MlxWhisperCheck` and `WhisperModelCheck` in the health check suite
- `recordings/` directory — scanned by `meet transcribe` to resolve latest WAV (D-01)
- `metadata/` directory — Phase 2 writes here; Phase 3 and later phases read+extend the same JSON

</code_context>

<specifics>
## Specific Ideas

- Session stem display: after successful transcription, print something like `Session: 20260322-143000-abc12345` — user can copy-paste for `--session` in `meet summarize`.
- The `duration_hint` in metadata: derive from WAV file size (bytes / sample_rate / 2 for 16kHz mono PCM) rather than spawning ffprobe, to avoid a new dependency. This gives an approximate duration for the >90 min warning and for Phase 5's `meet list` display.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-local-transcription*
*Context gathered: 2026-03-22*
