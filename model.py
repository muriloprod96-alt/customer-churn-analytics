"""Train an interpretable churn propensity model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_FEATURES = [
    "age",
    "tenure_months",
    "monthly_charges",
    "support_tickets",
    "late_payments",
    "nps",
    "usage_hours",
    "last_login_days",
]
CATEGORICAL_FEATURES = [
    "region",
    "plan",
    "contract",
    "payment_method",
    "auto_pay",
]


def train(data_path: Path, report_dir: Path) -> dict[str, float]:
    data = pd.read_csv(data_path)
    x = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = data["churn"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=y
    )

    transformer = ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", drop="first"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    pipeline = Pipeline(
        [
            ("features", transformer),
            ("model", LogisticRegression(max_iter=2_000, class_weight="balanced")),
        ]
    )
    pipeline.fit(x_train, y_train)
    probability = pipeline.predict_proba(x_test)[:, 1]
    prediction = (probability >= 0.5).astype(int)
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "accuracy": float(accuracy_score(y_test, prediction)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
    }

    feature_names = pipeline.named_steps["features"].get_feature_names_out()
    coefficients = pipeline.named_steps["model"].coef_[0]
    importance = pd.DataFrame(
        {"feature": feature_names, "coefficient": coefficients}
    ).sort_values("coefficient", key=abs, ascending=False)

    report_dir.mkdir(parents=True, exist_ok=True)
    importance.to_csv(report_dir / "model_coefficients.csv", index=False)
    (report_dir / "model_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    (report_dir / "classification_report.txt").write_text(
        classification_report(y_test, prediction), encoding="utf-8"
    )

    top = importance.head(12).sort_values("coefficient")
    colors = ["#0F766E" if value < 0 else "#DC2626" for value in top["coefficient"]]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(top["feature"].str.replace("categorical__", "").str.replace("numeric__", ""), top["coefficient"], color=colors)
    ax.axvline(0, color="#0B1F3A", linewidth=0.8)
    ax.set_title("Principais fatores associados ao churn")
    ax.set_xlabel("Coeficiente da regressão logística")
    fig.tight_layout()
    figures = report_dir / "figures"
    figures.mkdir(exist_ok=True)
    fig.savefig(figures / "model_coefficients.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, default=Path("data/processed/customer_churn_clean.csv")
    )
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    print(json.dumps(train(args.data, args.reports), indent=2))


if __name__ == "__main__":
    main()

