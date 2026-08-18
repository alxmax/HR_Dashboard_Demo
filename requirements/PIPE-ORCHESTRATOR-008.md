---
id: PIPE-ORCHESTRATOR-008
status: baseline
layer: feature
owner: auto
depends_on: [PIPE-INGEST-HR-001, PIPE-TEAM-METRICS-002, PIPE-ATTRITION-003, PIPE-CLUSTER-004, PIPE-COMPLIANCE-005, PIPE-EMAIL-INTAKE-006, PIPE-CALENDAR-007]
risk: 2
---

# Pipeline orchestrator - one command, every artifact, byte-identical on re-run

> The single entry point a developer runs. Determinism is the load-bearing property:
> running it twice from a clean state must leave `data/` byte-identical.

## WHAT — Contract (normative)
Every line in this section is binding.

- `main()` runs the whole pipeline in one command and leaves `data/` holding every artifact the dashboard mirrors.
- Stages run in a fixed order: team metrics, attrition scoring, team clustering, compliance, email intake, calendar sync, then table snapshots and the overview.
- `_materialize_tables()` writes `data/employees.json`, `data/teams.json` and `data/projects.json` from the ingested tables, formatting every date as `YYYY-MM-DD`.
- `_nan_to_none()` replaces float NaN with null, because NaN is not valid JSON and browsers reject the file outright.
- `_dump()` writes every file with `sort_keys=True`, two-space indent and no ASCII escaping, so repeated runs produce byte-identical output.
- `_build_overview()` writes `data/overview.json` carrying the build date, the reference date, the top-line KPIs, the three model summaries, the compliance summary and the stage list.
- The build date comes from the `CI_BUILD_DATE` environment variable when it is set, and from `REFERENCE_TODAY` otherwise, so a reproducibility check can pin it.
- The orchestrator prepends `scripts/` to `sys.path`, which is what lets each stage import its siblings by bare module name.

## WHAT — Verify intent (open questions for the human)
- `pipeline_stages` in `overview.json` lists five stages, but `main()` runs seven. Should email intake and calendar sync be listed, or are they deliberately excluded from the published stage list?
- No stage is wrapped in error handling, so one failure aborts the run and leaves `data/` half-updated. Is fail-fast preferred over building into a temporary directory and swapping on success?
- `_nan_to_none()` only converts top-level float values, not values nested inside dicts or lists. Are nested NaN values impossible for these three tables?

## HOW — Acceptance (= tests)
- AC-1: Given a clean checkout, when the orchestrator runs, then it exits zero and `data/` holds all nine JSON artifacts plus `time_off.csv`.
- AC-2: Given `CI_BUILD_DATE` is pinned, when the pipeline runs twice from a clean state, then every generated JSON file is byte-identical between the two runs.
- AC-3: Given a table column holding NaN, when the tables are materialized, then the matching JSON value is null.
- AC-4: Given `CI_BUILD_DATE` is set to 2026-01-01, when the overview is built, then `overview.json` reports that build date.

## WHERE — Current implementation
- `scripts/build_people_analytics.py`
- `run_people_pipeline.bat` wraps this entry point for Windows.

## Notes & limitations
- The nine JSON artifacts of AC-1 are: `kpis.json`, `ai_attrition.json`, `ai_recommendations.json`, `compliance.json`, `calendar.json`, `employees.json`, `teams.json`, `projects.json` and `overview.json`.
- The dashboard does not consume these artifacts at runtime. `dashboard_demo.html` inlines its own snapshot of the same shapes, so the pipeline output and the dashboard can drift until a bundling step reconciles them.
- `data/time_off_audit.jsonl` is the one non-deterministic output, because it stamps the wall clock. It is git-ignored, which is why AC-2 holds for the JSON artifacts.
