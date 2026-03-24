# Phase 3: Note Generation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate structured meeting notes from a local transcript using Ollama llama3.1:8b. Three templates: `meeting`, `minutes`, `1on1`. Notes saved as local Markdown files. Adds Ollama health checks to `meet doctor`.

New capabilities (Notion saving, `meet list`, speaker attribution) belong in other phases.

</domain>

<decisions>
## Implementation Decisions

### Template Structure

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

### Strict Grounding Rule (all templates)

- **D-04:** Every template prompt must include: "Base your notes ONLY on what is said in the transcript. Only include decisions and next steps if EXPLICITLY mentioned." No invented content.

### Terminal Output

- **D-05:** After successful generation, print the saved file path and word count only. No preview, no full content printed. Example: `Notes saved: ~/.local/share/meeting-notes/notes/20260322-abc12345-meeting.md (312 words)`.
- **D-06:** Session stem printed at end (same pattern as `meet transcribe`) so user can reference it in later commands.

### Re-summarize Behavior

- **D-07:** If notes already exist for the session + template combination, overwrite silently — no prompt, no warning. Consistent with Phase 2's transcript overwrite (D-03). Fresh generation on every run.

### Session Metadata Extension

- **D-08:** Phase 3 extends `metadata/{stem}.json` (written by Phase 2) with these fields:
  - `notes_path` — absolute path to the notes Markdown file
  - `template` — template used (`meeting`, `minutes`, `1on1`)
  - `summarized_at` — ISO 8601 timestamp
  - `llm_model` — model identifier string (e.g. `llama3.1:8b`)

### Doctor Check Severity

- **D-09:** `OllamaRunningCheck` → **ERROR** when Ollama is not running. Fix suggestion: `Run: ollama serve`. Unlike Whisper, Ollama cannot auto-start — hard failure in `meet summarize` with no recovery path.
- **D-10:** `OllamaModelCheck` → **ERROR** when `llama3.1:8b` is not listed in `ollama list`. Fix suggestion: `Run: ollama pull llama3.1:8b`. Unlike mlx-whisper model which auto-downloads, Ollama will not fetch the model mid-command.

### Locked from Roadmap (not re-discussed)

- **D-11:** Ollama HTTP API: `POST localhost:11434/api/generate` — no streaming (wait for full response).
- **D-12:** Configurable timeout, default 120s. On timeout: actionable error message.
- **D-13:** Token estimation: `len(transcript) / 4`. If >8,000 tokens, use map-reduce chunking: split into ~6,000-token chunks, summarize each, combine into final notes.
- **D-14:** `--template` flag accepts `meeting` (default), `minutes`, `1on1`.
- **D-15:** Notes saved to `~/.local/share/meeting-notes/notes/{stem}-{template}.md`.
- **D-16:** Rich spinner during LLM generation ("Generating notes...").
- **D-17:** `meet summarize` resolves session via `--session <stem>` or auto-resolves latest transcript (same pattern as `meet transcribe`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Architecture
- `.planning/ROADMAP.md` §Phase 3 — Plan specs (3.1, 3.2, 3.3) and pitfalls P10–P13
- `.planning/PROJECT.md` — Tech stack constraints (Ollama, llama3.1:8b, not llama3.2) and grounding rule
- `.planning/REQUIREMENTS.md` §Note Generation — LLM-01 to LLM-07

### Existing Code Patterns
- `meeting_notes/services/transcription.py` — Model for `services/llm.py` structure (pure functions, no Click/Rich imports)
- `meeting_notes/cli/commands/transcribe.py` — Model for `cli/commands/summarize.py` (session resolution, spinner pattern, metadata write)
- `meeting_notes/core/state.py` — Atomic JSON write pattern for extending `metadata/{stem}.json`
- `meeting_notes/core/storage.py` — `get_data_dir()` and `ensure_dirs()` — `notes/` directory needs to be added
- `meeting_notes/core/health_check.py` — HealthCheck ABC that new checks must subclass
- `meeting_notes/services/checks.py` — Where Phase 3 checks get registered
- `meeting_notes/phases/02-local-transcription/02-CONTEXT.md` — Phase 2 decisions; metadata schema (D-10, D-11) that Phase 3 extends

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `services/transcription.py`: `run_with_spinner(task_fn, message)` — reuse or adapt for LLM call (threading + Rich Live elapsed timer)
- `core/state.py`: `write_state()` / `read_state()` — use for atomic extend of `metadata/{stem}.json`
- `core/storage.py`: `ensure_dirs()` — needs `notes/` directory added alongside `recordings/`, `transcripts/`, `metadata/`
- `cli/commands/transcribe.py`: session resolution pattern (`resolve_latest_wav` / `resolve_wav_by_stem`) — mirror for transcript resolution in summarize

### Established Patterns
- LLM service: pure functions in `services/llm.py`, no Click/Rich imports (mirrors `services/transcription.py`)
- CLI command: `click.command()` + module-level `Console()` (mirrors `transcribe.py`, `record.py`)
- Health checks: `HealthCheck` subclass with `check() -> CheckResult`; register in `services/checks.py` and import in `cli/commands/doctor.py`
- Metadata JSON: read existing `{stem}.json` → add Phase 3 fields → write back atomically

### Integration Points
- `cli/main.py` — register `summarize` command (same pattern as `transcribe`)
- `services/checks.py` — register `OllamaRunningCheck` and `OllamaModelCheck`
- `core/storage.py` — add `notes/` to `ensure_dirs()` and `get_notes_dir()`
- `metadata/{stem}.json` — Phase 3 reads this (for `wav_path`, session context) and writes new fields back

</code_context>

<specifics>
## Specific Ideas

- 1on1 template format is highly specific (performance documentation style). The LLM prompt must include the full section definitions as internal context so the model categorizes correctly, but must NOT output the definitions. The exact prompt structure: system instructions with category definitions, then the strict grounding rule, then the transcript.
- Session stem display: after successful generation, print `Session: {stem}` for copy-paste into `meet summarize --session` or future commands (same as `meet transcribe` output D-04 from Phase 2).
- `notes/` directory: currently `ensure_dirs()` creates `recordings/`, `transcripts/`, `metadata/`. Phase 3 needs to add `notes/` — small change to `core/storage.py`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-note-generation*
*Context gathered: 2026-03-22*
