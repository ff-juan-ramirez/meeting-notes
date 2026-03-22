---
status: diagnosed
phase: 02-local-transcription
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md]
started: 2026-03-22T21:15:00Z
updated: 2026-03-22T21:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. meet transcribe resolves latest WAV automatically
expected: Run `meet transcribe` with no --session flag. It should find the most recently modified .wav file in the recordings directory and transcribe it. The session stem (filename without extension) should be printed at the end.
result: issue
reported: "ran meet transcribe, got no output at all — no spinner, no error, no completion message, transcripts folder doesn't exist"
severity: blocker

### 2. meet transcribe --session resolves exact WAV stem
expected: Run `meet transcribe --session <stem>` where stem is the filename without .wav extension. It should transcribe that specific file (not the latest). If the stem doesn't exist, it should print a red error and exit.
result: blocked
blocked_by: prior-phase
reason: "~/.local/share/meeting-notes/ doesn't exist — ensure_dirs() not called by transcribe command, so no recordings dir and no WAV files available to test with"

### 3. Transcript saved to correct path
expected: After a successful `meet transcribe`, a file appears at `~/.local/share/meeting-notes/transcripts/{stem}.txt` containing the transcribed text.
result: blocked
blocked_by: prior-phase
reason: "~/.local/share/meeting-notes/ doesn't exist — same root cause as test 1"

### 4. Metadata JSON written with correct fields
expected: After transcription, `~/.local/share/meeting-notes/metadata/{stem}.json` exists and contains: wav_path, transcript_path, transcribed_at, word_count, whisper_model.
result: blocked
blocked_by: prior-phase
reason: "~/.local/share/meeting-notes/ doesn't exist — same root cause as test 1"

### 5. Rich spinner shown during transcription
expected: While mlx-whisper is running, a spinner with elapsed time (e.g. "[3s] Transcribing...") is visible in the terminal. It updates live — not a frozen cursor.
result: blocked
blocked_by: prior-phase
reason: "~/.local/share/meeting-notes/ doesn't exist — same root cause as test 1"

### 6. Short transcript warning
expected: If the resulting transcript has fewer than 50 words, a yellow warning is printed: something like "Transcript may be empty — check audio routing (N words)".
result: blocked
blocked_by: prior-phase
reason: "~/.local/share/meeting-notes/ doesn't exist — same root cause as test 1"

### 7. meet doctor reports mlx-whisper status
expected: Running `meet doctor` shows a check named "mlx-whisper" that reports OK (mlx-whisper importable) since mlx-whisper is installed.
result: pass

### 8. meet doctor reports Whisper model cache status
expected: Running `meet doctor` shows a check named "Whisper Model Cache". If the model has already been downloaded, it shows OK with the cache path. If not yet downloaded, it shows a yellow WARNING (not a red ERROR) saying the model will download on first use.
result: pass

## Summary

total: 8
passed: 2
issues: 1
pending: 0
skipped: 0
blocked: 5

## Gaps

- truth: "meet transcribe produces visible output — either an error message or a spinner followed by completion message and session stem"
  status: failed
  reason: "User reported: ran meet transcribe, got no output at all — no spinner, no error, no completion message, transcripts folder doesn't exist"
  severity: blocker
  test: 1
  artifacts: []
  missing: []
