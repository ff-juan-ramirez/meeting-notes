# Phase 6: Exportable Git Repo - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-23
**Phase:** 06-exportable-git-repo
**Areas discussed:** meet doctor --verbose, meet init wizard completeness, README structure and depth, Packaging decisions

---

## meet doctor --verbose

| Option | Description | Selected |
|--------|-------------|----------|
| Tool versions + model paths | Add version info per check: ffmpeg version, Python version, Ollama version/model tag, whisper model file path + size. Fix suggestions become commands to copy-paste. | ✓ |
| Just more detail per check | Expand each check's message with raw value checked. No new version/size data. | |
| Full debug dump | All of the above plus env vars, config file path/contents, and data dir paths. | |

**User's choice:** Tool versions + model paths (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Per check inline | Show version/path info immediately after each check line, indented. Consistent with existing fix_suggestion display. | ✓ |
| Summary block at bottom | --verbose adds a 'System Details' section at the end; current output unchanged. | |

**User's choice:** Per check inline (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| All checks that have data | Any check that runs a tool or reads a file emits verbose detail. Checks with no meaningful extra data skip verbose. | ✓ |
| Only the tricky hardware checks | Only BlackHoleCheck and FFmpegDeviceCheck emit verbose detail. | |
| All checks always | Every check emits at least one verbose line. | |

**User's choice:** All checks that have data (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Only on failure | Fix suggestions stay as they are — only shown on WARNING or ERROR. Verbose adds details, not fix suggestions for passing checks. | ✓ |
| Always on verbose | In --verbose mode, every check (even OK) shows its fix/reinstall command. | |

**User's choice:** Only on failure (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| My suggestion (Recommended) | BlackHole: device name + channel count. FFmpeg: version string. Python: full version + path. Ollama: running model + version. WhisperModel: model file path + size on disk. Notion: database name (masked token). DiskSpace: free GB. | ✓ |
| Just tool versions | Each check shows the version of its tool only. | |
| Paths and sizes only | No version strings — just file paths and sizes. | |

**User's choice:** My suggestion (Recommended)

---

## meet init wizard completeness

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, collect Notion creds too | ROADMAP 6.2 says: collect Notion token + database ID. All config written in one wizard run. | ✓ |
| No, keep Notion out of init | Notion is optional — user manually edits config.json. | |
| Yes, but make it optional/skippable | Ask for Notion creds but allow skipping. | |

**User's choice:** Yes, collect Notion creds too (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Ask: reconfigure or update | Detect existing config. Prompt for reconfigure everything vs update specific fields. | ✓ |
| Always re-run full wizard | Don't detect existing config — just overwrite. | |
| Show current values as defaults | Pre-fill all prompts with existing values. | |

**User's choice:** Ask: reconfigure or update (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — run doctor inline at end | ROADMAP 6.2 says this explicitly. Run HealthCheckSuite directly (no subprocess). | ✓ |
| No — just tell user to run it | Print message, user runs it manually. | |

**User's choice:** Yes — run doctor inline at end (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Parse + present choices | Parse avfoundation device list into a numbered menu. User picks from list. | ✓ |
| Keep current approach | Show raw ffmpeg stderr, user types index. | |

**User's choice:** Parse + present choices (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Menu: pick fields to update | Show numbered list of config fields with current values (token masked). User picks which to re-enter. | ✓ |
| Always ask all, pre-fill current values | Re-run full wizard with current values as defaults. | |

**User's choice:** Menu: pick fields to update (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — validate inline during init | After user pastes token, call Notion API to verify before writing config. | ✓ |
| No — write config, let doctor validate later | Collect token as-is, write config. | |

**User's choice:** Yes — validate inline during init (Recommended)

---

## README structure and depth

| Option | Description | Selected |
|--------|-------------|----------|
| Full reference with walkthrough | Prerequisites, installation, meet init quickstart, all 6 commands with flags and examples, config file format, troubleshooting section. | ✓ |
| Quickstart-focused | Prerequisites list, installation, core 5-command workflow. No deep reference. | |
| Minimal | What it is, how to install, 'run meet init to get started'. | |

**User's choice:** Full reference with walkthrough (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Step-by-step with ASCII diagram | Numbered steps + ASCII art showing signal routing through BlackHole → ffmpeg → WAV. | ✓ |
| Step-by-step, no diagram | Numbered steps only. | |
| Link to external guide | Brief mention + link to BlackHole GitHub instructions. | |

**User's choice:** Step-by-step with ASCII diagram (Recommended)

---

## Packaging decisions

| Option | Description | Selected |
|--------|-------------|----------|
| Keep <3.15 (current) | The project runs fine on 3.14. '<3.15' accurately reflects what's tested. | ✓ |
| Update to >=3.11 (no upper bound) | Remove the upper bound entirely. | |
| Set to <3.14 per ROADMAP | Conservative; ROADMAP's value was written before 3.14 was proven. | |

**User's choice:** Keep <3.15 (current) (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Keep minimum versions | Minimum bounds are correct for a distributed package. | ✓ |
| Pin to known-good exact versions | Replace '>=' with '==' for reproducibility. | |
| Use version ranges | e.g. 'click>=8.1,<9.0'. | |

**User's choice:** Keep minimum versions (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Keep full history as-is | Honest history including planning docs. | |
| Create a clean code-only branch (gsd:pr-branch) | Filter .planning/ commits, creating a clean branch for distribution. | ✓ |
| Squash to a single release commit | Collapse history to one semantic commit. | |

**User's choice:** Create a clean code-only branch via gsd:pr-branch

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — exclude user data dirs | Add recordings/, transcripts/, notes/ patterns per ROADMAP 6.3. | ✓ |
| No — data lives in XDG dirs | Data is outside the repo directory. No .gitignore entry needed. | |

**User's choice:** Yes — exclude user data dirs (Recommended)

---

## Claude's Discretion

- Exact formatting/layout of `meet init` wizard prompts
- README section ordering and prose style
- Whether to add LICENSE file
- ASCII diagram style and detail level

## Deferred Ideas

None — discussion stayed within phase scope.
