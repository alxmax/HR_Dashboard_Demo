"""Team-health clusterer — KMeans on aggregated team metrics.

Groups teams into 3 health buckets (``thriving`` / ``steady`` / ``at_risk``)
and emits a recommended next action per cluster. Deterministic via fixed
``random_state`` + ``n_init``.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from compute_team_metrics import build_kpis

CLUSTER_FEATURES = [
    "avg_perf_score",
    "avg_kpi_attainment",
    "on_track_pct",
    "avg_completion_pct",
    "avg_comp_ratio",
]
RANDOM_STATE = 42
N_CLUSTERS = 3


CLUSTER_PLAYBOOK = {
    "thriving": {
        "label": "thriving",
        "headline": "Protect and replicate",
        "actions": [
            "Document playbook for cross-team reuse",
            "Identify retention risks before competitors do",
            "Promote top contributor as mentor for adjacent teams",
        ],
    },
    "steady": {
        "label": "steady",
        "headline": "Unblock and accelerate",
        "actions": [
            "Audit blocked projects; reassign owners where appropriate",
            "Pair with a thriving team for delivery handoff",
            "Increase mid-cycle KPI check-ins from monthly to biweekly",
        ],
    },
    "at_risk": {
        "label": "at_risk",
        "headline": "Intervene now",
        "actions": [
            "Run skip-level 1:1s with every IC this week",
            "Re-scope at-risk projects with executive sponsor",
            "Trigger retention review for top-performers",
        ],
    },
}


def _name_clusters(centroids: np.ndarray) -> list[str]:
    """Map cluster indices to labels by mean centroid magnitude."""
    means = centroids.mean(axis=1)
    order = np.argsort(-means)
    names = [""] * len(means)
    names[order[0]] = "thriving"
    names[order[-1]] = "at_risk"
    for idx in order[1:-1]:
        names[idx] = "steady"
    return names


def build_recommendations() -> dict:
    kpis = build_kpis()
    teams = kpis["by_team"]

    X = np.array(
        [[t[col] for col in CLUSTER_FEATURES] for t in teams], dtype=float
    )
    Xz = StandardScaler().fit_transform(X)

    km = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=10,
    )
    labels = km.fit_predict(Xz)
    cluster_names = _name_clusters(km.cluster_centers_)

    records = []
    for team, label_idx in zip(teams, labels):
        cluster_name = cluster_names[label_idx]
        play = CLUSTER_PLAYBOOK[cluster_name]
        records.append(
            {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "cluster": cluster_name,
                "cluster_headline": play["headline"],
                "recommended_actions": play["actions"],
                "metrics_used": {col: team[col] for col in CLUSTER_FEATURES},
            }
        )

    records.sort(key=lambda r: r["team_id"])
    summary = {
        "n_teams": len(records),
        "model": "KMeans",
        "n_clusters": N_CLUSTERS,
        "features": CLUSTER_FEATURES,
        "random_state": RANDOM_STATE,
        "distribution": {
            name: sum(1 for r in records if r["cluster"] == name)
            for name in ("thriving", "steady", "at_risk")
        },
    }
    return {"summary": summary, "records": records}


def main(out_path: Path | None = None) -> dict:
    out_path = (
        out_path
        or Path(__file__).resolve().parents[1] / "data" / "ai_recommendations.json"
    )
    payload = build_recommendations()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    dist = payload["summary"]["distribution"]
    print(
        f"[cluster_team_health] wrote {out_path.name}: "
        f"{dist['thriving']} thriving / {dist['steady']} steady / "
        f"{dist['at_risk']} at-risk"
    )
    return payload


if __name__ == "__main__":
    main()
