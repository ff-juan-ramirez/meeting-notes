---
status: resolved
trigger: "Diarization failed: No module named 'pyannote' — pyannote.audio not installed despite being added to pyproject.toml"
created: 2026-03-27T00:00:00Z
updated: 2026-03-27T03:30:00Z
---

## Current Focus

hypothesis: CONFIRMED AND FIXED — pyannote 4.0.4 pipeline() returns DiarizeOutput dataclass. run_diarization() now unwraps it, returning exclusive_speaker_diarization (an Annotation with .itertracks()). 22 tests pass.
test: pytest tests/test_transcription.py — 22 passed, 0 failed
expecting: live diarization produces SPEAKER_XX labels
next_action: await human verification of live diarization output

## Symptoms

expected: With a valid HF token configured, meet transcribe runs pyannote diarization and produces SPEAKER_XX labels in .txt and .srt
actual: Diarization failed: No module named 'pyannote' — import fails at runtime
errors: ModuleNotFoundError: No module named 'pyannote'
reproduction: Run meet transcribe with HF token configured
started: Discovered during UAT of Phase 01

## Eliminated

- hypothesis: pyannote.audio is missing from pyproject.toml (never added)
  evidence: pyproject.toml in /Users/C9W7QTPQGK-juan.ramirez/Projects/meeting-notes-v0 contains pyannote.audio==3.3.2 — it IS declared
  timestamp: 2026-03-27T00:00:00Z

- hypothesis: pyannote.audio is not installable on macOS/Apple Silicon (platform incompatibility)
  evidence: pip install --dry-run pyannote.audio==3.3.2 succeeds; resolves all deps including torchaudio-2.11.0-cp314-cp314-macosx_12_0_arm64.whl — platform wheels exist and are compatible
  timestamp: 2026-03-27T00:00:00Z

- hypothesis: pyannote.audio 4.0.4 does not properly replace torchaudio.list_audio_backends
  evidence: pyannote 4.0.4 io.py has no call to list_audio_backends; the call comes from speechbrain (a pyannote dependency), not pyannote itself
  timestamp: 2026-03-27T02:00:00Z

- hypothesis: stale pyc files from pyannote 3.x contain old API calls
  evidence: grep of all .py files in site-packages/pyannote found zero calls to list_audio_backends; the caller is speechbrain/utils/torch_audio_backend.py
  timestamp: 2026-03-27T02:00:00Z

## Evidence

- timestamp: 2026-03-27T00:00:00Z
  checked: pip show meeting-notes (editable location field)
  found: Editable project location = /Users/C9W7QTPQGK-juan.ramirez/Projects/meeting-notes-v0/.claude/worktrees/agent-a169d200
  implication: The installed package is NOT from the main repo — it was installed from a now-stale git worktree

- timestamp: 2026-03-27T00:00:00Z
  checked: pyproject.toml in agent-a169d200 worktree
  found: dependencies = ["click>=8.1", "rich>=13.0"] — only two deps, no pyannote.audio, no mlx-whisper, no notion-client, no torchaudio
  implication: pip installed meeting-notes from a worktree that predates all Phase 01 dependency additions

- timestamp: 2026-03-27T00:00:00Z
  checked: pyproject.toml in main repo (/Users/C9W7QTPQGK-juan.ramirez/Projects/meeting-notes-v0)
  found: dependencies include pyannote.audio==3.3.2, mlx-whisper, notion-client>=2.0, requests>=2.28, torchaudio
  implication: The declaration is correct in the canonical repo — the dep was added but pip was never re-run from the correct path

- timestamp: 2026-03-27T00:00:00Z
  checked: pip show meeting-notes Requires field
  found: Requires: click, rich (only two packages — matches stale worktree, not main pyproject.toml)
  implication: Confirms pip's installed metadata comes from agent-a169d200, not the current dev tree

- timestamp: 2026-03-27T00:00:00Z
  checked: python3 -m pip show torchaudio
  found: WARNING: Package(s) not found: torchaudio
  implication: torchaudio is also missing — consistent with stale install; not just pyannote

- timestamp: 2026-03-27T00:00:00Z
  checked: pip install --dry-run "pyannote.audio==3.3.2" --break-system-packages
  found: All wheels resolve including macosx_12_0_arm64 — no platform errors
  implication: pyannote.audio 3.3.2 is fully compatible with this machine (Apple Silicon, Python 3.14)

