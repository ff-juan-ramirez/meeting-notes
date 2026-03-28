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

## Milestone: v1.1 — SRT Output and Speaker Diarization

**Shipped:** 2026-03-28
**Phases:** 1 | **Plans:** 5 | **Timeline:** 1 day (2026-03-27 → 2026-03-28)

### What Was Built

- SRT subtitle generation: `seconds_to_srt_timestamp()` + `generate_srt()` — every `meet transcribe` writes `.srt` alongside `.txt`
- `transcribe_audio()` refactored to return `(text, segments)` tuple; all callers updated in same plan
- `HuggingFaceConfig` dataclass + HF token step in `meet init` wizard (step 3.5)
- Three new health checks: `PyannoteCheck` (ERROR), `HuggingFaceTokenCheck` (WARNING), `PyannoteModelCheck` (WARNING)
- Full speaker diarization: `run_diarization()` + `assign_speakers_to_segments()` + `build_diarized_txt()` with graceful fallback
- `meet summarize` prefers diarized transcript when `diarized_transcript_path` is in metadata
- `meet init --update` flag for non-interactive field updates
- torchaudio≥2.9 compatibility via `torchaudio.list_audio_backends` monkey-patch

### What Worked

- **Gap closure plan (01-04)** as a separate plan was the right call — it kept the main plans clean and gave room to investigate the torchaudio/pyannote import conflict without deadline pressure.
- **RESEARCH.md Pitfall 5** explicitly documenting that diarized content should overwrite `.txt` prevented a design mistake (separate diarized file path). The pitfall list format continues to be high-value.
- **Lazy import** of `pyannote.audio.Pipeline` (inside `run_diarization()`, not at module level) kept startup time unaffected for users without pyannote installed.
- **Graceful fallback design**: diarization failure just logs a warning and falls back to undiarized output — no user-facing error for optional features.

### What Was Inefficient

- **Wave 0 stubs** (01-00) created 17 stubs but only a subset were converted to real tests by the end of the milestone. Stubs without follow-through implementation add maintenance overhead. In future milestones, either skip Wave 0 or commit to converting all stubs.
- **Multiple gap closure iterations**: 01-04 was revised twice based on plan checker feedback. Root cause: planning missed that `meet doctor` didn't wire the new pyannote checks — a discovery that should have happened in 01-02 planning.
- **pyannote version conflict debugging**: the torchaudio.list_audio_backends removal was not documented anywhere upstream. Took a full debug session to root-cause. Should be surfaced in health checks as a first-class check.

### Patterns Established

- **Optional dependency pattern**: wrap import in `try/except ImportError`, return `CheckStatus.ERROR` from the check. Don't propagate ImportError to callers — fail gracefully at the check boundary.
- **Diarization metadata baseline**: always write `diarization_succeeded: false`, `diarized_transcript_path: null`, `speaker_turns: []` even when diarization is skipped — prevents downstream KeyError.
- **Max-overlap speaker assignment**: match pyannote speaker turns to Whisper segments by finding the turn with the greatest temporal overlap per segment (not nearest-start or nearest-end).
- **Monkey-patch for missing library API**: when a dependency removes an API your other dependency calls at import time, inject a shim in your app's init path before the problematic import.

### Key Lessons

1. **Plan gap closure separately.** 01-04 as its own plan let the team close the UAT failures without revisiting already-reviewed plans. The pattern of "execute → UAT → gap closure plan if needed" is worth formalizing.
2. **Lazy import optional dependencies.** Any feature gated on an optional `pip install` should lazy-import inside the function, never at module level. Enforces this as a convention.
3. **Plan checker iterations add time but prevent rework.** The two rounds of 01-04 revision via the checker caught missing wire-up before execution — net time saving despite feeling slow.
4. **torchaudio monkey-patch lesson**: library version upgrades can silently remove APIs that transitive dependencies call at import time. When a new dependency fails to import, trace all `__init__.py` calls before assuming the dependency itself is broken.

### Cost Observations

- Sessions: ~7 plan executions over 1 day
- Notable: Post-MVP feature with integration complexity (pyannote + torchaudio version matrix) shipped in 1 day via gap closure pattern

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 6 | 16 | Initial project — established all patterns |
| v1.1 | 1 | 5 | Gap closure plan pattern + optional dependency pattern |

### Cumulative Quality

| Milestone | Tests | Timeline |
|-----------|-------|----------|
| v1.0 | 208 | 2 days |
| v1.1 | ~225 | 1 day |

### Top Lessons (Verified Across Milestones)

1. Design extension points in the first phase — pluggable architecture scales better than retrofit
2. Pitfalls list in the roadmap is more actionable than research docs for fast execution
3. Gap closure as a named plan pattern keeps main plans clean and UAT failures resolvable without revisiting reviewed work
4. Lazy-import optional dependencies — never at module level, always inside the function that uses them
