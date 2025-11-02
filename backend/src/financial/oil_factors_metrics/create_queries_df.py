from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, Optional, Tuple

import pandas as pd

TrendEntry = Dict[str, Any]


def _normalise_date(value: Any) -> Optional[date]:
    """Convert incoming values to `date` objects."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        parsed = pd.to_datetime(value, utc=False, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime().date()
    except Exception:
        return None


def _extract_reason(summary: Dict[str, Any]) -> Tuple[str, str]:
    """Return (driver_type, ai_reason) from the LLM summary payload."""
    if not isinstance(summary, dict):
        return "", ""

    if "primary_driver" in summary:
        primary_driver = str(summary.get("primary_driver", "")).strip()
        driver_type = str(summary.get("driver_type", "")).strip()
        if not driver_type:
            match = re.search(r"-\s*([^:]+):", primary_driver)
            driver_type = match.group(1).strip() if match else ""
        return driver_type, primary_driver

    macro_reason = str(summary.get("macro_reason", "")).strip()
    micro_reason = str(summary.get("micro_reason", "")).strip()
    combined = " ".join(part for part in (macro_reason, micro_reason) if part)
    driver_type = ""
    if macro_reason and not micro_reason:
        driver_type = "Macro"
    elif micro_reason and not macro_reason:
        driver_type = "Micro"
    elif macro_reason and micro_reason:
        driver_type = "Macro & Micro"
    return driver_type, combined


def _iter_trends(llm_summary: Dict[str, Any]) -> Iterable[TrendEntry]:
    """Yield flattened trend entries from the cached LLM summary."""
    if not isinstance(llm_summary, dict):
        return []

    payload = llm_summary.get("llm_summary", llm_summary)
    if not isinstance(payload, dict):
        return []

    for category in ("current_trends", "historical_trends"):
        trends = payload.get(category, {})
        if not isinstance(trends, dict):
            continue
        for name, data in trends.items():
            if not isinstance(data, dict):
                continue
            trend_time = data.get("time", {})
            summary = data.get("summary", {})
            start = _normalise_date(trend_time.get("start"))
            end = _normalise_date(trend_time.get("end"))
            driver_type, ai_reason = _extract_reason(summary)
            yield {
                "name": name,
                "start": start,
                "end": end,
                "driver_type": driver_type,
                "ai_reason": ai_reason,
            }


def _match_trend(
    row_start: Optional[date],
    row_end: Optional[date],
    trends: Iterable[TrendEntry],
    tolerance: int = 1,
) -> Optional[TrendEntry]:
    """Find the best matching trend within `tolerance` days."""
    best: Optional[TrendEntry] = None
    best_score: Optional[int] = None
    for trend in trends:
        trend_start = trend.get("start")
        trend_end = trend.get("end")

        if not trend_start or not trend_end or row_start is None or row_end is None:
            continue

        start_delta = abs((row_start - trend_start).days)
        end_delta = abs((row_end - trend_end).days)

        if start_delta <= tolerance and end_delta <= tolerance:
            score = start_delta + end_delta
            if best_score is None or score < best_score:
                best = trend
                best_score = score
    return best


def create_queries_df(
    impact_metrics_df: pd.DataFrame,
    factor_time_df: pd.DataFrame,
    llm_trend_summary: Dict[str, Any],
) -> pd.DataFrame:
    """
    Merge impact metrics, factor time ranges and LLM summaries into a unified DataFrame.
    """
    if impact_metrics_df is None or factor_time_df is None:
        return pd.DataFrame()

    if impact_metrics_df.empty or factor_time_df.empty:
        return pd.DataFrame()

    impact_df = impact_metrics_df.copy()
    factor_df = factor_time_df.copy()

    # Normalise column names for joins
    if "factor_name" in impact_df.columns:
        impact_df = impact_df.rename(columns={"factor_name": "factor"})
    elif "factor" not in impact_df.columns:
        impact_df = impact_df.rename(columns={impact_df.columns[0]: "factor"})

    if "factor_name" in factor_df.columns:
        factor_df = factor_df.rename(columns={"factor_name": "factor"})

    # Ensure scope is present for join; if missing, fill with 'unknown'
    if "scope" not in factor_df.columns:
        factor_df["scope"] = factor_df.get("factor_scope", "unknown")
    if "scope" not in impact_df.columns:
        impact_df["scope"] = "unknown"

    # Convert start/end dates to datetime.date for matching
    factor_df = factor_df.copy()
    factor_df["start_date"] = factor_df["start_date"].apply(_normalise_date)
    factor_df["end_date"] = factor_df["end_date"].apply(_normalise_date)

    merged = pd.merge(factor_df, impact_df, on=["factor", "scope"], how="left", suffixes=("_time", "_impact"))

    trends = list(_iter_trends(llm_trend_summary))
    if trends:
        matched_driver_type = []
        matched_reason = []
        for _, row in merged.iterrows():
            trend = _match_trend(row.get("start_date"), row.get("end_date"), trends)
            if trend:
                matched_driver_type.append(trend.get("driver_type", ""))
                matched_reason.append(trend.get("ai_reason", ""))
            else:
                matched_driver_type.append("")
                matched_reason.append("")
        merged["driver_type"] = matched_driver_type
        merged["AI_Reason"] = matched_reason
    else:
        merged["driver_type"] = ""
        merged["AI_Reason"] = ""

    # Restore ISO string format for dates to maintain JSON serialisability
    merged["start_date"] = merged["start_date"].apply(lambda d: d.isoformat() if isinstance(d, date) else "")
    merged["end_date"] = merged["end_date"].apply(lambda d: d.isoformat() if isinstance(d, date) else "")

    desired_order = [
        "factor",
        "scope",
        "trend_count",
        "weighted_mean",
        "weighted_variance",
        "risk_reward_ratio",
        "average_duration",
        "total_duration",
        "start_date",
        "end_date",
        "duration_days",
        "time_interval",
        "driver_type",
        "AI_Reason",
    ]

    existing_columns = [col for col in desired_order if col in merged.columns]
    remaining_columns = [col for col in merged.columns if col not in existing_columns]

    return merged[existing_columns + remaining_columns]