- timestamp: 2026-03-27T01:00:00Z
  checked: python3 -c "import pyannote.audio" after installing pyannote.audio 3.3.2
  found: AttributeError: module 'torchaudio' has no attribute 'list_audio_backends' in pyannote/audio/core/io.py:212
  implication: pyannote.audio 3.3.2 is incompatible with torchaudio>=2.9.0 (API removed); Python 3.14 has no torchaudio wheels older than 2.9.0

- timestamp: 2026-03-27T01:00:00Z
  checked: pip install "torchaudio<2.9.0" — available versions query
  found: Only versions 2.9.0, 2.9.1, 2.10.0, 2.11.0 available for Python 3.14 arm64
  implication: Cannot downgrade torchaudio; must upgrade pyannote.audio to 4.0+ which replaced torchaudio.list_audio_backends with torchcodec

- timestamp: 2026-03-27T01:00:00Z
  checked: Pipeline.from_pretrained signature in pyannote.audio 4.0.4
  found: Parameter is named 'token' not 'use_auth_token' — old kwarg would be silently ignored
  implication: transcription.py run_diarization() must use token=hf_token

- timestamp: 2026-03-27T01:00:00Z
  checked: pytest tests/test_transcription.py after all fixes applied
  found: 19 passed in 0.57s
  implication: No regressions introduced by the version upgrade and parameter rename

- timestamp: 2026-03-27T00:00:00Z
  checked: git worktree list
  found: Four worktrees — main repo, agent-a43b7778, agent-a59ff8d5, agent-abc3a83a. The installed editable path (agent-a169d200) is NOT in this list
  implication: agent-a169d200 is a deleted/pruned worktree; its directory still exists on disk but is no longer tracked by git

- timestamp: 2026-03-27T02:00:00Z
  checked: speechbrain/utils/torch_audio_backend.py source and full import traceback
  found: speechbrain 1.0.3 calls torchaudio.list_audio_backends() at dataio.py module-load time (line 36). torchaudio 2.11.0 removed this API. speechbrain's version check uses ">= 2 AND minor >= 1" (i.e. 2.1+) but this evaluates True for 2.11 too. The AttributeError propagates through: speechbrain.__init__ -> speechbrain.core -> dataio.dataloader -> dataio.dataset -> dataio.dataio -> check_torchaudio_backend() -> crash. pyannote's speaker_diarization.py imports this at pipeline load time.
  implication: Pipeline.from_pretrained fails when trying to load SpeakerDiarization class, which imports speaker_verification.py, which imports speechbrain, which crashes.

- timestamp: 2026-03-27T02:00:00Z
  checked: pyannote/audio/core/io.py — does passing pre-loaded waveform tensor bypass torchcodec?
  found: YES — when file is a dict with "waveform" + "sample_rate" keys, io.py skips AudioDecoder entirely (lines 313-317), using the tensor directly.
  implication: If we pre-load audio with torchaudio.load() and pass tensor dict to pipeline, torchcodec is never called. But speechbrain still crashes at import time, so this alone doesn't solve the problem.

- timestamp: 2026-03-27T02:00:00Z
  checked: what does speechbrain do when list_audio_backends returns []?
  found: logs a warning "SpeechBrain could not find any working torchaudio backend" and continues — no error raised.
  implication: Monkey-patching torchaudio.list_audio_backends = lambda: [] before importing speechbrain/pyannote will prevent the crash with only a harmless warning.

