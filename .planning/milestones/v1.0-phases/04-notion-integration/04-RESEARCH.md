# Phase 4: Notion Integration - Research

**Researched:** 2026-03-22
**Domain:** Notion API (notion-client Python SDK), service layer extension, health check pattern
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Save Trigger**
- D-01: `meet summarize` auto-saves to Notion when token is configured — no `--save` flag required.
- D-02: If token is not configured, print a one-line dim hint after local save: `"Notion not configured — run meet init to set up."` Do not fail, do not silently skip.
- D-03: Terminal output after successful Notion push extends Phase 3 pattern: existing `"Notes saved: <path> (N words)"` line followed by `"Notion: https://notion.so/..."`. Two lines, not merged.
- D-04: Show a Rich spinner `"Saving to Notion..."` during the API call — consistent with Phase 2/3 spinner pattern.
- D-05: Notion URL is stored in session metadata JSON (`notion_url` field) so Phase 5's `meet list` can display it.

**Notion Target**
- D-06: Target is a parent page — each meeting note becomes a child page under it. No database rows, no structured properties. Simple to set up in Notion.
- D-07: Notion token and parent page ID are stored in `~/.config/meeting-notes/config.json` only. No env var fallback.

**Page Title**
- D-08: Title extracted from generated notes file — first `# Heading` (H1) found; fall back to first non-empty line if no H1 exists. No separate LLM call.
- D-09: If title extraction fails (empty or very short notes), fall back to timestamp: `"Meeting Notes — {YYYY-MM-DD HH:MM}"`.

**Notion Failure Handling**
- D-10: If Notion push fails after notes saved locally, warn and continue (exit 0). Notes are safe locally.
- D-11: Failure warning is a Rich `[yellow]` warning panel showing `"Notion upload failed: <reason>"` with local notes path.

**Doctor Check Severity**
- D-12: Two separate health checks: `NotionTokenCheck` (token set + API call succeeds) and `NotionDatabaseCheck` (parent page ID set + accessible).
- D-13: `NotionTokenCheck` → WARNING (not ERROR) when token missing. Notion is optional. Fix suggestion: `"Run: meet init to configure Notion."`
- D-14: `NotionDatabaseCheck` → WARNING when parent page ID missing or inaccessible. Same rationale as D-13.

### Claude's Discretion

- Block structure: implement headings as `heading_2` blocks and bullet lists as `bulleted_list_item` blocks. Split text at ≤1,900 chars per block (NOTION-04). Retry logic: exponential backoff on HTTP 429 (NOTION-05). These are architectural implementation details — follow ROADMAP pitfalls P14 and P15.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NOTION-01 | `meet summarize` creates a Notion page with structured notes after generation | notion-client `pages.create()` with `parent.page_id` and `children` blocks; D-01 (auto-trigger when configured) |
| NOTION-02 | Notion page title is extracted from notes file (first H1, fallback to first non-empty line, fallback to timestamp) | D-08/D-09 — no LLM call; pure string parsing of generated markdown |
| NOTION-03 | Page content uses template structure as Notion blocks (heading_2 + bulleted_list_item blocks per section) | Notion API block reference; heading_2 and bulleted_list_item block JSON structures documented below |
| NOTION-04 | Long text sections split into ≤1,900-char Notion blocks to avoid API limits | Notion API cap is 2,000 chars per rich_text object; 1,900 provides safe margin |
| NOTION-05 | All Notion API calls include retry with exponential backoff on HTTP 429 | Notion returns HTTP 429 + `Retry-After` header; notion-client raises `APIResponseError` with status 429 |
| NOTION-06 | Notion token and target page ID stored in `~/.config/meeting-notes/config.json` | D-07; `NotionConfig` dataclass to add to `core/config.py` following `AudioConfig`/`WhisperConfig` pattern |
| NOTION-07 | `meet summarize` stores created Notion page URL in session metadata JSON | D-05; `notion_url` field in `metadata/{stem}.json` via existing read-merge-write pattern |

