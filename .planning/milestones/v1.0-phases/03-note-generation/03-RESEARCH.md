# Phase 3: Note Generation - Research

**Researched:** 2026-03-22
**Domain:** Ollama HTTP API, LLM prompt engineering, Python HTTP with timeout, map-reduce text chunking
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `meeting` template sections (in order): Summary, Decisions, Action Items. Bullet lists per section. Default template.
- **D-02:** `minutes` template sections (in order): Attendees, Agenda, Discussion, Decisions, Action Items. More formal structure.
- **D-03:** `1on1` template sections (in exact order): **Project Work**, **Technical Overview**, **Team Collaboration**, **Feedback**, **Personal notes**.

  1on1 formatting rules (must be encoded in prompt):
  - Section titles exactly as above — bold using markdown, no colons after titles
  - One blank line after each section title
  - Paragraph format inside each section (no bullet points)
  - No line separators between sections
  - No extra commentary outside the requested structure
  - Professional, concise language; neutral tone suitable for performance documentation
  - Categorize information under the most contextually appropriate section (not multiple)
  - Do not invent information; do not output the category explanations

  Internal category definitions (for LLM context, not output):
  - Project Work → status, blockers, recent progress
  - Technical Overview → architectural decisions, technical issues, tools, systems, improvements
  - Team Collaboration → communication, alignment, cross-team support
  - Feedback → upward/downward feedback, self-reflection, coaching moments, improvement opportunities
  - Personal notes → interests outside of work, personal context, stories that help understand the person

- **D-04:** Every template prompt must include: "Base your notes ONLY on what is said in the transcript. Only include decisions and next steps if EXPLICITLY mentioned." No invented content.
- **D-05:** After successful generation, print the saved file path and word count only. No preview, no full content printed. Example: `Notes saved: ~/.local/share/meeting-notes/notes/20260322-abc12345-meeting.md (312 words)`.
- **D-06:** Session stem printed at end (same pattern as `meet transcribe`) so user can reference it in later commands.
- **D-07:** If notes already exist for the session + template combination, overwrite silently — no prompt, no warning.
- **D-08:** Phase 3 extends `metadata/{stem}.json` with: `notes_path`, `template`, `summarized_at`, `llm_model`.
- **D-09:** `OllamaRunningCheck` → ERROR when Ollama is not running. Fix suggestion: `Run: ollama serve`.
- **D-10:** `OllamaModelCheck` → ERROR when `llama3.1:8b` is not listed in `ollama list`. Fix suggestion: `Run: ollama pull llama3.1:8b`.
- **D-11:** Ollama HTTP API: `POST localhost:11434/api/generate` — no streaming (wait for full response).
- **D-12:** Configurable timeout, default 120s. On timeout: actionable error message.
- **D-13:** Token estimation: `len(transcript) / 4`. If >8,000 tokens, use map-reduce chunking: split into ~6,000-token chunks, summarize each, combine into final notes.
- **D-14:** `--template` flag accepts `meeting` (default), `minutes`, `1on1`.
- **D-15:** Notes saved to `~/.local/share/meeting-notes/notes/{stem}-{template}.md`.
- **D-16:** Rich spinner during LLM generation ("Generating notes...").
- **D-17:** `meet summarize` resolves session via `--session <stem>` or auto-resolves latest transcript.

### Claude's Discretion

None stated — all decisions were locked.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LLM-01 | `meet summarize` generates structured notes from transcript using Ollama llama3.1:8b via HTTP API (localhost:11434/api/generate) | Verified: Ollama running v0.18.2; `POST /api/generate` with `stream:false` returns `{"response": "..."}` — confirmed live |
| LLM-02 | Three templates: `meeting` (default), `minutes`, `1on1` — selected via `--template` flag | Locked structure from D-01 to D-03; implemented as plain text template files in `templates/` |
| LLM-03 | LLM prompt enforces strict grounding: "Base your notes ONLY on what is said in the transcript. Only include decisions and next steps if EXPLICITLY mentioned." | D-04 locks this text verbatim; must be in every template file |
| LLM-04 | Notes saved to `~/.local/share/meeting-notes/notes/{uuid}-{template}.md` | storage.py pattern confirmed; `notes/` already added to `ensure_dirs()` (confirmed in storage.py) |
| LLM-05 | All Ollama HTTP requests have configurable timeout (default: 120s); timeout shows actionable error | `urllib.request.urlopen(timeout=)` or `requests.post(timeout=)` — both work. Timeout raises `socket.timeout` / `requests.exceptions.Timeout` |
| LLM-06 | If transcript exceeds 8,000 tokens, chunk it, summarize each chunk, combine summaries (map-reduce) | Token estimate: `len(text) // 4`. Split into 6,000-token (~24,000 char) chunks. Summarize each. Combine via second LLM call |
| LLM-07 | `meet summarize` shows Rich spinner while waiting for LLM response | `run_with_spinner` from `services/transcription.py` is directly reusable — same threading + Live pattern |
</phase_requirements>

