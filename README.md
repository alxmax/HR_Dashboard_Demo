# HR Dashboard

Self-contained HR analytics dashboard with a real Python pipeline behind it.
Double-click `dashboard_demo.html` to open — no server, no build step.

## What this is

A people-operations dashboard built as a portfolio piece. It demonstrates:

- A reproducible Python pipeline (pandas + scikit-learn)
- Two AI modules — **attrition risk** (IsolationForest) and **team-health clustering** (KMeans)
- An **email-automation workflow** — incoming leave requests are parsed and written to a CSV that the dashboard consumes
- A **single-file dashboard** with full drill-down, light/dark theme, English/Romanian toggle, and zero external runtime dependencies

## Open the dashboard

```
double-click dashboard_demo.html
```

The HTML ships with all data inlined as JS constants. Works under `file://` (no local server required).

On Windows, `run_people_pipeline.bat` will rebuild data from the CSV inputs and open the dashboard.

## Tabs

| Tab | What's in it |
|---|---|
| **Overview** | Top KPIs, attainment gauge, retention risk, bench risk, team performance |
| **People** | Full employee table with retention signal, compliance status, next step |
| **Teams** | Per-team cards with KPIs and AI-recommended actions |
| **Inbox & Automation** | Email → CSV intake demo, items needing review, people missing time logs |
| **Legend** | Plain-language definitions for every metric and term in the dashboard |

Click any number, row, or card to drill into the underlying records via a side drawer.
Top-right corner: `EN / RO` and `Dark / Light` toggles, both persistent.

## Pipeline

```
sample_data/*.csv (50 employees · 8 teams · 15 projects)
        │
        ▼
scripts/ingest_hr.py                  ← parse CSVs + derive columns
        │
        ├─► compute_team_metrics.py   → data/kpis.json
        ├─► score_attrition_risk.py   → data/ai_attrition.json     (IsolationForest)
        ├─► cluster_team_health.py    → data/ai_recommendations.json (KMeans, k=3)
        ├─► check_compliance.py       → data/compliance.json       (cert expiry + labor-law)
        └─► ingest_emails.py          → data/time_off.csv          (mock inbox → parser → CSV)
        │
        ▼
scripts/build_people_analytics.py     ← orchestrator (single command)
```

One command rebuilds every artifact:

```
python scripts/build_people_analytics.py
```

Two runs from a clean state produce byte-identical output. Fixed `random_state` on every sklearn module, `sort_keys=True` on every JSON dump, idempotent email intake keyed by message-id hash.

## Email automation

`scripts/ingest_emails.py` demonstrates an inbox → CSV pipeline ready to swap in a real provider:

- `InboxProvider` protocol — `MockInboxProvider` for the demo; replace with Gmail API or Microsoft Graph in production
- Regex + OCR-aware parser for leave types and date ranges
- Romanian + English keyword classification (medical / vacation / training / personal)
- Append-only CSV with full JSON audit log in `data/time_off_audit.jsonl`
- Idempotent: re-running the pipeline never duplicates rows (keyed on a sha1 of the message-id)

The dashboard's **Inbox & Automation** tab surfaces the resulting state — recent intake, parser-flagged items needing review, and people whose missing time logs don't line up with a known leave.

## Tech stack

Python 3.11 · pandas · scikit-learn · vanilla HTML / CSS / JS (no framework, no build step)

## Repository layout

```
.
├── dashboard_demo.html             # self-contained dashboard (~100 KB)
├── run_people_pipeline.bat         # Windows launcher
├── README.md
├── CLAUDE.md                       # context for AI coding assistants
├── sample_data/                    # CSV inputs (raw)
│   ├── employees.csv               # 50 rows, 17 columns
│   ├── teams.csv                   # 8 teams
│   └── projects.csv                # 15 projects
├── scripts/                        # Python pipeline
│   ├── ingest_hr.py
│   ├── compute_team_metrics.py
│   ├── score_attrition_risk.py
│   ├── cluster_team_health.py
│   ├── check_compliance.py
│   ├── ingest_emails.py
│   └── build_people_analytics.py
└── data/                           # generated artifacts
    ├── employees.json
    ├── teams.json
    ├── projects.json
    ├── kpis.json
    ├── ai_attrition.json
    ├── ai_recommendations.json
    ├── compliance.json
    ├── overview.json
    └── time_off.csv
```

## Sample input

```
emp_id | full_name      | role                    | tenure | comp_ratio | perf_score | risk
E001   | Andrei Pop     | Senior Backend Engineer | 4.2    | 1.05       | 4.3        | low
E008   | Diana Lupu     | Junior Backend Engineer | 0.3    | 0.82       | 3.1        | high
```

E001 lands in the low-risk bucket (tenure long, comp at-market, perf high). E008 hits the high-risk bucket on three signals — very short tenure, comp below market, and below-target performance. Same model, same seed, same output every run.

## Run from a clean checkout

```bash
pip install -r requirements.txt
python scripts/build_people_analytics.py
# then double-click dashboard_demo.html
```
