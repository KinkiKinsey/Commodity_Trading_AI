"""
Machine Learning Moving Average indicator (Gaussian RBF) adapted for backend use.

The implementation is ported from Ringshell_source_code/Tech_Index/rbf.py with
console printing and plotting dependencies removed. The function returns a
dictionary containing both the computed series and textual analysis that can be
consumed by downstream services.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _rbf_kernel(x1: np.ndarray, x2: np.ndarray, length_scale: float) -> np.ndarray:
    """Gaussian RBF kernel."""
    return np.exp(-((x1 - x2) ** 2) / (2 * (length_scale ** 2)))


def ml_moving_average(
    df: pd.DataFrame,
    window: int = 50,
    sigma: float = 10.0,
    mult: float = 2.0,
    forecast: int = 0,
) -> dict[str, object]:
    """
    Compute the machine learning moving average along with contextual metrics.

    Args:
        df: DataFrame containing at least ['date', 'close'] columns.
        window: Training window size for the RBF kernel.
        sigma: RBF kernel bandwidth.
        mult: Bandwidth multiplier when building the dynamic envelope.
        forecast: Optional forecast periods ahead (default 0, current bar).

    Returns:
        Dictionary containing:
            - summary level textual insights
            - band statistics
            - trend change metadata
            - raw series required for chart rendering
            - configuration parameters (window, sigma, mult)
    """
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working.sort_values("date", inplace=True)
    working.reset_index(drop=True, inplace=True)

    prices = working["close"].to_numpy()
    length = len(working)
    ml_line = np.full(length, np.nan)

    for idx in range(window, length):
        x_train = np.arange(window)
        y_train = prices[idx - window : idx]
        mean = np.mean(y_train)
        y_centered = y_train - mean

        kernel_matrix = _rbf_kernel(x_train[:, None], x_train[None, :], sigma)
        kernel_inv = np.linalg.pinv(kernel_matrix + 1e-6 * np.eye(window))

        x_test = np.arange(window + forecast)
        k_star = _rbf_kernel(x_test[:, None], x_train[None, :], sigma)
        k_row = k_star[-1] @ kernel_inv

        ml_line[idx] = float(k_row @ y_centered + mean)

    mae = pd.Series(np.abs(working["close"] - pd.Series(ml_line))).rolling(window).mean() * mult
    upper = ml_line + mae.to_numpy()
    lower = ml_line - mae.to_numpy()

    trend = np.full(length, np.nan)
    for idx in range(1, length):
        if working["close"].iat[idx] > upper[idx] and ml_line[idx] > ml_line[idx - 1]:
            trend[idx] = 1
        elif working["close"].iat[idx] < lower[idx] and ml_line[idx] < ml_line[idx - 1]:
            trend[idx] = 0
        else:
            trend[idx] = trend[idx - 1] if idx > 0 else 0

    trend_series = pd.Series(trend).ffill().fillna(0).astype(int)
    working["ml_ma"] = ml_line
    working["upper"] = upper
    working["lower"] = lower
    working["trend"] = trend_series.to_numpy()

    valid = working.dropna(subset=["ml_ma"])
    if valid.empty:
        raise ValueError("Insufficient data after applying moving average window.")

    current = valid.iloc[-1]
    current_price = float(current["close"])
    current_ml = float(current["ml_ma"])
    current_upper = float(current["upper"])
    current_lower = float(current["lower"])
    current_trend = int(current["trend"])

    distance_to_upper = current_upper - current_price
    distance_to_lower = current_price - current_lower
    band_width = current_upper - current_lower
    band_width_pct = (band_width / current_price * 100) if current_price else 0.0

    price_position_pct = (
        (current_price - current_lower) / band_width * 100 if band_width > 0 else 50.0
    )

    change_5d = current_ml - valid["ml_ma"].iloc[-6] if len(valid) > 5 else 0.0
    ml_slope = "rising" if change_5d > 0 else ("falling" if change_5d < 0 else "flat")

    price_above_ml = current_price > current_ml
    distance_from_ml = current_price - current_ml
    distance_from_ml_pct = (distance_from_ml / current_ml * 100) if current_ml else 0.0

    bullish_periods = int((valid["trend"] == 1).sum())
    bearish_periods = int((valid["trend"] == 0).sum())
    total_periods = len(valid)
    bullish_pct = bullish_periods / total_periods * 100 if total_periods else 0.0
    bearish_pct = bearish_periods / total_periods * 100 if total_periods else 0.0

    shifts = np.where(np.diff(valid["trend"].fillna(0)) != 0)[0] + 1
    segment_records: list[dict[str, object]] = []
    previous_pos = 0
    shift_positions = list(shifts) + [len(valid)]
    for pos in shift_positions:
        segment = valid.iloc[previous_pos:pos] if pos != len(valid) else valid.iloc[previous_pos:]
        if not segment.empty:
            segment_records.append(
                {
                    "start_pos": previous_pos,
                    "end_pos": previous_pos + len(segment) - 1,
                    "start_row": segment.iloc[0],
                    "end_row": segment.iloc[-1],
                    "trend": "BULLISH" if int(segment.iloc[-1]["trend"]) == 1 else "BEARISH",
                }
            )
        previous_pos = pos

    public_intervals = []
    for record in segment_records:
        start_date = record["start_row"]["date"].date().isoformat()
        end_date = record["end_row"]["date"].date().isoformat()
        public_intervals.append(
            {
                "start_date": start_date,
                "end_date": end_date,
                "trend": record["trend"],
            }
        )

    trend_points = []
    for record in segment_records[1:]:
        row = record["start_row"]
        trend_points.append(
            {
                "timestamp": row["date"].isoformat(),
                "price": float(row["close"]),
                "trend": record["trend"],
                "event_type": "reversal",
                "interval_ref": {
                    "start_date": record["start_row"]["date"].date().isoformat(),
                    "end_date": record["end_row"]["date"].date().isoformat(),
                },
            }
        )

    if len(segment_records) > 1:
        last_record = segment_records[-1]
        previous_record = segment_records[-2]
        shift_from = previous_record["trend"]
        shift_to = last_record["trend"]
        days_since_shift = int(
            (last_record["end_row"]["date"] - last_record["start_row"]["date"]).days
        )
    else:
        shift_from = shift_to = None
        days_since_shift = None

    band_series = working[["date", "upper", "lower"]].dropna()
    avg_band_width_pct = 0.0
    if not band_series.empty:
        avg_band_width = (band_series["upper"] - band_series["lower"]).mean()
        avg_band_width_pct = (
            avg_band_width / band_series["upper"].mean() * 100 if band_series["upper"].mean() else 0.0
        )

    expanding = band_width_pct > avg_band_width_pct * 1.1 if avg_band_width_pct else False
    contracting = band_width_pct < avg_band_width_pct * 0.9 if avg_band_width_pct else False

    trend_label = "BULLISH" if current_trend == 1 else "BEARISH"

    if current_price > current_upper:
        position_status = "ABOVE UPPER BAND"
        position_desc = (
            f"Price {current_price:.2f} is {abs(distance_to_upper):.2f} above upper band "
            f"({current_upper:.2f}) indicating a strong breakout."
        )
    elif current_price < current_lower:
        position_status = "BELOW LOWER BAND"
        position_desc = (
            f"Price {current_price:.2f} is {abs(distance_to_lower):.2f} below lower band "
            f"({current_lower:.2f}) indicating a strong breakdown."
        )
    elif price_position_pct > 70:
        position_status = "NEAR UPPER BAND"
        position_desc = (
            f"Price is at {price_position_pct:.1f}% of band width, approaching the upper band "
            f"({current_upper:.2f})."
        )
    elif price_position_pct < 30:
        position_status = "NEAR LOWER BAND"
        position_desc = (
            f"Price is at {price_position_pct:.1f}% of band width, approaching the lower band "
            f"({current_lower:.2f})."
        )
    else:
        position_status = "MID-RANGE"
        position_desc = f"Price is at {price_position_pct:.1f}% of band width; within normal range."

    if days_since_shift is not None and shift_from and shift_to:
        if days_since_shift < 7:
            trend_structure = (
                f"Recent trend shift from {shift_from} to {shift_to} {days_since_shift} days ago "
                f"(early stage). ML line is {ml_slope} ({change_5d:+.2f} over 5 days). "
                f"Price is {'above' if price_above_ml else 'below'} ML line by "
                f"{abs(distance_from_ml_pct):.2f}%."
            )
        elif days_since_shift < 14:
            trend_structure = (
                f"Trend shift from {shift_from} to {shift_to} {days_since_shift} days ago "
                f"(developing). ML line is {ml_slope} ({change_5d:+.2f} over 5 days)."
            )
        else:
            trend_structure = (
                f"Established {shift_to} trend ({days_since_shift} days since shift from {shift_from}). "
                f"ML line is {ml_slope} with strong directional move."
            )
    else:
        trend_structure = (
            f"No recent trend shifts detected. Market remains {trend_label}; ML line is {ml_slope}."
        )

    ml_context = (
        f"ML moving average at {current_ml:.2f}, {ml_slope} with {change_5d:+.2f} change over 5 days. "
        f"Price is {'above' if price_above_ml else 'below'} ML line by {abs(distance_from_ml):.2f} "
        f"({abs(distance_from_ml_pct):.1f}%). Current trend: {trend_label}."
    )

    if expanding:
        volatility_context = (
            f"Bands expanding: width {band_width:.2f} ({band_width_pct:.2f}%) above average "
            f"({avg_band_width_pct:.2f}%). Expect larger moves."
        )
    elif contracting:
        volatility_context = (
            f"Bands contracting: width {band_width:.2f} ({band_width_pct:.2f}%) below average "
            f"({avg_band_width_pct:.2f}%). Breakout risk increasing."
        )
    else:
        volatility_context = (
            f"Bands normal: width {band_width:.2f} ({band_width_pct:.2f}%) near average "
            f"({avg_band_width_pct:.2f}%)."
        )

    trend_distribution = (
        f"Historical distribution over {total_periods} days: "
        f"{bullish_pct:.1f}% bullish, {bearish_pct:.1f}% bearish. Total shifts: {len(shifts)}."
    )

    if current_trend == 1 and price_above_ml and ml_slope == "rising":
        if current_price > current_upper:
            recommendation = "Strong bullish: price above upper band with rising ML line."
        else:
            recommendation = "Bullish: price holds above ML line in bullish regime."
    elif current_trend == 0 and (not price_above_ml) and ml_slope == "falling":
        if current_price < current_lower:
            recommendation = "Strong bearish: price below lower band with falling ML line."
        else:
            recommendation = "Bearish: price remains below ML line in bearish regime."
    elif current_trend == 1 and ml_slope == "falling":
        recommendation = "Caution: bullish trend but ML line losing momentum."
    elif current_trend == 0 and ml_slope == "rising":
        recommendation = "Caution: bearish trend but ML line gaining momentum."
    elif days_since_shift and days_since_shift < 3:
        recommendation = (
            f"Early trend change: shifted to {shift_to} {days_since_shift} days ago. Await confirmation."
        )
    else:
        recommendation = f"Neutral: ML line {ml_slope}. No strong directional bias."

    if current_trend == 1:
        next_action = (
            f"Monitor bullish trend. Watch for a break below lower band ({current_lower:.2f}) "
            f"or ML line ({current_ml:.2f}) to confirm reversal."
        )
    else:
        next_action = (
            f"Monitor bearish trend. Watch for a break above upper band ({current_upper:.2f}) "
            f"or ML line ({current_ml:.2f}) to confirm reversal."
        )

    result = {
        "summary": f"{trend_label} trend. Price {current_price:.2f}, ML line {current_ml:.2f} ({ml_slope}). "
        f"{position_status}.",
        "position_context": position_desc,
        "trend_structure": trend_structure,
        "ml_ma_interpretation": ml_context,
        "band_analysis": volatility_context,
        "trend_distribution": trend_distribution,
        "recommendation": recommendation,
        "next_action": next_action,
        "time_intervals": public_intervals,
        "trend_points": trend_points,
        "series": working[["date", "close", "ml_ma", "upper", "lower", "trend"]]
        .copy()
        .to_dict(orient="records"),
        "parameters": {"window": window, "sigma": sigma, "mult": mult},
    }
    return result


__all__ = ["ml_moving_average"]
