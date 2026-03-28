# Phase 1: SRT Output and Speaker Diarization - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend `meet transcribe` to produce SRT files (with timestamps from Whisper segments) and add speaker diarization via pyannote-audio. Every transcription run produces both a `.txt` and `.srt`. Diarization identifies speakers and prefixes their labels in both output files. The `meet summarize` command uses diarized text when available.

Renaming speakers, `meet diarize` as a standalone command, and cloud-based alternatives are out of scope for this phase.

</domain>

<decisions>
## Implementation Decisions

### SRT Output
- **D-01:** Always generated alongside `.txt` — no flag required. Every `meet transcribe` run produces `transcripts/{stem}.srt`.
- **D-02:** Saved in `transcripts/` directory alongside `{stem}.txt` — same location, same stem.
- **D-03:** Segment-level timestamps only (`result["segments"]` from mlx_whisper). `word_timestamps=True` is not used.
- **D-04:** SRT file is not shown in `meet list` — it's an implementation detail, not a user-facing status.

### Speaker Diarization
- **D-05:** Library: `pyannote-audio` with `pyannote/speaker-diarization-3.1` pipeline.
- **D-06:** HuggingFace token collected in `meet init` wizard (new step), stored in `config.json` alongside Notion token.
- **D-07:** Diarization runs automatically as part of `meet transcribe` — no separate command or flag.
- **D-08:** If HF token is missing or diarization fails for any reason: warn (yellow) and continue without diarization. `.txt` and `.srt` are produced without speaker labels. Transcription is never blocked by diarization failure.

### Diarized Output Format
- **D-09:** Plain-text transcript (`.txt`) uses speaker prefix per paragraph — consecutive segments from the same speaker are grouped:
  ```
  SPEAKER_00:
  Hello, welcome to the call. Let me share the agenda.

  SPEAKER_01:
  Thanks for setting this up. I had a few questions...
  ```
- **D-10:** SRT entries prefixed with speaker tag: `SPEAKER_00: Hello, welcome to the call.`
- **D-11:** `meet summarize` automatically prefers the diarized `.txt` when available. Falls back to plain `.txt` if diarization was skipped.
- **D-12:** Speaker labels use pyannote defaults — `SPEAKER_00`, `SPEAKER_01`, etc. No renaming feature in this phase.

### Health Checks (meet doctor)
- **D-13:** `PyannoteCheck` — verifies `pyannote.audio` is importable. ERROR severity (diarization won't work at all without it).
- **D-14:** `HuggingFaceTokenCheck` — verifies HF token is present in config and can reach HuggingFace. WARNING severity (diarization degrades gracefully).
- **D-15:** `PyannoteModelCheck` — verifies `pyannote/speaker-diarization-3.1` model is cached locally. WARNING severity (auto-downloads on first use).

### Claude's Discretion
- Exact algorithm for merging pyannote speaker turns with Whisper segments (assign each segment to the speaker whose turn has the most overlap with the segment's time range).
- SRT index numbering and timestamp formatting (standard `HH:MM:SS,mmm` format).
- How to store diarization metadata (speaker turn data) in the session metadata JSON.
- pyannote model download UX (spinner message, same pattern as WhisperModelCheck).

</decisions>

<specifics>
## Specific Ideas

- No specific references or "I want it like X" moments — decisions were made from options presented.
- The graceful fallback pattern (warn + continue) mirrors the existing Notion behavior: optional capability, non-fatal when unavailable.

</specifics>

<canonical_refs>
## Canonical References

No external specs or ADRs — requirements are fully captured in decisions above.

### Key source files for downstream agents to read before planning:
- `meeting_notes/services/transcription.py` — Current mlx_whisper wrapper; `result["segments"]` is already returned by `mlx_whisper.transcribe()` but discarded; this is where SRT generation and diarization integration will go.
- `meeting_notes/cli/commands/transcribe.py` — Current `meet transcribe` command; where new output paths and diarization call will be wired.
- `meeting_notes/services/checks.py` — Where new health check classes are registered.
- `meeting_notes/cli/commands/init.py` — Where HF token collection step will be added to the `meet init` wizard.
- `meeting_notes/core/config.py` — Where HF token config field needs to be added.
- `meeting_notes/cli/commands/summarize.py` — Where diarized `.txt` preference logic will be added.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_with_spinner()` in `transcription.py` — Use for diarization progress display (same pattern as transcription).
- `write_state()` in `core/state.py` — Use for atomic metadata JSON updates (diarization turn data).
- `HealthCheck` ABC in `core/health_check.py` — Subclass for `PyannoteCheck`, `HuggingFaceTokenCheck`, `PyannoteModelCheck`.
- `Config` dataclass in `core/config.py` — Extend with `hf_token: str | None` field.

### Established Patterns
- mlx_whisper already returns `segments` list — each segment has `start` (float, seconds), `end` (float, seconds), `text` (str). SRT generation is pure formatting of this existing data.
- Health check severity: ERROR when the feature cannot work at all; WARNING when it degrades gracefully. Mirrors `OllamaRunningCheck` (ERROR) vs `WhisperModelCheck` (WARNING).
- Graceful degradation on optional features: `meet summarize` already works without Notion token. Same pattern applies to diarization.
- `result["text"]` is currently the only output from transcription; `result["segments"]` is available in the same dict and is unused.

### Integration Points
- `transcribe_audio()` in `transcription.py` must be modified (or a new function added) to return segments alongside text.
- Metadata JSON (`metadata/{stem}.json`) should be extended to record whether diarization succeeded and the speaker turn data.
- `meet summarize` session resolution logic reads `metadata/{stem}.json` — add `diarized_transcript_path` field there for clean lookup.
- `meet init` wizard flow is sequential Click prompts — add HF token step after existing Notion token step.

</code_context>

<deferred>
## Deferred Ideas

- Speaker renaming (`meet diarize --rename SPEAKER_00=Alice`) — future phase.
- `meet list` SRT/diarization status column — explicitly decided against; future phase if desired.
- Word-level SRT timestamps (`word_timestamps=True`) — future enhancement if needed.
- WhisperX as an alternative to pyannote-audio — not needed given pyannote choice.

</deferred>

---

*Phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline*
*Context gathered: 2026-03-27*
