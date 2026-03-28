# Stack Research: meeting-notes

**Domain:** Local meeting audio capture + transcription + LLM note generation CLI on macOS/Apple Silicon
**Date:** 2026-03-22 (updated 2026-03-27 for v1.2 Named Recordings)

---

## Recommended Stack

### Audio Capture

| Component | Choice | Version | Confidence |
|-----------|--------|---------|------------|
| Audio driver | BlackHole 2ch | latest (brew) | ✓ High |
| Capture tool | ffmpeg (avfoundation) | 6.x+ | ✓ High |
| Device selection | Index numbers only (`:1`, `:2`) | — | ✓ Validated |
| Mix strategy | `amix=inputs=2:normalize=0` | — | ✓ Validated |
| Output format | WAV, 16kHz, mono, pcm_s16le | — | ✓ Required |

**Why NOT Aggregate Device:** macOS Aggregate Devices add latency and are unreliable for capture; the two-input amix approach is deterministic.

### Transcription

| Component | Choice | Version | Confidence |
|-----------|--------|---------|------------|
| Framework | mlx-whisper | ≥0.4.0 | ✓ High |
| Model | mlx-community/whisper-large-v3-turbo | latest | ✓ High |
| Python | 3.11 or 3.12 | — | ✓ High |

**Why NOT insanely-fast-whisper:** Has CUDA dependency that breaks on Python 3.14 + Apple Silicon. MLX is native to Apple Silicon Neural Engine.
**Why NOT whisper-small/base:** Quality insufficient for meeting notes. turbo variant balances speed and accuracy well.
**Python version:** Avoid 3.14 (too new, breakage risk with ML deps). 3.11/3.12 are safest for the full dependency tree.

### LLM

| Component | Choice | Notes |
|-----------|--------|-------|
| Server | Ollama | Must be running before CLI use |
| Model | llama3.1:8b | Minimum quality for meeting summarization |
| Integration | HTTP API (`localhost:11434/api/generate`) | More stable than SDK |

**Why HTTP API over Ollama Python SDK:** Ollama doesn't have a first-party Python SDK. Third-party SDKs lag Ollama server updates. Direct HTTP is stable and dependency-free.
**Why NOT llama3.2:** Too small (1b/3b variants) — produces shallow summaries. llama3.1:8b is the minimum viable model.

### Notion Integration

| Component | Choice | Version |
|-----------|--------|---------|
| SDK | notion-client | ≥2.2.x |

**Rate limit:** 3 request units/second. Add `time.sleep(0.34)` between bulk API calls.
**Page creation pattern:** `notion.pages.create(parent={"database_id": ...}, properties={...}, children=[...])` — or plain page with `parent={"page_id": ...}`.

### CLI Framework

| Component | Choice | Version | Notes |
|-----------|--------|---------|-------|
| CLI | Click | ≥8.1 | Handles Ctrl+C via context managers |
| Terminal UI | Rich | ≥13.x | Progress, panels, live display |
| Config | python-dotenv or ~/.config/meeting-notes/config.json | — | XDG Base Dir preferred |

**Signal handling pattern for ffmpeg subprocess:**
```python
import signal, subprocess

proc = subprocess.Popen(["ffmpeg", ...])
def handle_sigint(sig, frame):
    proc.send_signal(signal.SIGINT)  # graceful ffmpeg stop
    proc.wait()
signal.signal(signal.SIGINT, handle_sigint)
```

### Python Packaging

| Choice | Rationale |
|--------|-----------|
| `pyproject.toml` (PEP 621) | 2025 standard; works with pip, uv, poetry |
| Entry point: `[project.scripts]` | `meet = "meeting_notes.cli:main"` |
| Dependency manager | `uv` (fast) or `pip` in venv |

### What NOT to Use

| Tool | Reason |
|------|--------|
| insanely-fast-whisper | CUDA dependency, breaks on Apple Silicon + Python 3.14 |
| llama3.2 | Too small for meeting summarization quality |
| m4a audio format | mlx-whisper cannot process it |
| ffmpeg device names | Unreliable across macOS versions |
| Aggregate Device | Unreliable for capture; amix is better |
| OpenAI Whisper API | Violates 100% local requirement |
| Any cloud LLM | Violates 100% local requirement |

---

## Installation Notes

1. `brew install blackhole-2ch ffmpeg` — ffmpeg must be built with avfoundation
2. `pip install mlx-whisper` — downloads model on first `mlx_whisper.transcribe()` call (~1.5GB for large-v3-turbo)
3. `ollama pull llama3.1:8b` — must be done before first use (~4.7GB)
4. `pip install notion-client click rich python-dotenv` — no conflicts with mlx-whisper

---

## v1.2 Named Recordings — Stack Additions

**Verdict: Zero new dependencies required.**

The named recordings feature is achievable entirely with the existing stack plus
Python's standard library. `pyproject.toml` does not need new entries.

### Slugification — Pure stdlib (no new dependency)

**Recommendation: inline function using `re` + `unicodedata`, place in `meeting_notes/core/storage.py`.**

```python
import re
import unicodedata

def slugify(text: str) -> str:
    """Convert arbitrary meeting name to filesystem-safe slug.

    Verified outputs:
        "1:1 with Gabriel"       -> "1-1-with-gabriel"
        "Q4 Planning & Review"   -> "q4-planning-review"
        "Team Meeting - Q1 2026" -> "team-meeting-q1-2026"
        "Jose / Maria sync"      -> "jose-maria-sync"
    """
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')
```

