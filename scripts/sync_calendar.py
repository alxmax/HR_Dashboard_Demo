"""Outlook calendar sync — Microsoft Graph protocol + mock provider.

Reads the next 14 days of HR-relevant events from a shared calendar
(training sessions, all-hands, review cycles, recorded leave) and emits
``data/calendar.json`` with a day-by-day summary the dashboard renders
in the sidebar.

Architecture mirrors ``ingest_emails.py``:
- ``CalendarProvider`` protocol abstracts the source
- ``MockGraphProvider`` returns deterministic events for the demo
- ``GraphCalendarProvider`` (commented stub) shows the production path:
  Microsoft Graph ``/me/calendar/events`` with OAuth2 client-credentials
  flow, paged through ``$top=50&$skip=...``

The protocol keeps the parser unit-testable without an Azure tenant.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Iterable, Protocol

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "calendar.json"

REFERENCE_TODAY = date(2026, 5, 14)
WINDOW_DAYS = 14

EVENT_CATEGORIES = {
    "training": "Training",
    "review": "Review cycle",
    "all_hands": "All-hands",
    "leave": "Recorded leave",
    "onboarding": "Onboarding",
    "interview": "Interview",
}


@dataclass(frozen=True)
class CalendarEvent:
    """One calendar entry as returned by an inbox provider."""
    event_id: str
    title: str
    category: str
    start: date
    end: date
    organizer: str
    attendees: int


@dataclass(frozen=True)
class DaySummary:
    """Aggregated day-level view written to ``data/calendar.json``."""
    iso_date: str
    weekday: str   # Mon..Sun
    n_events: int
    intensity: int   # 0..3 — drives heatmap colour in dashboard
    primary_category: str | None
    events: list[dict]


class CalendarProvider(Protocol):
    def fetch_window(self, *, start: date, end: date) -> Iterable[CalendarEvent]: ...


# ───────────────────────────────────────────────────────────────────────
# Production stub — Microsoft Graph (kept here for clarity, unused in demo)
# ───────────────────────────────────────────────────────────────────────

class GraphCalendarProvider:
    """Production path: Microsoft Graph /me/calendar/events.

    Not wired in this demo (would require Azure AD app registration +
    OAuth client_credentials flow + a real tenant). Documented here so the
    swap is mechanical:

        provider = GraphCalendarProvider(
            tenant_id=os.environ["AZ_TENANT_ID"],
            client_id=os.environ["AZ_CLIENT_ID"],
            client_secret=os.environ["AZ_CLIENT_SECRET"],
        )
        events = list(provider.fetch_window(start=today, end=today+14))

    Request shape:
        GET https://graph.microsoft.com/v1.0/users/{shared_calendar}/calendarView
        ?startDateTime=2026-05-14T00:00:00Z&endDateTime=2026-05-28T00:00:00Z
        &$select=id,subject,categories,start,end,organizer,attendees
        &$top=50
        Authorization: Bearer <token>

    Map Graph fields → CalendarEvent:
        subject        → title
        categories[0]  → category (after lowercase + slug)
        start.dateTime → start (parse ISO)
        end.dateTime   → end
        organizer.emailAddress.address → organizer
        len(attendees) → attendees
    """

    def __init__(self, *, tenant_id: str, client_id: str, client_secret: str) -> None:
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret

    def fetch_window(self, *, start: date, end: date) -> Iterable[CalendarEvent]:
        raise NotImplementedError(
            "GraphCalendarProvider is a documentation stub — swap in real "
            "OAuth + requests.get() to enable. Demo uses MockGraphProvider."
        )


# ───────────────────────────────────────────────────────────────────────
# Mock provider — deterministic demo data
# ───────────────────────────────────────────────────────────────────────

class MockGraphProvider:
    """Returns a hard-coded 14-day window for the demo pipeline."""

    def fetch_window(self, *, start: date, end: date) -> Iterable[CalendarEvent]:
        for sample in _MOCK_EVENTS:
            ev = CalendarEvent(**sample)
            if start <= ev.start <= end:
                yield ev


_MOCK_EVENTS = [
    # Day 0 (today: 2026-05-14)
    {"event_id":"evt-001","title":"All-hands · May","category":"all_hands","start":date(2026,5,14),"end":date(2026,5,14),"organizer":"alina.stoica@company.ro","attendees":50},
    {"event_id":"evt-002","title":"Q2 review kick-off","category":"review","start":date(2026,5,14),"end":date(2026,5,14),"organizer":"nicoleta.calin@company.ro","attendees":12},
    # Day 1
    {"event_id":"evt-003","title":"Manager training — feedback skills","category":"training","start":date(2026,5,15),"end":date(2026,5,15),"organizer":"madalina.albu@company.ro","attendees":8},
    {"event_id":"evt-004","title":"Onboarding day 1 — new hires","category":"onboarding","start":date(2026,5,15),"end":date(2026,5,15),"organizer":"dorina.petrescu@company.ro","attendees":3},
    # Day 2 (Sat — quiet)
    # Day 3 (Sun — quiet)
    # Day 4
    {"event_id":"evt-005","title":"Diana Lupu — medical leave","category":"leave","start":date(2026,5,18),"end":date(2026,5,22),"organizer":"system","attendees":1},
    {"event_id":"evt-006","title":"Engineering 1:1s (skip-level)","category":"review","start":date(2026,5,18),"end":date(2026,5,18),"organizer":"bogdan.radu@company.ro","attendees":6},
    # Day 5
    {"event_id":"evt-007","title":"Senior engineer interview panel","category":"interview","start":date(2026,5,19),"end":date(2026,5,19),"organizer":"madalina.albu@company.ro","attendees":4},
    {"event_id":"evt-008","title":"Andrei Cojanu — vacation","category":"leave","start":date(2026,5,19),"end":date(2026,5,26),"organizer":"system","attendees":1},
    # Day 6
    {"event_id":"evt-009","title":"Compensation review — Q2","category":"review","start":date(2026,5,20),"end":date(2026,5,20),"organizer":"mihaela.bratu@company.ro","attendees":5},
    {"event_id":"evt-010","title":"SSM annual refresher","category":"training","start":date(2026,5,20),"end":date(2026,5,20),"organizer":"sebastian.olaru@company.ro","attendees":42},
    # Day 7
    {"event_id":"evt-011","title":"Sergiu Marcu — vacation","category":"leave","start":date(2026,5,20),"end":date(2026,5,27),"organizer":"system","attendees":1},
    # Day 8
    # Day 9 (Sat)
    # Day 10 (Sun)
    # Day 11
    {"event_id":"evt-012","title":"All-hands — Q2 results preview","category":"all_hands","start":date(2026,5,25),"end":date(2026,5,25),"organizer":"alina.stoica@company.ro","attendees":50},
    {"event_id":"evt-013","title":"Hiring panel — Data Science lead","category":"interview","start":date(2026,5,25),"end":date(2026,5,25),"organizer":"andreea.tudor@company.ro","attendees":4},
    # Day 12
    {"event_id":"evt-014","title":"Iulia Constantin — vacation","category":"leave","start":date(2026,5,26),"end":date(2026,6,6),"organizer":"system","attendees":1},
    {"event_id":"evt-015","title":"Performance calibration session","category":"review","start":date(2026,5,26),"end":date(2026,5,26),"organizer":"nicoleta.calin@company.ro","attendees":8},
    # Day 13
    {"event_id":"evt-016","title":"Quarterly skip-levels — Customer Success","category":"review","start":date(2026,5,27),"end":date(2026,5,27),"organizer":"carmen.dobre@company.ro","attendees":7},
]


# ───────────────────────────────────────────────────────────────────────
# Aggregator
# ───────────────────────────────────────────────────────────────────────

def _expand_multiday(events: list[CalendarEvent]) -> dict[date, list[CalendarEvent]]:
    """Expand multi-day events (e.g. 5-day leave) into per-day occurrences."""
    by_day: dict[date, list[CalendarEvent]] = {}
    for ev in events:
        cur = ev.start
        while cur <= ev.end:
            by_day.setdefault(cur, []).append(ev)
            cur += timedelta(days=1)
    return by_day


def _intensity(n: int) -> int:
    """Bucket event count into a 0..3 heatmap intensity."""
    if n == 0: return 0
    if n == 1: return 1
    if n <= 3: return 2
    return 3


def build_calendar(provider: CalendarProvider | None = None) -> dict:
    provider = provider or MockGraphProvider()
    window_start = REFERENCE_TODAY
    window_end = REFERENCE_TODAY + timedelta(days=WINDOW_DAYS - 1)

    events = list(provider.fetch_window(start=window_start, end=window_end))
    by_day = _expand_multiday(events)

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days = []
    for i in range(WINDOW_DAYS):
        d = window_start + timedelta(days=i)
        day_events = by_day.get(d, [])
        cats: dict[str, int] = {}
        for ev in day_events:
            cats[ev.category] = cats.get(ev.category, 0) + 1
        primary = max(cats.items(), key=lambda kv: kv[1])[0] if cats else None
        days.append(asdict(DaySummary(
            iso_date=d.isoformat(),
            weekday=weekdays[d.weekday()],
            n_events=len(day_events),
            intensity=_intensity(len(day_events)),
            primary_category=primary,
            events=[
                {
                    "event_id": ev.event_id,
                    "title": ev.title,
                    "category": ev.category,
                    "organizer": ev.organizer,
                    "attendees": ev.attendees,
                }
                for ev in day_events
            ],
        )))

    return {
        "summary": {
            "reference_today": REFERENCE_TODAY.isoformat(),
            "window_days": WINDOW_DAYS,
            "n_events": len(events),
            "provider": "MockGraphProvider",
            "categories": list(EVENT_CATEGORIES.keys()),
        },
        "days": days,
    }


def main() -> dict:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = build_calendar()
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(
        f"[sync_calendar] wrote {OUT_JSON.name}: "
        f"{payload['summary']['n_events']} events across "
        f"{payload['summary']['window_days']} days"
    )
    return payload


if __name__ == "__main__":
    main()
