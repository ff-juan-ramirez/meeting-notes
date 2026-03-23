# Phase 4: Notion Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 04-notion-integration
**Areas discussed:** Save trigger, Page title source, Notion failure handling

---

## Save Trigger

| Option | Description | Selected |
|--------|-------------|----------|
| Always (when configured) | Auto-save when token is configured — one command, local file + Notion page | ✓ |
| Opt-in via --save flag | Explicit flag required; default stays local-only | |
| Always, with --no-save to skip | Push by default; --no-save to skip | |

**User's choice:** Always (when configured)
**Notes:** No --save flag needed. Auto-push when token exists.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Skip silently, no mention | No token = no Notion step, no output | |
| Print a one-line hint | Print "Notion not configured — run meet init to set up." | ✓ |
| Fail with an error | Hard fail if token not set | |

**User's choice:** Print a one-line hint
**Notes:** Advisory hint, not a warning or error. Helps discovery.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Add Notion URL line | Existing line + "Notion: https://notion.so/..." on a second line | ✓ |
| Replace output with combined line | Single merged line | |
| You decide | Match existing output style | |

**User's choice:** Add Notion URL line
**Notes:** Extends Phase 3 output pattern minimally.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, spinner while pushing | "Saving to Notion..." spinner during API call | ✓ |
| No spinner, silent push | Silent, URL shown at completion only | |
| You decide | Follow existing conventions | |

**User's choice:** Yes, spinner while pushing

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, show URL in meet list | Notion URL column in meet list for pushed sessions | ✓ |
| No, just local session info | URL only in metadata JSON | |
| Deferred — that's Phase 5 | Phase 4 stores URL, Phase 5 displays it | |

**User's choice:** Yes, show URL in meet list
**Notes:** Phase 4 stores the URL; Phase 5 displays it in meet list.

---

| Option | Description | Selected |
|--------|-------------|----------|
| WARNING — Notion is optional | Missing token → WARNING in meet doctor | ✓ |
| ERROR — Notion is required | Missing token → ERROR (blocking) | |
| You decide | Follow severity patterns | |

**User's choice:** WARNING — Notion is optional

---

| Option | Description | Selected |
|--------|-------------|----------|
| Config.json only | Token in ~/.config/meeting-notes/config.json | ✓ |
| Env var fallback (NOTION_TOKEN) | Config first, then env var | |
| Env var only | NOTION_TOKEN env var only | |

**User's choice:** Config.json only

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, separate NotionDatabaseCheck | Two checks: token check + database/page check | ✓ |
| Combine into one check | Single unified check | |
| You decide | Follow existing granularity | |

**User's choice:** Yes, separate NotionDatabaseCheck

---

| Option | Description | Selected |
|--------|-------------|----------|
| Parent page — child pages only | Each note = child page under parent | ✓ |
| Database — entries with properties | Database rows with metadata properties | |
| Support both | Auto-detect page vs database | |
| You decide | Simpler/more natural for users | |

**User's choice:** Parent page — child pages only

---

## Page Title Source

| Option | Description | Selected |
|--------|-------------|----------|
| Extract from generated notes | First H1 or first non-empty line — no extra LLM call | ✓ |
| Separate LLM call to generate title | Second Ollama call for a short title | |
| Timestamp-based title | "Meeting Notes — 2026-03-22 14:30" always | |
| You decide | Best title with least complexity | |

**User's choice:** Extract from generated notes
**Notes:** No extra LLM call. Reuses already-generated notes file.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Timestamp fallback | "Meeting Notes — {date} {time}" if extraction fails | ✓ |
| First N words of transcript | First 10-15 transcript words as title | |
| Raise an error | Fail push if title can't be extracted | |

**User's choice:** Timestamp fallback

---

| Option | Description | Selected |
|--------|-------------|----------|
| First H1 or first non-empty line | Look for # heading; fall back to first non-empty line | ✓ |
| First sentence of Summary section | Find ## Summary, extract first bullet | |
| You decide | Implement sensible extraction | |

**User's choice:** First H1 or first non-empty line

---

## Notion Failure Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Warn and continue | Exit 0, print error reason, notes safe locally | ✓ |
| Fail the command (exit 1) | Hard fail if Notion push fails | |
| Silent fail, log to file | Log to errors.log, clean terminal | |

**User's choice:** Warn and continue (exit 0)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Styled Rich warning panel | [yellow] panel with reason + local notes path | ✓ |
| Plain text warning line | Simple "Warning: Notion upload failed — notes saved locally at <path>" | |
| You decide | Match existing error/warning style | |

**User's choice:** Styled Rich warning panel

---

## Claude's Discretion

- Block structure for Notion pages (heading_2, bulleted_list_item, ≤1,900 char splits)
- Exponential backoff implementation details for HTTP 429
- Exact hint text styling ("Notion not configured" uses Rich `dim`)

## Deferred Ideas

None.
