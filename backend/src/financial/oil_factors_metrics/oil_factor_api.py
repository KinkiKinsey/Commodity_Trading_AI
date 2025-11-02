"""
Oil factor API: thin wrapper that retrieves pre-computed outputs from Redis.

The heavy lifting (yfinance downloads, model calls, incremental updates, etc.)
is now handled offline by the data pipeline. The FastAPI endpoint only needs to
pull the cached CSV snapshots and merge them into the unified queries dataframe.
"""

from __future__ import annotations

import pandas as pd
from fastapi import HTTPException

from io import StringIO

from src.financial.DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage
from .create_queries_df import create_queries_df


def _redis_key(prefix: str, ticker: str) -> str:
    normalised = ticker.replace(".", "_").replace("=", "_")
    return f"Crude_Oil:Future_Contract:{normalised}:{prefix}"


def _load_queries_snapshot(ticker: str) -> pd.DataFrame | None:
    """
    Prefer the pre-computed Queries_DF.csv snapshot pushed by the data pipeline.
    This keeps the API aligned with the latest Redis refresh cycle and avoids
    re-computing joins that have already been materialised upstream.
    """
    redis_client = RedisDatabaseStorage()
    csv_key = _redis_key("Queries_DF.csv", ticker)
    csv_payload = redis_client.redis_client.get(csv_key)

    if not csv_payload:
        return None

    try:
        frame = pd.read_csv(StringIO(csv_payload))
    except Exception as exc:  # pragma: no cover - pandas parsing errors are data dependent
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse cached Queries_DF.csv for {ticker}: {exc}",
        ) from exc

    if frame is None or frame.empty:
        return None

    return frame


def _load_cached_components(ticker: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    redis_client = RedisDatabaseStorage()

    impact_csv = redis_client.redis_client.get(_redis_key("Impact_Metrics.csv", ticker))
    factor_csv = redis_client.redis_client.get(_redis_key("Factor_Time.csv", ticker))
    llm_json = redis_client.get_json(_redis_key("LLM_Trend_Analyst_Result", ticker))

    if not impact_csv or not factor_csv or not isinstance(llm_json, dict) or "llm_summary" not in llm_json:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Pre-computed oil factor data not found for {ticker}. "
                "Please ensure the upstream job pushes Impact_Metrics.csv, "
                "Factor_Time.csv and LLM_Trend_Analyst_Result to Redis."
            ),
        )

    impact_df = pd.read_csv(StringIO(impact_csv))
    factor_df = pd.read_csv(StringIO(factor_csv))
    return impact_df, factor_df, llm_json


def _build_queries_df(ticker: str) -> pd.DataFrame:
    snapshot = _load_queries_snapshot(ticker)
    if snapshot is not None:
        return snapshot

    impact_df, factor_df, llm_summary = _load_cached_components(ticker)
    return create_queries_df(
        impact_metrics_df=impact_df,
        factor_time_df=factor_df,
        llm_trend_summary=llm_summary,
    )


async def get_oil_factors(
    ticker: str = "CLZ25.NYM",
    language: str = "Chinese",  # retained for interface compatibility; not used
    force_refresh: bool = False,  # retained for interface compatibility; not used
) -> pd.DataFrame:
    return _build_queries_df(ticker)


def get_oil_factors_sync(
    ticker: str = "CLZ25.NYM",
    language: str = "Chinese",
    force_refresh: bool = False,
) -> pd.DataFrame:
    return _build_queries_df(ticker)

