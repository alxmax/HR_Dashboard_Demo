---
id: PIPE-EMAIL-INTAKE-006
status: baseline
layer: feature
owner: auto
depends_on: []
risk: 3  # matches a leave request to a named employee; a wrong match writes a wrong record
---

# Email intake - inbox messages parsed into time-off rows

> Turns leave-request emails into `data/time_off.csv` rows. An `InboxProvider`
> protocol (a small interface with one `fetch_unread` method) abstracts the mail
> source, so the parser runs without network access.

## WHAT — Contract (normative)
Every line in this section is binding.

- `main()` turns unread inbox messages into rows in `data/time_off.csv`, one row per message.
- The provider supplies messages: `MockInboxProvider` yields the ten demo messages, and a Gmail or Microsoft Graph provider drops in without touching the parser.
- `_intake_id()` keys each row by the first twelve hex characters of the SHA-1 of the message id, prefixed with `intake-`.
- `append_rows()` skips a message whose `intake_id` already appears in the CSV, so re-running the job never double-ingests.
- `_classify_type()` matches subject and body against English and Romanian keyword sets.
- Keyword sets are tried in the order medical, vacation, training, personal. The first hit wins.
- `_classify_type()` returns `Unknown` when no keyword set matches.
- `_extract_dates()` reads the first `YYYY-MM-DD` to `YYYY-MM-DD` range it finds, accepting `to`, an arrow, a dash, `until` or `pana la` as the separator.
- `_match_employee()` matches the local part of the sender address against the employee directory, and rejects any sender outside the `company.ro` domain.
- `parse()` marks a row `needs_review`, with a stated reason, in three cases: unknown sender, unreadable date range, or unclassified leave type.
- `parse()` marks every other row `parsed`.
- `source` records `Gmail API + OCR` when the message carries a PDF attachment and `Gmail API` when it does not.
- Every newly written row is also appended to `data/time_off_audit.jsonl` with an ingest timestamp.

## WHAT — Verify intent (open questions for the human)
- `_match_employee()` falls back to a loose match on the last dot-segment of the sender, so `a.cojanu@company.ro` matches any directory entry ending in `.cojanu`. With two employees sharing a surname the first iteration order wins silently. Should an ambiguous sender go to `needs_review` instead?
- The candidate key list includes the sender local part with `.x` appended. What directory shape does that suffix target?
- The audit log records `datetime.now()`, the only non-deterministic value the pipeline writes. Git-ignoring the file is the current mitigation. Is that sufficient, or should the timestamp come from the message instead?
- `source` says "Gmail API" regardless of which provider supplied the message. Should it name the actual provider?

## HOW — Acceptance (= tests)
- AC-1: Given a CSV already written by a first run, when `main()` runs again, then it adds no rows.
- AC-2: Given a message from a sender outside `company.ro`, when it is parsed, then its status is `needs_review` and the note names the sender.
- AC-3: Given a body reading `Concediu medical 2026-05-02 -> 2026-05-05`, when it is parsed, then `leave_type` is `Medical`, `date_from` is 2026-05-02 and `date_to` is 2026-05-05.
- AC-4: Given a known sender and no parsable date range, when the message is parsed, then its status is `needs_review`.
- AC-5: Given a message whose `has_pdf` is true, when it is parsed, then `source` is `Gmail API + OCR`.

## WHERE — Current implementation
- `scripts/ingest_emails.py`

## Notes & limitations
- OCR is named in the `source` string but not performed. `has_pdf` is a flag on the mock message, and no attachment is ever read.
- The CSV is append-only. A row corrected by hand is not reconciled on the next run, because idempotency keys on the message id alone.
