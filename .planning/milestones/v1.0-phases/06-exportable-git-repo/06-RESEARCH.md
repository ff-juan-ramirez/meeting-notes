# Phase 6: Exportable Git Repo - Research

**Researched:** 2026-03-23
**Domain:** Python CLI packaging, Click option extension, Rich interactive prompts, README documentation, git hygiene
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**meet doctor --verbose (D-01 to D-06)**
- D-01: `--verbose` is a `meet doctor`-only flag. Added as `@click.option('--verbose', is_flag=True)` on the `doctor` command.
- D-02: Verbose detail lines appear inline under each check line, indented with extra spaces — consistent with the existing `fix_suggestion` display pattern (`"    [dim]Detail: ...[/dim]"`).
- D-03: Only checks that have meaningful extra data emit verbose lines. Checks with no meaningful runtime data (e.g. OpenaiWhisperConflictCheck) skip verbose output.
- D-04: Fix suggestions continue to appear only on WARNING or ERROR — even in `--verbose` mode.
- D-05: Per-check verbose detail content (see CONTEXT.md for full list per check class).
- D-06: `--verbose` is compatible with `--quiet` — quiet wins. If both flags are passed, quiet suppresses all output including verbose lines.

**meet init Full Wizard (D-07 to D-13)**
- D-07: `meet init` collects Notion token + database/page ID interactively as required fields.
- D-08: Existing config detection: prompt `"Config already exists. (R)econfigure everything from scratch, or (U)pdate specific fields?"`.
- D-09: Update-specific-fields flow: numbered menu showing all config fields with current values (Notion token masked). Only selected fields are re-prompted.
- D-10: Audio device detection: parse avfoundation device list into a numbered menu. User selects by number.
- D-11: Notion token validation: make `GET /users/me` call before writing config. Show clear error if invalid; prompt to re-enter.
- D-12: `meet init` runs `meet doctor` inline at the end using `HealthCheckSuite` directly (no subprocess call). Without `--verbose`.
- D-13: Test recording for mic permission (SETUP-02) is preserved — runs after config write, before inline doctor check.

**README (D-14 to D-15)**
- D-14: Full reference document with: What it is, Prerequisites (with install commands), Audio MIDI Setup walkthrough, Installation, Quickstart workflow, all 6 commands with flags and examples, Config file format, Troubleshooting section.
- D-15: Audio MIDI Setup section uses step-by-step numbered instructions plus an ASCII art diagram showing signal routing.

**Packaging & Distribution (D-16 to D-19)**
- D-16: `python_requires` stays `">=3.11,<3.15"` (current value — already correct).
- D-17: Dependency pinning stays as minimum versions (e.g., `click>=8.1`). No exact pinning.
- D-18: After Phase 6 implementation, run `/gsd:pr-branch` to create a clean code-only branch filtering `.planning/` doc commits.
- D-19: `.gitignore` additions: `recordings/`, `transcripts/`, `notes/`, `.env` (defensive patterns for user data dirs).

### Claude's Discretion

- Exact formatting/layout of the `meet init` wizard prompts (Rich panels, progress indicators)
- README section ordering and prose style
- Whether to add `LICENSE` file (MIT or similar)
- ASCII diagram style and detail level in README

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 6 finalizes the project for distribution. The three primary deliverables are: (1) extending `meet doctor` with a `--verbose` flag that adds inline detail lines per check, (2) rewriting `meet init` as a full interactive wizard with device selection, Notion credential validation, reconfigure/update flows, and an inline doctor run at the end, and (3) writing `README.md` and cleaning up `.gitignore`.

The implementation is largely an extension of existing patterns already established in prior phases. No new libraries are needed. The `checks.py` file needs a `verbose_detail()` method (or equivalent) added to each check class. The `doctor.py` command needs `--verbose` wiring. The `init.py` command needs a near-complete rewrite. All patterns — `console`, `ctx.obj`, `config.save()`, `HealthCheckSuite.run_all()` — are already in place.

The most nuanced implementation challenge is the `meet init` wizard: parsing the ffmpeg device list into a numbered menu, collecting Notion credentials with live API validation, handling the reconfigure vs. update-specific-fields branching, and running the inline doctor check at the end. All of this builds on stable, already-installed dependencies (Rich, Click, notion-client).

**Primary recommendation:** Extend existing check classes with `verbose_detail() -> str | None`, add `--verbose` to `doctor.py`, rewrite `init.py` as a staged wizard using existing `console` and `Config` patterns, write README, update `.gitignore`.

