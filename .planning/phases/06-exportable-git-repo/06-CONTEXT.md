# Phase 6: Exportable Git Repo - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Package the project as a clean, cloneable git repo. Deliverables:
- `meet doctor --verbose` flag — tool versions, model paths, device details inline per check
- `meet init` full wizard — device selection menu, Notion credentials, reconfigure flow, inline doctor run
- `README.md` — full reference with prerequisites walkthrough, Audio MIDI Setup ASCII diagram, all commands
- `.gitignore` updates — add user data dir patterns
- `pyproject.toml` finalization — already correct, no changes needed
- Clean code-only branch via gsd:pr-branch for distribution

New capabilities (shell completion, search, auto-update, v2 features) belong in future phases.

</domain>

<decisions>
## Implementation Decisions

### `meet doctor --verbose`

- **D-01:** `--verbose` is a `meet doctor`-only flag (not global). Added as `@click.option('--verbose', is_flag=True)` on the `doctor` command.
- **D-02:** Verbose detail lines appear **inline under each check line**, indented with extra spaces — consistent with the existing `fix_suggestion` display pattern (`"    [dim]Detail: ...[/dim]"`).
- **D-03:** Only checks that have meaningful extra data emit verbose lines. Checks with no meaningful runtime data (e.g. OpenaiWhisperConflictCheck) skip verbose output.
- **D-04:** Fix suggestions continue to appear **only on WARNING or ERROR** — even in `--verbose` mode. Verbose adds detail lines; it does not add fix suggestions for passing checks.
- **D-05:** Per-check verbose detail content:
  - `BlackHoleCheck`: device name at the found index + channel count (e.g., `"BlackHole 2ch, 2 channels"`)
  - `FFmpegDeviceCheck`: ffmpeg version string (`ffmpeg -version` first line)
  - `PythonVersionCheck`: full version string + Python executable path (`sys.executable`)
  - `OllamaRunningCheck`: Ollama version from `/api/version` endpoint
  - `OllamaModelCheck`: model tag confirmed pulled (e.g., `"llama3.1:8b confirmed in local library"`)
  - `WhisperModelCheck`: model file path + size on disk (in MB/GB)
  - `MlxWhisperCheck`: mlx-whisper package version
  - `NotionTokenCheck`: Notion workspace/database name (token shown masked, e.g., `"ntn_***...abc"`)
  - `DiskSpaceCheck`: free space in GB (e.g., `"47.2 GB free"`)
- **D-06:** `--verbose` is compatible with `--quiet` — quiet wins. If both flags are passed, quiet suppresses all output including verbose lines.

### `meet init` Full Wizard

- **D-07:** `meet init` collects Notion token + database/page ID interactively as **required fields** (not optional). Full wizard covers: audio devices + Notion credentials in one run.
- **D-08:** Existing config detection: on startup, check if `config.json` exists. If yes, prompt:
  `"Config already exists. (R)econfigure everything from scratch, or (U)pdate specific fields?"`. Choices: reconfigure (re-run full wizard) or update (show field menu).
- **D-09:** Update-specific-fields flow: present a numbered menu showing all config fields with current values (Notion token masked). User picks which field(s) to re-enter. Only selected fields are re-prompted; others retain current values.
- **D-10:** Audio device detection: parse avfoundation device list from ffmpeg stderr into a numbered menu. User selects "BlackHole 2ch" from the list by number rather than reading raw output and typing an index. Show parsed device name + index for confirmation.
- **D-11:** Notion token validation: after user pastes token, make a quick Notion API call (`GET /users/me`) to verify it's valid before writing config. Show clear error if invalid; prompt to re-enter.
- **D-12:** `meet init` runs `meet doctor` inline at the end using `HealthCheckSuite` directly (no subprocess call). Uses same output format as standalone `meet doctor` (without `--verbose`). Displays results as the final step of wizard.
- **D-13:** Test recording for mic permission (existing SETUP-02 behavior) is preserved — runs after config is written, before `meet doctor` inline check.

### README

- **D-14:** README is a **full reference document** with: What it is, Prerequisites (with install commands), Audio MIDI Setup walkthrough, Installation, Quickstart workflow, all 6 commands with flags and examples, Config file format, Troubleshooting section.
- **D-15:** Audio MIDI Setup section uses **step-by-step numbered instructions** plus an **ASCII art diagram** showing the signal routing (System audio → BlackHole → ffmpeg capture; Microphone → ffmpeg capture; ffmpeg amix → WAV file). This is the most complex prerequisite and needs the most detail.

### Packaging & Distribution