</phase_requirements>

---

## Summary

Phase 4 adds a Notion push step to `meet summarize` and two new health checks to `meet doctor`. The integration is straightforward: convert the generated markdown notes into Notion block objects, call `notion_client.Client.pages.create()` with the parent page ID from config, and store the returned page URL in session metadata. The project already uses a pure-service-layer pattern (`services/llm.py`), a pluggable health-check system (`core/health_check.py` + `services/checks.py`), and atomic metadata reads/writes (`core/state.py`) — all three are directly reused.

The key technical constraints are two Notion API limits: rich text objects cap at 2,000 characters (use ≤1,900 for safety) and `create page` accepts up to 100 child blocks per call. For well-structured meeting notes these limits are unlikely to trigger in practice, but the text-splitting logic must be implemented regardless (NOTION-04). The 429 rate-limit is handled via `APIResponseError` from `notion-client`, which also carries a `Retry-After` header.

The `notion-client` package (v3.0.0 as of February 2026) is already installed system-wide (`pip show notion-client` confirms version 3.0.0 at `/opt/homebrew/lib/python3.14/site-packages`). It needs to be added to `pyproject.toml` dependencies. The package uses `httpx` (not `requests`) as its HTTP transport — no conflict with the existing `requests` dependency used by `services/llm.py`.

**Primary recommendation:** Implement `services/notion.py` as a pure-function module (no Click/Rich) mirroring `services/llm.py`. Add `NotionConfig` to `core/config.py`. Extend `cli/commands/summarize.py` with a post-generation Notion push block using `run_with_spinner`. Register two WARNING-severity checks in `services/checks.py`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| notion-client | 3.0.0 | Official Notion API Python SDK (sync + async) | Mandated by project (PROJECT.md). Wraps the REST API; handles auth headers, error types (`APIResponseError`), and pagination helpers. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.23.0 | HTTP transport (notion-client dependency) | Pulled in automatically by notion-client; no direct usage needed |
| rich | >=13.0 | Spinner and warning panel output | Already in pyproject.toml; reuse `run_with_spinner` from `services/transcription.py` |
| requests | >=2.28 | Used only by services/llm.py (Ollama) | Not used by Notion service — notion-client uses httpx internally |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| notion-client 3.0.0 (sync) | AsyncClient | Async adds complexity; this project is sync throughout. Use sync Client. |
| pages.create() with all blocks inline | pages.create() + append_block_children() | If notes exceed 100 blocks, a follow-up `blocks.children.append()` call is needed. Research shows 100-block limit applies only to the `children` array in one request. |

**Installation:**
```bash
pip install notion-client
```

Add to `pyproject.toml` dependencies:
```toml
"notion-client>=2.0",
```

**Version verification:** `pip show notion-client` returned version 3.0.0 (installed 2026-03-22 at system site-packages). PyPI confirms 3.0.0 released February 16, 2026.

---

## Architecture Patterns

### Recommended Project Structure

No new directories. New files follow the existing layout:

```
meeting_notes/
├── services/
│   ├── llm.py              # existing — model for notion.py
│   └── notion.py           # NEW: pure functions, no Click/Rich
├── core/
│   └── config.py           # EXTEND: add NotionConfig dataclass + Config.notion field
├── cli/
│   └── commands/
│       ├── summarize.py    # EXTEND: add Notion push block after generate_notes()
│       └── doctor.py       # EXTEND: register NotionTokenCheck, NotionDatabaseCheck
└── services/
    └── checks.py           # EXTEND: add NotionTokenCheck, NotionDatabaseCheck classes
```

### Pattern 1: NotionConfig Dataclass (mirrors AudioConfig)

**What:** Add `NotionConfig` to `core/config.py` with `token` and `parent_page_id` fields, both defaulting to `None`. Extend `Config` with a `notion` field. Update `Config.load()` to deserialize `notion` section.

**When to use:** Config required before any Notion API call; checked in both `summarize.py` and health checks.