---

## Standard Stack

### Core (all already installed — no new dependencies needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.3.1 | CLI framework, `@click.option`, `click.prompt`, `click.confirm` | Already the CLI layer; adds `--verbose` as `is_flag=True` |
| rich | 14.3.3 | Terminal output, `console.print`, Rich markup | Already the UI layer; panels, dim text, color all used |
| notion-client | 3.0.0 | Notion API, `client.users.me()` for token validation | Already a dependency; token validation reuses same client |

### No New Dependencies

This phase adds NO new packages to `pyproject.toml`. All required functionality is covered by the existing dependency set:
- `click.prompt()` — interactive prompts with validation
- `rich.console.Console.print()` — all output
- `notion_client.Client(auth=token).users.me()` — token validation
- `HealthCheckSuite.run_all()` — inline doctor check
- `Config.save()` — atomic config write

**Version verification:** Confirmed via `importlib.metadata` in the project venv.

---

## Architecture Patterns

### Pattern 1: Adding verbose_detail to HealthCheck Classes

**What:** Each check class gains a method that returns optional detail text when `--verbose` is active. Colocating verbose logic with check logic avoids doctor.py knowing check internals.

**When to use:** For all check classes that have meaningful runtime data (D-05 specifics).

**Approach:** Add `verbose_detail(config: Config | None = None) -> str | None` to `HealthCheck` base class (returns `None` by default). Subclasses override when they have useful data. The base class default means `OpenaiWhisperConflictCheck` requires no override (D-03).

```python
# Source: existing pattern in health_check.py — extend base class

class HealthCheck(ABC):
    name: str = "Unnamed Check"

    @abstractmethod
    def check(self) -> CheckResult: ...

    def verbose_detail(self) -> str | None:
        """Override to return inline detail text for --verbose mode."""
        return None
```

```python
# Source: existing checks.py pattern — BlackHoleCheck example
class BlackHoleCheck(HealthCheck):
    def verbose_detail(self) -> str | None:
        devices = _parse_audio_devices()
        device_name = devices.get(self.device_index)
        if device_name:
            # Channel count not easily available from ffmpeg device list
            return f"{device_name}"
        return None
```

### Pattern 2: doctor.py --verbose wiring

**What:** Pass `verbose` bool through to output loop. After each check result line, if `verbose=True` and `check.verbose_detail()` returns a string, print it indented.

**Current doctor.py output loop:**
```python
for check, result in results:
    icon = STATUS_ICONS[result.status]
    if not quiet:
        console.print(f"  {icon} {check.name}: {result.message}")
        if result.fix_suggestion:
            console.print(f"    [dim]Fix: {result.fix_suggestion}[/dim]")
```

**Extended loop with verbose:**
```python
for check, result in results:
    icon = STATUS_ICONS[result.status]
    if not quiet:
        console.print(f"  {icon} {check.name}: {result.message}")
        if verbose:
            detail = check.verbose_detail()
            if detail:
                console.print(f"    [dim]{detail}[/dim]")
        if result.fix_suggestion and result.status != CheckStatus.OK:
            console.print(f"    [dim]Fix: {result.fix_suggestion}[/dim]")
```

Note: D-04 says fix suggestions appear only on WARNING or ERROR. Current code already has `if result.fix_suggestion:` without status check — this phase is the right time to enforce the `status != OK` guard.

### Pattern 3: meet init Wizard Flow

**What:** Staged interactive wizard with branching for reconfigure vs. update-specific-fields.

**Wizard stages (in order):**
1. Check for existing config.json
2. If exists: prompt R/U choice
   - R (reconfigure): proceed through full wizard from step 3
   - U (update): show numbered field menu, re-prompt selected fields only
3. Detect ffmpeg audio devices → parse with existing `_parse_audio_devices()` → numbered menu
4. User selects system audio device (BlackHole) and microphone by number
5. Prompt Notion token → validate with `client.users.me()` → re-prompt on failure
6. Prompt Notion database/page ID
7. Build Config, call `config.save(config_path)`
8. Test recording (existing SETUP-02 behavior — 1s ffmpeg run)
9. Run `HealthCheckSuite.run_all()` inline — display results in doctor output style
10. Print completion message

