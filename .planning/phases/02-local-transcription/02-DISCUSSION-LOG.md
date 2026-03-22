# Phase 2: Local Transcription - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 02-local-transcription
**Areas discussed:** Session resolution, Transcript format, Model not cached behavior, Session metadata

---

## Session Resolution

| Option | Description | Selected |
|--------|-------------|----------|
| Latest WAV in recordings/ | Scan recordings/ and pick the most recently modified .wav file. Simple, no extra state needed. | ✓ |
| last_session.json pointer | meet stop writes a last_session.json. meet transcribe reads it. Survives reboots but adds state management. | |
| Require --session always | No default resolution — --session UUID is mandatory. | |

**User's choice:** Latest WAV in recordings/
**Notes:** Simple, no extra state needed.

| Option | Description | Selected |
|--------|-------------|----------|
| Full stem match | Exact match on WAV filename minus .wav extension. Deterministic. | ✓ |
| Prefix/substring match | Match any WAV whose name starts with or contains the given string. | |

**User's choice:** Full stem match
**Notes:** Deterministic, no ambiguity.

| Option | Description | Selected |
|--------|-------------|----------|
| Overwrite silently | Re-transcribe and overwrite existing transcript. | ✓ |
| Error and exit | Refuse to overwrite — user must delete manually. | |
| Add --force flag | Default to error, but allow overwrite with --force. | |

**User's choice:** Overwrite silently

| Option | Description | Selected |
|--------|-------------|----------|
| WAV filename stem | Show full stem (e.g. 20260322-143000-abc12345) so user can pass to --session. | ✓ |
| Short 8-char hex only | Show just the random hex suffix. | |
| Both | Show full path + session stem. | |

**User's choice:** WAV filename stem

---

## Transcript Format

| Option | Description | Selected |
|--------|-------------|----------|
| Plain text only | Just the concatenated transcript text. Simple, directly usable by Phase 3. | ✓ |
| Plain text + segments file | Save .txt + .json with timestamped segments. | |
| Timestamped text inline | Embed timestamps inline in .txt file. | |

**User's choice:** Plain text only

| Option | Description | Selected |
|--------|-------------|----------|
| WAV stem naming | transcripts/{stem}.txt matching the recordings/ naming. | ✓ |
| Different naming | Use a different convention. | |

**User's choice:** Yes, WAV stem — consistent with recordings/ naming.

---

## Model Not Cached Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-download with spinner | mlx-whisper downloads automatically. Show 'Downloading model...' Rich spinner. | ✓ |
| Fail with instructions | Detect missing model, print download instructions, exit. | |
| Warn then auto-download | Print warning, then proceed with download. | |

**User's choice:** Auto-download with spinner
**Notes:** Most ergonomic — user isn't surprised by wait.

| Option | Description | Selected |
|--------|-------------|----------|
| WARNING | Model missing is non-fatal — transcription auto-downloads. | ✓ |
| ERROR | Treat missing model as blocking error. | |

**User's choice:** WARNING — consistent with DiskSpaceCheck behavior.

| Option | Description | Selected |
|--------|-------------|----------|
| OK + model path | Show full cache path when model is present. | ✓ |
| OK only | Minimal output. | |
| OK + size | Show approximate model size. | |

**User's choice:** OK + model path

---

## Session Metadata

| Option | Description | Selected |
|--------|-------------|----------|
| Write partial metadata now | Phase 2 writes metadata/{stem}.json; later phases append. | ✓ |
| Defer all metadata to Phase 5 | No metadata writes in Phase 2. | |

**User's choice:** Write partial metadata now
**Notes:** Enables incremental `meet list` even before Phase 5.

Fields selected for Phase 2 metadata:
- wav_path + transcript_path ✓
- transcribed_at timestamp ✓
- word_count + duration_hint ✓
- whisper_model name ✓

---

## Claude's Discretion

- Duration hint derivation: compute from WAV file size (bytes / sample_rate / 2 for 16kHz mono PCM) rather than spawning ffprobe — avoids a new dependency.

## Deferred Ideas

None.