**Example:**
```python
# Source: mirrors existing AudioConfig/WhisperConfig pattern in core/config.py
@dataclass
class NotionConfig:
    token: str | None = None
    parent_page_id: str | None = None

@dataclass
class Config:
    version: int = 1
    audio: AudioConfig = field(default_factory=AudioConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    notion: NotionConfig = field(default_factory=NotionConfig)
```

`Config.load()` extension:
```python
notion_data = data.get("notion", {})
notion = NotionConfig(
    token=notion_data.get("token", None),
    parent_page_id=notion_data.get("parent_page_id", None),
)
return cls(version=data.get("version", 1), audio=audio, whisper=whisper, notion=notion)
```

### Pattern 2: services/notion.py Structure (mirrors services/llm.py)

**What:** Pure functions, no Click/Rich imports. Single public entry point `create_page()`. Internal helpers for block building and text splitting.

**When to use:** Called from `summarize.py` after local notes are saved.

```python
# Source: mirrors services/llm.py structure; Notion API reference for block shapes
from notion_client import Client
from notion_client.errors import APIResponseError
import time

NOTION_API_VERSION = "2022-06-28"
MAX_RICH_TEXT_CHARS = 1900   # Notion hard limit is 2000; use 1900 for safety
MAX_CHILDREN_PER_REQUEST = 100  # Notion hard limit; split if notes have >100 blocks
RETRY_BASE_DELAY = 1.0       # seconds; doubles on each retry
MAX_RETRIES = 4

def create_page(token: str, parent_page_id: str, title: str, notes_markdown: str) -> str:
    """Create a Notion child page under parent_page_id.

    Returns the full page URL (https://notion.so/{page_id_no_hyphens}).
    Raises RuntimeError on non-recoverable API error.
    """
    client = Client(auth=token)
    blocks = _markdown_to_blocks(notes_markdown)
    # Only first 100 blocks go in create call; rest appended separately
    first_batch = blocks[:MAX_CHILDREN_PER_REQUEST]
    overflow = blocks[MAX_CHILDREN_PER_REQUEST:]

    response = _call_with_retry(
        client.pages.create,
        parent={"page_id": parent_page_id},
        properties={
            "title": [{"type": "text", "text": {"content": title}}]
        },
        children=first_batch,
    )
    page_id = response["id"]

    # Append overflow blocks in batches of 100
    for i in range(0, len(overflow), MAX_CHILDREN_PER_REQUEST):
        batch = overflow[i:i + MAX_CHILDREN_PER_REQUEST]
        _call_with_retry(
            client.blocks.children.append,
            block_id=page_id,
            children=batch,
        )

    # Return canonical URL
    page_id_clean = page_id.replace("-", "")
    return f"https://notion.so/{page_id_clean}"
```

### Pattern 3: Text Splitting and Block Building

**What:** Parse generated markdown into heading_2 and bulleted_list_item blocks. Split long text at ≤1,900 chars.

```python
# Source: Notion API reference /reference/block
def _split_text(text: str, max_chars: int = MAX_RICH_TEXT_CHARS) -> list[str]:
    """Split text into chunks of at most max_chars characters.

    Splits on whitespace boundary when possible.
    """
    if len(text) <= max_chars:
        return [text]
    chunks = []
    while len(text) > max_chars:
        split_at = text.rfind(" ", 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def _rich_text(content: str) -> list[dict]:
    return [{"type": "text", "text": {"content": content}}]


def _markdown_to_blocks(markdown: str) -> list[dict]:
    """Convert markdown to Notion block objects.

    Lines starting with '# ' become heading_2 blocks.
    Lines starting with '- ' or '* ' become bulleted_list_item blocks.
    All other non-empty lines become paragraph blocks.
    Long text is split into multiple blocks of the same type.
    """
    blocks = []
    for line in markdown.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("# "):
            text = line[2:].strip()
            block_type = "heading_2"
        elif line.startswith("## "):
            text = line[3:].strip()
            block_type = "heading_2"
        elif line.startswith("### "):
            text = line[4:].strip()
            block_type = "heading_2"
        elif line.startswith(("- ", "* ")):
            text = line[2:].strip()
            block_type = "bulleted_list_item"
        else:
            text = line
            block_type = "paragraph"

        for chunk in _split_text(text):
            blocks.append({
                "object": "block",
                "type": block_type,
                block_type: {"rich_text": _rich_text(chunk)},
            })
    return blocks
```