**Key implementation detail — device menu:**
```python
# Source: existing _parse_audio_devices() in checks.py — already parses into dict
devices = _parse_audio_devices()  # {0: "MacBook Air Microphone", 1: "BlackHole 2ch", ...}
for idx, name in sorted(devices.items()):
    console.print(f"  [{idx}] {name}")
system_idx = click.prompt("Select system audio device index (BlackHole)", type=int, default=1)
```

**Key implementation detail — Notion token validation loop:**
```python
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

while True:
    token = click.prompt("Notion integration token", hide_input=True)
    try:
        client = NotionClient(auth=token)
        client.users.me()
        break  # valid
    except APIResponseError:
        console.print("[red]Token invalid. Please check and try again.[/red]")
    except Exception as e:
        console.print(f"[yellow]Could not verify token: {e}. Saving anyway.[/yellow]")
        break
```

**Key implementation detail — inline doctor run:**
```python
# Source: health_check.py HealthCheckSuite.run_all() — already returns (check, result) pairs
# Uses same STATUS_ICONS and output pattern as doctor.py

from meeting_notes.core.health_check import CheckStatus, HealthCheckSuite
from meeting_notes.cli.commands.doctor import STATUS_ICONS  # or redefine locally

suite = HealthCheckSuite()
suite.register(PythonVersionCheck())
# ... register all checks with config values ...
results = suite.run_all()
for check, result in results:
    icon = STATUS_ICONS[result.status]
    console.print(f"  {icon} {check.name}: {result.message}")
    if result.fix_suggestion and result.status != CheckStatus.OK:
        console.print(f"    [dim]Fix: {result.fix_suggestion}[/dim]")
```

### Pattern 4: Update-Specific-Fields Menu

**What:** Show all config fields with current values; user types comma-separated numbers (or single number) to select which to re-enter.

**Config fields to expose:**
1. System audio device index (current: `config.audio.system_device_index`)
2. Microphone device index (current: `config.audio.microphone_device_index`)
3. Notion token (current: masked `ntn_***...abc` or `[not set]`)
4. Notion database/page ID (current: `config.notion.parent_page_id` or `[not set]`)
5. Whisper language (current: `config.whisper.language` or `auto`)

**Token masking pattern:**
```python
def mask_token(token: str | None) -> str:
    if not token:
        return "[not set]"
    if len(token) <= 8:
        return "***"
    return token[:4] + "***" + token[-3:]
```

### Anti-Patterns to Avoid