---

## Summary

Phase 3 adds `meet summarize`, which loads a transcript, calls Ollama llama3.1:8b over HTTP, and saves structured Markdown notes. The architecture precisely mirrors Phase 2: a pure-function service module (`services/llm.py`) wraps the HTTP API, and a Click command (`cli/commands/summarize.py`) handles session resolution, spinner, file I/O, and metadata extension. Health checks follow the established `HealthCheck` subclass pattern registered in `services/checks.py`.

The Ollama HTTP API has been verified live on this machine. Ollama v0.18.2 is running, `llama3.1:8b` is pulled and present. The `POST /api/generate` endpoint with `stream: false` returns a JSON object where `response` contains the full LLM output. No streaming parser is needed. The `requests` library (v2.32.5) is available in the project venv and is the simplest choice for HTTP with timeout.

The critical complexity in this phase is the 1on1 template prompt construction (must include category definitions as internal context but NOT output them) and the map-reduce chunking path for long transcripts. Both are fully specified in CONTEXT.md decisions. The `notes/` directory was already added to `ensure_dirs()` in `core/storage.py` — no change needed there.

**Primary recommendation:** Mirror `services/transcription.py` and `cli/commands/transcribe.py` exactly. Use `requests.post(timeout=120)` for the Ollama call. Reuse `run_with_spinner` directly from the transcription module.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.32.5 (installed) | HTTP POST to Ollama API with timeout | Already in venv; simpler timeout handling than urllib; `requests.exceptions.Timeout` is explicit |
| rich | >=13.0 (project dep) | Spinner during generation | Already used; `run_with_spinner` from transcription.py is reusable |
| click | >=8.1 (project dep) | CLI command with `--template` and `--session` options | Already used throughout project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| urllib.request | stdlib | Alternative to requests for Ollama HTTP | Only if `requests` not available — it is, so use requests |
| pathlib | stdlib | Notes file path construction | Already used everywhere |
| json | stdlib | Serialize Ollama request body and parse response | Already used |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests | urllib.request | urllib has clumsier timeout (socket.timeout, must wrap differently); requests is already in venv |
| requests | httpx | httpx is also in venv but async-first; synchronous blocking call is simpler and sufficient here |
| templates as .txt files | inline strings | File templates are more maintainable and follow established project pattern |

**Installation:**

No new packages required. `requests` is already installed in the project venv (v2.32.5). No `pyproject.toml` change needed for Phase 3 HTTP calls — but `requests` should be added as an explicit project dependency since it is now a direct requirement.

```bash
# Verify requests is available:
python3 -c "import requests; print(requests.__version__)"
```

**Version verification:**
- `requests` 2.32.5 — confirmed installed in project venv
- `ollama` 0.18.2 — confirmed running at localhost:11434
- `llama3.1:8b` model — confirmed present in `ollama list`

---

## Architecture Patterns

### Recommended Project Structure

New files for Phase 3:
```
meeting_notes/
├── services/
│   └── llm.py               # Pure functions: generate_notes(), estimate_tokens(), chunk_transcript()
├── cli/
│   └── commands/
│       └── summarize.py     # Click command: meet summarize
└── templates/
    ├── meeting.txt          # Prompt template for meeting notes
    ├── minutes.txt          # Prompt template for formal minutes
    └── 1on1.txt             # Prompt template for 1-on-1 notes

tests/
├── test_llm_service.py      # Unit tests: generate_notes(), chunking, token estimation
└── test_summarize_command.py # CLI integration tests: mirrors test_transcribe_command.py
```

### Pattern 1: LLM Service Module (mirrors services/transcription.py)