### Pattern 4: Exponential Backoff on HTTP 429

**What:** Wrap API calls in a retry loop. Notion returns HTTP 429 with a `Retry-After` header. `notion-client` raises `APIResponseError` with `.status` attribute.

```python
# Source: Notion API /reference/request-limits; notion-client error handling
def _call_with_retry(fn, *args, **kwargs):
    """Call fn(*args, **kwargs) with exponential backoff on HTTP 429."""
    delay = RETRY_BASE_DELAY
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except APIResponseError as exc:
            if exc.status == 429 and attempt < MAX_RETRIES:
                time.sleep(delay)
                delay *= 2
                continue
            raise  # non-429 or exhausted retries
```

### Pattern 5: Title Extraction from Markdown (D-08/D-09)

**What:** Pure string parsing — no LLM call.

```python
def extract_title(notes_markdown: str, fallback_timestamp: str) -> str:
    """Extract page title from generated notes.

    1. First line starting with '# ' (H1).
    2. First non-empty line if no H1.
    3. fallback_timestamp if notes are empty or too short.
    """
    lines = notes_markdown.splitlines()
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped
    return fallback_timestamp  # e.g. "Meeting Notes — 2026-03-22 14:30"
```

### Pattern 6: summarize.py Notion Push Block (extends existing command)

**What:** After local notes are saved and metadata written, add a Notion push block that respects D-02, D-03, D-04, D-10, D-11.

```python
# Source: mirrors existing run_with_spinner pattern in summarize.py
from meeting_notes.core.config import Config
from meeting_notes.core.storage import get_config_dir
# (at top of summarize.py alongside existing imports)
from meeting_notes.services.notion import create_page, extract_title

# In summarize() command, after write_state():
config_path = get_config_dir() / "config.json"
config = Config.load(config_path)

if config.notion.token is None or config.notion.parent_page_id is None:
    console.print("[dim]Notion not configured — run meet init to set up.[/dim]")
    notion_url = None
else:
    fallback_ts = datetime.now(timezone.utc).strftime("Meeting Notes — %Y-%m-%d %H:%M")
    title = extract_title(notes, fallback_ts)
    try:
        notion_url = run_with_spinner(
            lambda: create_page(
                token=config.notion.token,
                parent_page_id=config.notion.parent_page_id,
                title=title,
                notes_markdown=notes,
            ),
            "Saving to Notion...",
        )
        console.print(f"Notion: {notion_url}")
    except Exception as exc:
        from rich.panel import Panel
        console.print(Panel(
            f"[yellow]Notion upload failed: {exc}[/yellow]\nNotes saved locally: {notes_path}",
            style="yellow",
        ))
        notion_url = None

# Extend metadata with notion_url (None if skipped or failed)
existing = read_state(metadata_path) or {}
existing["notion_url"] = notion_url
write_state(metadata_path, existing)
```

Note: The metadata write for `notion_url` should happen after the Notion push attempt, as a second merge, not merged into the initial write (which already ran for Phase 3 fields). This is safe — `read_state` returns the file written above, and `write_state` replaces it atomically.

### Pattern 7: NotionTokenCheck and NotionDatabaseCheck (mirrors OllamaRunningCheck)

**What:** HealthCheck subclasses registered in `services/checks.py`. Both return WARNING (not ERROR) per D-13/D-14.

