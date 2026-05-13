"""Ingest raw HR CSVs into normalized DataFrames.

Single entry point: ``load_all()`` returns three DataFrames (employees, teams,
projects) with parsed dates and a few derived columns the downstream modules
expect (``days_since_review``, project ``on_track`` flag, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REFERENCE_TODAY = pd.Timestamp("2026-05-13")


@dataclass(frozen=True)
class HRTables:
    employees: pd.DataFrame
    teams: pd.DataFrame
    projects: pd.DataFrame


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_employees(path: Path | None = None) -> pd.DataFrame:
    path = path or _root() / "sample_data" / "employees.csv"
    df = pd.read_csv(path)
    df["hire_date"] = pd.to_datetime(df["hire_date"])
    df["last_review_date"] = pd.to_datetime(df["last_review_date"])
    df["days_since_review"] = (
        (REFERENCE_TODAY - df["last_review_date"]).dt.days.astype(int)
    )
    return df.sort_values("emp_id").reset_index(drop=True)


def load_teams(path: Path | None = None) -> pd.DataFrame:
    path = path or _root() / "sample_data" / "teams.csv"
    df = pd.read_csv(path)
    return df.sort_values("team_id").reset_index(drop=True)


def load_projects(path: Path | None = None) -> pd.DataFrame:
    path = path or _root() / "sample_data" / "projects.csv"
    df = pd.read_csv(path)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["due_date"] = pd.to_datetime(df["due_date"])
    df["kpi_attainment"] = df["kpi_actual"] / df["kpi_target"]
    df["on_track"] = (df["status"].isin(["in_progress", "completed"])) & (
        df["kpi_attainment"] >= 0.85
    )
    return df.sort_values("project_id").reset_index(drop=True)


def load_all() -> HRTables:
    return HRTables(
        employees=load_employees(),
        teams=load_teams(),
        projects=load_projects(),
    )


if __name__ == "__main__":
    tables = load_all()
    print(
        f"employees={len(tables.employees)} teams={len(tables.teams)} "
        f"projects={len(tables.projects)}"
    )
