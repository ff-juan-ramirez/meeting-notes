# Phase 06: Session ID Column - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 06-add-session-id-column-to-meet-list-untruncated-and-wire-it-as-a-selector-for-meet-summarize-session
**Areas discussed:** Wire-as-selector scope, Column placement + formatting

---

## "Wire as selector" scope

| Option | Description | Selected |
|--------|-------------|----------|
| Just display the ID | Show full stem in meet list so users copy-paste to --session. Exact match already works. | ✓ |
| Slug-prefix matching | Implement partial SESSRES-01 — --session accepts recording name slug. | |

**User's choice:** Just display the ID — no slug-prefix matching needed.
**Notes:** User also confirmed: "if no session specified it uses the last record" — existing `resolve_latest_transcript` (mtime) is correct, no change needed.

---

## Default behavior (no --session)

| Option | Description | Selected |
|--------|-------------|----------|
| Confirm existing behavior | Latest transcript by mtime — no code change | ✓ |
| Match meet list order | Align to transcribed_at metadata field | |

**User's choice:** Existing behavior is correct.

---

## Column placement

| Option | Description | Selected |
|--------|-------------|----------|
| Last column (after Notion URL) | Least disruptive, right-side for copy-paste | ✓ |
| First column (before Date) | Most prominent | |
| Between Status and Notion URL | Groups operational columns | |

**User's choice:** Last column, after Notion URL.

---

## JSON output

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — add session_id field | Add stem as session_id to --json output | ✓ |
| No — table only | Keep JSON as-is | |

**User's choice:** Add session_id to --json output.

---

## Claude's Discretion

- Column header label ("Session ID" vs "ID")
- Rich table truncation behavior (no max_width — Rich expands as needed)
- Test naming

## Deferred Ideas

- SESSRES-01 slug-prefix matching — confirmed deferred
- meet transcribe --session scope — not in this phase
