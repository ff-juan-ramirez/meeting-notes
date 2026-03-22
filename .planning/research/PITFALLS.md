# Pitfalls Research: meeting-notes

**Domain:** Local meeting transcription CLI — macOS/Apple Silicon
**Date:** 2026-03-22
**Note:** Does NOT repeat pitfalls already documented in PROJECT.md (device names unreliable, .m4a format, insanely-fast-whisper, llama3.2 too small, LLM hallucination prompt). These are additional, non-obvious pitfalls.

---

## Phase 1 — Audio Capture

### ffmpeg + avfoundation

**P1: Device index order is volatile**
- Warning signs: Recording produces silence after plugging/unplugging USB audio devices, or after macOS update
- Cause: avfoundation re-enumerates devices; index 1 may no longer be BlackHole after USB audio or AirPods connect
- Prevention: `meet doctor` must verify the device at index 1 IS BlackHole by parsing `ffmpeg -f avfoundation -list_devices` output — not just that the index exists
- Phase: Phase 1 (doctor validation) + Phase 6 (doctor full implementation)

**P2: amix requires matching sample rates — no auto-resampling**
- Warning signs: Distorted or stuttering output WAV that still passes length checks
- Cause: If BlackHole and microphone run at different native sample rates (e.g., 48kHz vs 44.1kHz), amix produces artifacts without an explicit `aformat` filter before mixing
- Prevention: Add `-af aformat=sample_rates=16000` or explicit resampling before amix: `[0:a]aresample=16000[a0];[1:a]aresample=16000[a1];[a0][a1]amix=...`
- Phase: Phase 1

**P3: WAV header not written on crash or disk-full**
- Warning signs: mlx-whisper fails with "invalid audio format" or "no such codec"; file size looks plausible
- Cause: ffmpeg writes the WAV RIFF header (size fields) at the END of recording, not the beginning. If the process dies mid-recording, the header is malformed or zeroed
- Prevention: Use `meet stop` which sends SIGTERM (graceful finish) rather than SIGKILL. Document clearly. `meet doctor` should check available disk space (>5GB warning)
- Phase: Phase 1 (signal handling) + Phase 6 (disk space check)

**P4: Microphone permission prompt interrupts first recording**
- Warning signs: `meet record` starts but hangs; macOS shows system dialog "Allow access to microphone?"
- Cause: First time any process accesses the mic, macOS requires explicit user approval
- Prevention: `meet init` or `meet doctor` should trigger a short (~1s) test recording to force the permission prompt before the real meeting. Document this in setup wizard
- Phase: Phase 1

**P5: Audio routing changes when headphones are plugged in mid-session**
- Warning signs: System audio track goes silent mid-recording; BlackHole still listed in devices but output is now going to headphones instead
- Cause: macOS switches system output device automatically when headphones connect; BlackHole is no longer in the Multi-Output Device chain for the new output
- Prevention: Document this limitation. Consider adding a warning in `meet record` output: "Ensure BlackHole Multi-Output Device is set as system output before recording."
- Phase: Phase 1 (documentation + doctor)

---

## Phase 2 — Transcription

### mlx-whisper

**P6: Model download happens silently on first `meet transcribe` — no progress**
- Warning signs: `meet transcribe` appears frozen for 5-10 minutes on first run
- Cause: mlx-community/whisper-large-v3-turbo is ~3GB; HuggingFace download starts without any indication
- Prevention: `meet doctor` must check if model is cached locally (`~/.cache/huggingface/hub/`). If not, warn user and offer to pre-download: `python -c "import mlx_whisper; mlx_whisper.transcribe('dummy.wav')"` or trigger download explicitly
- Phase: Phase 2 + Phase 6 (doctor check)

**P7: Memory pressure on long recordings (>90 min)**
- Warning signs: Transcription starts, then slows dramatically; Activity Monitor shows swap usage
- Cause: mlx-whisper loads the full WAV (800MB-1.2GB for 2-hour meeting) + model weights simultaneously. On 8GB M-series Macs, this causes swap thrashing
- Prevention: Warn user if recording is >90 minutes. Consider chunking: split WAV into 30-min segments, transcribe individually, concatenate. Document memory requirements (16GB recommended for meetings >1hr)
- Phase: Phase 2

**P8: Silent audio segments produce gaps — no error raised**
- Warning signs: Transcript missing sections; notes say "the meeting discussed X" with no substance
- Cause: Whisper returns empty string for silence >2s. If audio routing failed (see P5), entire sections are empty. No exception is raised.
- Prevention: After transcription, check if transcript is empty or <50 words — warn user. In `meet transcribe`, show character count of output
- Phase: Phase 2

**P9: Language misdetection on short clips or heavy accents**
- Warning signs: Transcript contains garbled text mixing two languages; notes are nonsensical
- Cause: Whisper auto-detects language but can misclassify with accented English or code-switching. No confidence score is exposed
- Prevention: Allow users to pin language in config: `"whisper": {"language": null}` (null = auto, "en" = forced). Document in `meet init`
- Phase: Phase 2

---

## Phase 3 — Note Generation

### Ollama

**P10: Ollama isn't running — cryptic connection error**
- Warning signs: `meet summarize` fails with `ConnectionRefusedError` or `requests.exceptions.ConnectionError`
- Cause: Ollama daemon isn't started; user must manually run `ollama serve` or configure it to auto-start
- Prevention: `meet doctor` must check `http://localhost:11434`. If down, show: "Ollama is not running. Start it with: `ollama serve`". Consider auto-starting Ollama via `subprocess.Popen(["ollama", "serve"])` if not running
- Phase: Phase 3 + Phase 6 (doctor check)