**What:** Pure functions, no Click/Rich imports. All Ollama HTTP logic isolated here.
**When to use:** Always — service layer must remain import-independent from CLI.

```python
# Source: mirrors meeting_notes/services/transcription.py pattern
import json
import urllib.error
from pathlib import Path
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_TIMEOUT = 120  # seconds, configurable
TOKEN_CHARS = 4       # chars per token estimate
CHUNK_TOKEN_LIMIT = 6000  # tokens per chunk
MAX_TOKENS_BEFORE_CHUNKING = 8000


def estimate_tokens(text: str) -> int:
    """Estimate token count as len(text) // 4."""
    return len(text) // TOKEN_CHARS


def generate_notes(prompt: str, timeout: int = OLLAMA_TIMEOUT) -> str:
    """POST to Ollama API and return the response text.

    Raises requests.exceptions.Timeout on timeout.
    Raises requests.exceptions.ConnectionError when Ollama is not running.
    Raises RuntimeError on non-200 response.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text}")
    data = response.json()
    return data["response"]
```

### Pattern 2: Session Resolution for Transcripts (mirrors transcribe.py)

**What:** Resolve transcript path from `--session` stem or latest transcript file.
**When to use:** `meet summarize` command startup.

```python
# Source: mirrors cli/commands/transcribe.py resolve_latest_wav / resolve_wav_by_stem pattern
def resolve_latest_transcript(transcripts_dir: Path) -> Path:
    """Return most recently modified .txt file. Raises FileNotFoundError if none."""
    txts = sorted(transcripts_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime)
    if not txts:
        raise FileNotFoundError("No transcripts found in transcripts directory.")
    return txts[-1]


def resolve_transcript_by_stem(transcripts_dir: Path, stem: str) -> Path:
    """Return transcript matching exact stem. Raises FileNotFoundError if not found."""
    candidate = transcripts_dir / f"{stem}.txt"
    if not candidate.exists():
        raise FileNotFoundError(f"No transcript found for session: {stem}")
    return candidate
```

### Pattern 3: Metadata Extension (using core/state.py)

**What:** Read existing `{stem}.json`, merge Phase 3 fields, write back atomically.
**When to use:** After successful note generation in `summarize.py`.

```python
# Source: core/state.py write_state / read_state pattern
from meeting_notes.core.state import read_state, write_state

metadata_path = metadata_dir / f"{stem}.json"
existing = read_state(metadata_path) or {}
existing.update({
    "notes_path": str(notes_path.resolve()),
    "template": template,
    "summarized_at": datetime.now(timezone.utc).isoformat(),
    "llm_model": OLLAMA_MODEL,
})
write_state(metadata_path, existing)
```

### Pattern 4: Map-Reduce Chunking

**What:** Split transcript into ~6,000-token (~24,000 char) chunks, summarize each independently, then combine summaries.
**When to use:** Only when `estimate_tokens(transcript) > 8000`.

```python
# Source: derived from D-13 decision; standard map-reduce LLM pattern
CHUNK_CHARS = CHUNK_TOKEN_LIMIT * TOKEN_CHARS  # 24000 chars

def chunk_transcript(text: str) -> list[str]:
    """Split text into ~6,000-token chunks (24,000 chars). Split on sentence boundary if possible."""
    chunks = []
    while len(text) > CHUNK_CHARS:
        # Try to split on nearest newline before CHUNK_CHARS
        split_at = text.rfind("\n", 0, CHUNK_CHARS)
        if split_at == -1:
            split_at = CHUNK_CHARS
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks
```

### Pattern 5: Health Check Registration (mirrors existing checks.py pattern)

**What:** `OllamaRunningCheck` and `OllamaModelCheck` subclass `HealthCheck`, registered in `services/checks.py`, imported in `cli/commands/doctor.py`.
**When to use:** Phase 3 health check addition.

