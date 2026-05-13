"""Per-team people-metric rollup feeding the KPIs tab of the dashboard."""
from __future__ import annotations

import json
from pathlib import Path

from ingest_hr import load_all


def build_kpis() -> dict:
    tables = load_all()
    emp, teams, proj = tables.employees, tables.teams, tables.projects

    by_team_emp = emp.groupby("team_id").agg(
        avg_tenure_years=("tenure_years", "mean"),
        avg_perf_score=("perf_score", "mean"),
        avg_comp_ratio=("comp_ratio", "mean"),
        headcount_actual=("emp_id", "count"),
        training_hours_total=("training_hours_ytd", "sum"),
    )
    by_team_proj = proj.groupby("team_id").agg(
        projects_total=("project_id", "count"),
        projects_on_track=("on_track", "sum"),
        avg_completion_pct=("completion_pct", "mean"),
        avg_kpi_attainment=("kpi_attainment", "mean"),
    )
    rollup = teams.merge(by_team_emp, on="team_id", how="left").merge(
        by_team_proj, on="team_id", how="left"
    )
    rollup["on_track_pct"] = (
        rollup["projects_on_track"] / rollup["projects_total"]
    ).round(3)
    rollup = rollup.fillna(0)

    # Top-line KPIs (org-wide)
    top = {
        "headcount_total": int(emp.shape[0]),
        "teams_total": int(teams.shape[0]),
        "projects_total": int(proj.shape[0]),
        "projects_on_track_pct": round(float(proj["on_track"].mean()), 3),
        "avg_perf_score": round(float(emp["perf_score"].mean()), 2),
        "avg_tenure_years": round(float(emp["tenure_years"].mean()), 2),
        "avg_comp_ratio": round(float(emp["comp_ratio"].mean()), 3),
        "training_hours_ytd_total": int(emp["training_hours_ytd"].sum()),
        "kpi_attainment_org": round(float(proj["kpi_attainment"].mean()), 3),
    }

    team_rows = []
    for _, row in rollup.iterrows():
        team_rows.append(
            {
                "team_id": row["team_id"],
                "team_name": row["team_name"],
                "department": row["department"],
                "headcount": int(row["headcount_actual"]),
                "annual_budget_eur": int(row["annual_budget_eur"]),
                "avg_perf_score": round(float(row["avg_perf_score"]), 2),
                "avg_tenure_years": round(float(row["avg_tenure_years"]), 2),
                "avg_comp_ratio": round(float(row["avg_comp_ratio"]), 3),
                "projects_total": int(row["projects_total"]),
                "projects_on_track": int(row["projects_on_track"]),
                "on_track_pct": float(row["on_track_pct"]),
                "avg_completion_pct": round(float(row["avg_completion_pct"]), 1),
                "avg_kpi_attainment": round(float(row["avg_kpi_attainment"]), 3),
                "training_hours_total": int(row["training_hours_total"]),
            }
        )

    return {"top_line": top, "by_team": team_rows}


def main(out_path: Path | None = None) -> dict:
    out_path = out_path or Path(__file__).resolve().parents[1] / "data" / "kpis.json"
    payload = build_kpis()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(f"[compute_team_metrics] wrote {out_path.name}: "
          f"{len(payload['by_team'])} team rows")
    return payload


if __name__ == "__main__":
    main()
