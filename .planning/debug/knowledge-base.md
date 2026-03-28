# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## pyannote-not-installed — pyannote ModuleNotFoundError and 4.x API incompatibilities in diarization
- **Date:** 2026-03-27
- **Error patterns:** ModuleNotFoundError, pyannote, No module named pyannote, torchaudio, list_audio_backends, DiarizeOutput, AttributeError, itertracks, torchcodec, speechbrain, AudioDecoder, diarization, SPEAKER
- **Root cause:** Five compounding issues: (1) Editable install pointed at a deleted git worktree with only two deps (click, rich), missing all Phase 01 additions. (2) pyannote.audio 3.3.2 calls torchaudio.list_audio_backends() which was removed in torchaudio 2.9.0+. (3) After upgrading to pyannote.audio 4.0.4, its dependency speechbrain 1.0.3 also calls torchaudio.list_audio_backends() at module load time. (4) torchcodec .dylib fails to load because it requires a symbol absent from PyTorch 2.10.0; torchaudio.load() also fails since it exclusively uses torchcodec in 2.11.0. (5) pyannote 4.x pipeline() returns a DiarizeOutput dataclass (not a plain Annotation); calling .itertracks() directly on it raises AttributeError.
- **Fix:** (1) pip install -e . from main repo to fix stale editable pointer. (2) Upgrade pyannote.audio constraint to >=4.0 in pyproject.toml. (3) Use token= kwarg in Pipeline.from_pretrained (renamed from use_auth_token=). (4) Add torchaudio.list_audio_backends = lambda: [] shim before importing pyannote. (5) Pre-load WAV audio with soundfile.read(), convert to torch tensor, pass {"waveform": tensor, "sample_rate": int} dict to pipeline() — bypasses broken torchcodec/AudioDecoder entirely. (6) Unwrap DiarizeOutput in run_diarization(): detect via hasattr and return exclusive_speaker_diarization (plain Annotation optimised for transcription). (7) Update tests to match pyannote 4.x API (22 passing).
- **Files changed:** pyproject.toml, meeting_notes/services/transcription.py, tests/test_transcription.py
---
