---
status: diagnosed
phase: 01-srt-output-and-speaker-diarization-for-transcription-pipeline
source: [01-00-SUMMARY.md, 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md]
started: 2026-03-27T00:00:00Z
updated: 2026-03-27T00:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: complete
name: testing complete
awaiting: n/a

## Tests

### 1. SRT file created alongside .txt
expected: Run `meet transcribe` on an audio file. In the `transcripts/` directory, a `.srt` file appears with the same stem as the `.txt` file. The SRT file uses standard subtitle format: 1-based index, HH:MM:SS,mmm --> HH:MM:SS,mmm timestamps, and the transcript text.
result: pass

### 2. Metadata includes SRT and diarization fields
expected: After `meet transcribe` completes, the session metadata JSON includes these fields: `srt_path` (path to the .srt file), `diarization_succeeded` (true or false), `diarized_transcript_path` (path or null), and `speaker_turns` (list, may be empty).
result: pass

### 3. Init wizard collects HuggingFace token
expected: Run `meet init` (fresh setup). After the Notion credentials step, the wizard prompts for a HuggingFace token. Pressing Enter (blank) skips it — the wizard continues and completes without error. Entering a token saves it to config.
result: pass

### 4. Init update shows HuggingFace token field
expected: Run `meet init --update`. The update menu lists field `[7] HuggingFace token` alongside the existing fields. Selecting 7 prompts for a new HF token value.
result: issue
reported: "there is no meet init --update option"
severity: major

### 5. meet doctor shows HuggingFace and Pyannote health checks
expected: Run `meet doctor`. The output includes the 3 new checks added in Plan 01-02: `PyannoteCheck` (ERROR if pyannote.audio not installed), `HuggingFaceTokenCheck` (WARNING if no token configured), and `PyannoteModelCheck` (WARNING if model cache absent). These checks should appear alongside the existing checks.
result: issue
reported: "i don't see the check for hugging faces and the new stuff added to meet doctor"
severity: major

### 6. Diarization skips with warning when no HF token configured
expected: Run `meet transcribe` without a HuggingFace token in config. The command prints a yellow warning message (something like "HuggingFace token not configured") and completes with a plain `.txt` transcript (no speaker labels). The `.srt` is still written with plain text.
result: skipped
reason: User tested with HF token configured; Test 2 implicitly confirmed no-token path (diarization_succeeded=false in metadata)

### 7. Diarization graceful failure — yellow warning, plain output continues
expected: If diarization fails mid-run (e.g., network error, bad token), the command prints a yellow warning and continues — producing a plain `.txt` and `.srt` without speaker labels. The command does NOT crash.
result: pass

### 8. Diarized .txt has SPEAKER_XX labels when diarization succeeds
expected: With a valid HF token configured, run `meet transcribe` on an audio file. The resulting `.txt` contains speaker-labeled paragraphs in the format `SPEAKER_00:\n<text>` (or `SPEAKER_01:`, etc.), grouping consecutive same-speaker segments together. The `.srt` also includes speaker labels.
result: issue
reported: "Diarization failed: No module named 'pyannote' — pyannote.audio not installed despite being added to pyproject.toml"
severity: major

### 9. meet summarize prefers diarized transcript from metadata
expected: After a successful diarized transcription (HF token set, diarization succeeded), run `meet summarize` on the session. The summary uses the diarized transcript content (with SPEAKER_XX labels) rather than the plain transcript — producing a summary that reflects who said what.
result: blocked
blocked_by: prior-phase
reason: Cannot test until pyannote.audio is installed and diarization succeeds

## Summary

total: 9
passed: 4
issues: 3
pending: 0
skipped: 1
blocked: 1

## Gaps

- truth: "meet doctor shows PyannoteCheck, HuggingFaceTokenCheck, and PyannoteModelCheck in health check output"
  status: failed
  reason: "User reported: i don't see the check for hugging faces and the new stuff added to meet doctor"
  severity: major
  test: 5
  root_cause: "doctor.py was never updated to import or register the 3 new check classes. PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck are fully implemented in checks.py (lines 430, 454, 487) but doctor.py import block and suite.register() calls omit all 3."
  artifacts:
    - path: "meeting_notes/cli/commands/doctor.py"
      issue: "Missing 3 imports and 3 suite.register() calls"
    - path: "meeting_notes/services/checks.py"
      issue: "Correct — no changes needed"
  missing:
    - "Add PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck to imports in doctor.py"
    - "Add suite.register(PyannoteCheck()), suite.register(HuggingFaceTokenCheck(config.huggingface.token)), suite.register(PyannoteModelCheck()) after existing registrations"
  debug_session: ".planning/debug/meet-doctor-missing-pyannote-checks.md"

- truth: "meet init --update shows field [7] HuggingFace token in the update menu"
  status: failed
  reason: "User reported: there is no meet init --update option"
  severity: major
  test: 4
  root_cause: "The --update Click option was never added to the init command decorator. The update menu logic (_update_specific_fields with field [7] HuggingFace token) is fully implemented and reachable interactively, but there is no @click.option('--update') decorator so meet init --update is rejected by Click."
  artifacts:
    - path: "meeting_notes/cli/commands/init.py"
      issue: "Missing @click.option('--update', is_flag=True) decorator and early-exit branch in init() body"
  missing:
    - "Add @click.option('--update', is_flag=True, default=False) decorator to init command"
    - "Add guard at top of init() body: when update=True, load config and call _update_specific_fields() directly"
  debug_session: ".planning/debug/meet-init-update-flag-missing.md"

- truth: "meet transcribe runs pyannote diarization and produces SPEAKER_XX labels in .txt and .srt"
  status: failed
  reason: "User reported: Diarization failed: No module named 'pyannote' — pyannote.audio not installed despite being added to pyproject.toml"
  severity: major
  test: 8
  root_cause: "The meet CLI is installed as an editable package pointing to a deleted git worktree (.claude/worktrees/agent-a169d200) whose pyproject.toml only has click and rich. pip was never re-run from the main repo after the worktree was discarded. The main repo pyproject.toml correctly declares pyannote.audio==3.3.2 — no code changes needed, just reinstall."
  artifacts:
    - path: ".claude/worktrees/agent-a169d200/pyproject.toml"
      issue: "Stale editable install source — only click + rich, missing all Phase 01 deps"
    - path: "pyproject.toml"
      issue: "Correct — pyannote.audio==3.3.2 declared"
  missing:
    - "Run `pip install -e .` from main repo root to re-register editable install against current pyproject.toml"
  debug_session: ".planning/debug/pyannote-not-installed.md"
