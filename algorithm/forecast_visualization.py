"""Generate presentation charts for Algorithm A baseline forecasts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ModuleNotFoundError:  # pragma: no cover - exercised by CLI environment
    plt = None

try:
    from algorithm.baseline_model import BaselinePredictor
    from algorithm.evaluation import _list_categories
except ImportError:  # pragma: no cover - supports running from algorithm/
    from baseline_model import BaselinePredictor
    from evaluation import _list_categories


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "global_ecommerce_sales.csv"
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "testing"
    / "images"
    / "moving_average_vs_actual_0617.png"
)


def build_moving_average_comparison(
    data: Any | None = None,
    window: int = 7,
    recent_days: int = 60,
) -> list[dict[str, Any]]:
    """Build actual vs one-step moving average points for each category."""

    source = data if data is not None else DEFAULT_RAW_DATA_PATH
    predictor = BaselinePredictor(source, window=window)
    rows = predictor._normalize_rows(source)
    categories = _list_categories(rows)
    forecast_window = _safe_positive_int(window, default=7)
    display_days = _safe_positive_int(recent_days, default=60)

    comparisons: list[dict[str, Any]] = []
    for category in categories:
        series = predictor._build_daily_series(rows, category)
        dates = sorted(series)
        actual_values = [max(0.0, series[day]) for day in dates]
        moving_average_values = _one_step_moving_average(actual_values, forecast_window)

        points = [
            {
                "date": day.strftime("%Y-%m-%d"),
                "actual_sales": round(actual, 2),
                "moving_average_sales": round(max(0.0, forecast), 2),
            }
            for day, actual, forecast in zip(
                dates[-display_days:],
                actual_values[-display_days:],
                moving_average_values[-display_days:],
            )
        ]
        comparisons.append({"category": category, "points": points})

    return comparisons


def generate_moving_average_chart(
    data: Any | None = None,
    output_path: str | Path | None = None,
    window: int = 7,
    recent_days: int = 60,
) -> Path:
    """Generate a PNG chart for presentation and return the output path."""

    if plt is None:
        raise RuntimeError("matplotlib is required to generate forecast charts")

    comparisons = build_moving_average_comparison(data, window, recent_days)
    target = Path(output_path) if output_path is not None else DEFAULT_OUTPUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    figure, axes = plt.subplots(2, 2, figsize=(14, 8), constrained_layout=True)
    flat_axes = axes.flatten()

    for axis, item in zip(flat_axes, comparisons):
        points = item["points"]
        x_values = [point["date"] for point in points]
        actual_values = [point["actual_sales"] for point in points]
        forecast_values = [point["moving_average_sales"] for point in points]

        axis.plot(x_values, actual_values, label="Actual Sales", linewidth=1.8)
        axis.plot(
            x_values,
            forecast_values,
            label="7-Day Moving Average",
            linewidth=1.8,
        )
        axis.set_title(item["category"])
        axis.set_xlabel("Date")
        axis.set_ylabel("Daily Sales")
        axis.tick_params(axis="x", labelrotation=45, labelsize=8)
        axis.grid(True, alpha=0.25)
        axis.legend(loc="upper left", fontsize=8)

        step = max(1, len(x_values) // 6)
        for index, label in enumerate(axis.get_xticklabels()):
            label.set_visible(index % step == 0 or index == len(x_values) - 1)

    for axis in flat_axes[len(comparisons):]:
        axis.set_visible(False)

    figure.suptitle(
        "Moving Average Forecast vs Actual Sales (Last 60 Days)",
        fontsize=14,
        fontweight="bold",
    )
    figure.savefig(target, dpi=150)
    plt.close(figure)
    return target


def _one_step_moving_average(values: list[float], window: int) -> list[float]:
    forecasts: list[float] = []
    forecast_window = _safe_positive_int(window, default=7)
    for index, _ in enumerate(values):
        history = values[max(0, index - forecast_window):index]
        forecasts.append(sum(history) / len(history) if history else 0.0)
    return forecasts


def _safe_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return parsed if parsed > 0 else max(1, int(default))


def main() -> None:
    output_path = generate_moving_average_chart()
    print(f"Generated forecast comparison chart: {output_path}")


if __name__ == "__main__":
    main()
