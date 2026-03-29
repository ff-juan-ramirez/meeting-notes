---
status: resolved
trigger: "meet doctor does not show PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck"
created: 2026-03-27T00:00:00Z
updated: 2026-03-27T00:00:00Z
---

## Current Focus

hypothesis: The 3 new check classes exist in checks.py but are never imported or registered in doctor.py
test: Read both files and compare the import list in doctor.py against classes defined in checks.py
expecting: Import list in doctor.py omits PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck
next_action: DONE — root cause confirmed

## Symptoms

expected: Run `meet doctor` shows PyannoteCheck (ERROR if pyannote.audio not importable), HuggingFaceTokenCheck (WARNING if no token), PyannoteModelCheck (WARNING if model cache absent)
actual: Only existing pre-Phase-01 checks appear — the 3 new checks are absent from output
errors: None — checks silently absent, no crash
reproduction: Run `meet doctor`
started: Discovered during Phase 01 UAT

## Eliminated

(none — root cause found on first read)

## Evidence

- timestamp: 2026-03-27T00:00:00Z
  checked: meeting_notes/services/checks.py — full file read
  found: PyannoteCheck (line 430), HuggingFaceTokenCheck (line 454), PyannoteModelCheck (line 487) are all fully implemented and correct
  implication: The check classes exist and are ready to use

- timestamp: 2026-03-27T00:00:00Z
  checked: meeting_notes/cli/commands/doctor.py — import block (lines 10-22) and suite.register calls (lines 37-47)
  found: Import block lists 11 check classes — BlackHoleCheck, DiskSpaceCheck, FFmpegDeviceCheck, MlxWhisperCheck, NotionDatabaseCheck, NotionTokenCheck, OllamaModelCheck, OllamaRunningCheck, OpenaiWhisperConflictCheck, PythonVersionCheck, WhisperModelCheck. PyannoteCheck, HuggingFaceTokenCheck, and PyannoteModelCheck are completely absent from both the import list and the suite.register() calls.
  implication: The 3 new checks are never imported, never registered, and therefore never run or displayed

## Resolution

root_cause: doctor.py was not updated when the 3 new check classes were added to checks.py in Plan 01-02. The import block (lines 10-22) and the suite.register() block (lines 37-47) both omit PyannoteCheck, HuggingFaceTokenCheck, and PyannoteModelCheck. The classes are fully implemented in checks.py but are dead code from doctor's perspective — nothing wires them in.

fix: |
  1. Add PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck to the import from checks.py in doctor.py
  2. Add suite.register() calls for each:
     - suite.register(PyannoteCheck())
     - suite.register(HuggingFaceTokenCheck(config.huggingface_token))  [or equivalent config field]
     - suite.register(PyannoteModelCheck())
  Note: HuggingFaceTokenCheck requires a token argument — need to verify the config field name for the HF token.

verification: empty until verified
files_changed: [meeting_notes/cli/commands/doctor.py]
