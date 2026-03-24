# Phase 2: Local Transcription - Research

**Researched:** 2026-03-22
**Domain:** mlx-whisper transcription, Rich progress UI, Python config extension
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `meet transcribe` with no `--session` flag resolves to the most recently modified `.wav` file in `recordings/`. Fails clearly if directory is empty.
- **D-02:** `--session` accepts the full WAV filename stem (e.g. `20260322-143000-abc12345`). Exact match only — no prefix/substring matching.
- **D-03:** If a transcript already exists for the session, overwrite silently (no prompt, no error).
- **D-04:** After successful transcription, display the WAV filename stem so the user can pass it to `--session` in later commands.
- **D-05:** Save plain text only to `transcripts/{stem}.txt` — just the concatenated transcript text from `mlx_whisper.transcribe()["text"]`. No timestamps, no segments file.
- **D-06:** Transcript filename uses the same stem as the WAV file (e.g. `20260322-143000-abc12345.txt`).
- **D-07:** If model not cached, `meet transcribe` auto-downloads it — show `Downloading model...` Rich spinner.
- **D-08:** `WhisperModelCheck` returns WARNING (not ERROR) when model is not cached. Message: `WARNING  Whisper model not cached — will download on first use (run: meet transcribe)`.
- **D-09:** When model IS cached, `WhisperModelCheck` shows: `OK  Whisper model cached at ~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo`.
- **D-10:** Phase 2 writes a partial `metadata/{stem}.json` on successful transcription.
- **D-11:** Metadata fields: `wav_path`, `transcript_path`, `transcribed_at` (ISO 8601), `word_count`, `whisper_model`.
- **D-12:** mlx-whisper call: `mlx_whisper.transcribe(path, path_or_hf_repo="mlx-community/whisper-large-v3-turbo")`
- **D-13:** Warn if transcript word count < 50.
- **D-14:** Warn if WAV file duration > 90 minutes.
- **D-15:** Config supports `"whisper": {"language": null}` — null = auto-detect, string = forced language.
- **D-16:** Rich spinner with elapsed time during transcription.
- **D-17:** Two health checks: `MlxWhisperCheck` (import succeeds) and `WhisperModelCheck` (model cached). Both registered with `meet doctor`.

### Claude's Discretion

None specified — all decisions were locked.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRANS-01 | `meet transcribe` runs mlx-whisper (mlx-community/whisper-large-v3-turbo) on the last or specified recording and produces a plain text transcript | `mlx_whisper.transcribe()` confirmed available; `["text"]` key yields plain text |
| TRANS-02 | Transcript saved to `~/.local/share/meeting-notes/transcripts/{uuid}.txt` | `storage.py` already creates `transcripts/` dir; `get_data_dir()` returns XDG path |
| TRANS-03 | `meet transcribe` shows a Rich progress indicator while running — does not appear frozen | Rich `Live` + `Spinner` confirmed working pattern from Phase 1 commands |
| TRANS-04 | If transcript is empty or fewer than 50 words, warn the user | Word count via `len(text.split())` — simple and sufficient |
| TRANS-05 | Whisper language detection is automatic; user can pin language via config | `language` is passed via `**decode_options`; `None` triggers auto-detect; config needs `whisper` section |

</phase_requirements>

---

## Summary

Phase 2 adds `meet transcribe`, a thin service wrapper around `mlx_whisper.transcribe()`, plus two health checks. The implementation is straightforward because Phase 1 built all the infrastructure it needs: `core/storage.py` provides paths, `core/state.py` provides atomic JSON writes, `core/health_check.py` provides the ABC, and `services/checks.py` is the registry. The command pattern is well-established by `record.py`.

The only novel concerns are: (1) how to pass `language` through to mlx-whisper's `**decode_options`, (2) how to derive WAV duration without `ffprobe`, (3) threading the Rich spinner while mlx-whisper runs synchronously in the main thread, and (4) extending the Config dataclass to support a `whisper` section.

