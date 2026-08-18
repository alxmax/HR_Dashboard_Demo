---
id: PIPE-INGEST-HR-001
status: baseline
layer: bus
owner: auto
depends_on: []
risk: 2  # every other stage reads these tables - a parsing change propagates everywhere
---

# HR CSV ingest - normalized employee, team and project tables

> Foundation stage. Every downstream stage reads its data through this module, so its
> column names, dtypes and sort order are the shared vocabulary of the pipeline.

## WHAT — Contract (normative)
Every line in this section is binding.

- `load_employees()` reads `sample_data/employees.csv` and returns a pandas DataFrame sorted by `emp_id` with a reset index.
- `load_employees()` parses `hire_date` and `last_review_date` into pandas timestamps.
- `load_employees()` adds `days_since_review`, the whole-day count from `last_review_date` to `REFERENCE_TODAY`, as an integer.
- `REFERENCE_TODAY` is the fixed timestamp `2026-05-13`. The module never reads the wall clock, so repeated runs produce identical output.
- `load_teams()` reads `sample_data/teams.csv` and returns it sorted by `team_id` with a reset index.
- `load_projects()` reads `sample_data/projects.csv`, parses `start_date` and `due_date`, and sorts by `project_id`.
- `load_projects()` adds `kpi_attainment`, the ratio of `kpi_actual` to `kpi_target`.
- `load_projects()` adds the boolean `on_track`: true when `status` is `in_progress` or `completed` and `kpi_attainment` is at least 0.85.
- `load_all()` returns a frozen `HRTables` dataclass holding the employees, teams and projects DataFrames.
- Each loader accepts an optional `path` argument that overrides the default CSV location, so a test can supply a fixture.

## WHAT — Verify intent (open questions for the human)
- `REFERENCE_TODAY` is `2026-05-13` here, but `sync_calendar.py` fixes its own `REFERENCE_TODAY` at `2026-05-14`. Is the one-day gap deliberate, or should both read one shared constant?
- `on_track` uses a 0.85 attainment cut-off. Is that an HR-agreed threshold or a placeholder?
- `kpi_attainment` divides by `kpi_target` with no zero guard. Is a zero target impossible in the source data, or should it yield null rather than infinity?

## HOW — Acceptance (= tests)
- AC-1: Given the shipped `sample_data/employees.csv`, when `load_employees()` runs, then rows ascend by `emp_id` and the index runs 0 to n-1.
- AC-2: Given an employee whose `last_review_date` is 100 days before `REFERENCE_TODAY`, when `load_employees()` runs, then `days_since_review` for that row is 100.
- AC-3: Given a project with status `completed` and attainment 0.84, when `load_projects()` runs, then its `on_track` is false.
- AC-4: Given a project with status `blocked` and attainment 1.2, when `load_projects()` runs, then its `on_track` is false.
- AC-5: Given `load_all()` runs twice, when the two results are compared, then every column is equal.

## WHERE — Current implementation
- `scripts/ingest_hr.py`

## Notes & limitations
- No schema validation. A renamed CSV column surfaces as a `KeyError` deep inside a downstream stage rather than as a clear message here.
