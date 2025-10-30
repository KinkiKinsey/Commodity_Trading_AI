import pandas as pd
from io import StringIO
from typing import Dict, Any

from DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage


def _ticker_storage_key(ticker: str) -> str:
    return ticker.replace('.', '_').replace('=', '_')


def FactorMetrics_FrontendCheck() -> pd.DataFrame:
    """
    Inspect Redis and list available oil factor artifacts per ticker.

    Returns a DataFrame with columns:
    - ticker
    - has_impact_metrics
    - has_factor_time
    - has_queries_df
    - has_llm_summary
    - has_metadata
    """
    storage = RedisDatabaseStorage()
    r = storage.redis_client

    base_prefix = "Crude_Oil:Future_Contract:"

    # Collect all candidate keys once
    keys = r.keys(f"{base_prefix}*")

    per_ticker: Dict[str, Dict[str, Any]] = {}
    for k in keys:
        # Expect keys like: Crude_Oil:Future_Contract:{TICKER_KEY}:{Artifact}
        parts = k.split(":")
        if len(parts) < 4:
            continue
        ticker_key = parts[2]
        artifact = parts[3]

        d = per_ticker.setdefault(ticker_key, {
            "has_impact_metrics": False,
            "has_factor_time": False,
            "has_queries_df": False,
            "has_llm_summary": False,
            "has_metadata": False,
        })

        if artifact == "Impact_Metrics.csv":
            d["has_impact_metrics"] = True
        elif artifact == "Factor_Time.csv":
            d["has_factor_time"] = True
        elif artifact == "Queries_DF.csv":
            d["has_queries_df"] = True
        elif artifact == "LLM_Trend_Analyst_Result":
            d["has_llm_summary"] = True
        elif artifact == "Metadata":
            d["has_metadata"] = True

    rows = []
    for ticker_key, flags in per_ticker.items():
        # Reverse storage key to display original-like ticker (best effort)
        # We cannot fully recover dots/equals; show underscore form for clarity.
        rows.append({
            "ticker": ticker_key,
            **flags,
        })

    return pd.DataFrame(rows).sort_values("ticker").reset_index(drop=True)


def FactorMetrics_Queries_Call(ticker: str) -> pd.DataFrame:
    """
    Fetch the Queries DF for a given ticker from Redis and return as DataFrame.

    Expects key pattern:
    Crude_Oil:Future_Contract:{ticker_storage_key}:Queries_DF.csv
    """
    storage = RedisDatabaseStorage()
    r = storage.redis_client

    storage_key = _ticker_storage_key(ticker)
    key = f"Crude_Oil:Future_Contract:{storage_key}:Queries_DF.csv"

    data = r.get(key)
    if not data:
        raise FileNotFoundError(f"Queries DF not found in Redis for ticker '{ticker}' (key: {key})")

    return pd.read_csv(StringIO(data))


