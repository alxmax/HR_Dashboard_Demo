"""People Analytics pipeline orchestrator — one command, every artifact.

Pipeline order:
  1. ``ingest_hr`` — parse HR CSVs (transitively loaded by the three steps below)
  2. ``compute_team_metrics``   -> ``data/kpis.json``
  3. ``score_attrition_risk``   -> ``data/ai_attrition.json``
  4. ``cluster_team_health``    -> ``data/ai_recommendations.json``
  5. Materialize ``data/{employees,teams,projects}.json`` (table snapshots)
  6. Build ``data/overview.json`` (top-line metrics + run metadata)

Determinism:
  - All sklearn modules use fixed ``random_state``
  - JSON output uses ``sort_keys=True`` to stabilize byte-level diffs
  - The build timestamp is read from ``CI_BUILD_DATE`` env var when present
    (so reproducibility checks in CI compare byte-identical files); otherwise
    falls back to ``REFERENCE_TODAY`` from ``ingest_hr``.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_compliance  # noqa: E402
import cluster_team_health  # noqa: E402
import compute_team_metrics  # noqa: E402
import ingest_emails  # noqa: E402
import score_attrition_risk  # noqa: E402
from ingest_hr import REFERENCE_TODAY, load_all  # noqa: E402


def _dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)


def _nan_to_none(records: list[dict]) -> list[dict]:
    """Replace NaN with None. NaN is invalid JSON per RFC 8259 — node/jq/browsers reject it."""
    import math
    out = []
    for r in records:
        cleaned = {}
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                cleaned[k] = None
            else:
                cleaned[k] = v
        out.append(cleaned)
    return out


def _materialize_tables(out_dir: Path) -> None:
    tables = load_all()

    employees = tables.employees.copy()
    employees["hire_date"] = employees["hire_date"].dt.strftime("%Y-%m-%d")
    employees["last_review_date"] = employees["last_review_date"].dt.strftime(
        "%Y-%m-%d"
    )
    _dump(out_dir / "employees.json", _nan_to_none(employees.to_dict(orient="records")))

    _dump(out_dir / "teams.json", _nan_to_none(tables.teams.to_dict(orient="records")))

    projects = tables.projects.copy()
    projects["start_date"] = projects["start_date"].dt.strftime("%Y-%m-%d")
    projects["due_date"] = projects["due_date"].dt.strftime("%Y-%m-%d")
    projects["kpi_attainment"] = projects["kpi_attainment"].round(3)
    projects["on_track"] = projects["on_track"].astype(bool)
    _dump(out_dir / "projects.json", _nan_to_none(projects.to_dict(orient="records")))

    print(
        f"[build_people_analytics] wrote tables: employees={len(employees)} "
        f"teams={len(tables.teams)} projects={len(projects)}"
    )


def _build_overview(
    out_dir: Path,
    kpis: dict,
    attrition: dict,
    reco: dict,
    compliance: dict,
) -> None:
    build_date = os.environ.get("CI_BUILD_DATE", REFERENCE_TODAY.strftime("%Y-%m-%d"))
    payload = {
        "build_date": build_date,
        "reference_today": REFERENCE_TODAY.strftime("%Y-%m-%d"),
        "top_line": kpis["top_line"],
        "attrition_summary": attrition["summary"],
        "recommendations_summary": reco["summary"],
        "compliance_summary": compliance["summary"],
        "pipeline_stages": [
            {"stage": "ingest_hr", "outputs": ["employees", "teams", "projects"]},
            {"stage": "compute_team_metrics", "outputs": ["data/kpis.json"]},
            {"stage": "score_attrition_risk", "outputs": ["data/ai_attrition.json"]},
            {
                "stage": "cluster_team_health",
                "outputs": ["data/ai_recommendations.json"],
            },
            {"stage": "check_compliance", "outputs": ["data/compliance.json"]},
        ],
    }
    _dump(out_dir / "overview.json", payload)
    print(f"[build_people_analytics] wrote overview.json (build_date={build_date})")


def main() -> None:
    data_dir = ROOT / "data"
    kpis = compute_team_metrics.main()
    attrition = score_attrition_risk.main()
    reco = cluster_team_health.main()
    compliance = check_compliance.main()
    ingest_emails.main()
    _materialize_tables(data_dir)
    _build_overview(data_dir, kpis, attrition, reco, compliance)
    print("[build_people_analytics] done.")


if __name__ == "__main__":
    main()
