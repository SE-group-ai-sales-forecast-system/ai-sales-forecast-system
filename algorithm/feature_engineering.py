"""Feature engineering for Algorithm B (LightGBM)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


def rows_to_daily_frame(data: Any) -> pd.DataFrame:
    """Normalize raw orders or daily_sales into (ds, category, y)."""
    if isinstance(data, (str, Path)):
        df = pd.read_csv(data)
    elif hasattr(data, "to_dict"):
        df = data.copy()
    else:
        df = pd.DataFrame(list(data))

    if "ds" in df.columns and "category" in df.columns and "y" in df.columns:
        daily = df[["ds", "category", "y"]].copy()
    else:
        date_col = "Order_Date" if "Order_Date" in df.columns else "date"
        cat_col = "Product_Category" if "Product_Category" in df.columns else "category"
        qty_col = "Quantity" if "Quantity" in df.columns else "y"
        daily = (
            df.assign(ds=pd.to_datetime(df[date_col], errors="coerce"))
            .groupby(["ds", cat_col], as_index=False)[qty_col]
            .sum()
            .rename(columns={cat_col: "category", qty_col: "y"})
        )

    daily["ds"] = pd.to_datetime(daily["ds"], errors="coerce")
    daily["y"] = pd.to_numeric(daily["y"], errors="coerce").fillna(0.0)
    daily["category"] = daily["category"].astype(str)
    return daily.dropna(subset=["ds"]).sort_values(["category", "ds"])


def fill_missing_days(daily: pd.DataFrame) -> pd.DataFrame:
    """Fill calendar gaps with zero sales per category."""
    frames: list[pd.DataFrame] = []
    for category, group in daily.groupby("category"):
        start = group["ds"].min()
        end = group["ds"].max()
        full_index = pd.date_range(start, end, freq="D")
        expanded = (
            group.set_index("ds")
            .reindex(full_index, fill_value=0.0)
            .rename_axis("ds")
            .reset_index()
        )
        expanded["category"] = category
        frames.append(expanded)
    return pd.concat(frames, ignore_index=True)


def add_lag_features(
    daily: pd.DataFrame,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """Add lag features grouped by category."""
    lags = lags or [1, 7]
    df = fill_missing_days(daily)
    for lag in lags:
        df[f"lag_{lag}"] = df.groupby("category")["y"].shift(lag)
    return df


def build_training_frame(
    data: Any,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """Return feature table ready for LightGBM training."""
    daily = rows_to_daily_frame(data)
    featured = add_lag_features(daily, lags=lags)
    lag_cols = [col for col in featured.columns if col.startswith("lag_")]
    return featured.dropna(subset=lag_cols).reset_index(drop=True)


def recent_avg_daily_sales(
    data: Any,
    category: str,
    lookback_days: int = 30,
) -> float:
    """Average daily sales in the last N calendar days."""
    daily = fill_missing_days(rows_to_daily_frame(data))
    subset = daily[daily["category"] == str(category)]
    if subset.empty:
        return 0.0

    end_date = subset["ds"].max().date()
    start_date = end_date - timedelta(days=lookback_days - 1)
    window = subset[
        (subset["ds"].dt.date >= start_date) & (subset["ds"].dt.date <= end_date)
    ]
    total = float(window["y"].sum())
    return total / lookback_days