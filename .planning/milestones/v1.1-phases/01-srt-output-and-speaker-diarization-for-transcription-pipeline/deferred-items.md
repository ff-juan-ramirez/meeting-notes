# Deferred Items

Pre-existing test failures found during 01-00 execution. These are out of scope for this plan.

## Pre-existing Test Failures (not caused by 01-00 changes)

1. **tests/test_init.py::test_first_time_init_runs_full_wizard**
   - Failure: init wizard prompts for storage path (new feature added after tests written?)
   - Not related to Wave 0 stubs

2. **tests/test_llm_service.py::test_templates_contain_grounding_rule**
   - Failure: template missing "Base your notes ONLY on what is said in the transcript" grounding rule
   - Not related to Wave 0 stubs

3. **tests/test_storage.py::test_get_data_dir_default**
   - Failure: data dir returns ~/Documents/meeting-notes instead of ~/.local/share/meeting-notes
   - Likely an intentional change to default storage path (see PROJECT.md: "default ~/Documents/meeting-notes")
   - Not related to Wave 0 stubs
