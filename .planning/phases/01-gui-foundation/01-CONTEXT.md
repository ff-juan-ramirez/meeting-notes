# Phase 01: GUI Foundation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the application skeleton: `meet-gui` launches a MainWindow with a sidebar that navigates to 6 placeholder screens, the visual system is centralized in `theme.py`, and `services/llm.py` gains template CRUD functions. No fully-built views (those are Phase 02–04). The `meet` CLI must remain unchanged.

</domain>

<decisions>
## Implementation Decisions

### Overall Approach
- **D-01:** All implementation decisions deferred to Claude's discretion — the user confirmed `GUI-MILESTONE-PLAN.md` is the authoritative spec. Follow it faithfully.
- **D-02:** Use `meeting-notes-ui-mockups.pdf` as the visual/structural reference for layout and content. Exact pixel-perfect match not required; treat it as a structural guide.

### Claude's Discretion
All visual choices (color palette, dark/light theme, sidebar icon treatment, placeholder view content) are Claude's to decide, guided by the mockup PDF and milestone plan. Recommended defaults:
- Derive colors from the mockup PDF visually; default to a clean dark theme matching macOS native feel if mockup is ambiguous
- Sidebar: icons + text (standard macOS app nav pattern)
- Placeholder views: centered `QLabel` with screen name (minimal, avoids premature work)
- TMPL-06: Switch `meet summarize --template` validation to use `list_templates()` — no backward-compat concern since built-in names ("meeting", "minutes", "1on1") will still be in the list

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Primary Design Spec
- `GUI-MILESTONE-PLAN.md` — complete file structure, architecture diagram, per-screen layout spec, code stubs for `app.py`, `theme.py`, `main_window.py`, entry point, and PyInstaller spec

### Visual Reference
- `meeting-notes-ui-mockups.pdf` — 6-page mockup (one per screen); use as structural guide for layout and content. Menlo monospace for transcript/notes areas, Helvetica Neue for UI text.

### Existing Code to Extend
- `meeting_notes/services/llm.py` — existing `load_template()` and `VALID_TEMPLATES` tuple to be replaced by CRUD functions (`list_templates`, `save_template`, `delete_template`, `duplicate_template`)
- `meeting_notes/core/config.py` — `Config` dataclass with `AudioConfig`, `WhisperConfig`, `NotionConfig`, `HuggingFaceConfig` subconfigs; used by `app.py` at startup
- `meeting_notes/core/storage.py` — `get_config_dir()`, `ensure_dirs()` used in app entry point

### Templates
- `meeting_notes/templates/` — built-in templates: `meeting.txt`, `minutes.txt`, `1on1.txt`
- User templates dir (new): `~/.config/meeting-notes/templates/` (created if missing)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `meeting_notes/core/config.py`: `Config.load(path)` / `Config.save(path)` — used in `gui/app.py` and `views/settings.py`
- `meeting_notes/core/storage.py`: `get_config_dir()`, `ensure_dirs()` — used in app entry point
- `meeting_notes/services/llm.py`: `load_template()` to be refactored (TMPL-01 through TMPL-06)
- `meeting_notes/templates/`: 3 built-in `.txt` files — must remain as built-ins

### Established Patterns
- Config is loaded via `Config.load(path)` returning a dataclass — not a singleton
- No existing GUI code; `gui/` directory does not exist yet — fully greenfield
- CLI uses Click + Rich; GUI must NOT import Click or Rich in the GUI path
- ML imports (`mlx_whisper`, `pyannote.audio`, `torchaudio`) must be lazy-imported inside workers only (startup latency requirement, GUI-01)

### Integration Points
- `pyproject.toml`: add `pyside6>=6.7` to `[project.optional-dependencies]` gui group and `meet-gui` script entry point
- `services/llm.py`: add CRUD functions + update `meet summarize` CLI to use `list_templates()` for template validation (TMPL-06)
- Workers (Phase 02+) will call existing service functions; worker interfaces established in Phase 01 as empty stubs (or created in later phases)

</code_context>

<specifics>
## Specific Ideas

- From `GUI-MILESTONE-PLAN.md`: `window.setMinimumSize(900, 600)`, `window.resize(1100, 700)` — use these exact dimensions
- From `GUI-MILESTONE-PLAN.md`: `app.setAttribute(Qt.AA_UseHighDpiPixmaps)` for HiDPI support
- Font spec: `Menlo` (10pt) for transcript/notes text areas; `Helvetica Neue` for all UI text (20pt h1, 13pt h2, 11pt body, 9pt small)
- Sidebar items in order: Dashboard, Sessions, Record, Templates, Settings, Health Check

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-gui-foundation*
*Context gathered: 2026-03-30*
