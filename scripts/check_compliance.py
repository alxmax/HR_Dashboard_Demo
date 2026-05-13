"""Compliance checker — flags expired or near-expiry HR certifications.

Tracks four certification types (mandatory under RO labor law for most roles):
  - Periodic medical check (control medical periodic)
  - Occupational safety training (protectia muncii)
  - First-aid certification (prim ajutor)
  - Management training (mandatory for leads / managers only)

For each employee, computes ``days_until_expiry`` per certification, an overall
``status`` (compliant / expiring / expired), and a ``hours_worked_ytd``
flag (over 1800h = high overtime, signals burnout/labor-law risk).

Output: ``data/compliance.json`` with summary + per-employee records.
Deterministic — pure function of CSV input + ``REFERENCE_TODAY``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ingest_hr import REFERENCE_TODAY, load_employees

WARN_DAYS = 60
OVERTIME_THRESHOLD_HOURS = 1800

CERT_COLS = {
    "medical_check_expiry": "Periodic medical check",
    "safety_training_expiry": "Occupational safety",
    "first_aid_cert_expiry": "First aid",
    "mgmt_training_expiry": "Management training",
}


def _days_until(expiry: pd.Timestamp | None) -> int | None:
    if expiry is None or pd.isna(expiry):
        return None
    return int((expiry - REFERENCE_TODAY).days)


def _cert_status(days: int | None) -> str:
    if days is None:
        return "not_required"
    if days < 0:
        return "expired"
    if days <= WARN_DAYS:
        return "expiring"
    return "valid"


def build_compliance() -> dict:
    emp = load_employees()
    for col in CERT_COLS:
        emp[col] = pd.to_datetime(emp[col], errors="coerce")

    records = []
    for _, e in emp.iterrows():
        certs = []
        overall_worst = "valid"
        for col, label in CERT_COLS.items():
            days = _days_until(e[col])
            status = _cert_status(days)
            certs.append(
                {
                    "kind": label,
                    "expiry": e[col].strftime("%Y-%m-%d") if pd.notna(e[col]) else None,
                    "days_until_expiry": days,
                    "status": status,
                }
            )
            if status == "expired":
                overall_worst = "expired"
            elif status == "expiring" and overall_worst != "expired":
                overall_worst = "expiring"

        hours_ytd = int(e["hours_worked_ytd"])
        overtime_flag = hours_ytd >= OVERTIME_THRESHOLD_HOURS
        records.append(
            {
                "emp_id": e["emp_id"],
                "full_name": e["full_name"],
                "team_id": e["team_id"],
                "hours_worked_ytd": hours_ytd,
                "overtime_flag": overtime_flag,
                "overall_cert_status": overall_worst,
                "certifications": certs,
            }
        )

    records.sort(key=lambda r: (
        # expired first, then expiring, then valid; within each, by team
        {"expired": 0, "expiring": 1, "valid": 2}[r["overall_cert_status"]],
        r["emp_id"],
    ))

    summary = {
        "reference_today": REFERENCE_TODAY.strftime("%Y-%m-%d"),
        "warn_window_days": WARN_DAYS,
        "overtime_threshold_hours": OVERTIME_THRESHOLD_HOURS,
        "n_employees": len(records),
        "n_expired": sum(1 for r in records if r["overall_cert_status"] == "expired"),
        "n_expiring": sum(1 for r in records if r["overall_cert_status"] == "expiring"),
        "n_compliant": sum(1 for r in records if r["overall_cert_status"] == "valid"),
        "n_overtime": sum(1 for r in records if r["overtime_flag"]),
        "n_missing_first_aid": sum(
            1 for r in records
            for c in r["certifications"]
            if c["kind"] == "First aid" and c["status"] == "not_required"
        ),
    }
    return {"summary": summary, "records": records}


def main(out_path: Path | None = None) -> dict:
    out_path = (
        out_path
        or Path(__file__).resolve().parents[1] / "data" / "compliance.json"
    )
    payload = build_compliance()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    s = payload["summary"]
    print(
        f"[check_compliance] wrote {out_path.name}: "
        f"{s['n_expired']} expired / {s['n_expiring']} expiring / "
        f"{s['n_compliant']} valid · {s['n_overtime']} over {s['overtime_threshold_hours']}h"
    )
    return payload


if __name__ == "__main__":
    main()
