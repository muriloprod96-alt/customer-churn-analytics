from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from generate_data import build_dataset  # noqa: E402
from prepare_data import prepare  # noqa: E402


class PipelineTests(unittest.TestCase):
    def test_generated_dataset_has_expected_shape_and_target(self):
        data = build_dataset(rows=500, seed=7)
        self.assertEqual(len(data), 500)
        self.assertTrue(data["customer_id"].is_unique)
        self.assertTrue(set(data["churn"].unique()).issubset({0, 1}))
        self.assertGreater(data["churn"].mean(), 0.08)
        self.assertLess(data["churn"].mean(), 0.65)

    def test_prepare_creates_business_features(self):
        with TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.csv"
            output = Path(directory) / "clean.csv"
            build_dataset(rows=100, seed=9).to_csv(raw, index=False)
            prepared = prepare(raw, output)
            self.assertTrue(output.exists())
            self.assertIn("annual_revenue", prepared.columns)
            self.assertIn("risk_segment", prepared.columns)
            self.assertFalse(pd.isna(prepared["risk_segment"]).any())


if __name__ == "__main__":
    unittest.main()