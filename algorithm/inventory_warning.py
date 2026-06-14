"""Inventory warning logic for Algorithm B."""

from __future__ import annotations

from typing import Any, Callable

from algorithm.feature_engineering import recent_avg_daily_sales, rows_to_daily_frame

PredictFn = Callable[[str, int], dict[str, list[Any]]]


class InventoryWarningEngine:
    """Simulated inventory warnings by Product_Category."""

    def __init__(
        self,
        data: Any,
        predict_fn: PredictFn | None = None,
        lookback_days: int = 30,
        stock_cover_days: int = 14,
        forecast_horizon: int = 7,
        safety_factor: float = 1.2,
    ):
        self.data = data
        self.predict_fn = predict_fn
        self.lookback_days = lookback_days
        self.stock_cover_days = stock_cover_days
        self.forecast_horizon = forecast_horizon
        self.safety_factor = safety_factor

    def list_categories(self) -> list[str]:
        daily = rows_to_daily_frame(self.data)
        return sorted(daily["category"].astype(str).unique().tolist())

    def compute_warnings(self) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []

        for category in self.list_categories():
            avg_daily = recent_avg_daily_sales(
                self.data, category, lookback_days=self.lookback_days
            )
            current_stock = avg_daily * self.stock_cover_days

            predicted_demand = 0.0
            if self.predict_fn is not None:
                forecast = self.predict_fn(category, self.forecast_horizon)
                predicted_demand = float(sum(forecast.get("sales", [])))

            safe_stock = predicted_demand * self.safety_factor
            is_short = current_stock < safe_stock

            warnings.append(
                {
                    "product_id": category,
                    "product_name": category,
                    "current_stock": int(round(current_stock)),
                    "predicted_demand": int(round(predicted_demand)),
                    "status": "库存不足" if is_short else "正常",
                    "suggested_order": int(round(max(0.0, safe_stock - current_stock)))
                    if is_short
                    else 0,
                }
            )

        warnings.sort(key=lambda x: (x["status"] != "库存不足", x["product_id"]))
        return warnings


def compute_inventory_warnings(
    data: Any,
    predict_fn: PredictFn | None = None,
) -> list[dict[str, Any]]:
    return InventoryWarningEngine(data, predict_fn=predict_fn).compute_warnings()