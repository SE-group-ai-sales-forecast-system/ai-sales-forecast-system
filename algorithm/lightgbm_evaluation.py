"""Evaluation helpers for Algorithm B (LightGBM)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
import pandas as pd

from algorithm.feature_engineering import build_training_frame

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "global_ecommerce_sales.csv"


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred) -> float:
    diff = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.sqrt(np.mean(diff ** 2)))


def mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate_lightgbm(
    predictor,
    data: Any | None = None,
    test_days: int = 30,
) -> list[dict[str, Any]]:
    """Hold-out last N days per category, one-step-ahead with true lag features."""
    source = data if data is not None else DEFAULT_RAW_DATA_PATH
    frame = build_training_frame(source, lags=predictor.lags)
    rows: list[dict[str, Any]] = []

    for category, group in frame.groupby("category"):
        cat = str(category)
        if cat not in predictor.models:
            continue
        if len(group) <= test_days + max(predictor.lags):
            continue

        test = group.tail(test_days)
        for _, row in test.iterrows():
            features = {f"lag_{lag}": row[f"lag_{lag}"] for lag in predictor.lags}
            pred = float(predictor.models[cat].predict(pd.DataFrame([features]))[0])
            actual = float(row["y"])
            rows.append({"category": cat, "actual": actual, "predicted": pred})

    if not rows:
        return []

    result = pd.DataFrame(rows)
    summary = []
    for category, group in result.groupby("category"):
        summary.append(
            {
                "category": category,
                "observations": len(group),
                "mae": round(mae(group["actual"], group["predicted"]), 4),
                "rmse": round(rmse(group["actual"], group["predicted"]), 4),
                "mape_pct": round(mape(group["actual"], group["predicted"]), 2),
            }
        )
    return summary


def format_lightgbm_markdown_table(results: list[dict[str, Any]]) -> str:
    lines = [
        "| Category | Observations | MAE | RMSE | MAPE(%) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in results:
        lines.append(
            "| {category} | {observations} | {mae:.4f} | {rmse:.4f} | {mape_pct:.2f} |".format(
                **row
            )
        )
    return "\n".join(lines)


def main() -> None:
    try:
        from algorithm.lightgbm_model import LightGBMPredictor
    except ModuleNotFoundError as exc:
        if exc.name == "lightgbm":
            print("LightGBM evaluation skipped: optional dependency 'lightgbm' is not installed.")
            return
        raise

    with TemporaryDirectory() as model_dir:
        predictor = LightGBMPredictor(
            DEFAULT_RAW_DATA_PATH,
            model_path=Path(model_dir) / "lightgbm_by_category.pkl",
        )
        results = evaluate_lightgbm(predictor)
    print(format_lightgbm_markdown_table(results))


if __name__ == "__main__":
    main()
