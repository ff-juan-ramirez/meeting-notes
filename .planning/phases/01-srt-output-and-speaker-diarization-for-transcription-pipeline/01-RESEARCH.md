# Phase 1: SRT Output and Speaker Diarization - Research

**Researched:** 2026-03-27
**Domain:** pyannote-audio speaker diarization, SRT subtitle generation, mlx-whisper segment integration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**SRT Output**
- D-01: Always generated alongside `.txt` — no flag required. Every `meet transcribe` run produces `transcripts/{stem}.srt`.
- D-02: Saved in `transcripts/` directory alongside `{stem}.txt` — same location, same stem.
- D-03: Segment-level timestamps only (`result["segments"]` from mlx_whisper). `word_timestamps=True` is not used.
- D-04: SRT file is not shown in `meet list` — it's an implementation detail, not a user-facing status.

**Speaker Diarization**
- D-05: Library: `pyannote-audio` with `pyannote/speaker-diarization-3.1` pipeline.
- D-06: HuggingFace token collected in `meet init` wizard (new step), stored in `config.json` alongside Notion token.
- D-07: Diarization runs automatically as part of `meet transcribe` — no separate command or flag.
- D-08: If HF token is missing or diarization fails for any reason: warn (yellow) and continue without diarization. `.txt` and `.srt` are produced without speaker labels. Transcription is never blocked by diarization failure.

**Diarized Output Format**
- D-09: Plain-text transcript (`.txt`) uses speaker prefix per paragraph — consecutive segments from the same speaker are grouped.
- D-10: SRT entries prefixed with speaker tag: `SPEAKER_00: Hello, welcome to the call.`
- D-11: `meet summarize` automatically prefers the diarized `.txt` when available. Falls back to plain `.txt` if diarization was skipped.
- D-12: Speaker labels use pyannote defaults — `SPEAKER_00`, `SPEAKER_01`, etc. No renaming feature in this phase.

**Health Checks (meet doctor)**
- D-13: `PyannoteCheck` — verifies `pyannote.audio` is importable. ERROR severity.
- D-14: `HuggingFaceTokenCheck` — verifies HF token is present in config and can reach HuggingFace. WARNING severity.
- D-15: `PyannoteModelCheck` — verifies `pyannote/speaker-diarization-3.1` model is cached locally. WARNING severity.