```python
# Source: mirrors OllamaRunningCheck pattern in services/checks.py
from notion_client import Client
from notion_client.errors import APIResponseError

class NotionTokenCheck(HealthCheck):
    """Verify Notion token is set in config and API call succeeds."""
    name = "Notion Token"

    def __init__(self, token: str | None) -> None:
        self.token = token

    def check(self) -> CheckResult:
        if not self.token:
            return CheckResult(
                status=CheckStatus.WARNING,
                message="Notion token not configured",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        try:
            client = Client(auth=self.token)
            client.users.me()  # lightweight auth validation call
            return CheckResult(status=CheckStatus.OK, message="Notion token valid")
        except APIResponseError as exc:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Notion token invalid: {exc}",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        except Exception as exc:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Notion API unreachable: {exc}",
                fix_suggestion="Check network or Notion token.",
            )


class NotionDatabaseCheck(HealthCheck):
    """Verify parent page ID is set and accessible."""
    name = "Notion Parent Page"

    def __init__(self, token: str | None, parent_page_id: str | None) -> None:
        self.token = token
        self.parent_page_id = parent_page_id

    def check(self) -> CheckResult:
        if not self.parent_page_id:
            return CheckResult(
                status=CheckStatus.WARNING,
                message="Notion parent page ID not configured",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        if not self.token:
            return CheckResult(
                status=CheckStatus.WARNING,
                message="Notion token not set — cannot verify parent page",
                fix_suggestion="Run: meet init to configure Notion.",
            )
        try:
            client = Client(auth=self.token)
            client.pages.retrieve(page_id=self.parent_page_id)
            return CheckResult(status=CheckStatus.OK, message="Notion parent page accessible")
        except APIResponseError as exc:
            return CheckResult(
                status=CheckStatus.WARNING,
                message=f"Notion parent page inaccessible: {exc}",
                fix_suggestion="Check page ID and that the integration has access.",
            )
```

**Register in doctor.py:**
```python
# Add to doctor.py imports
from meeting_notes.services.checks import NotionTokenCheck, NotionDatabaseCheck

# Add to suite.register() calls
suite.register(NotionTokenCheck(config.notion.token))
suite.register(NotionDatabaseCheck(config.notion.token, config.notion.parent_page_id))
```

### Anti-Patterns to Avoid

- **Passing `None` as token to `Client(auth=None)`:** notion-client v3 will make unauthenticated calls and get 401 errors rather than failing fast. Always guard with `if not self.token` before constructing the client.
- **Building one rich_text entry with full-length text:** Notion hard-caps rich_text content at 2,000 chars. Text longer than 1,900 chars MUST be split into multiple blocks (not multiple rich_text entries in one block — the array of rich_text objects also has a 100-element limit).
- **Passing more than 100 blocks in `children` during `pages.create()`:** The API returns HTTP 400. Use the overflow append pattern (Pattern 2 above).
- **Catching all exceptions silently in the service layer:** notion.py should let all errors bubble up. The caller (`summarize.py`) decides how to handle failures (D-10/D-11). Keep notion.py free of Rich/CLI concerns.
- **Storing token in env vars:** D-07 mandates `config.json` only. No `os.environ` lookup in the Notion service.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Notion API auth + headers | Custom HTTP client with bearer token | `notion_client.Client(auth=token)` | Handles auth header, API version header, error parsing, and logging out of the box |
| Error type detection | `if response.status_code == 429` | `APIResponseError.status` attribute | notion-client wraps all HTTP errors in `APIResponseError` with `.status`, `.code` (enum), and `.message` |
| Pagination helpers | Custom loop over `next_cursor` | `iterate_paginated_api()` / `collect_paginated_api()` | Not needed for this phase (we write, not read), but good to know |
| Rich text length validation | Custom char count check | Not needed — just use `_split_text()` helper with 1,900 limit | The API will 400 if you exceed 2,000; just always split proactively |

**Key insight:** notion-client is a thin, pass-through SDK — it maps Python kwargs directly to the REST API body/path/query. The Notion API reference IS the SDK documentation for request shapes.

---