`unicodedata` and `re` are stdlib modules present in every Python version this project
supports (>=3.11). The function was tested locally against all realistic meeting name
inputs and produces correct output.

**Why not `python-slugify` (8.0.4, MIT)?**

`python-slugify` is the community standard (~62M monthly PyPI downloads) and would
work. However, it pulls in `text-unidecode` as a required transitive dependency, which
is dual-licensed GPL + Perl Artistic. Adding a GPL-licensed transitive dependency to a
project that ships under MIT is a licensing concern worth avoiding when 5 lines of
stdlib produce identical output for every Latin/ASCII meeting name this tool will
realistically encounter.

**If non-Latin Unicode coverage becomes needed later** (Chinese, Arabic, Cyrillic
meeting names where romanization is wanted rather than stripping), add
`python-slugify[unidecode]` at that point. The `slugify()` function signature stays
identical — swap the body, no caller changes required.

### Click — Optional Positional Argument Pattern

**Recommendation: `@click.argument("name", required=False, default=None)`**

Click 8.x supports optional positional arguments natively. This is the idiomatic
pattern when the argument is the command's primary subject and the user may omit it.

```python
@click.command()
@click.argument("name", required=False, default=None, metavar="NAME")
@click.pass_context
def record(ctx: click.Context, name: str | None):
    """Start a recording session.

    NAME is an optional label for the recording (e.g. "1:1 with Gabriel").
    If omitted, the recording is identified by timestamp only.
    """
    slug = slugify(name) if name else None
    ...
```

Invocation:
```
meet record                          # name is None -> timestamp-only filename
meet record "1:1 with Gabriel"       # name -> "1-1-with-gabriel-<timestamp>.wav"
meet record standup                  # name -> "standup-<timestamp>.wav"
```

**Why positional argument, not `--name` option?**

The name is what the command acts on — it is the primary subject, not a modifier.
Click's convention is: positional argument = main subject, option = modifier/flag.
Positional is also faster to type for the common case (`meet record standup` vs
`meet record --name standup`). `required=False` with `default=None` gives clean
None-check logic downstream with no special handling needed.

**Add `metavar="NAME"`** so the help text renders as `meet record [NAME]` rather than
the default `meet record [ARGS]...`, which is misleading for a single optional string.

**Why not `nargs=-1` variadic?**

Variadic (`nargs=-1`) makes Click pass a tuple, requiring `" ".join(name)` to
reconstruct the string — an awkward workaround. `required=False` with `nargs=1`
(the default) keeps the parameter a simple `str | None`.

### Filename Generation — Integration Point

`get_recording_path()` in `meeting_notes/core/storage.py` currently produces:

```
recordings/{timestamp}-{session_id[:8]}.wav
```

Extend it to accept an optional `name` parameter:

```
recordings/{slug}-{timestamp}-{session_id[:8]}.wav   # when name provided
recordings/{timestamp}-{session_id[:8]}.wav           # when name is None (unchanged)
```

The slug is **prepended** (not appended) so that `meet list` sorted by filename still
groups named recordings meaningfully. The `stem` derivation in the `stop` command
(`Path(output_path).stem`) propagates the name through to the metadata filename
automatically — no changes needed there.

**State and metadata propagation:** Store `recording_name` (raw user string) in both
`state.json` (written at `record` time) and the session metadata JSON (written at
`stop` time). The raw name is kept separately from the slug so `meet list` and Notion
can display the original human-readable title.

### Alternatives Considered (v1.2 specific)

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Slugification | stdlib `re` + `unicodedata` | `python-slugify` 8.0.4 | Adds `text-unidecode` (GPL+Perl Artistic) transitive dep; no behavioral gain for Latin/ASCII names |
| Slugification | stdlib | `awesome-slugify` | Unmaintained since 2016 |
| Slugification | stdlib | `unicode-slugify` | Mozilla-internal, inactive, poor Snyk health score, Django dep |
| Click pattern | `@click.argument(required=False)` | `@click.option("--name")` | Options are modifiers; the name is the command's primary subject |
| Click pattern | `@click.argument(required=False)` | `nargs=-1` variadic | Returns tuple, requires join hack, confusing for a single string value |

---

## Sources

- [python-slugify on PyPI](https://pypi.org/project/python-slugify/) — version 8.0.4, MIT + text-unidecode dep confirmed (HIGH confidence)
- [unicode-slugify health analysis via Snyk](https://snyk.io/advisor/python/unicode-slugify) — inactive, not recommended (MEDIUM confidence)
- [Click Arguments documentation](https://click.palletsprojects.com/en/stable/arguments/) — `required=False` pattern (HIGH confidence)
- [pallets/click issue #94 — Optional arguments](https://github.com/pallets/click/issues/94) — confirmed supported (HIGH confidence)
- [pallets/click issue #3045 — 2025 usage](https://github.com/pallets/click/issues/3045) — `required=False` in recent use (HIGH confidence)
- Local Python 3.14 test — stdlib slugify verified against PROJECT.md example and 6 edge cases, all correct (HIGH confidence — tested in project venv)

---

*Stack research for: meeting-notes CLI on macOS/Apple Silicon*
*Researched: 2026-03-22 | Updated: 2026-03-27 (v1.2 Named Recordings)*
