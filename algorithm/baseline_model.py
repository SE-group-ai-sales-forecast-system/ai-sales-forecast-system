"""Baseline forecasting model for Algorithm A.

The model intentionally keeps the implementation simple and stable:
it predicts future sales with a moving average by default, and can also
use simple exponential smoothing as a conservative backup strategy.
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


class BaselinePredictor:
    """Stable baseline predictor for Algorithm A.

    Supported input shapes:
    - raw order records with ``Order_Date``, ``Product_Category`` or
      ``Product_Name``, and ``Quantity`` columns
    - daily records with ``ds``, ``category``, and ``y`` columns
    - a pandas DataFrame with either of the above schemas
    - a CSV file path with either of the above schemas
    """

    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"

    def __init__(
        self,
        data: Any | None = None,
        window: int = 7,
        strategy: str = MOVING_AVERAGE,
        alpha: float = 0.2,
    ):
        self.data = data
        self.window = self._safe_positive_int(window, default=7)
        self.strategy = self._normalize_strategy(strategy)
        self.alpha = self._normalize_alpha(alpha)

    def predict(
        self,
        product_id: str,
        days: int = 7,
        data: Any | None = None,
        window: int | None = None,
        strategy: str | None = None,
        alpha: float | None = None,
    ) -> dict[str, list[Any]]:
        """Predict future sales for ``product_id``.

        Returns the format expected by ``backend.services.predict_service``:
        ``{"dates": [...], "sales": [...]}``.
        """

        horizon = self._safe_positive_int(days, default=7)
        rows = self._normalize_rows(data if data is not None else self.data)
        series = self._build_daily_series(rows, product_id)
        forecast_window = self._safe_positive_int(window, default=self.window)
        forecast_strategy = self._normalize_strategy(strategy or self.strategy)
        smoothing_alpha = self._normalize_alpha(
            self.alpha if alpha is None else alpha
        )

        if series:
            last_date = max(series)
            values = [series[day] for day in sorted(series)]
            if forecast_strategy == self.EXPONENTIAL_SMOOTHING:
                forecast_value = self._exponential_smoothing(values, smoothing_alpha)
            else:
                recent_values = values[-forecast_window:]
                forecast_value = self._safe_average(recent_values, values)
        else:
            last_date = datetime.now().date()
            forecast_value = 0.0

        dates = [
            (last_date + timedelta(days=offset)).strftime("%Y-%m-%d")
            for offset in range(1, horizon + 1)
        ]
        sales = [round(max(0.0, forecast_value), 2) for _ in range(horizon)]
        return {"dates": dates, "sales": sales}

    def _normalize_rows(self, data: Any | None) -> list[dict[str, Any]]:
        if data is None:
            return []

        if isinstance(data, (str, Path)):
            path = Path(data)
            if not path.exists():
                return []
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                return [dict(row) for row in csv.DictReader(file)]

        if hasattr(data, "to_dict"):
            try:
                return list(data.to_dict(orient="records"))
            except TypeError:
                return list(data.to_dict("records"))

        if isinstance(data, dict):
            return [data]

        if isinstance(data, Iterable):
            return [dict(row) for row in data]

        return []

    def _build_daily_series(
        self,
        rows: list[dict[str, Any]],
        product_id: str,
    ) -> dict[date, float]:
        series: dict[date, float] = {}
        target = str(product_id)

        for row in rows:
            date_value = self._first_present(row, ["ds", "Order_Date", "date"])
            item_value = self._first_present(
                row,
                ["category", "Product_Category", "Product_Name", "product_id"],
            )
            sales_value = self._first_present(row, ["y", "Quantity", "sales"])

            if not date_value or str(item_value) != target:
                continue

            parsed_date = self._parse_date(date_value)
            parsed_sales = self._parse_float(sales_value)
            if parsed_date is None or parsed_sales is None:
                continue

            series[parsed_date] = series.get(parsed_date, 0.0) + parsed_sales

        return self._fill_missing_dates(series)

    def _fill_missing_dates(self, series: dict[date, float]) -> dict[date, float]:
        if not series:
            return {}

        start_date = min(series)
        end_date = max(series)
        days_count = (end_date - start_date).days
        return {
            start_date + timedelta(days=offset): series.get(
                start_date + timedelta(days=offset),
                0.0,
            )
            for offset in range(days_count + 1)
        }

    def _first_present(self, row: dict[str, Any], keys: list[str]) -> Any | None:
        for key in keys:
            if key in row and row[key] is not None:
                return row[key]
        return None

    def _parse_date(self, value: Any):
        if hasattr(value, "date"):
            return value.date()

        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _safe_average(
        self,
        values: list[float],
        fallback_values: list[float],
    ) -> float:
        usable_values = values or fallback_values
        if not usable_values:
            return 0.0
        return sum(usable_values) / len(usable_values)

    def _exponential_smoothing(self, values: list[float], alpha: float) -> float:
        if not values:
            return 0.0

        level = values[0]
        for actual in values[1:]:
            level = alpha * actual + (1 - alpha) * level
        return level

    def _normalize_strategy(self, strategy: str | None) -> str:
        if strategy == self.EXPONENTIAL_SMOOTHING:
            return self.EXPONENTIAL_SMOOTHING
        return self.MOVING_AVERAGE

    def _normalize_alpha(self, alpha: float) -> float:
        try:
            parsed_alpha = float(alpha)
        except (TypeError, ValueError):
            return 0.2
        return min(1.0, max(0.0, parsed_alpha))

    def _safe_positive_int(self, value: Any, default: int) -> int:
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return max(1, int(default))
