"""Generate a deterministic synthetic customer churn dataset.

The project deliberately avoids real customer data. Relationships between
features and churn are simulated so the analysis has realistic business
patterns without exposing personal information.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


SNAPSHOT_DATE = pd.Timestamp("2026-06-30")


def sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-value))


def build_dataset(rows: int = 5_000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    customer_id = [f"CUST-{i:05d}" for i in range(1, rows + 1)]
    region = rng.choice(
        ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"],
        rows,
        p=[0.43, 0.18, 0.22, 0.10, 0.07],
    )
    age = np.clip(rng.normal(39, 12, rows).round(), 18, 75).astype(int)
    plan = rng.choice(["Básico", "Padrão", "Premium"], rows, p=[0.38, 0.44, 0.18])
    contract = rng.choice(
        ["Mensal", "Anual", "Bienal"], rows, p=[0.57, 0.31, 0.12]
    )
    payment_method = rng.choice(
        ["Cartão", "Pix", "Boleto", "Débito automático"],
        rows,
        p=[0.34, 0.28, 0.22, 0.16],
    )
    tenure_months = np.clip(rng.gamma(2.4, 12, rows).round(), 1, 72).astype(int)
    base_charge = pd.Series(plan).map({"Básico": 59, "Padrão": 99, "Premium": 159}).to_numpy()
    monthly_charges = np.maximum(39, base_charge + rng.normal(0, 14, rows)).round(2)
    support_tickets = np.clip(rng.poisson(1.7, rows), 0, 10)
    late_payments = np.clip(rng.poisson(0.65, rows), 0, 6)
    nps = np.clip(np.rint(rng.normal(7.1, 2.1, rows)), 0, 10).astype(int)
    usage_hours = np.clip(rng.gamma(4.2, 8.5, rows), 1, 120).round(1)
    last_login_days = np.clip(rng.gamma(1.5, 5.5, rows).round(), 0, 60).astype(int)
    auto_pay = rng.choice(["Sim", "Não"], rows, p=[0.56, 0.44])

    score = (
        -2.0
        + 1.05 * (contract == "Mensal")
        + 0.52 * (tenure_months <= 6)
        + 0.18 * support_tickets
        + 0.25 * late_payments
        - 0.20 * (nps - 5)
        + 0.045 * last_login_days
        - 0.58 * (auto_pay == "Sim")
        - 0.30 * (plan == "Premium")
        + 0.006 * (monthly_charges - 90)
        - 0.009 * (usage_hours - 30)
    )
    churn_probability = sigmoid(score)
    churn = rng.binomial(1, churn_probability)

    signup_date = SNAPSHOT_DATE - pd.to_timedelta(tenure_months * 30, unit="D")
    signup_date -= pd.to_timedelta(rng.integers(0, 30, rows), unit="D")
    churn_offset = np.minimum(
        tenure_months * 30,
        rng.integers(7, 181, rows),
    )
    churn_date = np.where(
        churn == 1,
        (SNAPSHOT_DATE - pd.to_timedelta(churn_offset, unit="D")).strftime("%Y-%m-%d"),
        "",
    )

    frame = pd.DataFrame(
        {
            "customer_id": customer_id,
            "signup_date": signup_date.strftime("%Y-%m-%d"),
            "region": region,
            "age": age,
            "plan": plan,
            "contract": contract,
            "payment_method": payment_method,
            "tenure_months": tenure_months,
            "monthly_charges": monthly_charges,
            "support_tickets": support_tickets,
            "late_payments": late_payments,
            "nps": nps,
            "usage_hours": usage_hours,
            "last_login_days": last_login_days,
            "auto_pay": auto_pay,
            "churn": churn,
            "churn_date": churn_date,
        }
    )
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/customer_churn.csv"),
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_dataset(args.rows, args.seed).to_csv(args.output, index=False)
    print(f"Generated {args.rows:,} rows at {args.output}")


if __name__ == "__main__":
    main()

