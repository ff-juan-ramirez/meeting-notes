# Phase 02: Sessions & Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Downstream agents read `02-CONTEXT.md` instead.

**Date:** 2026-03-30
**Facilitator:** Claude (gsd:discuss-phase)

---

## Area 1: Worker Progress UX

**Q: While transcription or summarization is running, what should the detail panel look like?**

Options presented:
- Buttons disabled + status label *(Recommended)*
- Spinner replaces button
- Progress bar below buttons

**Selected:** Buttons disabled + status label
> Preview confirmed: Transcribe/Summarize buttons both disable; status label below shows progress text.

---

**Q: After the operation completes, how should the detail panel update?**

Options presented:
- Auto-refresh + status clears *(Recommended)*
- Auto-refresh + success banner
- Manual refresh required

**Selected:** Auto-refresh + status clears
> Panel reloads session metadata from disk; status label clears; button states update based on new session status.

---

## Area 2: Empty State

**Q: When the user opens Sessions with no recorded sessions yet, what should the left panel show?**

Options presented:
- Centered placeholder message *(Recommended)*
- Plain empty list
- Empty list + link to Record

**Selected:** Centered placeholder message
> "No sessions yet. Start a recording to get started." — filter bar still shows above.

---

**Q: When nothing is selected, what should the right detail panel show?**

Options presented:
- Select-a-session prompt *(Recommended)*
- Right panel hidden until selection
- Right panel shows empty template

**Selected:** Select-a-session prompt
> "Select a session to view details." centered in the right panel. No action buttons shown.

---

## Area 3: Dashboard Recording Indicator

**Q: How should the active recording state look on the Dashboard?**

Options presented:
- Status pill with color change *(Recommended)*
- Status label + elapsed time as separate fields
- Large indicator block

**Selected:** Status pill with color change
> Gray pill = "Idle"; red pill = "● Recording • 0:03:42". Compact, inline with the action button.

---

**Q: Should the "Stop" button on the Dashboard stop the recording inline, or navigate to Record view?**

Options presented:
- Navigate to Record view *(Recommended)*
- Stop inline from Dashboard

**Selected:** Navigate to Record view
> "Go to Record" when recording is active; navigates to Record view (which owns the stop action). Dashboard does not invoke StopWorker directly.

---

*Discussion complete — context written to 02-CONTEXT.md*
