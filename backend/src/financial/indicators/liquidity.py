"""
Liquidity zone analysis (buyside/sellside) for backend services.

Ported from Ringshell_source_code/Tech_Index/liquidity.py with plotting removed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def liquidity_zones(
    df: pd.DataFrame,
    liq_len: int = 7,
    liq_margin: float = 2.3,
    show_buyside: bool = True,
    show_sellside: bool = True,
    show_voids: bool = True,
) -> dict[str, object]:
    """
    Detect liquidity pools and voids.

    Args:
        df: DataFrame containing ['date','open','high','low','close'].
        liq_len: Pivot lookback window.
        liq_margin: Zone height scaling factor.
        show_buyside: Whether to include buyside zones.
        show_sellside: Whether to include sellside zones.
        show_voids: Whether to include liquidity gaps.
    """
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working.sort_values("date", inplace=True)
    working.reset_index(drop=True, inplace=True)

    working["swing_high"] = (
        (working["high"] > working["high"].shift(1))
        & (working["high"] > working["high"].shift(-1))
    ) * working["high"]
    working["swing_low"] = (
        (working["low"] < working["low"].shift(1))
        & (working["low"] < working["low"].shift(-1))
    ) * working["low"]

    working["tr"] = np.maximum(
        working["high"] - working["low"],
        np.maximum(
            (working["high"] - working["close"].shift(1)).abs(),
            (working["low"] - working["close"].shift(1)).abs(),
        ),
    )
    working["atr"] = working["tr"].rolling(10).mean()

    zones = []
    for idx in range(liq_len, len(working)):
        atr = working.loc[idx, "atr"]
        date = working.loc[idx, "date"]
        if np.isnan(atr):
            continue
        if show_buyside and not np.isnan(working.loc[idx, "swing_high"]):
            price = float(working.loc[idx, "swing_high"])
            zones.append(
                {
                    "type": "buyside",
                    "start": date,
                    "end": date + pd.Timedelta(days=10),
                    "top": price + liq_margin * atr,
                    "bottom": price,
                    "anchor": price,
                }
            )
        if show_sellside and not np.isnan(working.loc[idx, "swing_low"]):
            price = float(working.loc[idx, "swing_low"])
            zones.append(
                {
                    "type": "sellside",
                    "start": date,
                    "end": date + pd.Timedelta(days=10),
                    "top": price,
                    "bottom": price - liq_margin * atr,
                    "anchor": price,
                }
            )

    voids = []
    if show_voids:
        working["gap_up"] = (working["low"] - working["high"].shift(2)) > working["atr"] * 2
        working["gap_down"] = (working["high"].shift(2) - working["low"]) > working["atr"] * 2
        for idx in range(2, len(working)):
            if working.loc[idx, "gap_up"]:
                voids.append(
                    {
                        "type": "bullish",
                        "start": working.loc[idx - 2, "date"],
                        "end": working.loc[idx, "date"],
                        "top": float(working.loc[idx, "low"]),
                        "bottom": float(working.loc[idx - 2, "high"]),
                    }
                )
            elif working.loc[idx, "gap_down"]:
                voids.append(
                    {
                        "type": "bearish",
                        "start": working.loc[idx - 2, "date"],
                        "end": working.loc[idx, "date"],
                        "top": float(working.loc[idx - 2, "low"]),
                        "bottom": float(working.loc[idx, "high"]),
                    }
                )

    current_price = float(working["close"].iloc[-1])
    current_high = float(working["high"].iloc[-1])
    current_low = float(working["low"].iloc[-1])
    current_atr = float(working["atr"].iloc[-1])

    buyside_zones = [z for z in zones if z["type"] == "buyside"]
    sellside_zones = [z for z in zones if z["type"] == "sellside"]

    def _distance_to_zone(zone: dict) -> float:
        if zone["type"] == "buyside":
            return zone["bottom"] - current_price
        return current_price - zone["top"]

    buyside_above = [z for z in buyside_zones if z["bottom"] > current_price]
    sellside_below = [z for z in sellside_zones if z["top"] < current_price]
    nearest_buyside = min(buyside_above, key=_distance_to_zone) if buyside_above else None
    nearest_sellside = min(sellside_below, key=_distance_to_zone) if sellside_below else None

    in_buyside = any(z["bottom"] <= current_price <= z["top"] for z in buyside_zones)
    in_sellside = any(z["bottom"] <= current_price <= z["top"] for z in sellside_zones)

    liquidity_summary = []
    if in_buyside:
        liquidity_summary.append("Price currently inside buyside liquidity.")
    if in_sellside:
        liquidity_summary.append("Price currently inside sellside liquidity.")

    if nearest_buyside:
        distance = nearest_buyside["bottom"] - current_price
        liquidity_summary.append(
            f"Nearest buyside pool at {nearest_buyside['bottom']:.2f} "
            f"(distance {distance:.2f}, {distance / max(current_price, 1e-9) * 100:.1f}%)."
        )
    if nearest_sellside:
        distance = current_price - nearest_sellside["top"]
        liquidity_summary.append(
            f"Nearest sellside pool at {nearest_sellside['top']:.2f} "
            f"(distance {distance:.2f}, {distance / max(current_price, 1e-9) * 100:.1f}%)."
        )
    if not liquidity_summary:
        liquidity_summary.append("Price between major liquidity pools.")

    unfilled_voids_above = [v for v in voids if v["top"] >= current_price]
    unfilled_voids_below = [v for v in voids if v["bottom"] <= current_price]

    if in_buyside:
        recommendation = "Monitor for rejection after liquidity sweep; potential short setup."
    elif in_sellside:
        recommendation = "Monitor for bounce after sellside sweep; potential long setup."
    elif nearest_buyside and abs(nearest_buyside["bottom"] - current_price) < current_atr * 2:
        recommendation = "Approaching buyside liquidity; watch for breakout or rejection."
    elif nearest_sellside and abs(current_price - nearest_sellside["top"]) < current_atr * 2:
        recommendation = "Approaching sellside liquidity; watch for breakdown or bounce."
    elif len(unfilled_voids_below) > len(unfilled_voids_above):
        recommendation = "Liquidity voids below suggest risk of pullback."
    elif len(unfilled_voids_above) > len(unfilled_voids_below):
        recommendation = "Liquidity voids above could cap rallies."
    else:
        recommendation = "Neutral positioning between liquidity clusters."

    next_action = "Wait for price to interact with nearest liquidity pools before committing."
    if in_buyside and nearest_sellside:
        next_action = (
            f"Plan short entries with targets near {nearest_sellside['bottom']:.2f} - "
            f"{nearest_sellside['top']:.2f}. Consider stops above {current_high + current_atr:.2f}."
        )
    elif in_sellside and nearest_buyside:
        next_action = (
            f"Plan long entries with targets near {nearest_buyside['bottom']:.2f} - "
            f"{nearest_buyside['top']:.2f}. Consider stops below {current_low - current_atr:.2f}."
        )

    result = {
        "summary": " ".join(liquidity_summary),
        "nearest_buyside": (
            {
                "start": nearest_buyside["start"].isoformat(),
                "end": nearest_buyside["end"].isoformat(),
                "bottom": float(nearest_buyside["bottom"]),
                "top": float(nearest_buyside["top"]),
            }
            if nearest_buyside
            else None
        ),
        "nearest_sellside": (
            {
                "start": nearest_sellside["start"].isoformat(),
                "end": nearest_sellside["end"].isoformat(),
                "bottom": float(nearest_sellside["bottom"]),
                "top": float(nearest_sellside["top"]),
            }
            if nearest_sellside
            else None
        ),
        "voids": [
            {
                "type": v["type"],
                "start": v["start"].isoformat(),
                "end": v["end"].isoformat(),
                "top": v["top"],
                "bottom": v["bottom"],
            }
            for v in voids
        ],
        "recommendation": recommendation,
        "next_action": next_action,
        "series": working[
            ["date", "close", "swing_high", "swing_low", "atr"]
        ]
        .copy()
        .to_dict(orient="records"),
        "parameters": {
            "liq_len": liq_len,
            "liq_margin": liq_margin,
            "show_buyside": show_buyside,
            "show_sellside": show_sellside,
            "show_voids": show_voids,
        },
    }
    return result


__all__ = ["liquidity_zones"]