- **Subprocess call to `meet doctor` from `meet init`:** D-12 locks this as a direct `HealthCheckSuite` call — no subprocess. Subprocess would fail if the package isn't on PATH at that moment.
- **Importing from doctor.py for STATUS_ICONS:** Creates circular import risk. Either import `STATUS_ICONS` from `doctor.py` (it's a module-level dict — safe) or redefine the three-entry dict in `init.py`.
- **Prompting Notion fields before audio fields:** Audio device selection comes first in the wizard (CONTEXT.md ordering). Notion comes after.
- **Writing config before Notion token is validated:** Token validation loop must complete (or user explicitly skips) before calling `config.save()`.

### Recommended Project Structure (no changes)

The existing structure is complete. Phase 6 modifies:
```
meeting_notes/
├── cli/
│   └── commands/
│       ├── doctor.py         # Add --verbose flag and detail output
│       └── init.py           # Full wizard rewrite
├── core/
│   └── health_check.py       # Add verbose_detail() to HealthCheck base (optional)
├── services/
│   └── checks.py             # Add verbose_detail() per check class (D-05)
.gitignore                    # Append user data patterns
README.md                     # New file
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Interactive prompts with defaults | Custom stdin reading | `click.prompt(default=...)` | Handles echo suppression, type coercion, keyboard interrupt |
| Masked password input | Custom terminal control | `click.prompt(hide_input=True)` | Hides typing in terminal, handles TTY edge cases |
| API call to validate Notion token | Custom HTTP | `notion_client.Client.users.me()` | Already a dep; raises `APIResponseError` with status code |
| Audio device list parsing | Re-implement | `_parse_audio_devices()` in `checks.py` | Already exists and is tested |
| Doctor output in init | Subprocess or copy-paste | Import `HealthCheckSuite`, `STATUS_ICONS` | Reuse existing logic directly per D-12 |

**Key insight:** Every primitive needed for this phase (device parsing, token validation, health checks, config save, Rich output) already exists in the codebase. Phase 6 is orchestration, not new infrastructure.

---

## Common Pitfalls

### Pitfall 1: Notion token validation — wrong exception type
**What goes wrong:** Catching `Exception` broadly hides whether a token is invalid vs. the network is down. The distinction matters for the retry loop.
**Why it happens:** `notion_client.errors.APIResponseError` is the token-invalid signal; network issues raise requests exceptions.
**How to avoid:** Catch `APIResponseError` first (invalid token — prompt again). Catch broader `Exception` second (network issue — offer to save anyway with a warning).
**Warning signs:** Test with a known-invalid token and verify the re-prompt fires.

### Pitfall 2: Circular import — doctor.py STATUS_ICONS
**What goes wrong:** `init.py` imports `STATUS_ICONS` from `doctor.py`; `doctor.py` imports from `checks.py`; if `checks.py` ever imports from `init.py`, circular import.
**Why it happens:** Sharing a small constant dict via import.
**How to avoid:** Either (a) define `STATUS_ICONS` in a shared location (e.g., `cli/ui.py` or a new `cli/constants.py`), or (b) redefine it inline in `init.py` — it's only 3 entries.

### Pitfall 3: verbose_detail() called before check() runs
**What goes wrong:** Some verbose detail depends on data fetched during `check()` (e.g., `BlackHoleCheck` calls `_parse_audio_devices()` in both). Calling `verbose_detail()` independently doubles the subprocess calls.
**Why it happens:** Separating check logic from verbose detail logic.
**How to avoid:** Option A — `verbose_detail()` can call `_parse_audio_devices()` again (cheap, fast). Option B — `check()` stores parsed data on `self` as a side effect for `verbose_detail()` to reuse (caching). Given the small cost of the ffmpeg probe, Option A is simpler.

### Pitfall 4: ffmpeg device list parsing — index vs. display choice
**What goes wrong:** User sees menu index 0, 1, 2 but types a different number because they misread the output.
**Why it happens:** The numbered menu and the actual device indices must match exactly.
**How to avoid:** Display `[{idx}] {name}` where `idx` is the actual ffmpeg device index (from `_parse_audio_devices()` keys), not a re-indexed menu position. The user picks the actual device index, not a menu position.

### Pitfall 5: .gitignore patterns for XDG paths outside repo
**What goes wrong:** `recordings/`, `transcripts/`, `notes/` live under `~/.local/share/meeting-notes/` — outside the repo — so `.gitignore` entries do nothing for normal usage.
**Why it happens:** D-19 notes these are "defensive patterns" for the edge case where a user runs the tool from within the repo directory.
**How to avoid:** Add the patterns with a comment explaining they're defensive. No functional harm, prevents confusion.

### Pitfall 6: --verbose + --quiet interaction (D-06)
**What goes wrong:** Verbose detail lines printed when `quiet=True` is set.
**Why it happens:** Forgetting to check quiet before printing verbose lines.
**How to avoid:** The `if not quiet:` guard already wraps all output in `doctor.py`. The verbose block must be inside this guard — not outside it.

### Pitfall 7: README Audio MIDI Setup instructions accuracy
**What goes wrong:** ASCII diagram shows wrong device indices or wrong signal flow.
**Why it happens:** The specific indices (`:1` for BlackHole, `:2` for mic) are locked decisions — they must appear correctly in the README.
**How to avoid:** Cross-reference CONTEXT.md D-05 (device indices), STATE.md locked decisions, and REQUIREMENTS.md AUDIO-06 ("never device names").

---

## Code Examples

### Adding --verbose to doctor.py

```python
# Source: CONTEXT.md D-01, D-02, D-04, D-06

@click.command()
@click.option('--verbose', is_flag=True, help="Show detailed check information.")
@click.pass_context
def doctor(ctx: click.Context, verbose: bool):
    """Check system prerequisites for meeting-notes."""
    quiet = ctx.obj.get("quiet", False) if ctx.obj else False
    # quiet wins over verbose (D-06)
    if quiet:
        verbose = False
    # ... rest of setup ...
    for check, result in results:
        icon = STATUS_ICONS[result.status]
        if not quiet:
            console.print(f"  {icon} {check.name}: {result.message}")
            if verbose:
                detail = check.verbose_detail()
                if detail:
                    console.print(f"    [dim]{detail}[/dim]")
            if result.fix_suggestion and result.status != CheckStatus.OK:
                console.print(f"    [dim]Fix: {result.fix_suggestion}[/dim]")
```

### WhisperModelCheck verbose_detail (model path + size)

```python
# Source: CONTEXT.md D-05, existing WhisperModelCheck in checks.py

class WhisperModelCheck(HealthCheck):
    def verbose_detail(self) -> str | None:
        if not MODEL_CACHE_DIR.exists():
            return None
        # Sum all files in model cache directory
        total_bytes = sum(f.stat().st_size for f in MODEL_CACHE_DIR.rglob("*") if f.is_file())
        if total_bytes >= 1024 ** 3:
            size_str = f"{total_bytes / (1024**3):.1f} GB"
        else:
            size_str = f"{total_bytes / (1024**2):.0f} MB"
        return f"{MODEL_CACHE_DIR} ({size_str})"
```

### OllamaRunningCheck verbose_detail (version from API)

```python
# Source: CONTEXT.md D-05

class OllamaRunningCheck(HealthCheck):
    def verbose_detail(self) -> str | None:
        try:
            resp = requests.get("http://localhost:11434/api/version", timeout=5)
            if resp.status_code == 200:
                version = resp.json().get("version", "unknown")
                return f"Ollama {version}"
        except Exception:
            pass
        return None
```

### NotionTokenCheck verbose_detail (masked token)

```python
# Source: CONTEXT.md D-05

class NotionTokenCheck(HealthCheck):
    def verbose_detail(self) -> str | None:
        if not self.token:
            return None
        masked = self.token[:4] + "***" + self.token[-3:] if len(self.token) > 7 else "***"
        return f"Token: {masked}"
```

### FFmpegDeviceCheck verbose_detail (ffmpeg version)

```python
# Source: CONTEXT.md D-05

class FFmpegDeviceCheck(HealthCheck):
    def verbose_detail(self) -> str | None:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=5,
            )
            first_line = result.stdout.splitlines()[0] if result.stdout else None
            return first_line
        except Exception:
            return None
