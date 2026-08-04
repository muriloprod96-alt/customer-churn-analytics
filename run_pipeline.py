"""Run the full local analytics pipeline."""

from pathlib import Path

from analysis import create_outputs
from generate_data import build_dataset
from model import train
from prepare_data import prepare


def main() -> None:
    raw = Path("data/raw/customer_churn.csv")
    processed = Path("data/processed/customer_churn_clean.csv")
    raw.parent.mkdir(parents=True, exist_ok=True)
    build_dataset().to_csv(raw, index=False)
    prepare(raw, processed)
    create_outputs(processed, Path("reports"))
    train(processed, Path("reports"))
    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()