### Claude's Discretion
- Exact algorithm for merging pyannote speaker turns with Whisper segments (assign each segment to the speaker whose turn has the most overlap with the segment's time range).
- SRT index numbering and timestamp formatting (standard `HH:MM:SS,mmm` format).
- How to store diarization metadata (speaker turn data) in the session metadata JSON.
- pyannote model download UX (spinner message, same pattern as WhisperModelCheck).

### Deferred Ideas (OUT OF SCOPE)
- Speaker renaming (`meet diarize --rename SPEAKER_00=Alice`) — future phase.
- `meet list` SRT/diarization status column — explicitly decided against; future phase if desired.
- Word-level SRT timestamps (`word_timestamps=True`) — future enhancement if needed.
- WhisperX as an alternative to pyannote-audio — not needed given pyannote choice.
</user_constraints>

---

## Summary

This phase extends `meet transcribe` in two directions: (1) writing a `.srt` subtitle file from mlx-whisper's already-returned `result["segments"]`, and (2) running pyannote-audio's `speaker-diarization-3.1` pipeline to label speakers in both output files. SRT generation is pure Python string formatting — no new dependencies required. Diarization is the heavier addition: `pyannote.audio==3.3.2` pulls in `torchaudio>=2.2.0`, `speechbrain>=1.0.0`, `lightning>=2.0.1`, and a HuggingFace model download (~1 GB).

The critical implementation risk is the Python 3.14 environment. pyannote-audio 3.3.2 officially classifies only Python 3.9–3.11. The project already runs on Python 3.14 (confirmed by pyproject.toml and the live environment). Compatibility must be validated by actually installing pyannote.audio 3.3.2 with its full dependency tree — this is a Wave 0 gate, not an assumption. The graceful-fallback architecture (D-08) means that even if diarization fails at import time on this user's machine, the feature degrades to plain transcription and the plan succeeds.

Speaker-segment merging is the core algorithmic challenge: Whisper returns segments with timestamps; pyannote returns speaker turns with timestamps. The two must be fused by overlap arithmetic. The project's discretion section assigns each Whisper segment to the speaker whose turn covers the most of that segment's time range — a well-understood, single-pass algorithm.

**Primary recommendation:** Pin `pyannote.audio==3.3.2` (not 4.x). Version 4.x introduced `torchcodec>=0.7.0` and an exact `torch==2.8.0` pin that conflicts with the system torch 2.10.0 already installed for mlx-whisper. Version 3.3.2 requires `torch>=2.0.0` and `torchaudio>=2.2.0` — far more compatible with the existing environment.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyannote.audio | 3.3.2 | Speaker diarization pipeline | Locked by D-05; 3.x avoids 4.x torch==2.8.0 exact pin that conflicts with installed torch 2.10.0 |
| torchaudio | >=2.2.0 (pulled by pyannote) | Audio I/O for pyannote 3.x | Required transitive dep of pyannote 3.3.2 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| huggingface-hub | >=0.13.0 (already installed 1.7.2) | HF token verification in HuggingFaceTokenCheck | Already available; use `HfApi().whoami(token=...)` to validate tokens |
| speechbrain | >=1.0.0 | Speaker embedding (pyannote 3.x dep) | Pulled automatically by pyannote 3.3.2 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyannote.audio 3.3.2 | pyannote.audio 4.0.4 | 4.x pins exact torch==2.8.0, conflicts with torch 2.10.0 installed for mlx-whisper; uses 6x more VRAM; torchcodec dep not yet stable on Apple Silicon |
| pyannote.audio 3.3.2 | WhisperX | Deferred by user (D-deferred) |

**Installation:**
```bash
pip install "pyannote.audio==3.3.2"
```

Note: `torchaudio` must be installed separately first if not present. With torch 2.10.0 already installed:
```bash
pip install torchaudio
pip install "pyannote.audio==3.3.2"
```

**Version verification:**
```bash
# Already verified via wheel inspection 2026-03-27
# pyannote.audio 3.3.2 requires: torch>=2.0.0, torchaudio>=2.2.0, speechbrain>=1.0.0
# System has: torch==2.10.0 (via mlx-whisper), torchaudio: NOT INSTALLED, huggingface-hub==1.7.2
```

---

## Architecture Patterns

### Recommended Project Structure

No new directories required. Changes touch existing files:

```
meeting_notes/
├── core/
│   └── config.py                  # Add hf_token field to Config dataclass
├── services/
│   ├── transcription.py           # Modify transcribe_audio() to return (text, segments)
│   │                              # Add generate_srt() function
│   │                              # Add run_diarization() function
│   └── checks.py                  # Add PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck
├── cli/
│   └── commands/
│       ├── transcribe.py          # Wire SRT save + diarization call + diarized .txt
│       ├── init.py                # Add HF token wizard step + _update_specific_fields entry
│       └── summarize.py           # Add diarized .txt preference logic
tests/
├── test_transcription.py          # Extend with SRT generation + segment-speaker merge tests
├── test_transcribe_command.py     # Extend with SRT file creation + diarization path tests
├── test_summarize_command.py      # Extend with diarized .txt preference tests
├── test_checks.py                 # (new) PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck
└── test_init.py                   # Extend with HF token wizard step tests
```

### Pattern 1: mlx_whisper Segment Return

mlx_whisper.transcribe() already returns segments in `result["segments"]`. The current code discards this:

```python
# Current (transcription.py line 44)
return result["text"]

# New signature must return both text and segments
def transcribe_audio(wav_path: Path, config: Config) -> tuple[str, list[dict]]:
    ...
    return result["text"], result["segments"]
```

Each segment dict has: `{"start": float, "end": float, "text": str, ...}`

### Pattern 2: SRT Generation (pure formatting)

```python
# Source: SRT format specification + verified against AssemblyAI/DigitalOcean examples
def seconds_to_srt_timestamp(seconds: float) -> str:
    """Convert float seconds to SRT HH:MM:SS,mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segments: list[dict], speaker_map: dict[int, str] | None = None) -> str:
    """Generate SRT content from Whisper segments.

    speaker_map: optional {segment_index: speaker_label} for diarized output.
    Each SRT entry: index\\nHH:MM:SS,mmm --> HH:MM:SS,mmm\\ntext\\n\\n
    """
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_ts = seconds_to_srt_timestamp(seg["start"])
        end_ts = seconds_to_srt_timestamp(seg["end"])
        text = seg["text"].strip()
        if speaker_map and i - 1 in speaker_map:
            text = f"{speaker_map[i - 1]}: {text}"
        lines.append(f"{i}\n{start_ts} --> {end_ts}\n{text}\n")
    return "\n".join(lines)
```

### Pattern 3: pyannote Pipeline Loading and Diarization

```python
# Source: pyannote/speaker-diarization-3.1 HuggingFace README (verified 2026-03-27)
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="HUGGINGFACE_ACCESS_TOKEN_GOES_HERE",
)

# Run on WAV file (mono 16kHz — matches project's recording format)
diarization = pipeline("audio.wav")

# Iterate speaker turns
for turn, _, speaker in diarization.itertracks(yield_label=True):
    # turn.start: float seconds
    # turn.end: float seconds
    # speaker: str e.g. "SPEAKER_00", "SPEAKER_01"
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s {speaker}")
```

Note: `use_auth_token` is the correct parameter name for pyannote 3.x / speaker-diarization-3.1. The newer `token=` parameter name is for 4.x community models.

### Pattern 4: Segment-Speaker Overlap Assignment (Claude's Discretion)

```python
def assign_speakers_to_segments(
    segments: list[dict],
    diarization,  # pyannote Annotation object
) -> dict[int, str]:
    """Return {segment_index: speaker_label} by maximum overlap.

    For each Whisper segment, find the pyannote speaker turn that
    overlaps the most with [seg.start, seg.end]. Ties broken by
    iteration order (first match wins).
    """
    speaker_map = {}
    for idx, seg in enumerate(segments):
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg_dur = seg_end - seg_start
        if seg_dur <= 0:
            continue

        best_speaker = None
        best_overlap = 0.0

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            overlap_start = max(seg_start, turn.start)
            overlap_end = min(seg_end, turn.end)
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker

        if best_speaker is not None:
            speaker_map[idx] = best_speaker

    return speaker_map
```

### Pattern 5: HuggingFace Token Validation

```python
# Source: huggingface_hub 1.7.2 (installed, verified 2026-03-27)
from huggingface_hub import HfApi
from huggingface_hub.errors import RepositoryNotFoundError

def validate_hf_token(token: str) -> bool:
    """Return True if token is valid, raises on network failure."""
    api = HfApi()
    api.whoami(token=token)  # raises if invalid
    return True
```

### Pattern 6: HuggingFace Model Cache Path

The pyannote/speaker-diarization-3.1 model caches to:
```
~/.cache/huggingface/hub/models--pyannote--speaker-diarization-3.1/
```
The embedded segmentation model caches to:
```
~/.cache/huggingface/hub/models--pyannote--segmentation-3.0/
```

For `PyannoteModelCheck`, check for the first path's existence — mirrors `WhisperModelCheck` pattern in `checks.py`.

### Pattern 7: Diarized .txt Format (D-09)

```python
def build_diarized_txt(segments: list[dict], speaker_map: dict[int, str]) -> str:
    """Group consecutive segments from the same speaker into paragraphs.

    SPEAKER_00:
    Hello, welcome to the call.

    SPEAKER_01:
    Thanks for setting this up.
    """
    lines = []
    current_speaker = None
    current_texts = []

    for idx, seg in enumerate(segments):
        speaker = speaker_map.get(idx)
        text = seg["text"].strip()
        if not text:
            continue
        if speaker != current_speaker:
            if current_speaker is not None and current_texts:
                lines.append(f"{current_speaker}:")
                lines.append(" ".join(current_texts))
                lines.append("")
            current_speaker = speaker
            current_texts = [text]
        else:
            current_texts.append(text)

    # Flush final speaker block
    if current_speaker is not None and current_texts:
        lines.append(f"{current_speaker}:")
        lines.append(" ".join(current_texts))

    return "\n".join(lines)
```

### Pattern 8: Config Extension for HF Token

```python
# Extend Config dataclass — mirrors NotionConfig pattern
@dataclass
class HuggingFaceConfig:
    token: str | None = None

@dataclass
class Config:
    ...
    huggingface: HuggingFaceConfig = field(default_factory=HuggingFaceConfig)
```

Config.load() must be extended to parse `"huggingface": {"token": ...}` from JSON, with the same defensive `.get("huggingface", {})` pattern used for `notion` and `whisper`.

### Pattern 9: Diarized Transcript Metadata

The metadata JSON for a session should be extended (read-merge-write, per established project pattern):

```json
{
  "wav_path": "...",
  "transcript_path": "...",
  "srt_path": "transcripts/{stem}.srt",
  "diarization_succeeded": true,
  "diarized_transcript_path": "transcripts/{stem}.txt",
  "speaker_turns": [
    {"start": 0.2, "end": 1.5, "speaker": "SPEAKER_00"},
    {"start": 2.0, "end": 5.3, "speaker": "SPEAKER_01"}
  ]
}
```

When diarization fails: `"diarization_succeeded": false`, `"diarized_transcript_path": null`, `"speaker_turns": []`.

`meet summarize` reads `diarized_transcript_path` from metadata for session-based resolution; for latest-transcript resolution it checks if a diarized version exists by naming convention.

### Pattern 10: meet summarize Diarized Preference Logic

`summarize.py` currently resolves transcript by stem or latest mtime. With diarization:
- Session-based: read `metadata/{stem}.json`, use `diarized_transcript_path` if present and non-null, else fall back to `transcript_path`.
- Latest: same logic but discover via the latest metadata file with a transcript.

### Anti-Patterns to Avoid

- **Calling pipeline() without try/except:** pyannote raises various exceptions on network errors, auth failures, and unsupported audio formats. Always wrap in broad `except Exception` per D-08 pattern.
- **Not stripping segment text:** mlx-whisper segments often start with a space — always `.strip()` before writing to SRT or TXT.
- **Passing `language=None` to mlx_whisper:** Established project pitfall — omit the kwarg entirely for auto-detect (documented in STATE.md).
- **Mutating Config fields in the dataclass without extending Config.load():** The `load()` classmethod manually maps each section; a new `huggingface` section will silently be ignored without explicit handling.
- **Using `use_auth_token` vs `token` parameter:** For pyannote 3.x / speaker-diarization-3.1, use `use_auth_token=`. For newer 4.x community models, `token=` is correct. Since the project uses 3.1, always use `use_auth_token=`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Speaker diarization | Custom speaker clustering | `pyannote/speaker-diarization-3.1` | End-to-end neural pipeline; handles segmentation, embedding, clustering in one call |
| HF token validation | Manual HTTP request to huggingface.co | `HfApi().whoami(token=...)` | Official SDK; handles auth headers, error types, rate limits |
| SRT timestamp formatting | Custom time formatter | The 4-line formula (hours/minutes/secs/millis) | No library needed — it's arithmetic and string formatting |

**Key insight:** Speaker diarization is deceptively complex — segmentation, voice activity detection, speaker embedding, and agglomerative clustering are all distinct problems solved by the pyannote pipeline. The single-function call to `pipeline("audio.wav")` handles all of them.

---

## Common Pitfalls

### Pitfall 1: pyannote 4.x torch==2.8.0 Exact Pin
**What goes wrong:** Installing `pyannote.audio` without a version pin installs 4.0.4, which requires `torch==2.8.0` exactly. The project already has `torch==2.10.0` (installed as an mlx-whisper dependency). pip will either downgrade torch (breaking mlx-whisper) or refuse to install.
**Why it happens:** pyannote 4.0.2 introduced an exact pin to prevent segfaults in torchcodec.
**How to avoid:** Pin to `pyannote.audio==3.3.2` in pyproject.toml. Version 3.3.2 requires `torch>=2.0.0` — compatible with torch 2.10.0.
**Warning signs:** `pip install pyannote.audio` without a version resolves to 4.0.4 and shows torch downgrade notice.

### Pitfall 2: torchaudio Not Installed
**What goes wrong:** torchaudio is a required dependency of pyannote 3.3.2 but is not currently in the environment. If `pip install pyannote.audio==3.3.2` is run without torchaudio present, pyannote imports will fail at runtime with `ModuleNotFoundError: No module named 'torchaudio'`.
**Why it happens:** torchaudio must match the torch version. With torch 2.10.0, install `torchaudio` (pip resolves the correct version).
**How to avoid:** Install `torchaudio` as an explicit dependency in pyproject.toml alongside `pyannote.audio==3.3.2`. Wave 0 plan must include an environment validation step.
**Warning signs:** `PyannoteCheck` fails with ImportError at runtime even after pyannote.audio is installed.

### Pitfall 3: HuggingFace Model Requires User Conditions Acceptance
**What goes wrong:** Even with a valid HF token, `Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")` raises a 403/GatedRepoError if the user has not accepted the model's conditions on huggingface.co.
**Why it happens:** Both `pyannote/segmentation-3.0` and `pyannote/speaker-diarization-3.1` are gated — you must accept usage terms on the HuggingFace website before downloading.
**How to avoid:** `HuggingFaceTokenCheck` can only verify the token is valid (whoami succeeds) — it cannot verify that the user has accepted model conditions. `PyannoteModelCheck` checking local cache presence is the reliable signal. The setup instructions in README/doctor fix_suggestion must tell users to accept conditions at huggingface.co/pyannote/speaker-diarization-3.1 and huggingface.co/pyannote/segmentation-3.0.
**Warning signs:** Yellow warning during `meet transcribe` saying "Diarization failed" with a 403 in the exception message.

### Pitfall 4: Python 3.14 Compatibility of pyannote 3.3.2
**What goes wrong:** pyannote.audio 3.3.2 classifies Python 3.9–3.11 only. The project runs Python 3.14. This is a known compatibility risk. Dependencies like `speechbrain`, `lightning`, and `asteroid-filterbanks` may have their own Python version constraints.
**Why it happens:** 3.3.2 was released before Python 3.14. No explicit Python 3.14 breakage has been found in research, but it cannot be guaranteed without a test install.
**How to avoid:** Wave 0 must include an actual `pip install pyannote.audio==3.3.2` in the project venv and verify `import pyannote.audio` succeeds. If the install fails, the fallback is: document the failure, keep the graceful-degradation path (D-08) as the default behavior, and the user will always get `.txt`+`.srt` without speaker labels until the environment issue is resolved.
**Warning signs:** pip install raises `Requires-Python >=3.9` conflict for sub-dependencies; `PyannoteCheck` returns ERROR during `meet doctor`.

### Pitfall 5: summarize.py Resolving Wrong Transcript
**What goes wrong:** After diarization, the `.txt` file contains speaker-labeled text. `meet summarize` currently reads the latest `.txt` file. If both plain and diarized files existed in a previous design, the wrong one could be used. In this design, the diarized content **overwrites** the plain `.txt` — so the `.txt` is always the most enriched version available.
**Why it happens:** The decision (D-09 + D-11) means the `.txt` itself carries the diarized content when diarization succeeded. There is no separate `_diarized.txt` file.
**How to avoid:** The `diarized_transcript_path` field in metadata points to the same `.txt` path when diarization succeeded. `meet summarize` uses `diarized_transcript_path` from metadata when doing session-based lookup; for latest-transcript mode it reads the same latest `.txt`. No separate file path logic is needed — metadata field signals whether the content is diarized.
**Warning signs:** Summarize output does not contain speaker labels despite successful diarization.

### Pitfall 6: SRT Segment Index Must Start at 1
**What goes wrong:** SRT format requires sequential 1-based indices. If index starts at 0 or resets, some video players silently drop subtitles or fail to render them.
**Why it happens:** Off-by-one errors in `enumerate(segments)`.
**How to avoid:** Always use `enumerate(segments, start=1)` when generating SRT index numbers.
**Warning signs:** First subtitle not displaying; index=0 in SRT output.

### Pitfall 7: init.py _update_specific_fields Numbering Shift
**What goes wrong:** `_update_specific_fields()` in `init.py` maps field numbers (1–6) to config fields. Adding the HF token field shifts all subsequent numbers or breaks the existing menu if not handled carefully.
**Why it happens:** Sequential numbering in a manually-maintained list.
**How to avoid:** Add the HF token as field 7 (after existing field 6 "Storage path") or insert it between Notion fields (4) and Whisper language (5) and renumber. Either way, update both the `fields` list and the `if N in selected:` blocks atomically.
**Warning signs:** Selecting field 5 or 6 in the update menu applies to the wrong config key.

---

## Code Examples

### SRT Timestamp Formatting
```python
# Standard SRT HH:MM:SS,mmm format — verified against subtitle spec
def seconds_to_srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
```

### pyannote Pipeline Usage (3.x API)
```python
# Source: huggingface.co/pyannote/speaker-diarization-3.1 README (verified 2026-03-27)
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=hf_token,  # NOT token= — that's 4.x API
)
diarization = pipeline(str(wav_path))

speaker_turns = []
for turn, _, speaker in diarization.itertracks(yield_label=True):
    speaker_turns.append({
        "start": turn.start,
        "end": turn.end,
        "speaker": speaker,
    })
```

### HuggingFace Token Validation
```python
# Source: huggingface_hub 1.7.2 installed API (verified 2026-03-27)
from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

def check_hf_token(token: str) -> bool:
    """Returns True on valid token, raises HfHubHTTPError on auth failure."""
    api = HfApi()
    api.whoami(token=token)
    return True
```

### PyannoteModelCheck Cache Path
```python
# Mirrors WhisperModelCheck pattern in checks.py
HF_HUB_CACHE = Path.home() / ".cache" / "huggingface" / "hub"
PYANNOTE_DIARIZATION_CACHE = HF_HUB_CACHE / "models--pyannote--speaker-diarization-3.1"
PYANNOTE_SEGMENTATION_CACHE = HF_HUB_CACHE / "models--pyannote--segmentation-3.0"

class PyannoteModelCheck(HealthCheck):
    name = "Pyannote Model Cache"

    def check(self) -> CheckResult:
        if PYANNOTE_DIARIZATION_CACHE.exists():
            return CheckResult(status=CheckStatus.OK, message="pyannote model cached locally")
        return CheckResult(
            status=CheckStatus.WARNING,
            message="pyannote/speaker-diarization-3.1 not cached — will download on first use",
            fix_suggestion=(
                "Run: meet transcribe (auto-downloads). "
                "First, accept conditions at huggingface.co/pyannote/speaker-diarization-3.1 "
                "and huggingface.co/pyannote/segmentation-3.0"
            ),
        )
```

### init.py HF Token Collection (sequential Click prompt pattern)
```python
# Mirrors _collect_notion_credentials() in init.py
def _collect_hf_token() -> str | None:
    """Prompt for HuggingFace token (optional — user can skip)."""
    console.print("\nHuggingFace token is required for speaker diarization.")
    console.print("Create one at: https://hf.co/settings/tokens")
    console.print("Accept model conditions at:")
    console.print("  https://huggingface.co/pyannote/speaker-diarization-3.1")
    console.print("  https://huggingface.co/pyannote/segmentation-3.0")
    token = click.prompt(
        "HuggingFace access token (leave blank to skip)",
        default="",
        hide_input=True,
    )
    if not token:
        console.print("[yellow]Skipping HuggingFace token — speaker diarization will be disabled.[/yellow]")
        return None
    try:
        from huggingface_hub import HfApi
        HfApi().whoami(token=token)
        console.print("[green]HuggingFace token valid.[/green]")
    except Exception as e:
        console.print(f"[yellow]Could not verify token ({e}). Saving anyway.[/yellow]")
    return token
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual speaker labeling | pyannote/speaker-diarization-3.1 neural pipeline | 2023 | Single-function call for end-to-end diarization |
| torchaudio audio backend (pyannote 3.x) | torchcodec backend (pyannote 4.x) | pyannote 4.0.0 (Nov 2024) | 4.x adds exact torch pin — stick with 3.x for this project |
| `use_auth_token=` parameter | `token=` parameter | pyannote 4.x / newer HF models | Use `use_auth_token=` for speaker-diarization-3.1 |

**Deprecated/outdated:**
- pyannote.audio 4.0.x: Not deprecated, but the exact `torch==2.8.0` pin is actively complained about in GitHub issues (2026). For this project, 3.3.2 is more compatible.
- `use_auth_token=`: Not deprecated in pyannote 3.x context — still correct for speaker-diarization-3.1.

---

## Open Questions

1. **Python 3.14 install compatibility of pyannote.audio 3.3.2**
   - What we know: pyannote 3.3.2 classifies Python 3.9–3.11. The project runs Python 3.14. torch 2.10.0 already installed.
   - What's unclear: Whether speechbrain, lightning, asteroid-filterbanks all install without error on 3.14. No definitive answer found in research.
   - Recommendation: Wave 0 must include an actual install attempt in the project venv. If install fails, plan should document the failure path and rely on D-08 graceful degradation.

2. **torchaudio version compatibility with torch 2.10.0**
   - What we know: pyannote 3.3.2 requires `torchaudio>=2.2.0`. torch 2.10.0 is installed.
   - What's unclear: Whether the corresponding torchaudio 2.10.0 exists as a wheel for macOS arm64 Python 3.14.
   - Recommendation: Wave 0 install step: `pip install torchaudio` and verify it resolves cleanly against torch 2.10.0.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.14.3 | — |
| torch | pyannote.audio 3.3.2 (torch>=2.0.0) | ✓ | 2.10.0 | — |
| torchaudio | pyannote.audio 3.3.2 (torchaudio>=2.2.0) | ✗ | — | Must be installed; no fallback |
| huggingface-hub | HuggingFaceTokenCheck, Pipeline.from_pretrained | ✓ | 1.7.2 | — |
| pyannote.audio | Speaker diarization | ✗ | — | D-08 graceful degradation (warn, continue) |
| mlx-whisper | Transcription (existing) | ✓ | installed | — |
| pyannote/speaker-diarization-3.1 model | Diarization pipeline | ✗ (not cached) | — | Auto-downloads on first use |

**Missing dependencies with no fallback:**
- `torchaudio` — required by pyannote 3.3.2; must be installed alongside pyannote.audio.

**Missing dependencies with fallback (graceful degradation per D-08):**
- `pyannote.audio` — not installed; diarization skips with yellow warning, transcription continues normally.
- `pyannote/speaker-diarization-3.1` model — not cached; downloads on first use (WARNING in meet doctor).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured in pyproject.toml) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` testpaths = ["tests"] |
| Quick run command | `pytest tests/test_transcription.py tests/test_transcribe_command.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `seconds_to_srt_timestamp()` correct formatting | unit | `pytest tests/test_transcription.py::test_srt_timestamp_format -x` | ❌ Wave 0 |
| `generate_srt()` produces valid SRT structure | unit | `pytest tests/test_transcription.py::test_generate_srt -x` | ❌ Wave 0 |
| `generate_srt()` with speaker_map prefixes speaker tag | unit | `pytest tests/test_transcription.py::test_generate_srt_with_speakers -x` | ❌ Wave 0 |
| `assign_speakers_to_segments()` overlap algorithm | unit | `pytest tests/test_transcription.py::test_speaker_segment_merge -x` | ❌ Wave 0 |
| `build_diarized_txt()` groups consecutive speakers | unit | `pytest tests/test_transcription.py::test_diarized_txt_grouping -x` | ❌ Wave 0 |
| `transcribe_audio()` returns (text, segments) tuple | unit | `pytest tests/test_transcription.py::test_transcribe_returns_segments -x` | ❌ Wave 0 |
| `meet transcribe` writes `.srt` alongside `.txt` | integration | `pytest tests/test_transcribe_command.py::test_srt_file_created -x` | ❌ Wave 0 |
| `meet transcribe` diarization graceful fallback on missing HF token | integration | `pytest tests/test_transcribe_command.py::test_diarization_skips_without_hf_token -x` | ❌ Wave 0 |
| `meet transcribe` diarization graceful fallback on diarization error | integration | `pytest tests/test_transcribe_command.py::test_diarization_graceful_failure -x` | ❌ Wave 0 |
| `meet summarize` prefers diarized `.txt` via metadata | integration | `pytest tests/test_summarize_command.py::test_prefers_diarized_transcript -x` | ❌ Wave 0 |
| `PyannoteCheck` returns ERROR when pyannote not importable | unit | `pytest tests/test_checks.py::test_pyannote_check_error -x` | ❌ Wave 0 |
| `HuggingFaceTokenCheck` returns WARNING when token missing | unit | `pytest tests/test_checks.py::test_hf_token_check_warning_no_token -x` | ❌ Wave 0 |
| `PyannoteModelCheck` returns WARNING when model not cached | unit | `pytest tests/test_checks.py::test_pyannote_model_check_warning -x` | ❌ Wave 0 |
| `Config` round-trips `huggingface.token` field | unit | `pytest tests/test_config.py::test_config_hf_token_roundtrip -x` | ❌ Wave 0 |
| `meet init` wizard collects and saves HF token | integration | `pytest tests/test_init.py::test_init_collects_hf_token -x` | ❌ Wave 0 |
| `_update_specific_fields` includes HF token field | integration | `pytest tests/test_init.py::test_update_includes_hf_token -x` | ❌ Wave 0 |
| metadata JSON includes srt_path, diarization_succeeded fields | integration | `pytest tests/test_transcribe_command.py::test_metadata_includes_srt_fields -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_transcription.py tests/test_transcribe_command.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_checks.py` — new file covering PyannoteCheck, HuggingFaceTokenCheck, PyannoteModelCheck
- [ ] All test functions in the "File Exists? ❌ Wave 0" column above — extend existing files or create new ones

*(Existing test infrastructure: pytest already configured, conftest.py has tmp_path fixtures, CliRunner pattern established in test_transcribe_command.py — all reusable)*

---

## Sources

### Primary (HIGH confidence)
- pyannote/speaker-diarization-3.1 HuggingFace README (fetched 2026-03-27) — pipeline API, output format, itertracks usage, use_auth_token parameter
- pyannote_audio-3.3.2 wheel METADATA (extracted 2026-03-27) — exact dependency list: torch>=2.0.0, torchaudio>=2.2.0, speechbrain>=1.0.0, Requires-Python>=3.9
- huggingface_hub 1.7.2 installed API (verified 2026-03-27) — HfApi().whoami(token=...) signature
- mlx-whisper result["segments"] format — verified from existing transcription.py and project CONTEXT.md

### Secondary (MEDIUM confidence)
- PyPI pyannote-audio 4.0.4 page (fetched 2026-03-27) — latest version is 4.x; 3.x is last stable without torchcodec dep
- GitHub issues pyannote/pyannote-audio #1976 — exact torch==2.8.0 pin in 4.0.2 creates ecosystem conflict (2026)
- SRT format spec — multiple corroborating sources (AssemblyAI, DigitalOcean, Riverside) confirm HH:MM:SS,mmm format

### Tertiary (LOW confidence)
- pyannote-audio GitHub releases page — version history dates (3.3.1 Jun 2024, 4.0.x Nov-Feb 2024-2026)
- Python 3.14 compatibility of speechbrain/lightning — no official statement found; flagged as open question

---

## Project Constraints (from CLAUDE.md)

No CLAUDE.md found in this project. Constraints are inferred from STATE.md established decisions:

- Tech stack locked — do not suggest alternatives (mlx-whisper, not WhisperX; llama3.1:8b, not alternatives)
- WAV only — never .m4a
- Python 3.14 environment (venv installed via `pip install -e .`)
- HealthCheck ABC pattern: subclass must implement `check() -> CheckResult`, register in HealthCheckSuite
- Health check severity: ERROR when feature cannot work at all; WARNING when feature degrades gracefully
- Atomic state writes via `write_state()` (temp+replace pattern)
- Read-merge-write pattern for metadata JSON updates (never clobber existing fields)
- Graceful degradation pattern: warn in yellow, continue — mirrors Notion optional behavior

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — exact wheel metadata extracted, version confirmed
- Architecture: HIGH — all integration points identified from reading source files directly
- Pitfalls: HIGH (P1-P3, P6-P7) / MEDIUM (P4-P5) — P4 Python 3.14 compatibility unverified without install
- Environment: HIGH — directly probed with pip/python commands

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (pyannote-audio releases infrequently; 30-day window is safe)
