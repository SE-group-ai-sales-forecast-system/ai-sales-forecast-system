import unittest
from datetime import datetime

from algorithm.baseline_model import BaselinePredictor


class BaselinePredictorTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"ds": "2026-06-01", "category": "Technology", "y": 10},
            {"ds": "2026-06-02", "category": "Technology", "y": 20},
            {"ds": "2026-06-03", "category": "Technology", "y": 30},
            {"ds": "2026-06-01", "category": "Furniture", "y": 100},
            {"ds": "2026-06-02", "category": "Furniture", "y": 120},
        ]

    def test_predict_days_count(self):
        predictor = BaselinePredictor(self.rows, window=2)

        result = predictor.predict("Technology", days=3)

        self.assertEqual(len(result["dates"]), 3)
        self.assertEqual(len(result["sales"]), 3)

    def test_predict_dates_are_continuous(self):
        predictor = BaselinePredictor(self.rows, window=2)

        result = predictor.predict("Technology", days=2)
        dates = [datetime.strptime(value, "%Y-%m-%d").date() for value in result["dates"]]

        self.assertEqual((dates[1] - dates[0]).days, 1)
        self.assertEqual(result["dates"][0], "2026-06-04")

    def test_predict_sales_are_non_negative(self):
        predictor = BaselinePredictor(self.rows, window=2)

        result = predictor.predict("Technology", days=2)

        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_filters_category(self):
        predictor = BaselinePredictor(self.rows, window=2)

        result = predictor.predict("Technology", days=1)

        self.assertEqual(result["sales"], [25.0])

    def test_predict_supports_raw_order_columns(self):
        rows = [
            {"Order_Date": "2026-06-01", "Product_Category": "Office Supplies", "Quantity": "4"},
            {"Order_Date": "2026-06-02", "Product_Category": "Office Supplies", "Quantity": "8"},
        ]
        predictor = BaselinePredictor(rows, window=7)

        result = predictor.predict("Office Supplies", days=1)

        self.assertEqual(result["sales"], [6.0])

    def test_predict_keeps_zero_sales_days(self):
        rows = [
            {"ds": "2026-06-01", "category": "Technology", "y": 0},
            {"ds": "2026-06-02", "category": "Technology", "y": 10},
        ]
        predictor = BaselinePredictor(rows, window=2)

        result = predictor.predict("Technology", days=1)

        self.assertEqual(result["sales"], [5.0])


if __name__ == "__main__":
    unittest.main()