**Primary recommendation:** Follow `services/audio.py` and `cli/commands/record.py` exactly as models. Use `threading.Thread` to run `mlx_whisper.transcribe()` in a background thread while displaying a Rich spinner in the foreground. Extend `Config` with a `WhisperConfig` dataclass following the same `AudioConfig` pattern.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mlx-whisper | installed (confirmed) | Apple Silicon speech-to-text | Locked project decision; uses MLX backend |
| rich | >=13.0 (already in pyproject.toml) | Spinner/progress during transcription | Already project dependency |
| click | >=8.1 (already in pyproject.toml) | CLI command definition | Already project dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| threading (stdlib) | stdlib | Run transcription in background thread so spinner renders | Needed for foreground Rich Live + background blocking call |
| pathlib (stdlib) | stdlib | File path manipulation | Already used throughout project |
| json (stdlib) | stdlib | Metadata serialization | Already used via `core/state.py` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `threading.Thread` for spinner | `concurrent.futures.ThreadPoolExecutor` | ThreadPoolExecutor adds no benefit for one task; threading is simpler |
| WAV size-based duration estimate | `ffprobe` subprocess | `ffprobe` adds new dependency; size formula is exact for known format (16kHz mono s16le = 32000 bytes/sec) |

**Installation:** No new packages required. mlx-whisper is already installed (`python3 -c "import mlx_whisper"` passes). All other libraries are stdlib or already in `pyproject.toml`.

**Note on pyproject.toml:** `mlx-whisper` should be added to `dependencies` in `pyproject.toml` for distribution completeness, even though it is already installed in the dev environment.

---

## Architecture Patterns

### Recommended Project Structure

New files this phase creates:

```
meeting_notes/
├── services/
│   └── transcription.py      # mlx-whisper wrapper (new)
├── cli/
│   └── commands/
│       └── transcribe.py     # meet transcribe command (new)
└── core/
    └── config.py             # extend with WhisperConfig (modify)

tests/
├── test_transcription.py     # service unit tests (new)
└── test_transcribe_command.py # CLI command tests (new)
```

### Pattern 1: Service Module (mirrors `services/audio.py`)

`services/transcription.py` follows the same shape as `services/audio.py`: pure functions, no Click imports, no Rich imports, takes only primitives and `Config`.

```python
# Source: existing meeting_notes/services/audio.py pattern
import mlx_whisper
from pathlib import Path
from meeting_notes.core.config import Config


def transcribe_audio(wav_path: Path, config: Config) -> str:
    """Run mlx-whisper on a WAV file. Returns transcript text."""
    kwargs = {}
    if config.whisper.language is not None:
        kwargs["language"] = config.whisper.language
    result = mlx_whisper.transcribe(
        str(wav_path),
        path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        **kwargs,
    )
    return result["text"]
```

**Key finding:** `language` is passed via `**decode_options` in mlx_whisper's signature — NOT as a top-level keyword argument. When `decode_options["language"]` is `None`, mlx-whisper auto-detects. When it is a string (e.g. `"en"`), it forces that language. Setting `language=None` explicitly in kwargs causes mlx-whisper to default to `"en"` in its internal logic — therefore, when config language is `null`/`None`, do NOT pass `language` at all (omit the key entirely).

### Pattern 2: Rich Spinner with Background Thread

mlx-whisper is synchronous and blocking. The Rich spinner must render in the main thread while transcription runs in a background thread.

```python
# Source: Rich docs + threading stdlib pattern
import threading
import time
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

console = Console()

def _run_with_spinner(fn, message: str):
    """Run fn() in a background thread; show spinner with elapsed time."""
    result = {}
    exc_holder = {}

    def worker():
        try:
            result["value"] = fn()
        except Exception as e:
            exc_holder["error"] = e

    thread = threading.Thread(target=worker, daemon=True)
    start = time.time()
    thread.start()

    with Live(console=console, refresh_per_second=10) as live:
        while thread.is_alive():
            elapsed = time.time() - start
            live.update(Text(f"{message} [{elapsed:.0f}s]"))
            time.sleep(0.1)

    thread.join()
    if "error" in exc_holder:
        raise exc_holder["error"]
    return result["value"]
```

