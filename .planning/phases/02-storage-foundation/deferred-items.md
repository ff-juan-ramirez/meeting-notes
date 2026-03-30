# Deferred Items — Phase 02: Storage Foundation

## Pre-existing test failure (out of scope)

**File:** `tests/test_storage.py::test_get_data_dir_default`

**Issue:** Test asserts `get_data_dir()` returns a path ending in `.local/share/meeting-notes`, but `storage.py` was changed in commit `cb3a91a` ("change default folders to store recordings") to return `~/Documents/meeting-notes`. The test was not updated to match the intentional change.

**Status:** Pre-existing before this plan. Not caused by Phase 02 changes. Deferred per deviation rule scope boundary.

**Suggested fix:** Update `test_get_data_dir_default` to assert `str(result).endswith("Documents/meeting-notes")` to match the current `storage.py` implementation.

*Logged: 2026-03-28*
