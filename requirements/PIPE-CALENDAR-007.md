---
id: PIPE-CALENDAR-007
status: baseline
layer: feature
owner: auto
depends_on: []
risk: 1
---

# Calendar sync - fourteen-day window of HR-relevant events

> Mirrors the shape of the email intake stage: a `CalendarProvider` protocol abstracts
> the source, a mock provider serves the demo, and a Microsoft Graph provider is
> documented but deliberately not implemented.

## WHAT — Contract (normative)
Every line in this section is binding.

- `build_calendar()` returns a day-by-day summary covering `WINDOW_DAYS` (14) days starting at `REFERENCE_TODAY` (2026-05-14).
- The provider supplies events. `MockGraphProvider` yields the demo events, and `GraphCalendarProvider` documents the production request shape and field mapping.
- `GraphCalendarProvider.fetch_window()` raises `NotImplementedError`, so swapping it in by accident fails loudly instead of returning an empty calendar.
- `MockGraphProvider` yields only events whose start date falls inside the requested window.
- `_expand_multiday()` repeats a multi-day event on every date it covers, so a five-day leave appears on five days.
- Each day reports its ISO date, three-letter weekday, event count, intensity, and the category holding the most events that day.
- `_intensity()` maps the day event count to a heatmap level from 0 to 3, which the dashboard renders as colour depth.
- The level thresholds are: 0 events gives 0, 1 event gives 1, 2-3 events gives 2, 4 or more events gives 3.
- Every day in the window appears in the output, including days with no events.
- `main()` writes `data/calendar.json` with `sort_keys=True`.

## WHAT — Verify intent (open questions for the human)
- `REFERENCE_TODAY` is 2026-05-14 here and 2026-05-13 in `ingest_hr.py`. Is the one-day offset deliberate, or should both read one shared constant?
- The mock provider filters on start date only, so an event that began before the window but is still running inside it is dropped. Should the real Graph provider behave the same way?
- A tie in `primary_category` is broken by whichever category `max()` reaches first, which depends on insertion order. Should a tie be surfaced instead of hidden?

## HOW — Acceptance (= tests)
- AC-1: Given the mock provider, when `build_calendar()` runs, then `days` holds exactly 14 entries in ascending date order.
- AC-2: Given a leave event spanning 2026-05-18 to 2026-05-22, when the calendar is built, then it appears on all five days.
- AC-3: Given a day holding four events, when its intensity is computed, then the intensity is 3.
- AC-4: Given a day with no events, when it is emitted, then `n_events` is 0, `intensity` is 0 and `primary_category` is null.
- AC-5: Given `GraphCalendarProvider.fetch_window()` is called, when it executes, then it raises `NotImplementedError`.

## WHERE — Current implementation
- `scripts/sync_calendar.py`

## Notes & limitations
- The dashboard does not read `data/calendar.json` at runtime. It renders its own inlined `CALENDAR_DAYS` constant, so the two can drift until a bundling step lands.