```python
# Source: mirrors meeting_notes/services/checks.py MlxWhisperCheck pattern
import subprocess
import requests
from meeting_notes.core.health_check import CheckResult, CheckStatus, HealthCheck

class OllamaRunningCheck(HealthCheck):
    name = "Ollama Service"

    def check(self) -> CheckResult:
        try:
            resp = requests.get("http://localhost:11434", timeout=5)
            if resp.status_code == 200:
                return CheckResult(status=CheckStatus.OK, message="Ollama is running")
        except requests.exceptions.ConnectionError:
            pass
        return CheckResult(
            status=CheckStatus.ERROR,
            message="Ollama is not running",
            fix_suggestion="Run: ollama serve",
        )


class OllamaModelCheck(HealthCheck):
    name = "Ollama Model (llama3.1:8b)"

    def check(self) -> CheckResult:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10,
            )
            if "llama3.1:8b" in result.stdout:
                return CheckResult(status=CheckStatus.OK, message="llama3.1:8b model is available")
            return CheckResult(
                status=CheckStatus.ERROR,
                message="llama3.1:8b model not found in ollama list",
                fix_suggestion="Run: ollama pull llama3.1:8b",
            )
        except FileNotFoundError:
            return CheckResult(
                status=CheckStatus.ERROR,
                message="ollama CLI not found",
                fix_suggestion="Install Ollama: https://ollama.com",
            )
```

### Template File Structure

The `templates/` directory lives at `meeting_notes/templates/` (package resource) or at project root. Since these are read at runtime, using `Path(__file__).parent.parent / "templates"` from `services/llm.py` is the correct pattern for a package-relative path.

```
# meeting.txt — grounding rule + section specification
Base your notes ONLY on what is said in the transcript.
Only include decisions and next steps if EXPLICITLY mentioned.

Generate structured meeting notes with these sections:

## Summary
[bullet points]

## Decisions
[bullet points]

## Action Items
[bullet points]

Transcript:
{transcript}
```

The `1on1.txt` template must include category definitions as system context but instruct the model NOT to output them:

```
You are generating structured 1-on-1 meeting notes for performance documentation.

Internal category definitions (DO NOT output these):
- Project Work: status, blockers, recent progress
- Technical Overview: architectural decisions, technical issues, tools, systems, improvements
- Team Collaboration: communication, alignment, cross-team support
- Feedback: upward/downward feedback, self-reflection, coaching moments, improvement opportunities
- Personal notes: interests outside of work, personal context, stories that help understand the person

Base your notes ONLY on what is said in the transcript.
Only include decisions and next steps if EXPLICITLY mentioned.

Format rules:
- Use exactly these section titles in bold markdown: **Project Work**, **Technical Overview**, **Team Collaboration**, **Feedback**, **Personal notes**
- No colon after section titles
- One blank line after each section title
- Paragraph format inside each section (no bullet points)
- No line separators between sections
- No extra commentary outside the requested structure
- Professional, concise language; neutral tone suitable for performance documentation
- Categorize each item under exactly one section — do not repeat information

**Project Work**

**Technical Overview**

**Team Collaboration**

**Feedback**

**Personal notes**

Transcript:
{transcript}
```

### Anti-Patterns to Avoid

- **Passing `stream: true` to Ollama:** Will produce NDJSON chunks instead of a single response. Always set `stream: false`.
- **Using `json=` and `data=` together in requests.post:** Use only `json=payload` — this sets Content-Type automatically.
- **Catching bare `Exception` for timeout:** Catch `requests.exceptions.Timeout` specifically so other errors are not swallowed.
- **Building template strings in Python code:** Prompts belong in `.txt` files — keeps the LLM prompts auditable and editable without code changes.
- **Writing to `metadata/{stem}.json` without reading first:** Phase 2 wrote the initial fields. Phase 3 must read-then-merge, not overwrite the whole file.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP with timeout | Custom socket code | `requests.post(timeout=120)` | Timeout, connection errors, JSON decode all handled |
| Atomic file write | Custom temp+rename | `write_state()` from `core/state.py` | Already tested, POSIX rename is atomic |
| Background thread + spinner | New threading pattern | `run_with_spinner()` from `services/transcription.py` | Already tested, exception re-raise, Live elapsed timer |
| Session resolution | New glob pattern | Mirror `resolve_latest_wav` / `resolve_wav_by_stem` pattern | Same pattern proven in transcribe.py |

**Key insight:** Phase 3 is an additive phase — all hard infrastructure already exists. The value is in wiring it together correctly with the right prompt design.

---

## Common Pitfalls

### Pitfall 1: Ollama Not Running at `meet summarize` Time
**What goes wrong:** `requests.post()` raises `ConnectionError` with a cryptic socket message.
**Why it happens:** Ollama must be started manually with `ollama serve`. It does not auto-start on macOS.
**How to avoid:** Catch `requests.exceptions.ConnectionError` in `generate_notes()` and re-raise as a descriptive error: "Ollama is not running. Run: ollama serve". Also caught by `OllamaRunningCheck` in `meet doctor`.
**Warning signs:** `ConnectionRefusedError` or `ConnectionError` from requests.

