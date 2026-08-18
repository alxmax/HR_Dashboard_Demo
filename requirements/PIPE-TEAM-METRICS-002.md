---
id: PIPE-TEAM-METRICS-002
status: baseline
layer: bus
owner: auto
depends_on: [PIPE-INGEST-HR-001]
risk: 1
---

# Team KPI rollup - per-team and org-wide people metrics

> Shared capability. The dashboard reads its KPI tab from here, and the team-health
> clusterer reads its feature matrix from the same `build_kpis()` return value.

## WHAT — Contract (normative)
Every line in this section is binding.

- `build_kpis()` returns a dict with two keys: `top_line` for org-wide numbers and `by_team` for one row per team.
- `build_kpis()` groups employees by `team_id` to average tenure, performance score and comp ratio, count headcount, and sum year-to-date training hours.
- `build_kpis()` groups projects by `team_id` to count projects, count on-track projects, and average completion percentage and KPI attainment.
- Both rollups are left-joined onto the team roster, so a team with no employees or no projects still appears in `by_team`.
- `on_track_pct` is on-track projects divided by total projects, rounded to three decimals.
- Values missing after the join become `0`, so a team with no projects reports zero rather than null.
- `top_line` reports headcount, team count, project count, org-wide on-track share, average performance score, average tenure, average comp ratio, total training hours and org KPI attainment.
- `main()` writes the payload to `data/kpis.json` with `sort_keys=True`, creating `data/` when absent.

## WHAT — Verify intent (open questions for the human)
- `fillna(0)` turns a team with zero projects into `on_track_pct: 0`, which the dashboard renders as "0% on track" rather than "no projects". Is that the intended reading?
- Rounding differs per field: three decimals for ratios, two for scores, one for completion. Are those precisions deliberate presentation choices?

## HOW — Acceptance (= tests)
- AC-1: Given the shipped sample data, when `build_kpis()` runs, then `by_team` holds one row per row in `teams.csv`.
- AC-2: Given a team with four projects of which three are on track, when `build_kpis()` runs, then its `on_track_pct` is 0.75.
- AC-3: Given a team in `teams.csv` with no matching projects, when `build_kpis()` runs, then its `projects_total` is 0 and its `on_track_pct` is 0.
- AC-4: Given `main()` runs twice, when the two `data/kpis.json` files are compared, then they are byte-identical.

## WHERE — Current implementation
- `scripts/compute_team_metrics.py`

## Notes & limitations
- `build_kpis()` calls `load_all()` itself instead of accepting injected tables, so a test cannot swap in a fixture without patching the import.