### Pattern 3: Config Extension (mirrors `AudioConfig` in `config.py`)

```python
# Source: existing meeting_notes/core/config.py pattern
@dataclass
class WhisperConfig:
    language: str | None = None  # None = auto-detect


@dataclass
class Config:
    version: int = 1
    audio: AudioConfig = field(default_factory=AudioConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        audio = AudioConfig(**data.get("audio", {}))
        whisper_data = data.get("whisper", {})
        # Handle explicit null: JSON null becomes Python None, which is correct
        whisper = WhisperConfig(language=whisper_data.get("language", None))
        return cls(version=data.get("version", 1), audio=audio, whisper=whisper)
```

### Pattern 4: Health Check (mirrors `DiskSpaceCheck` in `services/checks.py`)

```python
# Source: existing meeting_notes/services/checks.py pattern
from pathlib import Path

HF_HUB_CACHE = Path.home() / ".cache" / "huggingface" / "hub"
MODEL_CACHE_DIR = HF_HUB_CACHE / "models--mlx-community--whisper-large-v3-turbo"


class MlxWhisperCheck(HealthCheck):
    name = "mlx-whisper"

    def check(self) -> CheckResult:
        try:
            import mlx_whisper  # noqa: F401
            return CheckResult(status=CheckStatus.OK, message="mlx-whisper importable")
        except ImportError:
            return CheckResult(
                status=CheckStatus.ERROR,
                message="mlx-whisper not installed",
                fix_suggestion="pip install mlx-whisper",
            )


class WhisperModelCheck(HealthCheck):
    name = "Whisper Model Cache"

    def check(self) -> CheckResult:
        if MODEL_CACHE_DIR.exists():
            return CheckResult(
                status=CheckStatus.OK,
                message=f"Whisper model cached at {MODEL_CACHE_DIR}",
            )
        return CheckResult(
            status=CheckStatus.WARNING,
            message="Whisper model not cached — will download on first use (run: meet transcribe)",
            fix_suggestion="Run: meet transcribe (auto-downloads on first use)",
        )
```

### Pattern 5: WAV Duration from File Size

```python
# No external dependency — exact formula for known format
# 16kHz mono s16le = 16000 samples/sec * 2 bytes/sample = 32000 bytes/sec
BYTES_PER_SECOND = 16000 * 2  # 32000
WAV_HEADER_BYTES = 44  # standard PCM WAV header

def estimate_wav_duration_seconds(wav_path: Path) -> float:
    """Estimate duration of a 16kHz mono s16le WAV file from its size."""
    size = wav_path.stat().st_size
    audio_bytes = max(0, size - WAV_HEADER_BYTES)
    return audio_bytes / BYTES_PER_SECOND
```

90 minutes threshold = 5400 seconds. At 32000 bytes/sec, a 90-minute file is approximately 165 MB.

### Pattern 6: Session Resolution (last WAV)

```python
from pathlib import Path

def resolve_latest_wav(recordings_dir: Path) -> Path:
    """Return the most recently modified WAV file. Raises if none found."""
    wavs = sorted(recordings_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime)
    if not wavs:
        raise FileNotFoundError("No recordings found in recordings directory.")
    return wavs[-1]

def resolve_wav_by_stem(recordings_dir: Path, stem: str) -> Path:
    """Return the WAV file matching the exact stem. Raises if not found."""
    candidate = recordings_dir / f"{stem}.wav"
    if not candidate.exists():
        raise FileNotFoundError(f"No recording found for session: {stem}")
    return candidate
```

