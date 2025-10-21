"""
Relative Strength Index strategy adapted for backend consumption.

Based on Ringshell_source_code/Tech_Index/rsi.py with console output and plotting
removed. Returns structured metrics and textual commentary.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi_strategy(
    df: pd.DataFrame,
    length: int = 14,
    overbought: float = 70.0,
    oversold: float = 30.0,
) -> dict[str, object]:
    """
    Compute an RSI-driven signal with descriptive analytics.

    Args:
        df: DataFrame containing at least ['date','open','high','low','close'].
        length: RSI lookback window.
        overbought: Upper threshold.
        oversold: Lower threshold.
    """
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working.sort_values("date", inplace=True)
    working.reset_index(drop=True, inplace=True)

    delta = working["close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(length).mean()
    avg_loss = pd.Series(loss).rolling(length).mean()
    rs = avg_gain / avg_loss
    working["rsi"] = 100 - (100 / (1 + rs))

    working["buy_signal"] = (working["rsi"] > oversold) & (working["rsi"].shift(1) <= oversold)
    working["sell_signal"] = (working["rsi"] < overbought) & (working["rsi"].shift(1) >= overbought)

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
    current_rsi = float(current["rsi"])
    current_position = int(current["position"])
    current_price = float(current["close"])

    rsi_mean = float(working["rsi"].mean())
    rsi_std = float(working["rsi"].std())
    rsi_zscore = (current_rsi - rsi_mean) / rsi_std if rsi_std else 0.0
    rsi_percentile = (working["rsi"] < current_rsi).sum() / len(working) * 100

    in_overbought = current_rsi > overbought
    in_oversold = current_rsi < oversold
    zone = "overbought" if in_overbought else ("oversold" if in_oversold else "neutral")

    distance_to_overbought = overbought - current_rsi
    distance_to_oversold = current_rsi - oversold

    rsi_change_5d = current_rsi - working["rsi"].iloc[-6] if len(working) > 5 else 0.0
    rsi_trend = "rising" if rsi_change_5d > 2 else ("falling" if rsi_change_5d < -2 else "flat")

    buy_signals = working[working["buy_signal"]]
    sell_signals = working[working["sell_signal"]]

    if current_position == 1:
        current_phase = "BULLISH"
        opposite_signals = sell_signals
        same_signals = buy_signals
    elif current_position == -1:
        current_phase = "BEARISH"
        opposite_signals = buy_signals
        same_signals = sell_signals
    else:
        current_phase = "NEUTRAL"
        opposite_signals = pd.DataFrame()
        same_signals = pd.DataFrame()

    def _extract_last_signal() -> tuple[str | None, pd.Series | None, pd.Series | None]:
        if buy_signals.empty and sell_signals.empty:
            return None, None, None
        if buy_signals.empty:
            return "sell", sell_signals.iloc[-1], None
        if sell_signals.empty:
            return "buy", buy_signals.iloc[-1], None
        return (
            ("buy", buy_signals.iloc[-1], sell_signals.iloc[-1])
            if buy_signals.index[-1] > sell_signals.index[-1]
            else ("sell", sell_signals.iloc[-1], buy_signals.iloc[-1])
        )

    last_signal_info = _extract_last_signal()
    last_signal = last_signal_row = previous_signal_row = None
    if last_signal_info:
        last_signal, last_signal_row, previous_signal_row = last_signal_info

    if last_signal_row is not None:
        days_since = int((working["date"].iloc[-1] - last_signal_row["date"]).days)
        last_signal_price = float(last_signal_row["close"])
        last_signal_rsi = float(last_signal_row["rsi"])
    else:
        days_since = None
        last_signal_price = None
        last_signal_rsi = None

    if previous_signal_row is not None:
        days_prev_trend = int((last_signal_row["date"] - previous_signal_row["date"]).days)
        previous_signal_price = float(previous_signal_row["close"])
    else:
        days_prev_trend = None
        previous_signal_price = None

    if last_signal_row is not None and previous_signal_row is not None:
        price_move = float(last_signal_row["close"] - previous_signal_row["close"])
        price_move_pct = price_move / previous_signal_row["close"] * 100
        structure_status = (
            "MAJOR BREAK"
            if abs(price_move_pct) > 5
            else "MODERATE BREAK"
            if abs(price_move_pct) > 3
            else "MINOR SHIFT"
        )
    else:
        price_move_pct = 0.0
        structure_status = "UNDEFINED"

    confirmation_status = "CONFIRMED"
    if days_since is not None:
        if days_since < 3:
            confirmation_status = "EARLY"
        elif days_since < 7:
            confirmation_status = "DEVELOPING"

    rsi_momentum_per_day = rsi_change_5d / 5 if days_since and days_since > 0 else rsi_change_5d
    trend_strength = (
        "STRONG" if abs(rsi_momentum_per_day) > 1.5 else "MODERATE" if abs(rsi_momentum_per_day) > 0.7 else "WEAK"
    )

    last_opposite = (
        opposite_signals.iloc[-1] if not opposite_signals.empty else None
    )
    if last_opposite is not None and last_signal_row is not None:
        last_opposite_price = float(last_opposite["close"])
        reaction = float(current_price - last_signal_price)
        rejection_text = (
            f"Latest {last_signal} signal at {last_signal_price:.2f} (RSI {last_signal_rsi:.1f}). "
            f"Current price moved {reaction:+.2f} since signal."
        )
    else:
        rejection_text = "Insufficient data to evaluate rejection/continuation."

    if days_since and days_prev_trend:
        trend_structure = (
            f"{current_phase} regime. Last {last_signal} signal {days_since} days ago "
            f"(previous trend lasted {days_prev_trend} days, move {price_move_pct:+.2f}%)."
        )
    else:
        trend_structure = f"{current_phase} regime. Limited signal history."

    rsi_context = (
        f"RSI {current_rsi:.1f}, {rsi_trend}. Percentile {rsi_percentile:.1f}%. "
        f"Distance to overbought {distance_to_overbought:.1f}, to oversold {distance_to_oversold:.1f}."
    )

    reversal_text = (
        f"Latest {last_signal or 'n/a'} signal at price {last_signal_price or float('nan'):.2f}."
        if last_signal_price is not None
        else "RSI signals not triggered recently."
    )

    volatility_text = (
        f"RSI z-score {rsi_zscore:.2f}. "
        f"{'Extreme deviation' if abs(rsi_zscore) > 2 else 'Elevated' if abs(rsi_zscore) > 1 else 'Normal range'}."
    )

    total_signals = len(buy_signals) + len(sell_signals)
    returns = working["return"].replace([np.inf, -np.inf], np.nan).dropna()
    win_rate = (returns > 0).mean() * 100 if not returns.empty else 0.0
    total_return = (working["equity"].iloc[-1] - 1) * 100
    max_trade_return = (
        returns.max() * 100 if not returns.empty else 0.0
    )
    sharpe_ratio = (
        returns.mean() / returns.std() * np.sqrt(252) if not returns.empty and returns.std() else 0.0
    )

    perf_label = (
        "STRONG" if win_rate > 60 else "GOOD" if win_rate > 50 else "MODERATE" if win_rate > 40 else "WEAK"
    )
    risk_text = (
        f"{perf_label} performance: {win_rate:.1f}% win rate over {total_signals} signals, "
        f"total return {total_return:+.1f}%, max trade {max_trade_return:+.1f}%, Sharpe {sharpe_ratio:.2f}."
    )

    if in_oversold and rsi_trend == "rising":
        recommendation = "Strong buy: RSI oversold and rising with supportive structure."
    elif in_overbought and rsi_trend == "falling":
        recommendation = "Strong sell: RSI overbought and falling, watch for pullback."
    elif confirmation_status == "EARLY" and trend_strength == "WEAK":
        recommendation = (
            f"Caution: {last_signal or 'latest'} signal only {days_since} days old with weak momentum."
        )
    elif confirmation_status == "DEVELOPING" and trend_strength in {"MODERATE", "STRONG"}:
        recommendation = f"Hold position: {last_signal or 'current'} trend developing."
    elif confirmation_status == "CONFIRMED":
        recommendation = f"Trend confirmed: {current_phase.lower()} bias remains intact."
    elif zone == "neutral" and rsi_trend == "rising":
        recommendation = "Neutral-bullish: RSI trending up; monitor for breakout."
    elif zone == "neutral" and rsi_trend == "falling":
        recommendation = "Neutral-bearish: RSI trending down; monitor for breakdown."
    else:
        recommendation = (
            f"Wait for clearer signal. Distance to oversold {distance_to_oversold:.1f}, "
            f"to overbought {distance_to_overbought:.1f}."
        )

    if last_signal and confirmation_status == "EARLY":
        next_action = (
            f"Monitor {last_signal.upper()} setup closely. Needs more time for confirmation. "
            f"Watch RSI reaction near {oversold if last_signal == 'buy' else overbought}."
        )
    else:
        next_action = (
            f"Watch for RSI crossing below {oversold} or above {overbought} to confirm the next trigger."
        )

    result = {
        "summary": f"RSI {current_rsi:.1f} ({zone}), z-score {rsi_zscore:+.1f}. {trend_strength} {rsi_trend} momentum.",
        "position_context": (
            f"Current {current_price:.2f}. Last signal {last_signal or 'n/a'} at "
            f"{last_signal_price:.2f if last_signal_price else float('nan')}."
        ),
        "trend_structure": trend_structure,
        "pattern_context": rejection_text,
        "rsi_interpretation": rsi_context,
        "reversal_analysis": reversal_text,
        "volatility_assessment": volatility_text,
        "risk_metrics": risk_text,
        "recommendation": recommendation,
        "next_action": next_action,
        "series": working[
            ["date", "close", "rsi", "buy_signal", "sell_signal", "equity", "position"]
        ]
        .copy()
        .to_dict(orient="records"),
        "parameters": {"length": length, "overbought": overbought, "oversold": oversold},
    }
    return result


__all__ = ["rsi_strategy"]
