"""
Equal highs / equal lows detection with contextual statistics.

Ported from Ringshell_source_code/Tech_Index/eqh_eql.py, simplified for backend
consumption (no plotting or console output).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def equal_highs_lows(df: pd.DataFrame, threshold: float = 0.01, lookback: int = 50) -> dict[str, object]:
    """
    Identify equal highs (EQH) and equal lows (EQL) within a tolerance.

    Args:
        df: DataFrame containing ['date', 'high', 'low', 'close'].
        threshold: Relative tolerance used to flag equal levels.
        lookback: Window used when computing average range statistics.
    """
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working.sort_values("date", inplace=True)
    working.reset_index(drop=True, inplace=True)

    eqh, eql = [], []
    for idx in range(1, len(working)):
        if np.isfinite(working.loc[idx, "high"]) and np.isfinite(working.loc[idx - 1, "high"]):
            if abs(working.loc[idx, "high"] - working.loc[idx - 1, "high"]) / max(
                working.loc[idx, "high"], 1e-9
            ) < threshold:
                eqh.append({"date": working.loc[idx, "date"], "price": float(working.loc[idx, "high"])})
        if np.isfinite(working.loc[idx, "low"]) and np.isfinite(working.loc[idx - 1, "low"]):
            if abs(working.loc[idx, "low"] - working.loc[idx - 1, "low"]) / max(
                working.loc[idx, "low"], 1e-9
            ) < threshold:
                eql.append({"date": working.loc[idx, "date"], "price": float(working.loc[idx, "low"])})

    working["EQH"] = np.nan
    working["EQL"] = np.nan
    for item in eqh:
        idx = working.index[working["date"] == item["date"]]
        if len(idx):
            working.at[idx[0], "EQH"] = item["price"]
    for item in eql:
        idx = working.index[working["date"] == item["date"]]
        if len(idx):
            working.at[idx[0], "EQL"] = item["price"]

    current_price = float(working["close"].iloc[-1])
    recent = working.tail(lookback)
    avg_high = float(recent["high"].mean())
    avg_low = float(recent["low"].mean())
    avg_range = avg_high - avg_low if avg_high and avg_low else 0.0
    price_percent = (current_price - avg_low) / avg_range * 100 if avg_range else 50.0

    valuation = "EXPENSIVE" if price_percent > 70 else "CHEAP" if price_percent < 30 else "FAIR VALUE"

    recent_window = 30
    cutoff = working["date"].iloc[-1] - pd.Timedelta(days=recent_window)
    recent_eqh = [item for item in eqh if item["date"] >= cutoff]
    recent_eql = [item for item in eql if item["date"] >= cutoff]

    eqh_above = [item for item in recent_eqh if item["price"] > current_price]
    eql_below = [item for item in recent_eql if item["price"] <= current_price]
    nearest_eqh = (
        min(eqh_above, key=lambda x: x["price"] - current_price) if eqh_above else None
    )
    nearest_eql = (
        max(eql_below, key=lambda x: x["price"]) if eql_below else None
    )

    summary = (
        f"{valuation}. Current price {current_price:.2f} sits at {price_percent:.1f}% of the "
        f"{lookback}-day high/low range. Detected {len(recent_eqh)} EQH and {len(recent_eql)} EQL in the last "
        f"{recent_window} days."
    )

    liquidity_notes = (
        f"{len(eqh_above)} equal highs above (potential resistance), "
        f"{len(eql_below)} equal lows below (potential support)."
    )

    nearest_eqh_text = (
        f"{nearest_eqh['price']:.2f} (+{nearest_eqh['price'] - current_price:.2f})"
        if nearest_eqh
        else "None"
    )
    nearest_eql_text = (
        f"{nearest_eql['price']:.2f} (-{current_price - nearest_eql['price']:.2f})"
        if nearest_eql
        else "None"
    )

    balance = (
        "RESISTANCE HEAVY"
        if len(recent_eqh) > len(recent_eql) * 1.5
        else "SUPPORT HEAVY"
        if len(recent_eql) > len(recent_eqh) * 1.5
        else "BALANCED"
    )

    result = {
        "summary": summary,
        "valuation": valuation,
        "liquidity_notes": liquidity_notes,
        "balance": balance,
        "nearest_eqh": nearest_eqh_text,
        "nearest_eql": nearest_eql_text,
        "series": working[["date", "close", "EQH", "EQL"]].copy().to_dict(orient="records"),
        "parameters": {"threshold": threshold, "lookback": lookback},
    }
    return result


__all__ = ["equal_highs_lows"]