### Anti-Patterns to Avoid

- **Passing `language=None` to mlx-whisper:** When config language is null, omit the `language` key from kwargs entirely. If you pass `decode_options={"language": None}`, mlx-whisper's internal logic defaults it to `"en"` (not auto-detect).
- **Blocking main thread during transcription:** Call `mlx_whisper.transcribe()` directly in the click handler — Rich spinner will not render and the CLI appears frozen (violates TRANS-03).
- **Using ffprobe for duration:** Introduces a new subprocess dependency. The WAV size formula is exact for the known format and has no deps.
- **Glob `*.wav` and sort by name:** WAV filenames include timestamps so sorting by name would work, but sort by `st_mtime` is more robust and matches the intent (most recently MODIFIED).
- **`write_state` for metadata — don't invent new file writing:** Use the existing `core/state.py:write_state()` function. It handles atomic writes via temp+replace.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic JSON write for metadata | Custom file write with try/except | `core/state.py:write_state()` | Already handles temp+replace atomicity |
| Model download progress | Custom HuggingFace HTTP fetcher | mlx-whisper's built-in download | mlx-whisper delegates to HuggingFace Hub which handles resumable downloads |
| WAV file validation | Audio parsing library | File existence check + size > header | Over-engineering for this use case; mlx-whisper raises clearly on bad input |
| Word count | NLTK or spaCy | `len(text.split())` | Sufficient precision; avoids new dep |

**Key insight:** This phase's complexity lies in wiring existing pieces correctly, not in novel logic. The project's own `core/` infrastructure handles all the hard problems (storage, atomic writes, config, health checks).

---

## Runtime State Inventory

> Skipped — this is a greenfield feature phase, not a rename/refactor/migration.

---

## Common Pitfalls

### Pitfall 1: Language Auto-Detect vs. Forced Language
**What goes wrong:** Passing `language=None` explicitly to mlx-whisper causes it to default to `"en"`, not auto-detect. Auto-detect requires the `language` key to be absent from `decode_options` entirely.
**Why it happens:** mlx-whisper's source: `if decode_options.get("language", None) is None: decode_options["language"] = "en"`. So a `None` value gets replaced with `"en"`.
**How to avoid:** Conditionally include `language` in kwargs only when `config.whisper.language is not None`.
**Warning signs:** Non-English meeting transcripts come back in English text with `[Music]` hallucinations.

### Pitfall 2: Spinner Not Rendering (Frozen CLI)
**What goes wrong:** `mlx_whisper.transcribe()` blocks for minutes with no output — user thinks CLI crashed.
**Why it happens:** mlx-whisper is synchronous; if called in the main thread with `console.status()` as a context manager, Rich's Live display cannot refresh because the thread is blocked.
**How to avoid:** Run `mlx_whisper.transcribe()` in a `threading.Thread`; render spinner in main thread using `rich.live.Live`.
**Warning signs:** Console shows spinner momentarily then freezes; no elapsed time updates.

### Pitfall 3: Model Not Cached Warning vs. Download
**What goes wrong:** `WhisperModelCheck` raises ERROR blocking `meet doctor` exit code 0. Or: no spinner shown during auto-download, user panics seeing a long silent wait.
**Why it happens:** Confusion between "model unavailable" (blocking ERROR) and "model will auto-download" (informational WARNING).
**How to avoid:** `WhisperModelCheck` returns `CheckStatus.WARNING`, not ERROR (D-08). Show `Downloading model...` spinner before `mlx_whisper.transcribe()` call when model directory is absent.
**Warning signs:** `meet doctor` exits 1 on a fresh install; or `meet transcribe` appears frozen on first run.