## Common Pitfalls

### Pitfall 1: Rich Text 2,000-Char API Limit (P14)
**What goes wrong:** Notion returns HTTP 400 with "body failed validation: body.children[N].paragraph.rich_text[0].text.content.length should be ≤ 2000" for any rich_text content exceeding 2,000 characters.
**Why it happens:** Generated meeting notes can have long paragraphs. A single Action Items section might be 1,500 chars but the Decisions section 2,300 chars.
**How to avoid:** In `_split_text()`, use 1,900 chars (not 2,000) as the threshold. Split on last whitespace before the limit to avoid mid-word cuts.
**Warning signs:** HTTP 400 from `pages.create()` with "body failed validation" mentioning `.text.content.length`.

### Pitfall 2: HTTP 429 Rate Limiting Without Retry (P15)
**What goes wrong:** Notion enforces 3 requests/second per integration. Rapid consecutive calls (e.g., `create_page` immediately followed by `blocks.children.append`) can trigger 429.
**Why it happens:** The overflow append pattern makes multiple API calls in quick succession.
**How to avoid:** Use `_call_with_retry()` for every API call. Start with 1s delay, double on each retry, max 4 retries.
**Warning signs:** `APIResponseError` with `.status == 429`.

### Pitfall 3: 100-Block Limit on pages.create() children
**What goes wrong:** HTTP 400 "body.children.length should be ≤ 100" when notes generate more than 100 blocks.
**Why it happens:** Detailed meeting minutes templates can produce many bullet items.
**How to avoid:** Slice `blocks[:100]` for `pages.create()`, append the rest in batches via `blocks.children.append()`.
**Warning signs:** HTTP 400 with "children.length" in the error message.

### Pitfall 4: Metadata Double-Write Race
**What goes wrong:** Writing `notion_url` into metadata after the initial metadata write risks clobbering Phase 3 fields if the first write just completed.
**Why it happens:** `read_state` → `update` → `write_state` is not atomic relative to concurrent processes.
**How to avoid:** Use the established read-merge-write pattern: `existing = read_state(metadata_path) or {}` → `existing["notion_url"] = notion_url` → `write_state(metadata_path, existing)`. This reads the file that was just written (which includes Phase 3 fields) and merges, preserving all previous fields.
**Warning signs:** Missing `notes_path`, `template`, or `summarized_at` keys in metadata after Phase 4 runs.

### Pitfall 5: Config Load in summarize.py (config not yet loaded)
**What goes wrong:** Current `summarize.py` calls `ensure_dirs()` and `get_data_dir()` but never loads `Config` — there's no `config_path` or `config = Config.load()` in the existing code.
**Why it happens:** Phase 3 didn't need config (template comes from CLI flag, not config).
**How to avoid:** Add config loading at the top of `summarize()` command: `config_path = get_config_dir() / "config.json"` and `config = Config.load(config_path)`. This is safe — `Config.load()` returns defaults if the file doesn't exist.
**Warning signs:** `AttributeError: 'Config' object has no attribute 'notion'` if `NotionConfig` is missing from the dataclass.

### Pitfall 6: notion-client uses httpx, not requests
**What goes wrong:** Trying to catch `requests.exceptions.ConnectionError` from Notion API calls.
**Why it happens:** The rest of the project uses `requests`; it's natural to assume the same exception types.
**How to avoid:** Catch `notion_client.errors.APIResponseError` for API errors. For network failures, catch the generic `Exception` in the summarize.py wrapper (the service stays clean). The `run_with_spinner` pattern already re-raises any exception from the background thread.
**Warning signs:** Uncaught `httpx.ConnectError` or `httpx.TimeoutException` when Notion is unreachable.

---

## Code Examples

Verified patterns from official sources:

### Initialize notion-client (sync)
```python
# Source: https://github.com/ramnes/notion-sdk-py
from notion_client import Client

client = Client(auth="secret_...")
```

