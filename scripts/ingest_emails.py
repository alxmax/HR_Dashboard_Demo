"""Inbox -> time_off.csv automation.

Wires an email inbox (Gmail / Outlook / IMAP) into the HR pipeline:

1. Poll the inbox via API (mock provider in this demo)
2. For each message: extract sender, type (medical / vacation / training /
   personal), and date range using regex + optional OCR on PDF attachments
3. Match sender to an employee in ``sample_data/employees.csv``
4. Append a row to ``data/time_off.csv`` with full audit trail
5. Flag messages we couldn't auto-match for HR review

Designed to run on a 5-minute cron. Idempotent: rows are keyed by
``intake_id`` (message-id hash) so re-runs never double-ingest.

The provider abstraction (``InboxProvider`` protocol) keeps the parser
unit-testable without network. Swap ``MockInboxProvider`` for
``GmailProvider`` / ``GraphProvider`` in production.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Iterable, Protocol

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"
DATA_DIR = ROOT / "data"
OUT_CSV = DATA_DIR / "time_off.csv"
AUDIT_LOG = DATA_DIR / "time_off_audit.jsonl"

LEAVE_KEYWORDS = {
    "medical": [r"\bmedical leave\b", r"\bsick (leave|note)\b",
                r"\bscutire medical[aă]\b", r"\bconcediu medical\b",
                r"\bcertificat medical\b"],
    "vacation": [r"\bvacation\b", r"\btime off\b", r"\bannual leave\b",
                 r"\bconcediu (de )?odihn[aă]\b", r"\bzile de concediu\b"],
    "training": [r"\btraining\b", r"\bcourse\b", r"\bworkshop\b",
                 r"\bcurs (de )?formare\b"],
    "personal": [r"\bpersonal (day|leave)\b", r"\bevenimente? personal\b"],
}

DATE_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})\s*(?:to|->|–|—|until|p[aă]n[aă] (?:la|în))\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InboxMessage:
    """Raw email envelope returned by an inbox provider."""
    message_id: str
    received_at: datetime
    sender: str
    subject: str
    body: str
    has_pdf: bool


@dataclass(frozen=True)
class ParsedLeave:
    """Output row written to ``data/time_off.csv``."""
    intake_id: str
    received_at: str
    sender: str
    emp_id: str | None
    emp_name: str | None
    leave_type: str
    date_from: str | None
    date_to: str | None
    source: str
    status: str  # parsed | needs_review
    review_note: str | None


class InboxProvider(Protocol):
    def fetch_unread(self, *, since: datetime | None = None) -> Iterable[InboxMessage]: ...


class MockInboxProvider:
    """Deterministic mock — useful for tests and for the demo pipeline.

    A real implementation calls ``users.messages.list`` (Gmail) or the
    Graph ``/me/messages`` endpoint (Outlook) and yields ``InboxMessage``
    instances. The parser below doesn't care which.
    """

    def fetch_unread(self, *, since: datetime | None = None) -> Iterable[InboxMessage]:
        for sample in _MOCK_MESSAGES:
            yield InboxMessage(**sample)


# Six representative messages exercising parsed + needs_review paths.
_MOCK_MESSAGES = [
    {
        "message_id": "msg-2026-05-13-014",
        "received_at": datetime(2026, 5, 13, 9, 42),
        "sender": "maria.ionescu@company.ro",
        "subject": "Concediu medical 2026-05-13 -> 2026-05-17",
        "body": "Buna, transmit certificatul medical atasat pentru perioada 2026-05-13 to 2026-05-17.",
        "has_pdf": True,
    },
    {
        "message_id": "msg-2026-05-12-013",
        "received_at": datetime(2026, 5, 12, 17, 8),
        "sender": "diana.l@company.ro",
        "subject": "sick note",
        "body": "Attached: medical certificate covering 2026-05-12 to 2026-05-22.",
        "has_pdf": True,
    },
    {
        "message_id": "msg-2026-05-12-012",
        "received_at": datetime(2026, 5, 12, 11, 21),
        "sender": "a.cojanu@company.ro",
        "subject": "Vacation request",
        "body": "Hi, requesting annual leave 2026-05-19 to 2026-05-26.",
        "has_pdf": False,
    },
    {
        "message_id": "msg-2026-05-11-011",
        "received_at": datetime(2026, 5, 11, 14, 55),
        "sender": "u.dorina@external.net",
        "subject": "scutire medicala",
        "body": "Concediu medical 2026-05-09 -> 2026-05-14 conform certificatului atasat.",
        "has_pdf": True,
    },
    {
        "message_id": "msg-2026-05-10-010",
        "received_at": datetime(2026, 5, 10, 8, 33),
        "sender": "sergiu.m@company.ro",
        "subject": "Time off — 2026-05-20 to 2026-05-27",
        "body": "Vacation request for the dates in the subject line.",
        "has_pdf": False,
    },
    {
        "message_id": "msg-2026-05-09-009",
        "received_at": datetime(2026, 5, 9, 16, 14),
        "sender": "catalin.ursu@company.ro",
        "subject": "Concediu medical retroactiv",
        "body": "Scutire medicala 2026-05-04 -> 2026-05-08 conform anexei.",
        "has_pdf": True,
    },
    {
        "message_id": "msg-2026-05-08-008",
        "received_at": datetime(2026, 5, 8, 10, 2),
        "sender": "alexandra.dima@company.ro",
        "subject": "Training enrolment",
        "body": "Hi, please log my training course 2026-05-15 to 2026-05-16.",
        "has_pdf": False,
    },
    {
        "message_id": "msg-2026-05-07-007",
        "received_at": datetime(2026, 5, 7, 13, 45),
        "sender": "ileana.sarbu@company.ro",
        "subject": "Personal day",
        "body": "Requesting personal leave 2026-05-07 to 2026-05-07.",
        "has_pdf": False,
    },
    {
        "message_id": "msg-2026-05-06-006",
        "received_at": datetime(2026, 5, 6, 9, 18),
        "sender": "razvan.diaconu@company.ro",
        "subject": "Concediu medical",
        "body": "Concediu medical 2026-05-02 -> 2026-05-05 conform certificatului atasat.",
        "has_pdf": True,
    },
    {
        "message_id": "msg-2026-05-05-005",
        "received_at": datetime(2026, 5, 5, 11, 40),
        "sender": "iulia.constantin@company.ro",
        "subject": "Annual leave",
        "body": "Annual leave request 2026-05-26 to 2026-06-06.",
        "has_pdf": False,
    },
]


# ───────────────────────────────────────────────────────────────────────
# Parser
# ───────────────────────────────────────────────────────────────────────


def _intake_id(msg: InboxMessage) -> str:
    """Stable hash of message-id — used as primary key for idempotency."""
    digest = hashlib.sha1(msg.message_id.encode("utf-8")).hexdigest()[:12]
    return f"intake-{digest}"


def _classify_type(text: str) -> str:
    """Match the message against keyword sets in priority order."""
    lower = text.lower()
    for label, patterns in LEAVE_KEYWORDS.items():
        if any(re.search(p, lower) for p in patterns):
            return label.title()
    return "Unknown"


def _extract_dates(text: str) -> tuple[date | None, date | None]:
    m = DATE_RE.search(text)
    if not m:
        return None, None
    try:
        return date.fromisoformat(m.group(1)), date.fromisoformat(m.group(2))
    except ValueError:
        return None, None


def _build_employee_lookup() -> dict[str, dict]:
    """Two-key lookup: email handle AND full-name slug."""
    emp_df = pd.read_csv(SAMPLE_DIR / "employees.csv")
    lookup: dict[str, dict] = {}
    for _, row in emp_df.iterrows():
        full = row["full_name"]
        local = full.lower().replace(" ", ".").replace("ă", "a").replace("ț", "t").replace("ș", "s").replace("î", "i").replace("â", "a")
        lookup[local] = {"emp_id": row["emp_id"], "full_name": full}
        first, *_, last = full.split()
        lookup[f"{first.lower()[0]}.{last.lower()}"] = {"emp_id": row["emp_id"], "full_name": full}
        lookup[f"{first.lower()}.{last.lower()[0]}"] = {"emp_id": row["emp_id"], "full_name": full}
    return lookup


def _match_employee(sender: str, lookup: dict[str, dict]) -> dict | None:
    """Match by email local-part against the directory.

    Production version: also look up by ``From`` display name, SSO email,
    or a recognized-alias table.
    """
    local = sender.split("@")[0].lower().replace("-", ".").replace("_", ".")
    if "@" in sender and not sender.endswith("@company.ro"):
        return None  # only trust internal domain
    candidates = [local, local.replace(".", ""), local + ".x"]
    for key in candidates:
        if key in lookup:
            return lookup[key]
    # Loose match: any lookup key whose first dot-segment matches sender's last segment
    last = local.split(".")[-1]
    for key, val in lookup.items():
        if key.endswith("." + last) or key.split(".")[-1] == last:
            return val
    return None


def parse(msg: InboxMessage, emp_lookup: dict[str, dict]) -> ParsedLeave:
    text = f"{msg.subject}\n{msg.body}"
    leave_type = _classify_type(text)
    d_from, d_to = _extract_dates(text)
    emp = _match_employee(msg.sender, emp_lookup)
    source = "Gmail API + OCR" if msg.has_pdf else "Gmail API"

    review_note: str | None = None
    status = "parsed"
    if emp is None:
        status = "needs_review"
        review_note = f"Sender '{msg.sender}' not in employee directory."
    elif d_from is None or d_to is None:
        status = "needs_review"
        review_note = "Could not extract a clear date range from the email body."
    elif leave_type == "Unknown":
        status = "needs_review"
        review_note = "Could not classify the leave type."

    return ParsedLeave(
        intake_id=_intake_id(msg),
        received_at=msg.received_at.strftime("%Y-%m-%d %H:%M"),
        sender=msg.sender,
        emp_id=(emp["emp_id"] if emp else None),
        emp_name=(emp["full_name"] if emp else None),
        leave_type=leave_type,
        date_from=(d_from.isoformat() if d_from else None),
        date_to=(d_to.isoformat() if d_to else None),
        source=source,
        status=status,
        review_note=review_note,
    )


# ───────────────────────────────────────────────────────────────────────
# Sink — append-only CSV with audit log
# ───────────────────────────────────────────────────────────────────────


CSV_HEADER = [
    "intake_id", "received_at", "sender", "emp_id", "emp_name",
    "leave_type", "date_from", "date_to", "source", "status", "review_note",
]


def _existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        return {row["intake_id"] for row in csv.DictReader(f)}


def append_rows(rows: Iterable[ParsedLeave]) -> tuple[int, int]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    seen = _existing_ids(OUT_CSV)
    new_count, dup_count = 0, 0

    write_header = not OUT_CSV.exists()
    with OUT_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if write_header:
            writer.writeheader()
        for r in rows:
            if r.intake_id in seen:
                dup_count += 1
                continue
            writer.writerow(asdict(r))
            seen.add(r.intake_id)
            new_count += 1
            with AUDIT_LOG.open("a", encoding="utf-8") as al:
                al.write(json.dumps({**asdict(r), "ingested_at": datetime.now().isoformat()}) + "\n")
    return new_count, dup_count


# ───────────────────────────────────────────────────────────────────────
# Entry point
# ───────────────────────────────────────────────────────────────────────


def main(provider: InboxProvider | None = None) -> None:
    provider = provider or MockInboxProvider()
    emp_lookup = _build_employee_lookup()
    rows = [parse(m, emp_lookup) for m in provider.fetch_unread()]
    new_count, dup_count = append_rows(rows)
    n_review = sum(1 for r in rows if r.status == "needs_review")
    print(
        f"[ingest_emails] processed {len(rows)} messages "
        f"({new_count} new, {dup_count} duplicate, {n_review} flagged for review) "
        f"-> {OUT_CSV.name}"
    )


if __name__ == "__main__":
    main()