### Pitfall 4: Doctor Command Not Registering New Checks
**What goes wrong:** New checks are implemented in `services/checks.py` but `meet doctor` never runs them because `doctor.py` instantiates checks directly rather than reading from a registry.
**Why it happens:** Current `doctor.py` hard-codes `suite.register(BlackHoleCheck(...))` — new checks must be manually added here.
**How to avoid:** Add `suite.register(MlxWhisperCheck())` and `suite.register(WhisperModelCheck())` to `doctor.py` in Plan 2.2. This is a code edit, not automatic.
**Warning signs:** `meet doctor` output shows no Whisper-related check lines.

### Pitfall 5: Config Load Fails on New `whisper` Key
**What goes wrong:** Existing `config.json` files (written by Phase 1 `meet init`) do not have a `"whisper"` key. `Config.load()` crashes with `KeyError` or incorrect behavior.
**Why it happens:** If Config.load() uses `WhisperConfig(**data["whisper"])` without a default, it raises `KeyError` on existing configs.
**How to avoid:** Use `data.get("whisper", {})` — missing key returns empty dict, `WhisperConfig()` uses defaults.
**Warning signs:** `meet transcribe` crashes on machines that ran Phase 1 without re-running `meet init`.

### Pitfall 6: Session Stem Display Inconsistency
**What goes wrong:** `meet transcribe` prints a session ID that does not match the actual WAV stem, so copy-pasting to `--session` in Phase 3 fails.
**Why it happens:** Printing `session_id` from state.json (which is a hex UUID) instead of the WAV filename stem.
**How to avoid:** Derive stem from `wav_path.stem` (e.g., `20260322-143000-abc12345`), not from any stored UUID. D-04 specifies displaying the WAV filename stem.
**Warning signs:** `meet summarize --session <displayed-value>` returns "No recording found".

---

## Code Examples

### Full `mlx_whisper.transcribe()` Call with Language Option

```python
# Source: mlx_whisper source inspection + project pattern (verified 2026-03-22)
def transcribe_audio(wav_path: Path, config: "Config") -> str:
    decode_opts: dict = {}
    if config.whisper.language is not None:
        decode_opts["language"] = config.whisper.language
    # When language is None: omit key entirely — mlx-whisper auto-detects
    result = mlx_whisper.transcribe(
        str(wav_path),
        path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        **decode_opts,
    )
    return result["text"]
```

### WAV Duration Estimate + 90-Minute Warning

```python
# Source: project decision D-14 + CONTEXT.md specifics section
BYTES_PER_SECOND = 16000 * 2  # 32000 — 16kHz mono s16le
WAV_HEADER_BYTES = 44
WARN_DURATION_SECONDS = 90 * 60  # 5400

def estimate_wav_duration_seconds(wav_path: Path) -> float:
    audio_bytes = max(0, wav_path.stat().st_size - WAV_HEADER_BYTES)
    return audio_bytes / BYTES_PER_SECOND

# In command:
duration = estimate_wav_duration_seconds(wav_path)
if duration > WARN_DURATION_SECONDS:
    console.print(
        "[yellow]Warning:[/yellow] Recording is over 90 minutes. "
        "Transcription may cause memory pressure on Apple Silicon."
    )
```

### Metadata Write (Phase 2 fields only)

```python
# Source: core/state.py write_state pattern + D-11
from datetime import datetime, timezone
from meeting_notes.core.state import write_state

metadata = {
    "wav_path": str(wav_path.resolve()),
    "transcript_path": str(transcript_path.resolve()),
    "transcribed_at": datetime.now(timezone.utc).isoformat(),
    "word_count": len(transcript_text.split()),
    "whisper_model": "mlx-community/whisper-large-v3-turbo",
}
write_state(metadata_path, metadata)
```

### Registering New Checks in `doctor.py`

