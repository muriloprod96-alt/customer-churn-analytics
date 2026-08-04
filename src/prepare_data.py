"""Validate and enrich raw customer churn data."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "customer_id",
    "signup_date",
    "region",
    "plan",
    "contract",
    "tenure_months",
    "monthly_charges",
    "support_tickets",
    "late_payments",
    "nps",
    "usage_hours",
    "last_login_days",
    "auto_pay",
    "churn",
}


def prepare(raw_path: Path, output_path: Path) -> pd.DataFrame:
    data = pd.read_csv(raw_path)
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if data["customer_id"].duplicated().any():
        raise ValueError("customer_id must be unique")

    data["signup_date"] = pd.to_datetime(data["signup_date"], errors="raise")
    if "churn_date" in data.columns:
        data["churn_date"] = pd.to_datetime(data["churn_date"], errors="coerce")

    numeric = [
        "tenure_months",
        "monthly_charges",
        "support_tickets",
        "late_payments",
        "nps",
        "usage_hours",
        "last_login_days",
        "churn",
    ]
    data[numeric] = data[numeric].apply(pd.to_numeric, errors="raise")
    data["annual_revenue"] = (data["monthly_charges"] * 12).round(2)
    data["revenue_at_risk"] = (data["annual_revenue"] * data["churn"]).round(2)
    data["tenure_band"] = pd.cut(
        data["tenure_months"],
        bins=[0, 6, 12, 24, 48, float("inf")],
        labels=["0–6 meses", "7–12 meses", "13–24 meses", "25–48 meses", "49+ meses"],
    )
    data["engagement_level"] = pd.cut(
        data["usage_hours"],
        bins=[0, 20, 40, float("inf")],
        labels=["Baixo", "Médio", "Alto"],
    )
    risk_score = (
        2 * (data["contract"] == "Mensal").astype(int)
        + 2 * (data["nps"] <= 5).astype(int)
        + (data["support_tickets"] >= 3).astype(int)
        + (data["late_payments"] >= 2).astype(int)
        + (data["last_login_days"] >= 14).astype(int)
        + (data["auto_pay"] == "Não").astype(int)
    )
    data["risk_score"] = risk_score
    data["risk_segment"] = pd.cut(
        risk_score,
        bins=[-1, 1, 3, 8],
        labels=["Baixo", "Médio", "Alto"],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False, date_format="%Y-%m-%d")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("data/raw/customer_churn.csv"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/customer_churn_clean.csv")
    )
    args = parser.parse_args()
    prepared = prepare(args.raw, args.output)
    print(f"Prepared {len(prepared):,} rows at {args.output}")


if __name__ == "__main__":
    main()

