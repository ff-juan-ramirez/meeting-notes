# Phase 7: Notion Title at Summarize Time - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 07-for-the-notes-in-notion-if-the-user-specifies-a-title-i-want-that-title-to-be-in-the-notion-note-title
**Areas discussed:** Title flag design, Priority chain, Metadata persistence, Scope of title use

---

## Title Flag Design

| Option | Description | Selected |
|--------|-------------|----------|
| --title only | Long-form only, consistent with --template and --session | ✓ |
| --title / -t | Adds short alias (-t) | |

**User's choice:** `--title` only (long-form)
**Notes:** User confirmed the combined usage looks right: `meet summarize --session abc123 --title "Weekly Sync"`. Preferred consistency with existing long-form flags.

---

## Priority Chain

| Option | Description | Selected |
|--------|-------------|----------|
| --title always wins | --title > recording_name > extract_title() | ✓ |
| --title only when no recording_name | recording_name > --title > extract_title() | |

**User's choice:** `--title` always wins
**Notes:** User asked for clarification — confirmed that if `recording_name` is set (from `meet record "Name"`) but `--title` is not provided at summarize time, `recording_name` still wins (existing Phase 5 behavior unchanged). `--title` only overrides when explicitly passed.

---

## Metadata Persistence

| Option | Description | Selected |
|--------|-------------|----------|
| One-time only | Affects only this Notion push, no metadata write | ✓ |
| Persist to metadata | Saves --title back to session JSON as recording_name | |

**User's choice:** One-time only
**Notes:** `--title` is a runtime override, not a stored fact.

---

## Scope of Title Use

| Option | Description | Selected |
|--------|-------------|----------|
| Notion page title only | Local notes filename unchanged | ✓ |
| Notion title + local notes filename | Also renames the .md file to match the title | |

**User's choice:** Notion page title only
**Notes:** No filename changes, no additional complexity.

---

## Claude's Discretion

- Help text wording for `--title` flag
- Falsy check pattern (`if title:`) consistent with Phase 4/5

## Deferred Ideas

None.
