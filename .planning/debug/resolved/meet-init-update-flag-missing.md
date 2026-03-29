---
status: dismissed
trigger: "meet init --update shows field [7] HuggingFace token in the update menu"
created: 2026-03-27T00:00:00Z
updated: 2026-03-27T00:00:00Z
---

## Current Focus

hypothesis: The --update flag was never added to the Click command definition for `init`; the update path exists only as an interactive runtime branch, not as a CLI flag
test: Read init.py Click decorator and command signature
expecting: No `@click.option("--update", ...)` decorator on the `init` command
next_action: confirmed — root cause identified

## Symptoms

expected: `meet init --update` launches the update-fields menu listing field [7] HuggingFace token
actual: `meet init --update` fails — Click raises an error because `--update` is not a recognised option
errors: (none reported by user — just "there is no meet init --update option")
reproduction: Run `meet init --update` in a terminal
started: Discovered during Phase 01 UAT

## Eliminated

- hypothesis: _update_specific_fields() or _collect_hf_token() was not implemented
  evidence: Both functions are present and complete in init.py (lines 90-187). Field [7] HuggingFace token is listed in the fields array and handled in the if-7-selected branch.
  timestamp: 2026-03-27T00:00:00Z

- hypothesis: The update menu is only reached via a different command
  evidence: There is no separate `meet update` command in main.py. The only update path is inside `init`.
  timestamp: 2026-03-27T00:00:00Z

## Evidence

- timestamp: 2026-03-27T00:00:00Z
  checked: meeting_notes/cli/commands/init.py — @click.command() decorator and function signature (lines 243-247)
  found: `@click.command()` with no options defined; signature is `def init(ctx: click.Context)` — no `--update` parameter at all
  implication: Click will reject `meet init --update` with "no such option: --update"

- timestamp: 2026-03-27T00:00:00Z
  checked: meeting_notes/cli/commands/init.py — existing config branch (lines 254-267)
  found: When config already exists, the command interactively prompts "(R)econfigure everything from scratch, or (U)pdate specific fields?" and branches on the answer. The update path (_update_specific_fields) is only reachable by running `meet init` with a config already present and typing "U" at the interactive prompt.
  implication: The --update flag shortcut was planned (STATE.md records "[Phase 01-02]: Field [7] added to update menu") but the Click option to expose it as a CLI flag was never added to the command decorator.

- timestamp: 2026-03-27T00:00:00Z
  checked: meeting_notes/cli/main.py — all registered commands
  found: Commands registered: record, stop, doctor, init, transcribe, summarize, list_sessions. No `update` sub-command exists.
  implication: There is no alternative route to trigger the update menu via CLI flag.

- timestamp: 2026-03-27T00:00:00Z
  checked: STATE.md decision entry for Phase 01-02
  found: "[Phase 01-02]: Field [7] added to update menu for HuggingFace token — consistent with existing 1-6 field numbering"
  implication: The decision was recorded as "field added to update menu" — which is true. But the plan did not explicitly require adding an `--update` CLI flag. The UAT test assumed the flag would exist; the implementation only added the field to the interactive menu.

## Resolution

root_cause: The `init` Click command has no `--update` option defined. The update menu logic (_update_specific_fields with field [7] HuggingFace token) is fully implemented and reachable, but only through the interactive "U" prompt that appears when a config already exists. The CLI flag `--update` was never wired into the Click command decorator, so `meet init --update` is an unrecognised option.

fix: Add `@click.option("--update", is_flag=True, default=False, help="Update specific config fields.")` to the `init` command decorator, and add a branch at the top of the `init` function body: if `--update` is passed, load config and call `_update_specific_fields(config, config_path)` directly, bypassing the interactive (R)/(U) prompt.

verification: not yet applied
files_changed: []
