"""
Optimal RSI strategy with lightweight machine learning smoothing for backend use.

This module is derived from Ringshell_source_code/Tech_Index/opt_rsi.py. The
implementation keeps the core optimisation logic while trimming console output
and plotting. The goal is to expose a deterministic function that returns the
computed series together with textual commentary suitable for API responses.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _pine_sma(series: np.ndarray, length: int) -> np.ndarray:
    return pd.Series(series).rolling(length).mean().to_numpy()


def _pine_rma(series: np.ndarray, length: int) -> np.ndarray:
    if length > len(series):
        return np.full(len(series), np.nan)
    alpha = 1 / length
    result = np.full(len(series), np.nan)
    result[length - 1] = np.mean(series[:length])
    for idx in range(length, len(series)):
        result[idx] = alpha * series[idx] + (1 - alpha) * result[idx - 1]
    return result


def _pine_rsi(close: np.ndarray, length: int) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    up = np.where(delta > 0, delta, 0)
    down = np.where(delta < 0, -delta, 0)
    rs = _pine_rma(up, length) / _pine_rma(down, length)
    return 100 - 100 / (1 + rs)


def _rational_quadratic(series: np.ndarray, lookback: int = 8, relative_weight: float = 8.0, start: int = 25) -> float:
    weight_sum, value_sum = 0.0, 0.0
    limit = min(start, len(series))
    for i in range(limit):
        weight = (1 + (i ** 2 / (2 * (lookback ** 2) * relative_weight))) ** (-relative_weight)
        value_sum += series[i] * weight
        weight_sum += weight
    return value_sum / weight_sum if weight_sum else np.nan


def _optimal_rsi_length(
    close: np.ndarray,
    optimal_length: int = 200,
    rsi_count: int = 30,
    rsi_min: int = 4,
    ma_length: int = 14,
    backup_length: int = 14,
    use_rational_quadratic: bool = True,
) -> tuple[int, float]:
    source = close.copy()
    if use_rational_quadratic:
        source = np.array([_rational_quadratic(close[: idx + 1]) for idx in range(len(close))])

    cross_profits = np.zeros(rsi_count)
    max_length = min(rsi_min + rsi_count, len(close) - ma_length - 1)
    if max_length < rsi_min:
        return backup_length, 0.0

    actual_count = min(rsi_count, max_length - rsi_min + 1)
    for i in range(actual_count):
        length = rsi_min + i
        rsi = _pine_rsi(source, length)
        rsi_ma = _pine_sma(rsi, ma_length)
        cross_type = 0
        cross_close = 0.0
        total_profit = 0.0
        cross_count = 0
        for idx in range(1, min(optimal_length, len(close))):
            if np.isnan(rsi[idx]) or np.isnan(rsi_ma[idx]):
                continue
            bull = (rsi[idx - 1] < rsi_ma[idx - 1]) and (rsi[idx] > rsi_ma[idx])
            bear = (rsi[idx - 1] > rsi_ma[idx - 1]) and (rsi[idx] < rsi_ma[idx])
            if bull:
                if cross_type != 0:
                    total_profit += cross_close / close[idx]
                    cross_count += 1
                cross_close = close[idx]
                cross_type = 1
            elif bear:
                if cross_type != 0:
                    total_profit += close[idx] / cross_close
                    cross_count += 1
                cross_close = close[idx]
                cross_type = -1
        cross_profits[i] = total_profit / max(cross_count, 1)

    best_index = int(np.argmax(cross_profits[:actual_count]))
    best_percent = float(cross_profits[best_index])
    best_length = rsi_min + best_index if best_percent > -1e5 else backup_length
    return best_length, best_percent


def _smooth_rsi(series: np.ndarray, mode: str, length: int) -> np.ndarray:
    if mode == "EMA":
        return pd.Series(series).ewm(span=length, adjust=False).mean().to_numpy()
    if length <= 1:
        return series.copy()
    rolling = pd.Series(series).rolling(length).mean().to_numpy()
    filled = rolling.copy()
    mask = np.isnan(filled)
    filled[mask] = series[mask]
    return filled


def optimal_rsi_strategy(
    df: pd.DataFrame,
    optimal_length: int = 200,
    rsi_count: int = 30,
    rsi_min: int = 4,
    ma_length: int = 14,
    smoothing_length: int = 10,
    smoothing_mode: str = "Simple Average",
) -> dict[str, object]:
    """
    Run the optimal RSI search and return analytical context.

    Args:
        df: DataFrame with ['date','open','high','low','close'].
        optimal_length: Maximum history used for optimisation.
        rsi_count: Number of RSI lengths tested above rsi_min.
        rsi_min: Minimum RSI length to evaluate.
        ma_length: Moving average length applied on RSI for signals.
        smoothing_length: Window for the optional smoothing step.
        smoothing_mode: Either 'Simple Average' or 'EMA'.
    """
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working.sort_values("date", inplace=True)
    working.reset_index(drop=True, inplace=True)

    close = working["close"].to_numpy()

    best_length, best_percent = _optimal_rsi_length(
        close,
        optimal_length=optimal_length,
        rsi_count=rsi_count,
        rsi_min=rsi_min,
        ma_length=ma_length,
        backup_length=ma_length,
        use_rational_quadratic=True,
    )

    rsi_raw = _pine_rsi(close, best_length)
    rsi_ma = _pine_sma(rsi_raw, ma_length)
    rsi_smoothed = _smooth_rsi(rsi_raw, "EMA" if smoothing_mode.upper() == "EMA" else "Simple", smoothing_length)

    bull_cross = (rsi_smoothed[:-1] < rsi_ma[:-1]) & (rsi_smoothed[1:] > rsi_ma[1:])
    bear_cross = (rsi_smoothed[:-1] > rsi_ma[:-1]) & (rsi_smoothed[1:] < rsi_ma[1:])

    signals = np.zeros(len(rsi_smoothed))
    signals[1:][bull_cross] = 1
    signals[1:][bear_cross] = -1
    working["rsi_raw"] = rsi_raw
    working["rsi_smoothed"] = rsi_smoothed
    working["rsi_ma"] = rsi_ma
    working["signal"] = signals

    current_rsi = float(rsi_smoothed[-1])
    current_ma = float(rsi_ma[-1])
    rsi_delta = current_rsi - current_ma
    regime = "bullish" if rsi_delta > 0 else "bearish" if rsi_delta < 0 else "neutral"

    recent_signals = working[working["signal"] != 0].tail(10)
    total_signals = len(recent_signals)
    last_signal = (
        {
            "timestamp": recent_signals.iloc[-1]["date"].isoformat(),
            "type": "buy" if recent_signals.iloc[-1]["signal"] == 1 else "sell",
            "price": float(recent_signals.iloc[-1]["close"]),
            "rsi": float(recent_signals.iloc[-1]["rsi_smoothed"]),
        }
        if total_signals
        else None
    )

    returns = []
    last_price = None
    last_side = None
    for _, row in recent_signals.iterrows():
        if row["signal"] == 1:
            last_price = row["close"]
            last_side = 1
        elif row["signal"] == -1 and last_side == 1 and last_price:
            returns.append(row["close"] / last_price - 1)
            last_price = row["close"]
            last_side = -1
        elif row["signal"] == -1:
            last_price = row["close"]
            last_side = -1
        elif row["signal"] == 1 and last_side == -1 and last_price:
            returns.append(last_price / row["close"] - 1)
            last_price = row["close"]
            last_side = 1

    win_rate = (np.array(returns) > 0).mean() * 100 if returns else 0.0
    avg_return = np.mean(returns) * 100 if returns else 0.0

    trend_description = (
        f"RSI {current_rsi:.1f} vs MA {current_ma:.1f} ({rsi_delta:+.2f}). "
        f"Optimal length {best_length}, historical performance score {best_percent:.4f}."
    )

    recommendation = (
        "Momentum favours buyers." if regime == "bullish" else "Momentum favours sellers."
        if regime == "bearish"
        else "Momentum is neutral; wait for confirmation."
    )

    result = {
        "summary": f"Optimal RSI length {best_length}. Current regime {regime}.",
        "trend_structure": trend_description,
        "signal_win_rate": win_rate,
        "signal_avg_return": avg_return,
        "last_signal": last_signal,
        "recommendation": recommendation,
        "series": working[
            ["date", "close", "rsi_raw", "rsi_smoothed", "rsi_ma", "signal"]
        ]
        .copy()
        .to_dict(orient="records"),
        "parameters": {
            "optimal_length": optimal_length,
            "rsi_count": rsi_count,
            "rsi_min": rsi_min,
            "ma_length": ma_length,
            "smoothing_length": smoothing_length,
            "smoothing_mode": smoothing_mode,
        },
    }
    return result


__all__ = ["optimal_rsi_strategy"]
