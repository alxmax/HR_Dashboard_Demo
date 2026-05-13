"""Attrition risk scorer — IsolationForest on engineered HR features.

For each employee, produces:
  - ``risk_score`` in [0, 1] (higher = more anomalous / at risk)
  - ``risk_label`` in {low, medium, high}
  - top three contributing features (signed standardized values)

Determinism: fixed ``random_state``, sorted output by ``emp_id``.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ingest_hr import load_employees

FEATURE_COLS = [
    "tenure_years",
    "comp_ratio",
    "perf_score",
    "days_since_review",
    "promotions_count",
    "training_hours_ytd",
]
RANDOM_STATE = 42


def _label(score: float) -> str:
    if score >= 0.66:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


def _top_features(row: np.ndarray, names: list[str]) -> list[dict]:
    abs_vals = np.abs(row)
    top_idx = np.argsort(-abs_vals)[:3]
    return [
        {"feature": names[i], "z": round(float(row[i]), 2)}
        for i in top_idx
    ]


def build_attrition() -> dict:
    emp = load_employees()
    X = emp[FEATURE_COLS].to_numpy(dtype=float)

    scaler = StandardScaler()
    Xz = scaler.fit_transform(X)

    iso = IsolationForest(
        n_estimators=200,
        contamination=0.2,
        random_state=RANDOM_STATE,
    )
    iso.fit(Xz)
    raw_scores = -iso.score_samples(Xz)  # higher = more anomalous
    lo, hi = float(raw_scores.min()), float(raw_scores.max())
    norm = (raw_scores - lo) / (hi - lo) if hi > lo else np.zeros_like(raw_scores)

    rows = []
    for i, (_, employee) in enumerate(emp.iterrows()):
        score = float(round(norm[i], 3))
        rows.append(
            {
                "emp_id": employee["emp_id"],
                "full_name": employee["full_name"],
                "team_id": employee["team_id"],
                "risk_score": score,
                "risk_label": _label(score),
                "top_signals": _top_features(Xz[i], FEATURE_COLS),
            }
        )

    rows.sort(key=lambda r: r["emp_id"])
    summary = {
        "n_employees": len(rows),
        "n_high_risk": sum(1 for r in rows if r["risk_label"] == "high"),
        "n_medium_risk": sum(1 for r in rows if r["risk_label"] == "medium"),
        "n_low_risk": sum(1 for r in rows if r["risk_label"] == "low"),
        "model": "IsolationForest",
        "features": FEATURE_COLS,
        "random_state": RANDOM_STATE,
    }
    return {"summary": summary, "records": rows}


def main(out_path: Path | None = None) -> dict:
    out_path = (
        out_path
        or Path(__file__).resolve().parents[1] / "data" / "ai_attrition.json"
    )
    payload = build_attrition()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(
        f"[score_attrition_risk] wrote {out_path.name}: "
        f"{payload['summary']['n_high_risk']} high / "
        f"{payload['summary']['n_medium_risk']} medium / "
        f"{payload['summary']['n_low_risk']} low"
    )
    return payload


if __name__ == "__main__":
    main()
