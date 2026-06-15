"""Evaluation helpers for Algorithm A baseline forecasts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from algorithm.baseline_model import BaselinePredictor
except ImportError:  # pragma: no cover - supports running from algorithm/
    from baseline_model import BaselinePredictor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "global_ecommerce_sales.csv"


def evaluate_baseline_strategies(
    data: Any | None = None,
    window: int = 7,
    alpha: float = 0.2,
) -> list[dict[str, Any]]:
    """Evaluate moving average and simple exponential smoothing by category.

    The evaluation uses one-step-ahead forecasts over each category's dense
    daily sales series and reports MAE for answer/demo documentation.
    """

    source = data if data is not None else DEFAULT_RAW_DATA_PATH
    predictor = BaselinePredictor(source, window=window, alpha=alpha)
    rows = predictor._normalize_rows(source)
    categories = _list_categories(rows)

    results: list[dict[str, Any]] = []
    for category in categories:
        series = predictor._build_daily_series(rows, category)
        values = [series[day] for day in sorted(series)]
        moving_average_mae = _moving_average_mae(values, window)
        smoothing_mae = _exponential_smoothing_mae(values, alpha)
        best_strategy = (
            BaselinePredictor.EXPONENTIAL_SMOOTHING
            if smoothing_mae < moving_average_mae
            else BaselinePredictor.MOVING_AVERAGE
        )

        results.append(
            {
                "category": category,
                "observations": max(0, len(values) - 1),
                "moving_average_mae": round(moving_average_mae, 4),
                "exponential_smoothing_mae": round(smoothing_mae, 4),
                "best_strategy": best_strategy,
            }
        )

    return results


def format_markdown_table(results: list[dict[str, Any]]) -> str:
    """Format evaluation results as a compact Markdown table."""

    lines = [
        "| Category | Observations | Moving Average MAE | Exponential Smoothing MAE | Best Strategy |",
        "|---|---:|---:|---:|---|",
    ]
    for row in results:
        lines.append(
            "| {category} | {observations} | {moving_average_mae:.4f} | "
            "{exponential_smoothing_mae:.4f} | {best_strategy} |".format(**row)
        )
    return "\n".join(lines)


def _list_categories(rows: list[dict[str, Any]]) -> list[str]:
    categories: set[str] = set()
    for row in rows:
        value = _first_present(
            row,
            ["category", "Product_Category", "Product_Name", "product_id"],
        )
        if value is not None:
            categories.add(str(value))
    return sorted(categories)


def _first_present(row: dict[str, Any], keys: list[str]) -> Any | None:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _moving_average_mae(values: list[float], window: int) -> float:
    if len(values) < 2:
        return 0.0

    forecast_window = max(1, int(window))
    errors: list[float] = []
    for index in range(1, len(values)):
        history = values[max(0, index - forecast_window):index]
        forecast = sum(history) / len(history) if history else 0.0
        errors.append(abs(forecast - values[index]))
    return sum(errors) / len(errors)


def _exponential_smoothing_mae(values: list[float], alpha: float) -> float:
    if len(values) < 2:
        return 0.0

    smoothing_alpha = min(1.0, max(0.0, float(alpha)))
    level = values[0]
    errors: list[float] = []
    for actual in values[1:]:
        errors.append(abs(level - actual))
        level = smoothing_alpha * actual + (1 - smoothing_alpha) * level
    return sum(errors) / len(errors)


def main() -> None:
    results = evaluate_baseline_strategies()
    print(format_markdown_table(results))


if __name__ == "__main__":
    main()