```

### meet init — detecting and prompting for reconfigure vs. update

```python
# Source: CONTEXT.md D-08, D-09

if config_path.exists():
    config = Config.load(config_path)
    console.print("[bold]Config already exists.[/bold]")
    choice = click.prompt(
        "  (R)econfigure everything from scratch, or (U)pdate specific fields?",
        type=click.Choice(["R", "r", "U", "u"]),
        default="U",
    ).upper()
    if choice == "U":
        # Show numbered field menu and only re-prompt selected fields
        _update_specific_fields(config, config_path)
        return
    # else: fall through to full wizard
```

### .gitignore additions

```
# User data directories (defensive — these live in XDG data dir, not repo)
recordings/
transcripts/
notes/
.env
```

---

## Validation Architecture

nyquist_validation is enabled (from .planning/config.json).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths = ["tests"]) |
| Quick run command | `python3 -m pytest tests/test_doctor_command.py tests/test_init.py -x -q` |
| Full suite command | `python3 -m pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SETUP-01 | `meet init` collects Notion token, DB ID, audio devices, writes config | unit | `pytest tests/test_init.py -x` | ❌ Wave 0 |
| SETUP-02 | `meet init` triggers test recording for mic permission | unit (mock subprocess) | `pytest tests/test_init.py::test_init_triggers_test_recording -x` | ❌ Wave 0 |
| SETUP-03 | `meet doctor` reports pass/fail per component with fix suggestions | unit | `pytest tests/test_doctor_command.py -x` | ✅ (exists, extend) |
| SETUP-04 | `meet doctor` checks BlackHole, ffmpeg, Ollama, mlx-whisper, Notion, disk | unit | `pytest tests/test_doctor_command.py -x` | ✅ (exists, extend) |
| SETUP-05 | `meet doctor` checks Python version and openai-whisper conflict | unit | `pytest tests/test_doctor_command.py -x` | ✅ |
| SETUP-06 | `meet doctor` exits 1 on ERROR, 0 on OK/WARNING | unit | `pytest tests/test_doctor_command.py::test_doctor_exits_1_on_error -x` | ✅ |
| PKG-01 | pyproject.toml with entry point `meet = "meeting_notes.cli.main:main"` | smoke | `python3 -c "from meeting_notes.cli.main import main"` | ✅ (manual verify) |
| PKG-02 | Clean git repo with README.md, pyproject.toml, .gitignore | manual | file existence check | ❌ Wave 0 (README) |
| PKG-03 | README.md includes prerequisites and usage examples | manual | visual review | ❌ Wave 0 (README) |