### Pitfall 2: Map-Reduce Produces Fragmented Notes
**What goes wrong:** Each chunk gets summarized independently. If sections span chunk boundaries, bullet points for one topic appear in multiple chunk summaries.
**Why it happens:** Text split on char boundary doesn't respect semantic structure.
**How to avoid:** Split on `\n` boundary when possible (prefer newlines over mid-sentence splits). The combine step should use a second LLM call with a prompt like "Merge these partial summaries into one coherent set of notes in template format."
**Warning signs:** Duplicate action items, repeated decisions in final output.

### Pitfall 3: 1on1 Template Leaking Category Definitions into Output
**What goes wrong:** LLM outputs the internal category definitions as visible text in the final notes.
**Why it happens:** Without an explicit "DO NOT output these" instruction, the model may echo back the system context.
**How to avoid:** The 1on1 template must include the explicit instruction: "DO NOT output these" after the category definitions. Test with a short transcript that only touches one category.
**Warning signs:** Notes contain lines like "Project Work: status, blockers, recent progress" verbatim.

### Pitfall 4: Metadata Overwrite Erasing Phase 2 Fields
**What goes wrong:** `write_state(metadata_path, new_dict)` called with only Phase 3 fields — loses `wav_path`, `transcript_path`, `whisper_model` etc.
**Why it happens:** `write_state` replaces the entire file content.
**How to avoid:** Always `read_state(metadata_path) or {}` first, then `.update()` with Phase 3 fields, then `write_state()`.
**Warning signs:** `meet list` (Phase 5) can't find `transcript_path` for sessions that have been summarized.

### Pitfall 5: Notes File Path Uses UUID Instead of Stem
**What goes wrong:** Notes saved as `notes/{uuid}-meeting.md` but transcripts are `transcripts/{stem}.txt`. Cross-referencing breaks.
**Why it happens:** Inconsistent naming. The stem IS the naming convention (see Phase 2 D-10).
**How to avoid:** Notes path is `notes/{stem}-{template}.md` where stem comes from `transcript_path.stem`. The format is `{timestamp}-{short_uuid}` (e.g., `20260322-143000-abc12345`).
**Warning signs:** `meet list` can't find notes for a given stem.

### Pitfall 6: Timeout Exception Not Actionable
**What goes wrong:** Timeout after 120s exits with a raw traceback.
**Why it happens:** Not catching `requests.exceptions.Timeout` explicitly.
**How to avoid:** Catch `Timeout` in the CLI command (not in the service) and print: `[red]Error:[/red] Ollama timed out after 120s. The model may be overloaded — try again or increase timeout.`
**Warning signs:** Raw `ReadTimeout` traceback appears instead of formatted error message.

---

## Code Examples

### Verified: Ollama API Non-Streaming Call Shape
```python
# Verified live against ollama v0.18.2 on this machine
# POST http://localhost:11434/api/generate
# Request body:
{"model": "llama3.1:8b", "prompt": "...", "stream": false}

# Response body (confirmed fields):
{
  "model": "llama3.1:8b",
  "created_at": "2026-03-23T02:44:45.199302Z",
  "response": "...",        # ← full LLM output in this field
  "done": true,
  "done_reason": "stop",
  "total_duration": 605445333,
  "prompt_eval_count": 12,
  "eval_count": 23
}
# Extract: data["response"]
```

### Verified: requests.post with timeout
```python
import requests

def generate_notes(prompt: str, timeout: int = 120) -> str:
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.1:8b", "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()["response"]
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Ollama timed out after {timeout}s")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Ollama is not running. Run: ollama serve")
```

### Verified: ollama list output format
```
NAME               ID              SIZE      MODIFIED
llama3.1:8b        46e0c10c039e    4.9 GB    32 hours ago
llama3.2:latest    a80c4f17acd5    2.0 GB    34 hours ago
```
Detection: `"llama3.1:8b" in result.stdout` works. The model name appears at line start in the NAME column.