```python
# Source: existing meeting_notes/cli/commands/doctor.py + new imports
from meeting_notes.services.checks import (
    BlackHoleCheck,
    DiskSpaceCheck,
    FFmpegDeviceCheck,
    MlxWhisperCheck,       # NEW
    WhisperModelCheck,     # NEW
)

# In doctor() command body, after existing suite.register() calls:
suite.register(MlxWhisperCheck())
suite.register(WhisperModelCheck())
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| openai-whisper (CPU) | mlx-whisper (Apple Silicon MLX) | 2023 | 5-10x speedup on M-series; different import/API |
| `decode_options={"language": "en"}` | Omit `language` key for auto-detect | mlx-whisper design | Must not pass `None`; omit entirely for auto |

**Deprecated/outdated:**
- `openai-whisper`: Do not install alongside mlx-whisper (import conflict risk). Phase 6 adds a doctor check for this.

---

## Open Questions

1. **Rich spinner during HuggingFace model download**
   - What we know: mlx-whisper triggers HuggingFace Hub download automatically when model isn't cached; it prints progress to stdout
   - What's unclear: Whether HF Hub download progress can be suppressed or intercepted cleanly, or if the spinner will conflict with HF's own output
   - Recommendation: Show "Downloading model..." console message before the transcription call; don't try to intercept HF progress — let it print naturally. The spinner is for the transcription phase itself, not the download.

2. **`metadata/{stem}.json` — read-modify-write vs. write-only**
   - What we know: Phase 2 writes `metadata/{stem}.json`; future phases (3, 4, 5) append fields to the same file
   - What's unclear: Whether Phase 2 should read existing metadata before writing (if the user re-transcribes)
   - Recommendation: D-03 says overwrite silently. Write the full Phase 2 dict fresh — do NOT attempt to merge with existing metadata. Later phases will read + merge when they run.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| mlx-whisper | TRANS-01, transcription service | Yes | installed (import verified) | None — locked decision |
| whisper-large-v3-turbo model | TRANS-01 | Yes | cached at `~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo` | Auto-downloads on first use |
| Python 3.14 | Runtime | Yes | 3.14.3 | — |
| pytest 9.0.2 | Test suite | Yes | 9.0.2 | — |
| rich >=13.0 | TRANS-03 (spinner) | Yes | in pyproject.toml | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` testpaths = ["tests"] |
| Quick run command | `python3 -m pytest tests/test_transcription.py tests/test_transcribe_command.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRANS-01 | `transcribe_audio()` calls mlx-whisper and returns `result["text"]` | unit (mock mlx_whisper.transcribe) | `pytest tests/test_transcription.py::test_transcribe_audio_calls_mlx_whisper -x` | Wave 0 |
| TRANS-01 | `transcribe_audio()` passes `path_or_hf_repo="mlx-community/whisper-large-v3-turbo"` | unit (mock) | `pytest tests/test_transcription.py::test_transcribe_audio_uses_correct_model -x` | Wave 0 |
| TRANS-02 | Transcript saved to `transcripts/{stem}.txt` with correct content | unit (tmp_path) | `pytest tests/test_transcribe_command.py::test_transcript_saved_to_correct_path -x` | Wave 0 |
| TRANS-03 | Command does not block (spinner integration is not unit-testable but thread usage is) | unit (mock thread) | `pytest tests/test_transcription.py::test_run_with_spinner_returns_result -x` | Wave 0 |
| TRANS-04 | Warning printed when word count < 50 | unit (mock transcribe returning short text) | `pytest tests/test_transcribe_command.py::test_short_transcript_warning -x` | Wave 0 |
| TRANS-05 | Language=None omits language kwarg; language="en" passes it | unit (mock, inspect kwargs) | `pytest tests/test_transcription.py::test_language_none_omits_kwarg` | Wave 0 |
| TRANS-05 | Language="en" passes `language="en"` via decode_options | unit (mock, inspect kwargs) | `pytest tests/test_transcription.py::test_language_string_passes_kwarg` | Wave 0 |
| D-01 | Last WAV resolution picks most recently modified file | unit (tmp_path with two WAVs) | `pytest tests/test_transcribe_command.py::test_resolve_latest_wav` | Wave 0 |
| D-01 | Fails clearly when recordings dir is empty | unit | `pytest tests/test_transcribe_command.py::test_no_recordings_exits_with_error` | Wave 0 |
| D-02 | `--session STEM` resolves exact match only | unit | `pytest tests/test_transcribe_command.py::test_session_exact_match_only` | Wave 0 |
| D-08 | `WhisperModelCheck` returns WARNING when dir absent | unit (monkeypatch Path.exists) | `pytest tests/test_health_check.py::test_whisper_model_check_warning` | Wave 0 |
| D-09 | `WhisperModelCheck` returns OK when dir present | unit (monkeypatch) | `pytest tests/test_health_check.py::test_whisper_model_check_ok` | Wave 0 |
| D-14 | 90-minute duration warning fires | unit (mock file size) | `pytest tests/test_transcription.py::test_long_recording_warning` | Wave 0 |
| D-17 | `MlxWhisperCheck` returns OK when import succeeds | unit | `pytest tests/test_health_check.py::test_mlx_whisper_check_ok` | Wave 0 |
| D-17 | `MlxWhisperCheck` returns ERROR when import fails | unit (monkeypatch builtins) | `pytest tests/test_health_check.py::test_mlx_whisper_check_error` | Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/test_transcription.py tests/test_transcribe_command.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite (45 existing + new tests) green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_transcription.py` — unit tests for `services/transcription.py` (TRANS-01, TRANS-03, TRANS-04, TRANS-05, D-14)
- [ ] `tests/test_transcribe_command.py` — unit tests for `cli/commands/transcribe.py` (TRANS-02, D-01, D-02, D-04, D-10, D-11)
- [ ] New health check tests go into existing `tests/test_health_check.py` (D-08, D-09, D-17) — file already exists, add to it

