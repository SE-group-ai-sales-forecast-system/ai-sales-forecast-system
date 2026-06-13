"""LightGBM forecaster for Algorithm B."""

from __future__ import annotations

import pickle
from datetime import timedelta
from pathlib import Path
from typing import Any

import lightgbm as lgb
import pandas as pd

from algorithm.feature_engineering import (
    add_lag_features,
    build_training_frame,
    fill_missing_days,
    rows_to_daily_frame,
)

MODEL_DIR = Path(__file__).resolve().parent / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "lightgbm_by_category.pkl"


class LightGBMPredictor:
    """Category-level LightGBM predictor with baseline-compatible output."""

    def __init__(
        self,
        data: Any | None = None,
        model_path: str | Path | None = None,
        lags: list[int] | None = None,
    ):
        self.data = data
        self.lags = lags or [1, 7]
        self.model_path = Path(model_path or DEFAULT_MODEL_PATH)
        self.models: dict[str, lgb.Booster] = {}
        self._daily_cache: pd.DataFrame | None = None

        if self.model_path.exists():
            self.load(self.model_path)
        elif data is not None:
            self.train(data)

    def train(self, data: Any | None = None) -> "LightGBMPredictor":
        frame = build_training_frame(data or self.data, lags=self.lags)
        if frame.empty:
            raise ValueError("Not enough data to train LightGBM (need lag history).")

        feature_cols = [f"lag_{lag}" for lag in self.lags]
        self.models = {}

        for category, group in frame.groupby("category"):
            train_x = group[feature_cols]
            train_y = group["y"]
            if len(group) < 10:
                continue

            dataset = lgb.Dataset(train_x, label=train_y)
            params = {
                "objective": "regression",
                "metric": "mae",
                "learning_rate": 0.05,
                "num_leaves": 31,
                "feature_fraction": 0.9,
                "verbosity": -1,
            }
            self.models[str(category)] = lgb.train(
                params,
                dataset,
                num_boost_round=100,
            )

        self._daily_cache = fill_missing_days(rows_to_daily_frame(data or self.data))
        self.save(self.model_path)
        return self

    def predict(
        self,
        product_id: str,
        days: int = 7,
        data: Any | None = None,
    ) -> dict[str, list[Any]]:
        """Return {"dates": [...], "sales": [...]} for PredictService."""
        horizon = max(1, int(days))
        category = str(product_id)
        daily = fill_missing_days(rows_to_daily_frame(data or self.data or self._daily_cache))
        category_daily = daily[daily["category"] == category].copy()

        if category_daily.empty:
            return self._empty_forecast(horizon)

        if category not in self.models:
            # 未训练该类时，退化为最近7日均值（保证有输出）
            recent_mean = float(category_daily["y"].tail(7).mean())
            last_date = category_daily["ds"].max().date()
            return self._flat_forecast(last_date, horizon, recent_mean)

        working = category_daily.set_index("ds").sort_index()
        history = working["y"].tolist()
        last_date = working.index.max().date()
        predictions: list[float] = []

        for _ in range(horizon):
            lag_values = {}
            for lag in self.lags:
                idx = len(history) - lag
                lag_values[f"lag_{lag}"] = history[idx] if idx >= 0 else 0.0

            pred = float(
                self.models[category].predict(
                    pd.DataFrame([lag_values])
                )[0]
            )
            pred = max(0.0, pred)
            predictions.append(round(pred, 2))
            history.append(pred)

        dates = [
            (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, horizon + 1)
        ]
        return {"dates": dates, "sales": predictions}

    def save(self, path: str | Path | None = None) -> None:
        path = Path(path or self.model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"lags": self.lags, "models": self.models}
        with path.open("wb") as file:
            pickle.dump(payload, file)

    def load(self, path: str | Path | None = None) -> None:
        path = Path(path or self.model_path)
        with path.open("rb") as file:
            payload = pickle.load(file)
        self.lags = payload.get("lags", [1, 7])
        self.models = payload.get("models", {})

    @staticmethod
    def _flat_forecast(last_date, horizon: int, value: float) -> dict[str, list[Any]]:
        dates = [
            (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, horizon + 1)
        ]
        sales = [round(max(0.0, value), 2) for _ in range(horizon)]
        return {"dates": dates, "sales": sales}

    @staticmethod
    def _empty_forecast(horizon: int) -> dict[str, list[Any]]:
        from datetime import datetime

        start = datetime.now().date()
        dates = [
            (start + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, horizon + 1)
        ]
        return {"dates": dates, "sales": [0.0] * horizon}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "data" / "raw" / "global_ecommerce_sales.csv"
    predictor = LightGBMPredictor(csv_path)
    print(predictor.predict("Technology", days=7))