- **D-16:** `python_requires` stays `">=3.11,<3.15"` (current value in pyproject.toml). ROADMAP's `<3.14` was pre-Phase 1; the project runs confirmed on Python 3.14.
- **D-17:** Dependency pinning stays as **minimum versions** (current state, e.g., `click>=8.1`). Exact pinning would conflict with other tools in user venvs; minimum bounds are correct for a distributed package.
- **D-18:** Git cleanup: after Phase 6 implementation, run `/gsd:pr-branch` to create a **clean code-only branch** (filtering `.planning/` doc commits). This branch is the distribution target for sharing/cloning.
- **D-19:** `.gitignore` additions: add patterns for user data directories (`recordings/`, `transcripts/`, `notes/`) per ROADMAP 6.3. These live under XDG data dir outside the repo, but defensive patterns prevent accidental commits if user runs tool from within the repo directory. Also add `.env` if not already present.

### Claude's Discretion

- Exact formatting/layout of the `meet init` wizard prompts (Rich panels, progress indicators)
- README section ordering and prose style
- Whether to add `LICENSE` file (MIT or similar) — reasonable default for an open-source tool
- ASCII diagram style and detail level in README

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope
- `.planning/ROADMAP.md` §Phase 6 — Plans 6.1, 6.2, 6.3 and pitfalls P19, P20
- `.planning/REQUIREMENTS.md` §Packaging & Distribution — PKG-01, PKG-02, PKG-03
- `.planning/REQUIREMENTS.md` §Setup & Health Check — SETUP-01 to SETUP-06 (full implementation)
- `.planning/PROJECT.md` — Tech stack, constraints, core value

### Existing Implementation to Extend
- `meeting_notes/cli/commands/doctor.py` — Current doctor command (add `--verbose` flag, verbose detail lines)
- `meeting_notes/cli/commands/init.py` — Current init command (full rewrite to wizard)
- `meeting_notes/core/health_check.py` — HealthCheckSuite, CheckResult, CheckStatus (reuse in init)
- `meeting_notes/services/checks.py` — All check implementations (extend with verbose_detail method or similar)
- `pyproject.toml` — Current state (no changes needed to structure, only .gitignore)

### Prior Phase Patterns
- `.planning/phases/05-integrated-cli/05-CONTEXT.md` — Shared console, `--quiet` pattern, ctx.obj, error style
- `.planning/phases/04-notion-integration/04-CONTEXT.md` — Notion token validation pattern, NotionConfig fields

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/health_check.py::HealthCheckSuite.run_all()` — Returns `(check, result)` pairs. `meet init` can call this directly without subprocess to run doctor inline.
- `services/checks.py` — All check classes. Extending each with a `verbose_detail(config) -> str | None` method keeps verbose logic colocated with check logic.
- `cli/ui.py::console` — Shared Rich console. All new output in init/doctor extensions uses this.
- `core/config.py::Config`, `AudioConfig` — Already models audio device indices. Needs `NotionConfig` fields surfaced for init wizard.
- `services/notion.py` — Notion API client. The token validation in init can reuse the same `notion-client` SDK already present.

### Established Patterns
- Doctor output: `f"  {icon} {check.name}: {result.message}"` + `f"    [dim]Fix: {result.fix_suggestion}[/dim]"` — verbose detail follows the same indentation as fix_suggestion
- Error output: `console.print(f"[red]Error:[/red] {msg}"); sys.exit(1)` — keep this style in init wizard
- Config save: `config.save(config_path)` — atomic, uses existing `write_state` pattern
- Session context: `ctx.obj.get('quiet', False)` — all commands

### Integration Points
- `doctor.py::doctor()` — Add `@click.option('--verbose', is_flag=True)` parameter; pass to `suite.run_all()` or post-process results to emit detail lines
- `init.py::init()` — Full rewrite: detect existing config → wizard flow → write config → test recording → inline doctor
- `.gitignore` — Append user data patterns to existing file (Phase 1 created it for Python artifacts)

</code_context>

<specifics>
## Specific Ideas

- Verbose detail indented under check line: `"    [dim]{detail}[/dim]"` — same style as fix_suggestion, one level deeper
- Audio MIDI Setup ASCII diagram example layout:
  ```
  System Audio ──► BlackHole 2ch (device :1) ──┐
                                                ├──► ffmpeg amix ──► recording.wav
  MacBook Mic   ──────────────── (device :2) ──┘
  ```
- Init wizard field menu for "update specific fields": numbered list like `meet list --json` table approach — show all fields with current values, user types numbers to select
- Notion token validation: `client.users.me()` — if it raises `APIResponseError`, token is invalid

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-exportable-git-repo*
*Context gathered: 2026-03-23*