- timestamp: 2026-03-27T02:30:00Z
  checked: torchcodec import and libtorchcodec shared library loading
  found: torchcodec package is installed but ALL .dylib variants fail to load. FFmpeg 8 variant: Symbol not found _torch_dtype_float4_e2m1fn_x2 in libtorch_cpu.dylib (PyTorch 2.10.0 does not export this symbol). FFmpeg 7/6/5/4 variants: libavutil.59/58/57/56.dylib not found (only FFmpeg 7.x installed at /opt/homebrew/opt/ffmpeg/ but dylib path doesn't match). torchcodec.decoders.AudioDecoder is therefore never defined.
  implication: Any code path that calls AudioDecoder() will raise NameError, not ImportError. The try/except in pyannote/audio/core/io.py lines 42-52 only suppresses the import warning — it does not provide a fallback definition for AudioDecoder.

- timestamp: 2026-03-27T02:30:00Z
  checked: torchaudio.load() in torchaudio 2.11.0 (torchaudio/__init__.py)
  found: torchaudio.load() calls load_with_torchcodec() exclusively. The backend parameter is "ignored and accepted only for backwards compatibility." There is no soundfile or sox fallback. torchaudio.load() also fails when torchcodec is broken.
  implication: Cannot use torchaudio.load() to pre-load audio. Must use soundfile directly.

- timestamp: 2026-03-27T02:30:00Z
  checked: soundfile.read() on a valid WAV file
  found: soundfile 0.13.1 is installed and works. soundfile.read(path, dtype='float32', always_2d=True) returns (time, channel) ndarray. Transposing to (channel, time) and wrapping in torch.from_numpy() gives the exact shape pyannote expects: torch.Size([1, N]) for mono audio.
  implication: soundfile is the correct alternative backend — no torchcodec dependency.

- timestamp: 2026-03-27T02:30:00Z
  checked: pyannote Audio.__call__ waveform dict fast-path (io.py lines 313-317)
  found: When file dict contains "waveform" key, Audio.__call__ returns self.downmix_and_resample(waveform, sample_rate) without ever calling AudioDecoder. Audio.crop() has same fast-path (lines 362-392). downmix_and_resample() uses torchaudio.functional.resample() which does NOT require torchcodec.
  implication: Passing {"waveform": tensor, "sample_rate": int} to pipeline() completely bypasses the broken torchcodec/AudioDecoder path.

- timestamp: 2026-03-27T03:00:00Z
  checked: pyannote/audio/pipelines/speaker_diarization.py — DiarizeOutput class definition
  found: DiarizeOutput is a @dataclass with two Annotation fields: `speaker_diarization` (all turns including overlapping) and `exclusive_speaker_diarization` (non-overlapping turns, designed for transcription). The class has no `.itertracks()` method itself — callers must access one of the two Annotation fields. exclusive_speaker_diarization is documented as "adapted to downstream transcription."
  implication: run_diarization() must detect DiarizeOutput (via hasattr) and return exclusive_speaker_diarization. This unwrapping must happen inside run_diarization() so both call sites (assign_speakers_to_segments in transcription.py and speaker_turns loop in transcribe.py) receive a plain Annotation without code changes.

- timestamp: 2026-03-27T03:00:00Z
  checked: pytest tests/test_transcription.py after adding DiarizeOutput unwrap and updating mocks
  found: 22 passed, 0 failed (up from 21 before this fix). New test test_run_diarization_unwraps_diarize_output exercises the pyannote 4.x code path.
  implication: Fix is correct and non-regressive.

## Resolution

root_cause: Five compounding issues: (1) The `meet` CLI was installed from a deleted git worktree missing all Phase 01 deps. (2) pyannote.audio 3.3.2 called torchaudio.list_audio_backends() which was removed in torchaudio 2.9.0+. (3) After upgrading to pyannote.audio 4.0.4, its dependency speechbrain 1.0.3 ALSO calls torchaudio.list_audio_backends() at module load time — monkey-patching lambda:[] fixed this. (4) torchcodec (pyannote 4.x audio backend) is installed but its .dylib cannot load because it requires symbol _torch_dtype_float4_e2m1fn_x2 absent from PyTorch 2.10.0. Pre-loading audio with soundfile and passing a waveform dict bypasses AudioDecoder entirely. (5) pyannote 4.x pipeline() returns a DiarizeOutput dataclass (not a plain Annotation). Code calling .itertracks() directly on DiarizeOutput failed with AttributeError. run_diarization() must unwrap it, returning exclusive_speaker_diarization (Annotation with non-overlapping turns, optimal for transcript segment mapping).
fix: (1) Ran `pip install -e . --break-system-packages` from main repo to fix editable install pointer. (2) Upgraded pyannote.audio constraint from ==3.3.2 to >=4.0. (3) Updated run_diarization() to use token= instead of use_auth_token=. (4) Added torchaudio.list_audio_backends shim. (5) Pre-load WAV with soundfile.read() and pass {"waveform": tensor, "sample_rate": int} to pipeline. (6) Unwrap DiarizeOutput in run_diarization(): if result has `exclusive_speaker_diarization`, return that field (plain Annotation); otherwise return result directly (pyannote 3.x compat). (7) Updated tests: fixed two existing tests to use spec=['itertracks'] mock (simulating plain Annotation); added test_run_diarization_unwraps_diarize_output covering pyannote 4.x DiarizeOutput path.
verification: 22 tests pass (up from 21). Human confirmed live diarization produces SPEAKER_XX labels end-to-end.
files_changed: [pyproject.toml, meeting_notes/services/transcription.py, tests/test_transcription.py]