**New test coverage needed for this phase:**
- `--verbose` flag passes through to output: check that verbose detail lines appear
- `--verbose` + `--quiet` interaction: quiet wins
- `meet init` reconfigure vs. update branching
- Notion token validation loop: invalid token prompts re-entry
- Device selection menu renders from parsed device list
- Inline doctor run at end of init produces output

### Wave 0 Gaps

- [ ] `tests/test_init.py` — covers SETUP-01, SETUP-02, init wizard flows (reconfigure/update/Notion validation)
- [ ] Extend `tests/test_doctor_command.py` — `test_doctor_verbose_shows_detail`, `test_doctor_verbose_quiet_wins`

*(All other test infrastructure in place — pytest config, conftest.py, 176 passing tests as baseline)*

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.x | Runtime | ✓ | 3.14.x | — |
| pytest | Test runner | ✓ | 9.0.2 | — |
| click | CLI prompts, `--verbose` flag | ✓ | 8.3.1 | — |
| rich | Terminal output | ✓ | 14.3.3 | — |
| notion-client | Notion token validation in init | ✓ | 3.0.0 | — |
| ffmpeg | Device list parsing in init | ✓ | 8.1 | Error message if absent |
| requests | OllamaRunningCheck verbose_detail | ✓ | (installed) | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

All dependencies confirmed present in project venv.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw ffmpeg stderr dump in init | Parsed device menu (numbered list) | Phase 6 | User picks by number, not raw index |
| `meet init` dumps stderr and prompts for raw index | Wizard with detection + validation | Phase 6 | First-time setup is guided |
| `meet doctor` has no --verbose | `--verbose` adds inline detail per check | Phase 6 | Debugging without manual probing |
| init tells user to run doctor manually | init runs doctor inline at the end | Phase 6 | Full setup verified in one command |

---

## Open Questions

1. **Does `verbose_detail()` need config passed in?**
   - What we know: Most checks that need verbose data already store what they need at construction time (e.g., `BlackHoleCheck` has `self.device_index`). `NotionTokenCheck` has `self.token`. The Ollama checks need no config — they call the API.
   - What's unclear: Nothing — no check in D-05 requires config beyond what's already stored in `__init__`.
   - Recommendation: `verbose_detail(self) -> str | None` with no extra args. Checks use their already-stored state.

2. **STATUS_ICONS sharing between doctor.py and init.py**
   - What we know: Both need the same 3-entry dict. Currently only in `doctor.py`.
   - What's unclear: Whether to centralize to `cli/ui.py` or redefine.
   - Recommendation: Move `STATUS_ICONS` to `cli/ui.py` and import from both `doctor.py` and `init.py`. Keeps the single source of truth pattern already established for `console`.

3. **LICENSE file**
   - What we know: D-18 says "clean code-only branch for distribution." No LICENSE file exists.
   - What's unclear: User preference (MIT, Apache 2.0, etc.) — deferred to Claude's discretion.
   - Recommendation: Add `LICENSE` with MIT text (most permissive, standard for developer tools). If user wants different license, trivially changed.

---

## Sources

### Primary (HIGH confidence)

- Existing codebase: `meeting_notes/cli/commands/doctor.py`, `init.py`, `services/checks.py`, `core/health_check.py`, `core/config.py` — direct code inspection
- Existing tests: `tests/test_doctor_command.py` — 176 tests passing, baseline confirmed
- `pyproject.toml` — current package configuration verified
- Click documentation pattern: `@click.option('--verbose', is_flag=True)` — standard Click idiom, version 8.3.1 installed
- notion-client API: `client.users.me()` raises `APIResponseError` — verified in existing `NotionTokenCheck.check()` implementation (line 237-240 of checks.py)
- CONTEXT.md decisions D-01 through D-19 — locked decisions from user discussion

### Secondary (MEDIUM confidence)

- Ollama `/api/version` endpoint: returns `{"version": "..."}` — consistent with Ollama HTTP API conventions, used in `OllamaRunningCheck` pattern

### Tertiary (LOW confidence)

- None — all claims verified from codebase inspection or CONTEXT.md locked decisions

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries installed and version-confirmed in project venv
- Architecture: HIGH — all patterns directly observable in existing code; no new libraries
- Pitfalls: HIGH — derived from direct code inspection of existing implementation and CONTEXT.md decisions
- Test infrastructure: HIGH — 176 tests passing, pytest 9.0.2, config confirmed

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable dependencies, no fast-moving ecosystem concerns)
