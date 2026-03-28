# Discussion Log — Phase 1: SRT Output and Speaker Diarization

**Date:** 2026-03-27
**Mode:** Interactive (discuss)

---

## Areas Selected

All four gray areas selected for discussion.

---

## A — SRT Output Behavior

**Q: How should the SRT file be generated during `meet transcribe`?**
Options: Always alongside .txt / Opt-in via --srt flag / Always, but --no-srt to skip
→ **Always alongside .txt** (recommended)

**Q: Where should the .srt file be saved?**
Options: Same dir as .txt / Separate srt/ directory / Same dir as WAV recording
→ **Same dir as .txt** (`transcripts/{stem}.srt`)

**Q: Should the SRT use segment-level or word-level timestamps?**
Options: Segment-level / Word-level
→ **Segment-level** (recommended — already in `result["segments"]`, no extra config)

**Q: Should `meet list` show whether a session has an SRT file?**
Options: Yes — add SRT column/icon / No — SRT is an implementation detail
→ **No — SRT is an implementation detail**

---

## B — Diarization Library Choice

**Q: Which approach for speaker diarization?**
Options: pyannote-audio / Defer to later phase / Simple energy-based heuristic
→ **pyannote-audio** (recommended)

**Q: Where should the user provide the HuggingFace token?**
Options: Add to `meet init` wizard / Environment variable only / Prompt on first run
→ **Add to `meet init` wizard** (recommended)

**Q: Should diarization run automatically or as a separate command?**
Options: Automatic in `meet transcribe` / Separate `meet diarize` command / Flag on `meet transcribe`
→ **Automatic in `meet transcribe`** (recommended)

**Q: If HF token is missing or diarization fails, what should `meet transcribe` do?**
Options: Warn and continue / Fail with error / Silently skip
→ **Warn and continue without diarization** (recommended)

**Q: Which pyannote-audio pipeline/model to use?**
Options: pyannote/speaker-diarization-3.1 / pyannote/speaker-diarization@2.1 / Claude's discretion
→ **pyannote/speaker-diarization-3.1** (recommended)

---

## C — Diarized Output Format

**Q: How should speaker labels appear in the plain-text transcript (.txt)?**
Options: Speaker prefix per paragraph / Inline per segment / No change to .txt
→ **Speaker prefix per paragraph** (recommended)

**Q: How should speaker labels appear in the SRT file?**
Options: Speaker tag at start of each entry / Separate speaker track / No speaker labels in SRT
→ **Speaker tag at start of each entry** (recommended)

**Q: Should `meet summarize` automatically use the diarized transcript when available?**
Options: Yes — use diarized .txt if it exists / No — always use plain .txt
→ **Yes — use diarized .txt if it exists** (recommended)

**Q: Should speaker labels use generic names or allow user renaming?**
Options: Generic labels for now / Rename via `meet diarize --rename` / Claude's discretion
→ **Generic labels for now** (recommended)

---

## D — Health Checks

**Q: Which checks should be added to `meet doctor`?**
Options: PyannoteCheck (import) / HuggingFaceTokenCheck / PyannoteModelCheck / No new checks
→ **All three**: PyannoteCheck + HuggingFaceTokenCheck + PyannoteModelCheck

---

*For human reference only — not consumed by downstream agents.*