**P11: llama3.1:8b context window is ~128K tokens but generation degrades on very long transcripts**
- Warning signs: Notes from long meetings are repetitive, cut off, or miss the beginning
- Cause: While llama3.1:8b has a large context window, practical generation quality degrades on inputs >8K-12K tokens. A 2-hour meeting transcript is ~15K-20K tokens
- Prevention: Measure transcript token count before sending. If >8K tokens, split transcript into chunks, summarize each chunk, then summarize summaries ("map-reduce" approach). Add `--chunk` flag
- Phase: Phase 3

**P12: Ollama hangs indefinitely on very large prompts**
- Warning signs: `meet summarize` runs for >10 minutes with no output; process doesn't error out
- Cause: Ollama has no default timeout; very large prompts can cause the model to load-swap indefinitely
- Prevention: Set `timeout=120` on all HTTP requests to Ollama. If timeout is hit, show actionable error: "LLM timed out. Try `--chunk` flag or reduce transcript length."
- Phase: Phase 3

**P13: Model version changes silently on `ollama pull`**
- Warning signs: Summaries that previously worked well start hallucinating or producing worse output
- Cause: `ollama pull llama3.1:8b` updates to latest without pinning; prompt behavior can shift between model versions
- Prevention: Document this. Consider checking model digest in `meet doctor` and warning if it changed. Log model version in metadata JSON per session
- Phase: Phase 3

---

## Phase 4 — Notion Integration

### notion-client

**P14: Notion block size limit is 2,000 characters**
- Warning signs: Transcript appears truncated in Notion; no error from notion-client
- Cause: Notion API enforces a 2,000-character limit per text block. notion-client doesn't auto-split
- Prevention: When writing transcript or long note sections to Notion, split text into 1,900-char chunks and create multiple paragraph blocks
- Phase: Phase 4

**P15: Rate limiting causes silent failures on batch operations**
- Warning signs: First page creates successfully; subsequent calls silently queue or fail; user sees partial results in Notion
- Cause: Notion API rate limit is 3 requests/second. notion-client may retry silently or fail without useful error
- Prevention: Add `time.sleep(0.4)` between all Notion API calls. Catch HTTP 429 and implement exponential backoff
- Phase: Phase 4

**P16: Database property mismatch causes incomplete pages**
- Warning signs: Notion page created but missing fields (Date, Template Type, etc.)
- Cause: If user manually modified the target Notion database (deleted or renamed a property), notion-client silently skips missing fields
- Prevention: `meet doctor` must verify the Notion database has all required properties. `meet init` should set up the database schema automatically
- Phase: Phase 4 + Phase 6

**P17: Transcript text too large for a single Notion page**
- Warning signs: `notion-client` raises `APIResponseError` with "body too large" or similar
- Cause: Notion has undocumented page content size limits. A 2-hour transcript is ~30K words (~180K chars) which can exceed limits
- Prevention: Store only the structured notes in Notion. Keep the full transcript locally. Add a "Transcript available locally" note in the Notion page with the local file path
- Phase: Phase 4

---

## Cross-Cutting Concerns

**P18: Rich output breaks in non-TTY contexts (piped output, cron jobs)**
- Warning signs: Log files contain ANSI escape codes; `meet list --json | jq` has color codes polluting JSON
- Cause: Rich auto-detects TTY but can be unreliable in some terminal multiplexers (tmux, screen) or remote SSH sessions
- Prevention: Always use `--quiet` flag in documentation for scripting. Check `sys.stdout.isatty()` explicitly before Rich output. Use `rich.console.Console(force_terminal=False)` in non-TTY paths. Ensure `--json` output NEVER includes ANSI codes
- Phase: Phase 5 (CLI integration)

**P19: Python version: avoid 3.14, use 3.11 or 3.12**
- Warning signs: `import mlx` fails; breaking changes in stdlib
- Cause: Python 3.14 has breaking changes that affect ML dependency chains. 3.11/3.12 are the safest for the full dep tree (mlx-whisper, notion-client, click, rich)
- Prevention: Add `python_requires = ">=3.11,<3.14"` in pyproject.toml. `meet doctor` should check Python version
- Phase: Phase 6 (doctor)

**P20: Dependency conflict between openai-whisper and mlx-whisper**
- Warning signs: `import mlx_whisper` succeeds but uses wrong backend; transcription output is different from expected
- Cause: Users who have `openai-whisper` installed alongside `mlx-whisper` may encounter import conflicts
- Prevention: In setup docs and `meet init`, warn that `openai-whisper` must not be installed. `meet doctor` should check `pip list` for `openai-whisper` and warn
- Phase: Phase 6 (doctor)

---

## Priority Matrix

| Pitfall | Severity | Likelihood | Address In |
|---------|----------|------------|------------|
| P1: Volatile device indices | High | Medium | Phase 1 doctor |
| P2: amix sample rate mismatch | High | Low | Phase 1 ffmpeg command |
| P3: WAV header on crash | High | Medium | Phase 1 signal handling |
| P4: Mic permission prompt | Medium | High | Phase 1 init |
| P6: Model download silent | Medium | High | Phase 2 doctor |
| P10: Ollama not running | High | High | Phase 3 doctor |
| P11: Context window degradation | Medium | Medium | Phase 3 chunking |
| P12: Ollama timeout hang | High | Low | Phase 3 timeout |
| P14: Notion block size limit | High | Medium | Phase 4 text splitting |
| P15: Notion rate limiting | Medium | Low | Phase 4 backoff |
| P18: Rich non-TTY output | Medium | Low | Phase 5 TTY check |
| P19: Python version | High | Low | Phase 6 doctor + pyproject.toml |

---
*Researched: 2026-03-22*
