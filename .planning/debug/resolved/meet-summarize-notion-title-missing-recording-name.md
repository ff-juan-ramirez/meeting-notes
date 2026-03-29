---
status: resolved
trigger: "meet summarize without --title shows wrong Notion title — uses extract_title() instead of recording_name"
created: 2026-03-29T00:00:00Z
updated: 2026-03-29T00:00:00Z
---

## Root Cause

`transcribe.py` built a fresh `metadata` dict and called `write_state(metadata_path, metadata)` — a full replace, not a merge. This wiped `recording_name` (and `recording_slug`, `duration_seconds`) that `meet stop` had written to the metadata JSON.

When `meet summarize` later read `session_metadata.get("recording_name")`, the field was gone → fell back to `extract_title()` → Notion page titled "## Summary".

## Fix

Changed `transcribe.py` to read-merge-write (same pattern as `summarize.py` line 122):

```python
metadata = read_state(metadata_path) or {}
metadata.update({ ... })
write_state(metadata_path, metadata)
```

Commit: `9d6aeb2`

## Symptoms

expected: Notion page title = "Weekly Sync" (from recording_name set via meet record "Weekly Sync")
actual: Notion page title = "## Summary" (first H2 in generated notes, from extract_title())
errors: None — silent wrong behavior
reproduction: meet record "name" → meet transcribe → meet summarize → check Notion title