### Create child page under a parent page
```python
# Source: https://developers.notion.com/reference/post-page
response = client.pages.create(
    parent={"page_id": "parent-page-id-here"},
    properties={
        "title": [{"type": "text", "text": {"content": "My Meeting Notes"}}]
    },
    children=[
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "First bullet point"}}]
            },
        },
    ],
)
page_url = f"https://notion.so/{response['id'].replace('-', '')}"
```

### Append overflow blocks
```python
# Source: https://developers.notion.com/reference/patch-block-children
client.blocks.children.append(
    block_id=page_id,
    children=overflow_blocks,  # max 100 per call
)
```

### Retrieve a page (for NotionDatabaseCheck)
```python
# Source: https://developers.notion.com/reference/retrieve-a-page
client.pages.retrieve(page_id="parent-page-id")
```

### Validate token (for NotionTokenCheck)
```python
# Source: https://developers.notion.com/reference/get-self
client.users.me()
```

### Catch API errors
```python
# Source: https://github.com/ramnes/notion-sdk-py README
from notion_client.errors import APIResponseError

try:
    client.pages.create(...)
except APIResponseError as exc:
    if exc.status == 429:
        # rate limited — retry
        pass
    raise
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| notion-client | services/notion.py | Yes | 3.0.0 (system site-packages) | — |
| Python 3.14 | All | Yes | 3.14.3 | — |
| pytest | Tests | Yes | 9.0.2 | — |
| requests | services/llm.py (existing) | Yes | installed | — |

**Note:** `notion-client` is installed at the system level (`/opt/homebrew/lib/python3.14/site-packages`) but is NOT yet in `pyproject.toml`. It must be added as a project dependency: `"notion-client>=2.0"`. This ensures `pip install -e .` in a fresh venv will include it.

**Missing dependencies with no fallback:** None — notion-client is present.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths = ["tests"]) |
| Quick run command | `python3 -m pytest tests/test_notion_service.py tests/test_summarize_command.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NOTION-01 | `create_page()` calls `pages.create()` with correct parent and children | unit | `pytest tests/test_notion_service.py::test_create_page_calls_api -x` | Wave 0 |
| NOTION-02 | `extract_title()` returns H1 / fallback line / timestamp | unit | `pytest tests/test_notion_service.py::test_extract_title -x` | Wave 0 |
| NOTION-03 | `_markdown_to_blocks()` converts H1/H2/H3 to heading_2, bullets to bulleted_list_item | unit | `pytest tests/test_notion_service.py::test_markdown_to_blocks -x` | Wave 0 |
| NOTION-04 | `_split_text()` keeps chunks ≤1,900 chars; splits on whitespace | unit | `pytest tests/test_notion_service.py::test_split_text -x` | Wave 0 |
| NOTION-05 | `_call_with_retry()` retries on 429 with exponential delay; raises after max retries | unit | `pytest tests/test_notion_service.py::test_retry_on_429 -x` | Wave 0 |
| NOTION-06 | `NotionConfig` loads token+parent_page_id from config.json; missing fields default to None | unit | `pytest tests/test_config.py::test_notion_config_load -x` | Wave 0 (extend existing) |
| NOTION-07 | `summarize` command stores `notion_url` in metadata after successful push | unit | `pytest tests/test_summarize_command.py::test_summarize_stores_notion_url -x` | Wave 0 |
| D-02 | `summarize` prints dim hint when Notion not configured; does not fail | unit | `pytest tests/test_summarize_command.py::test_summarize_notion_not_configured -x` | Wave 0 |
| D-10 | `summarize` exits 0 and prints warning panel when Notion push fails | unit | `pytest tests/test_summarize_command.py::test_summarize_notion_failure_warns -x` | Wave 0 |
| D-12 | `NotionTokenCheck` returns WARNING when token missing | unit | `pytest tests/test_notion_checks.py::test_notion_token_check_missing -x` | Wave 0 |
| D-13 | `NotionTokenCheck` returns OK when token valid (mocked API) | unit | `pytest tests/test_notion_checks.py::test_notion_token_check_valid -x` | Wave 0 |
| D-14 | `NotionDatabaseCheck` returns WARNING when page_id missing | unit | `pytest tests/test_notion_checks.py::test_notion_database_check_missing -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_notion_service.py tests/test_notion_checks.py tests/test_summarize_command.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_notion_service.py` — covers NOTION-01 through NOTION-05, NOTION-07, D-02, D-10 (service layer + summarize command integration)
- [ ] `tests/test_notion_checks.py` — covers D-12, D-13, D-14 (NotionTokenCheck and NotionDatabaseCheck unit tests)
- [ ] `tests/test_config.py` — extend existing file to add `test_notion_config_load` (covers NOTION-06)
- [ ] `tests/test_summarize_command.py` — extend existing file with `test_summarize_notion_*` tests (covers D-02, D-10, NOTION-07)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| notion-client uses `requests` internally | notion-client 2.0+ uses `httpx` | v2.0 (2023) | Don't catch `requests.exceptions.*` from Notion calls |
| notion-client was unofficial | Official Notion-maintained SDK (notion-sdk-py) | 2021 | Use notion-client, not notion-py (unofficial, unmaintained) |