---

## Project Constraints (from CLAUDE.md)

CLAUDE.md does not exist in the working directory. No additional project constraints to enforce.

---

## Sources

### Primary (HIGH confidence)
- `mlx_whisper` — live import + `inspect.signature` + source inspection on installed package (2026-03-22)
- `meeting_notes/core/health_check.py` — read directly; HealthCheck ABC and CheckResult patterns confirmed
- `meeting_notes/services/checks.py` — read directly; DiskSpaceCheck WARNING pattern confirmed
- `meeting_notes/core/storage.py` — read directly; `get_data_dir()`, `ensure_dirs()` confirmed
- `meeting_notes/core/state.py` — read directly; atomic write pattern confirmed
- `meeting_notes/core/config.py` — read directly; AudioConfig dataclass pattern confirmed
- `meeting_notes/cli/commands/record.py` — read directly; command structure pattern confirmed
- `meeting_notes/cli/commands/doctor.py` — read directly; check registration pattern confirmed
- `meeting_notes/cli/main.py` — read directly; command registration pattern confirmed
- `~/.cache/huggingface/hub/` — `ls` verified model cached at `models--mlx-community--whisper-large-v3-turbo`
- `python3 -m pytest tests/ -q` — 45 tests passing confirmed

### Secondary (MEDIUM confidence)
- `.planning/phases/02-local-transcription/02-CONTEXT.md` — user decisions and locked constraints
- `.planning/REQUIREMENTS.md` — TRANS-01 to TRANS-05 requirements text
- `.planning/ROADMAP.md` — Phase 2 plan specs (2.1, 2.2) and pitfalls P6-P9

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — mlx-whisper installed and import-verified; all other libraries already in project
- Architecture: HIGH — all patterns derived from reading existing project source code directly
- Pitfalls: HIGH — language pitfall verified by reading mlx-whisper source; others verified from existing code patterns
- Test infrastructure: HIGH — pytest 9.0.2 confirmed, 45 tests passing, conftest.py fixtures read directly

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable libraries; mlx-whisper API unlikely to change)
