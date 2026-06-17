import unittest
from datetime import datetime
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from algorithm.baseline_model import BaselinePredictor
from algorithm.evaluation import evaluate_baseline_strategies, format_markdown_table
from algorithm.forecast_visualization import (
    build_moving_average_comparison,
    generate_moving_average_chart,
)
from algorithm.inventory_warning import compute_inventory_warnings
from backend.services.predict_service import PredictService

try:
    from algorithm.lightgbm_model import LightGBMPredictor
except ModuleNotFoundError as exc:
    if exc.name != "lightgbm":
        raise
    LightGBMPredictor = None


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

    def test_exponential_smoothing_strategy_keeps_contract(self):
        predictor = BaselinePredictor(
            self.rows,
            strategy="exponential_smoothing",
            alpha=0.5,
        )

        result = predictor.predict("Technology", days=3)

        self.assertEqual(result["dates"][0], "2026-06-04")
        self.assertEqual(len(result["dates"]), 3)
        self.assertEqual(len(result["sales"]), 3)
        self.assertEqual(result["sales"], [22.5, 22.5, 22.5])
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_exponential_smoothing_alpha_boundaries_do_not_crash(self):
        for alpha in (-1, 0, 1, 2, "bad"):
            with self.subTest(alpha=alpha):
                predictor = BaselinePredictor(
                    self.rows,
                    strategy="exponential_smoothing",
                    alpha=alpha,
                )

                result = predictor.predict("Technology", days="bad")

                self.assertEqual(len(result["dates"]), 7)
                self.assertEqual(len(result["sales"]), 7)
                self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_predict_with_real_raw_csv(self):
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"
        predictor = BaselinePredictor(csv_path, window=7)

        result = predictor.predict("Technology", days=7)

        self.assertEqual(len(result["dates"]), 7)
        self.assertEqual(len(result["sales"]), 7)
        self.assertEqual(result["dates"][0], "2026-01-01")
        self.assertTrue(all(isinstance(value, float) for value in result["sales"]))
        self.assertTrue(all(value >= 0 for value in result["sales"]))

    def test_evaluation_reports_real_csv_mae_by_category(self):
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"

        results = evaluate_baseline_strategies(csv_path, window=7, alpha=0.2)
        table = format_markdown_table(results)

        self.assertGreaterEqual(len(results), 4)
        self.assertIn("Technology", {row["category"] for row in results})
        self.assertIn("| Category |", table)
        for row in results:
            self.assertGreater(row["observations"], 0)
            self.assertGreaterEqual(row["moving_average_mae"], 0)
            self.assertGreaterEqual(row["exponential_smoothing_mae"], 0)
            self.assertIn(
                row["best_strategy"],
                {
                    BaselinePredictor.MOVING_AVERAGE,
                    BaselinePredictor.EXPONENTIAL_SMOOTHING,
                },
            )

    def test_forecast_visualization_builds_recent_category_points(self):
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"

        comparisons = build_moving_average_comparison(
            csv_path,
            window=7,
            recent_days=60,
        )

        self.assertEqual(len(comparisons), 4)
        self.assertIn("Technology", {item["category"] for item in comparisons})
        for item in comparisons:
            points = item["points"]
            self.assertEqual(len(points), 60)
            parsed_dates = [
                datetime.strptime(point["date"], "%Y-%m-%d").date()
                for point in points
            ]
            for previous, current in zip(parsed_dates, parsed_dates[1:]):
                self.assertEqual((current - previous).days, 1)
            for point in points:
                self.assertGreaterEqual(point["actual_sales"], 0)
                self.assertGreaterEqual(point["moving_average_sales"], 0)

        fallback_comparisons = build_moving_average_comparison(
            csv_path,
            window="bad",
            recent_days=0,
        )
        self.assertEqual(len(fallback_comparisons[0]["points"]), 60)

    def test_forecast_visualization_generates_non_empty_png(self):
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "moving_average_vs_actual.png"

            generated_path = generate_moving_average_chart(
                csv_path,
                output_path=output_path,
                window=7,
                recent_days=60,
            )

            self.assertEqual(generated_path, output_path)
            self.assertTrue(generated_path.exists())
            self.assertGreater(generated_path.stat().st_size, 0)

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

    def test_predict_service_normalizes_invalid_days_input(self):
        service = PredictService()

        for bad_days in (0, -3, 2.5, True, "bad", None):
            with self.subTest(days=bad_days):
                result = service.predict("Technology", bad_days, "baseline")

                self.assertEqual(result["dates"][0], "2026-01-01")
                self.assertEqual(len(result["dates"]), 7)
                self.assertEqual(len(result["sales"]), 7)
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

    def test_inventory_warning_can_use_predict_service_forecast(self):
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"
        service = PredictService()

        warnings = compute_inventory_warnings(
            csv_path,
            predict_fn=lambda category, days: service.predict(category, days, "baseline"),
        )

        self.assertGreaterEqual(len(warnings), 4)
        for item in warnings:
            self.assertIn("product_id", item)
            self.assertIn("product_name", item)
            self.assertIn("current_stock", item)
            self.assertIn("predicted_demand", item)
            self.assertIn("suggested_order", item)
            self.assertGreaterEqual(item["current_stock"], 0)
            self.assertGreaterEqual(item["predicted_demand"], 0)
            self.assertGreaterEqual(item["suggested_order"], 0)
            self.assertIn(item["status"], {"库存不足", "正常"})

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


class AlgorithmBTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"ds": f"2026-05-{day:02d}", "category": "Technology", "y": 10}
            for day in range(1, 31)
        ]
    def test_inventory_warning_detects_shortage(self):
        def fake_predict(category, days):
            return {"dates": ["x"] * days, "sales": [100.0] * days}
        warnings = compute_inventory_warnings(self.rows, predict_fn=fake_predict)
        tech = next(w for w in warnings if w["product_id"] == "Technology")
        # 日均10 × 14 = 140；预测700 × 1.2 = 840 → 库存不足
        self.assertEqual(tech["status"], "库存不足")
        self.assertGreater(tech["suggested_order"], 0)

    @unittest.skipIf(LightGBMPredictor is None, "lightgbm is not installed")
    def test_lightgbm_predict_output_shape(self):
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"
        predictor = LightGBMPredictor(csv_path)
        result = predictor.predict("Technology", days=7)
        self.assertEqual(len(result["dates"]), 7)
        self.assertEqual(len(result["sales"]), 7)
        self.assertTrue(all(v >= 0 for v in result["sales"]))

if __name__ == "__main__":
    unittest.main()
