"""
Bollinger Bands indicator adapted for backend use.

Ported from Ringshell_source_code/Tech_Index/bollinger.py with console output and
plotting removed. Returns Bollinger band statistics and textual description.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def bollinger_strategy(df: pd.DataFrame, length: int = 20, mult: float = 2.0) -> dict[str, object]:
    """
    Compute Bollinger Bands together with descriptive analytics.

    Args:
        df: DataFrame containing at least ['date', 'close', 'high', 'low'].
        length: Moving average window.
        mult: Standard deviation multiplier.

    Returns:
        Dictionary containing band data, signals, and textual insights.
    """
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working.sort_values("date", inplace=True)
    working.reset_index(drop=True, inplace=True)

    working["basis"] = working["close"].rolling(window=length).mean()
    working["stdev"] = working["close"].rolling(window=length).std()
    working["upper"] = working["basis"] + mult * working["stdev"]
    working["lower"] = working["basis"] - mult * working["stdev"]

    working["buy_signal"] = (working["close"] > working["lower"]) & (
        working["close"].shift(1) <= working["lower"].shift(1)
    )
    working["sell_signal"] = (working["close"] < working["upper"]) & (
        working["close"].shift(1) >= working["upper"].shift(1)
    )

    position = 0
    positions = []
    for buy, sell in zip(working["buy_signal"], working["sell_signal"]):
        if buy:
            position = 1
        elif sell:
            position = -1
        positions.append(position)
    working["position"] = positions

    working["return"] = working["close"].pct_change().fillna(0) * working["position"]
    working["equity"] = (1 + working["return"]).cumprod()

    current = working.iloc[-1]
    current_price = float(current["close"])
    current_basis = float(current["basis"])
    current_stdev = float(current["stdev"])
    current_upper = float(current["upper"])
    current_lower = float(current["lower"])

    distance_to_upper_pct = (current_upper - current_price) / current_price * 100
    distance_to_lower_pct = (current_price - current_lower) / current_price * 100
    distance_from_basis_pct = (
        (current_price - current_basis) / current_basis * 100 if current_basis else 0.0
    )

    band_width = current_upper - current_lower
    band_width_pct = (band_width / current_price * 100) if current_price else 0.0
    price_in_std = (
        (current_price - current_basis) / current_stdev if current_stdev else 0.0
    )

    bandwidth_series = (working["upper"] - working["lower"]) / working["basis"] * 100
    avg_bandwidth = bandwidth_series.mean()

    is_squeeze = band_width_pct < avg_bandwidth * 0.75 if avg_bandwidth else False
    is_expansion = band_width_pct > avg_bandwidth * 1.25 if avg_bandwidth else False

    recent = working.tail(30)
    upper_touches = int(
        ((recent["high"] >= recent["upper"]) | (recent["close"] >= recent["upper"])).sum()
    )
    lower_touches = int(
        ((recent["low"] <= recent["lower"]) | (recent["close"] <= recent["lower"])).sum()
    )

    returns = working["return"].replace([np.inf, -np.inf], np.nan).dropna()
    winning_days = int((returns > 0).sum())
    losing_days = int((returns < 0).sum())
    total_trades = winning_days + losing_days
    win_rate = winning_days / total_trades * 100 if total_trades else 0.0
    total_return = (working["equity"].iloc[-1] - 1) * 100
    sharpe_ratio = (
        (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() else 0.0
    )

    percent_b_pct = (
        (current_price - current_lower) / band_width * 100 if band_width else 50.0
    )

    if percent_b_pct > 100:
        position_status = "ABOVE UPPER BAND"
    elif percent_b_pct < 0:
        position_status = "BELOW LOWER BAND"
    elif percent_b_pct > 80:
        position_status = "NEAR UPPER BAND"
    elif percent_b_pct < 20:
        position_status = "NEAR LOWER BAND"
    else:
        position_status = "MID-RANGE"

    percentb_notes = f"%B is {percent_b_pct:.1f}%."
    if percent_b_pct > 100:
        percentb_notes += f" Price is {abs(current_upper - current_price):.2f} above upper band."
    elif percent_b_pct < 0:
        percentb_notes += f" Price is {abs(current_price - current_lower):.2f} below lower band."
    elif percent_b_pct > 80:
        percentb_notes += " Price is approaching the upper band."
    elif percent_b_pct < 20:
        percentb_notes += " Price is approaching the lower band."
    else:
        percentb_notes += " Price is within normal range."

    if is_squeeze:
        volatility_state = (
            f"Squeeze: bandwidth {band_width_pct:.2f}% which is "
            f"{((band_width_pct / avg_bandwidth - 1) * 100):.1f}% below average."
        )
    elif is_expansion:
        volatility_state = (
            f"Expansion: bandwidth {band_width_pct:.2f}% which is "
            f"{((band_width_pct / avg_bandwidth - 1) * 100):.1f}% above average."
        )
    else:
        volatility_state = f"Normal bandwidth {band_width_pct:.2f}%."

    if upper_touches > lower_touches * 1.5:
        band_interaction = f"{upper_touches} upper touches vs {lower_touches} lower touches (uptrend bias)."
    elif lower_touches > upper_touches * 1.5:
        band_interaction = f"{lower_touches} lower touches vs {upper_touches} upper touches (downtrend bias)."
    else:
        band_interaction = f"{upper_touches} upper and {lower_touches} lower touches (balanced)."

    performance_label = (
        "STRONG" if win_rate > 60 else "GOOD" if win_rate > 50 else "MODERATE" if win_rate > 40 else "WEAK"
    )
    performance_metrics = (
        f"{performance_label} performance: {win_rate:.1f}% win rate, total return {total_return:+.1f}%, "
        f"Sharpe {sharpe_ratio:.2f}."
    )

    summary = (
        f"{position_status}. Price {current_price:.2f}, basis {current_basis:.2f}, %B {percent_b_pct:.1f}%."
    )
    position_context = (
        f"Current {current_price:.2f}. Basis {current_basis:.2f} ({distance_from_basis_pct:+.1f}%). "
        f"Upper {current_upper:.2f} ({distance_to_upper_pct:+.1f}%), lower {current_lower:.2f} "
        f"({distance_to_lower_pct:+.1f}%)."
    )
    std_notes = (
        f"Standard deviation {current_stdev:.2f}. Bandwidth {band_width_pct:.2f}% "
        f"(average {avg_bandwidth:.2f}%). Price is {price_in_std:+.2f} standard deviations from mean."
    )

    result = {
        "summary": summary,
        "position_context": position_context,
        "std_analysis": std_notes,
        "percentb_interpretation": percentb_notes,
        "volatility_state": volatility_state,
        "band_interaction": band_interaction,
        "performance_metrics": performance_metrics,
        "series": working[
            ["date", "close", "basis", "upper", "lower", "buy_signal", "sell_signal", "equity"]
        ]
        .copy()
        .to_dict(orient="records"),
        "parameters": {"length": length, "mult": mult},
    }
    return result


__all__ = ["bollinger_strategy"]