**Deprecated/outdated:**
- `notion-py` (jamalex): Unofficial, reverse-engineered, unmaintained. Do not use.
- `notion-client` < 2.0: Used `requests` transport; v3.0.0 (Feb 2026) uses httpx.

---

## Open Questions

1. **notion-client in venv vs. system site-packages**
   - What we know: `pip show notion-client` returned v3.0.0 at `/opt/homebrew/lib/python3.14/site-packages`. The project uses a venv for development.
   - What's unclear: Whether the dev venv also has notion-client installed, or if it's relying on system packages.
   - Recommendation: Add `"notion-client>=2.0"` to `pyproject.toml` and run `pip install -e .` to install it into the project venv. The plan's Wave 0 task should include this step.

2. **`meet init` does not yet prompt for Notion token/parent_page_id**
   - What we know: Current `init.py` only collects audio device indices (Phase 1). `config.json` has no `notion` section yet.
   - What's unclear: Whether `meet init` should be extended in Phase 4 to collect Notion credentials, or whether it ships as-is and users manually edit `config.json`.
   - Recommendation: Per D-07 (token stored in config.json) and D-02 (hint says "run meet init to set up"), Phase 4 should extend `meet init` to prompt for Notion token and parent page ID. If the CONTEXT.md is silent on this, this is Claude's discretion — do it in Phase 4.2 alongside the health checks.

---

## Sources

### Primary (HIGH confidence)
- Notion API reference — `/reference/request-limits` — rate limits (429), rich_text 2,000 char cap, 100 block limit per request, 1,000 block / 500KB payload limit
- Notion API reference — `/reference/block` — heading_2 and bulleted_list_item JSON structures
- Notion API reference — `/reference/post-page` — create page request body, parent.page_id structure, children blocks
- `pip show notion-client` — version 3.0.0 confirmed installed, February 2026 release
- PyPI notion-client — version 3.0.0 released February 16, 2026

### Secondary (MEDIUM confidence)
- https://github.com/ramnes/notion-sdk-py — SDK README confirming `Client(auth=token)` init, `APIResponseError` exception type, httpx transport
- https://pypi.org/project/notion-client/ — version history and dependency on httpx>=0.23.0

### Tertiary (LOW confidence)
- WebSearch results for 1,900-char split approach — confirmed against official docs; the 2,000 char limit is authoritative

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — notion-client v3.0.0 confirmed installed; PyPI and pip show agree
- Architecture: HIGH — all patterns derived from existing project code + official Notion API reference
- Pitfalls: HIGH — limits verified against official Notion API reference docs; httpx vs requests confirmed from PyPI page

**Research date:** 2026-03-22
**Valid until:** 2026-09-22 (Notion API is stable; notion-client follows SemVer)