### Verified: run_with_spinner reuse pattern (from services/transcription.py)
```python
# run_with_spinner is importable from services/transcription.py
from meeting_notes.services.transcription import run_with_spinner

notes = run_with_spinner(
    lambda: generate_notes(prompt, timeout=120),
    "Generating notes..."
)
```

### Verified: notes/ directory already in ensure_dirs()
```python
# From core/storage.py (confirmed in code inspection):
def ensure_dirs() -> None:
    for d in [
        get_config_dir(),
        get_data_dir() / "recordings",
        get_data_dir() / "transcripts",
        get_data_dir() / "notes",      # ← already present
        get_data_dir() / "metadata",
    ]:
        d.mkdir(parents=True, exist_ok=True)
```
No change needed to `storage.py` — `notes/` is already included.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| ollama CLI | OllamaModelCheck | ✓ | 0.18.2 | — |
| Ollama HTTP service | LLM-01, all generate calls | ✓ | Running at localhost:11434 | — |
| llama3.1:8b model | LLM-01 | ✓ | Pulled (4.9 GB) | — |
| requests | HTTP to Ollama | ✓ | 2.32.5 | Use urllib.request (stdlib) |
| Python 3.14 | Runtime | ✓ | 3.14.3 | — |
| pytest | Testing | ✓ | 9.0.2 | — |

**Missing dependencies with no fallback:** None — all required dependencies are available.

**Missing dependencies with fallback:** None applicable.

**Note on pyproject.toml:** `requests` is currently NOT listed as a project dependency in `pyproject.toml`. Since Phase 3 uses it as a direct dependency, it must be added: `"requests>=2.28"`. This is a Wave 0 task.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` testpaths=["tests"] |
| Quick run command | `python3 -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q` |
| Full suite command | `python3 -m pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LLM-01 | `generate_notes()` POSTs to correct URL with correct payload | unit | `pytest tests/test_llm_service.py::test_generate_notes_calls_api -x` | ❌ Wave 0 |
| LLM-01 | `generate_notes()` returns `response` field from JSON | unit | `pytest tests/test_llm_service.py::test_generate_notes_returns_response -x` | ❌ Wave 0 |
| LLM-02 | `meet summarize --template meeting` uses meeting template | unit | `pytest tests/test_summarize_command.py::test_template_flag_meeting -x` | ❌ Wave 0 |
| LLM-02 | `meet summarize --template 1on1` uses 1on1 template | unit | `pytest tests/test_summarize_command.py::test_template_flag_1on1 -x` | ❌ Wave 0 |
| LLM-03 | Each template file contains the grounding rule verbatim | unit | `pytest tests/test_llm_service.py::test_templates_contain_grounding_rule -x` | ❌ Wave 0 |
| LLM-04 | Notes file saved to `notes/{stem}-{template}.md` | unit | `pytest tests/test_summarize_command.py::test_notes_saved_correct_path -x` | ❌ Wave 0 |
| LLM-05 | `generate_notes()` raises `TimeoutError` on Timeout | unit | `pytest tests/test_llm_service.py::test_generate_notes_timeout -x` | ❌ Wave 0 |
| LLM-05 | CLI prints actionable error on timeout | unit | `pytest tests/test_summarize_command.py::test_timeout_error_message -x` | ❌ Wave 0 |
| LLM-06 | `estimate_tokens()` returns `len(text) // 4` | unit | `pytest tests/test_llm_service.py::test_estimate_tokens -x` | ❌ Wave 0 |
| LLM-06 | `chunk_transcript()` splits into ≤6000-token chunks | unit | `pytest tests/test_llm_service.py::test_chunk_transcript -x` | ❌ Wave 0 |
| LLM-06 | Transcript >8000 tokens triggers chunked path | unit | `pytest tests/test_summarize_command.py::test_long_transcript_uses_chunking -x` | ❌ Wave 0 |
| LLM-07 | Spinner displayed during generation | unit | `pytest tests/test_summarize_command.py::test_spinner_shown -x` | ❌ Wave 0 |
| D-05 | Output shows file path and word count | unit | `pytest tests/test_summarize_command.py::test_output_shows_path_and_word_count -x` | ❌ Wave 0 |
| D-06 | Session stem printed after generation | unit | `pytest tests/test_summarize_command.py::test_session_stem_displayed -x` | ❌ Wave 0 |
| D-07 | Existing notes overwritten silently | unit | `pytest tests/test_summarize_command.py::test_existing_notes_overwritten -x` | ❌ Wave 0 |
| D-08 | Metadata extended with notes_path, template, summarized_at, llm_model | unit | `pytest tests/test_summarize_command.py::test_metadata_extended -x` | ❌ Wave 0 |
| D-09/D-10 | OllamaRunningCheck returns ERROR when not running | unit | `pytest tests/test_health_check.py::test_ollama_running_check_error -x` | ❌ Wave 0 |
| D-09/D-10 | OllamaModelCheck returns ERROR when model missing | unit | `pytest tests/test_health_check.py::test_ollama_model_check_error -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_llm_service.py tests/test_summarize_command.py -x -q`
- **Per wave merge:** `python3 -m pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_llm_service.py` — covers LLM-01, LLM-03, LLM-05, LLM-06 (token estimation, chunking)
- [ ] `tests/test_summarize_command.py` — covers LLM-02, LLM-04, LLM-06 (integration), LLM-07, D-05 to D-08
- [ ] Additional test cases in `tests/test_health_check.py` for OllamaRunningCheck and OllamaModelCheck (D-09, D-10)
- [ ] `requests` added to `pyproject.toml` dependencies: `"requests>=2.28"`

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ollama streaming (NDJSON chunks) | `stream: false` (wait for full response) | Always supported | Simpler parsing — single JSON blob |
| Custom HTTP timeout via socket | `requests.post(timeout=N)` | N/A | Clean exception hierarchy |

