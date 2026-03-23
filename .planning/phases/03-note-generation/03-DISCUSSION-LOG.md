# Phase 3: Note Generation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 03-note-generation
**Areas discussed:** Template structure, Terminal output, Re-summarize behavior, Doctor check severity

---

## Template Structure

### meeting template

| Option | Description | Selected |
|--------|-------------|----------|
| Summary + Decisions + Action Items | 3 sections: summary paragraph, decisions bullet list, action items bullet list | ✓ |
| Summary + Key Points + Decisions + Action Items | 4 sections adding discussion highlights | |

**User's choice:** Summary + Decisions + Action Items (recommended default)

### minutes template

| Option | Description | Selected |
|--------|-------------|----------|
| Attendees + Agenda + Discussion + Decisions + Action Items | 5 sections, traditional minutes format | ✓ |
| Same as meeting but with Attendees header | Lighter-weight formal option | |

**User's choice:** Attendees + Agenda + Discussion + Decisions + Action Items (recommended default)

### 1on1 template

| Option | Description | Selected |
|--------|-------------|----------|
| Custom | User-defined sections and format | ✓ |

**User's choice:** Custom format with detailed specifications:

Sections (in exact order): **Project Work**, **Technical Overview**, **Team Collaboration**, **Feedback**, **Personal notes**

Internal category definitions:
- Project Work → status, blockers, recent progress
- Technical Overview → architectural decisions, technical issues, tools, systems, improvements
- Team Collaboration → communication, alignment, cross-team support
- Feedback → upward/downward feedback, self-reflection, coaching moments, improvement opportunities
- Personal notes → interests outside of work, personal context, stories that help understand the person

Formatting requirements: bold section titles, no colons after titles, one blank line after each title, paragraph format (no bullets), no line separators, professional/neutral tone for performance documentation, do not output category definitions, do not invent information.

---

## Terminal Output

| Option | Description | Selected |
|--------|-------------|----------|
| Path + word count only | File path and word count confirmation | ✓ |
| Full notes printed | Complete notes to stdout | |
| Path + first section preview | File path plus Summary section | |

**User's choice:** Path + word count only — clean, scriptable, consistent with `meet transcribe` behavior.

---

## Re-summarize Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Silent overwrite | Overwrite existing notes without prompting | ✓ |
| Warn + confirm | Yellow warning + confirmation before overwrite | |

**User's choice:** Silent overwrite — consistent with Phase 2 transcript overwrite precedent (D-03).

---

## Doctor Check Severity

| Option | Description | Selected |
|--------|-------------|----------|
| Both ERROR | OllamaRunning → ERROR, OllamaModel → ERROR | ✓ |
| Running=ERROR, Model=WARNING | Split severity | |
| Both WARNING | Consistent with Phase 2 but misleading | |

**User's choice:** Both ERROR — Ollama cannot auto-recover (unlike Whisper which auto-downloads), so WARNING would mislead about recoverability.

---

## Claude's Discretion

None — all areas had explicit user decisions.

## Deferred Ideas

None.
