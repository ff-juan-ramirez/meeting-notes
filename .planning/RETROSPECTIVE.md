# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-24
**Phases:** 6 | **Plans:** 16 | **Timeline:** 2 days (2026-03-22 → 2026-03-23)

### What Was Built

- Full audio capture pipeline: ffmpeg two-device amix with BlackHole 2ch, SIGTERM/SIGKILL lifecycle, atomic state.json (`meet record` / `meet stop`)
- Local mlx-whisper transcription with session resolution, Rich spinner, and metadata persistence (`meet transcribe`)
- Ollama llama3.1:8b note generation with three templates, map-reduce chunking, and strict grounding prompt (`meet summarize`)
- Notion integration: auto-push, ≤1,900-char block splitting, exponential backoff on HTTP 429, notion_url in metadata
- Shared `cli/ui.py` console, TTY detection, `--quiet` flag, `meet list` with Rich table + filters
- Exportable git repo: full `meet init` wizard, `meet doctor --verbose` with per-check detail, README with Audio MIDI Setup ASCII diagram, MIT LICENSE
- 208 tests at ship

### What Worked

- **Pluggable health check ABC** designed in Phase 1 scaled cleanly — each phase added its own checks without touching existing ones. Architecture-first paid off.
- **TDD throughout** kept regressions near zero across 6 phases. Test stubs in Phase 1 (Wave 0) created a contract that made later phases faster.
- **Phase sequencing** was correct — hardware-dependent Phase 1 first meant all later phases had a stable WAV to work with (even in test environments).
- **Pitfall list in ROADMAP.md** surfaced known gotchas (P1–P20) before planning. Prevented multiple bugs that would have required rework.
- **Atomic state.json** via POSIX rename — simple pattern that prevented a whole class of crash-recovery bugs.

### What Was Inefficient

- **REQUIREMENTS.md traceability table** was never updated as phases completed — "Pending" across the board at milestone close. Needs updating at each phase transition, not just milestone close.
- **SUMMARY.md one_liner fields** weren't consistently filled in the YAML frontmatter — gsd-tools fell back to "One-liner:" for several summaries. Either enforce frontmatter format or use `## What Was Built` heading consistently.
- **Roadmap plan counts** (e.g., "2/3 plans executed") were stale in the archived ROADMAP — they tracked planning intent, not execution reality. Should be updated after each plan completes.
- **Phase 02 UAT** left 5 tests blocked (require real WAV hardware) — these will remain blocked until manual testing. Expected for a hardware-dependent project.

### Patterns Established

- **HealthCheck ABC pattern**: subclass implements `check() -> CheckResult` and `verbose_detail() -> str | None`. Register via `HealthCheckSuite.register()`. WARNING severity = non-fatal advisory; ERROR = tool won't work.
- **Session resolution pattern**: derive stem from `wav_path.stem` (not a stored UUID) for correct `--session <stem>` round-trip.
- **run_with_spinner pattern**: `threading.Thread` for background work; Rich Live spinner in main thread; `quiet=True` early-returns `fn()` directly (no thread overhead).
- **read-merge-write metadata**: always read existing JSON, merge new fields, write back — preserves fields from prior phases.
- **TTY detection**: `force_terminal=sys.stdout.isatty()` in shared console constructor — single source of truth.

### Key Lessons

1. **Design the extension point in Phase 1.** The `meet doctor` health check architecture was designed before any checks were written. This meant 5 subsequent phases could add checks without coordination conflicts.
2. **Pitfalls list > research docs for velocity.** The P1–P20 pitfall list in the roadmap was more actionable than generic research. Known edge cases with concrete fixes are what make planning useful.
3. **WARNING vs ERROR severity is a UX decision.** Optional features (Notion, model cache) use WARNING so `meet doctor` still exits 0. Required features (Ollama running) use ERROR. This distinction matters for first-run UX.
4. **mlx-whisper language kwarg gotcha**: passing `language=None` defaults to English — must omit the kwarg entirely for auto-detect. Document this per-dependency in context.
5. **setuptools.build_meta**: legacy backend removed in setuptools 82+. Always use `build-backend = "setuptools.build_meta"` explicitly.

### Cost Observations

- Sessions: ~14 individual plan executions over 2 days
- Notable: Full MVP from scratch in 2 days with 208 tests — GSD parallel wave execution was the key leverage point

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 6 | 16 | Initial project — established all patterns |

### Cumulative Quality

| Milestone | Tests | Timeline |
|-----------|-------|----------|
| v1.0 | 208 | 2 days |

### Top Lessons (Verified Across Milestones)

1. Design extension points in the first phase — pluggable architecture scales better than retrofit
2. Pitfalls list in the roadmap is more actionable than research docs for fast execution