**Deprecated/outdated:**
- Ollama `/api/chat` endpoint: This is for multi-turn chat. Phase 3 uses `/api/generate` for single-turn prompts (locked by D-11).

---

## Open Questions

1. **Template file location within the package**
   - What we know: No existing precedent in this codebase for bundled data files
   - What's unclear: Should templates live at `meeting_notes/templates/` (package) or `templates/` (project root)?
   - Recommendation: Use `meeting_notes/templates/` so they are included in the installed package. Load via `Path(__file__).parent.parent / "templates" / f"{template}.txt"` from `services/llm.py`.

2. **`requests` as project dependency**
   - What we know: `requests` is available in the dev venv but not in `pyproject.toml` dependencies
   - What's unclear: Whether mlx-whisper transitively pulls in `requests` (making it implicitly available) or it must be explicit
   - Recommendation: Add `"requests>=2.28"` to `pyproject.toml` dependencies in Wave 0. Explicit is better than implicit.

3. **Map-reduce combine prompt**
   - What we know: D-13 specifies the chunking strategy but not the combine prompt
   - What's unclear: Should the combine step reuse the same template prompt, or use a dedicated "merge summaries" prompt?
   - Recommendation: Use a dedicated combine prompt: "These are partial summaries of sections of a single meeting. Merge them into one coherent set of notes with sections [template-specific section list]. Remove duplicates. Preserve all unique information."

---

## Sources

### Primary (HIGH confidence)
- Live Ollama API test (localhost:11434) — verified request/response shape for `POST /api/generate` with `stream: false`
- Code inspection: `meeting_notes/services/transcription.py` — `run_with_spinner` pattern
- Code inspection: `meeting_notes/cli/commands/transcribe.py` — session resolution, metadata write pattern
- Code inspection: `meeting_notes/core/state.py` — `read_state` / `write_state` atomic write
- Code inspection: `meeting_notes/core/storage.py` — `ensure_dirs()` already includes `notes/`
- Code inspection: `meeting_notes/services/checks.py` — HealthCheck subclass registration pattern
- Code inspection: `meeting_notes/cli/commands/doctor.py` — how to register new checks
- Code inspection: `pyproject.toml` — project dependencies, missing `requests`
- Live `ollama list` output — confirmed `llama3.1:8b` present
- Live pip list — confirmed `requests` 2.32.5 and `httpx` 0.28.1 in project venv

### Secondary (MEDIUM confidence)
- 03-CONTEXT.md decisions D-01 to D-17 — locked specifications from user discussion

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified live; all libraries confirmed installed
- Architecture: HIGH — mirrors directly from existing codebase patterns
- API shape: HIGH — verified live against running Ollama instance
- Pitfalls: HIGH — derived from code inspection + decision constraints
- Template prompt design: MEDIUM — 1on1 format is highly specific; effectiveness depends on model behavior (hard to verify without runtime testing)

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (Ollama API is stable; llama3.1:8b model present)
