import unittest
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from algorithm.baseline_model import BaselinePredictor
from backend.services.predict_service import PredictService


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

    def test_predict_fills_missing_calendar_days_with_zero(self):
        rows = [
            {"Order_Date": "2026-06-01", "Product_Category": "Office Supplies", "Quantity": "4"},
            {"Order_Date": "2026-06-03", "Product_Category": "Office Supplies", "Quantity": "8"},
        ]
        predictor = BaselinePredictor(rows, window=3)

        result = predictor.predict("Office Supplies", days=1)

        self.assertEqual(result["dates"], ["2026-06-04"])
        self.assertEqual(result["sales"], [4.0])

    def test_predict_keeps_zero_sales_days(self):
        rows = [
            {"ds": "2026-06-01", "category": "Technology", "y": 0},
            {"ds": "2026-06-02", "category": "Technology", "y": 10},
        ]
        predictor = BaselinePredictor(rows, window=2)

        result = predictor.predict("Technology", days=1)

        self.assertEqual(result["sales"], [5.0])

    def test_predict_with_real_raw_csv(self):
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"
        predictor = BaselinePredictor(csv_path, window=7)

        result = predictor.predict("Technology", days=7)

        self.assertEqual(len(result["dates"]), 7)
        self.assertEqual(len(result["sales"]), 7)
        self.assertEqual(result["dates"][0], "2026-01-01")
        self.assertTrue(all(isinstance(value, float) for value in result["sales"]))
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_service_falls_back_to_baseline_when_lightgbm_missing(self):
        service = PredictService()
        service.lightgbm = None

        result = service.predict("Technology", 3, "lightgbm")

        self.assertEqual(len(result["dates"]), 3)
        self.assertEqual(len(result["sales"]), 3)
        self.assertEqual(result["dates"][0], "2026-01-01")
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_service_uses_default_raw_csv_without_uploaded_data(self):
        service = PredictService()

        result = service.predict("Technology", 7, "baseline")

        self.assertEqual(result["dates"][0], "2026-01-01")
        self.assertEqual(len(result["dates"]), 7)
        self.assertEqual(len(result["sales"]), 7)
        self.assertTrue(any(value > 0 for value in result["sales"]))
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_service_supports_required_horizons(self):
        service = PredictService()

        for days in (7, 14, 30):
            with self.subTest(days=days):
                result = service.predict("Technology", days, "baseline")

                self.assertEqual(len(result["dates"]), days)
                self.assertEqual(len(result["sales"]), days)
                self.assertEqual(result["dates"][0], "2026-01-01")
                self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_service_unknown_category_keeps_contract(self):
        service = PredictService()

        result = service.predict("Unknown Category", 7, "baseline")

        self.assertEqual(len(result["dates"]), 7)
        self.assertEqual(len(result["sales"]), 7)
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_service_falls_back_when_lightgbm_raises(self):
        class BrokenLightGBM:
            def predict(self, product_id, days, data=None):
                raise RuntimeError("model file missing")

        service = PredictService()
        service.lightgbm = BrokenLightGBM()

        result = service.predict("Technology", 7, "lightgbm")

        self.assertEqual(result["dates"][0], "2026-01-01")
        self.assertEqual(len(result["dates"]), 7)
        self.assertEqual(len(result["sales"]), 7)
        self.assertTrue(any(value > 0 for value in result["sales"]))
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_service_falls_back_when_lightgbm_returns_bad_contract(self):
        class BadLightGBM:
            def predict(self, product_id, days, data=None):
                return {"dates": [], "sales": []}

        service = PredictService()
        service.lightgbm = BadLightGBM()

        result = service.predict("Technology", 7, "lightgbm")

        self.assertEqual(result["dates"][0], "2026-01-01")
        self.assertEqual(len(result["dates"]), 7)
        self.assertEqual(len(result["sales"]), 7)
        self.assertTrue(any(value > 0 for value in result["sales"]))
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_api_returns_baseline_forecast(self):
        response = self._post_predict(
            {
                "product_id": "Technology",
                "days": 7,
                "model_type": "baseline",
            }
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["product_id"], "Technology")
        self.assertEqual(body["predicted_dates"][0], "2026-01-01")
        self.assertEqual(len(body["predicted_dates"]), 7)
        self.assertEqual(len(body["predicted_sales"]), 7)
        self.assertTrue(any(value > 0 for value in body["predicted_sales"]))
        self.assertTrue(all(value >= 0 for value in body["predicted_sales"]))

    def test_predict_api_uses_default_model_type(self):
        response = self._post_predict(
            {
                "product_id": "Technology",
                "days": 7,
            }
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["product_id"], "Technology")
        self.assertEqual(body["predicted_dates"][0], "2026-01-01")
        self.assertEqual(len(body["predicted_dates"]), 7)
        self.assertEqual(len(body["predicted_sales"]), 7)
        self.assertTrue(all(value >= 0 for value in body["predicted_sales"]))

    def test_predict_api_returns_lightgbm_or_baseline_fallback_forecast(self):
        response = self._post_predict(
            {
                "product_id": "Technology",
                "days": 14,
                "model_type": "lightgbm",
            }
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["product_id"], "Technology")
        self.assertEqual(body["predicted_dates"][0], "2026-01-01")
        self.assertEqual(len(body["predicted_dates"]), 14)
        self.assertEqual(len(body["predicted_sales"]), 14)
        self.assertTrue(all(value >= 0 for value in body["predicted_sales"]))

    def _post_predict(self, payload):
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError:
            self.skipTest("FastAPI is not installed in the current environment")

        from backend.main import app
        from api.predict import get_current_user

        app.dependency_overrides[get_current_user] = lambda: {
            "username": "algorithm-a-test",
            "role": "user",
        }
        try:
            client = TestClient(app)
            response = client.post("/api/predict", json=payload)
        finally:
            app.dependency_overrides.clear()

        return response


if __name__ == "__main__":
    unittest.main()
