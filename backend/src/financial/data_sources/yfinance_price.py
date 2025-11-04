"""
Lightweight Yahoo Finance helpers backed by yfinance.

These helpers are used by the oil factor pipeline so that we do not depend on
the Alpha Vantage based implementation that powers the K-line API.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import time

import pandas as pd
import yfinance as yf

MAX_RETRIES = 4
INITIAL_SLEEP_SECONDS = 15


def _download_ticker(
    ticker: str,
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> pd.DataFrame:
    sleep_seconds = INITIAL_SLEEP_SECONDS
    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            data = yf.download(
                ticker,
                start=start.strftime("%Y-%m-%d") if start else None,
                end=end.strftime("%Y-%m-%d") if end else None,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            if not data.empty:
                break
        except Exception as exc:  # pragma: no cover - network dependent
            last_exception = exc
            message = str(exc).lower()
            if attempt == MAX_RETRIES - 1 or not any(token in message for token in ("rate", "limit", "timed")):
                raise
        else:
            last_exception = None

        time.sleep(sleep_seconds)
        sleep_seconds *= 2
    else:
        if last_exception:
            raise last_exception
        data = pd.DataFrame()

    if data.empty:
        return data

    # Flatten multi-index columns if present.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Reset index first to get Date as a column
    data.reset_index(inplace=True)
    
    # Rename columns to lowercase
    data = data.rename(columns=str.lower)
    
    # Rename index/date column
    if 'index' in data.columns:
        data.rename(columns={"index": "date"}, inplace=True)
    
    return data


def get_yahoo_data(ticker: str, days: int = 365) -> pd.DataFrame:
    """
    Fetch historical close/volume data for the supplied ticker using yfinance.

    Returns a DataFrame with columns: date, close, volume.
    """
    end = datetime.utcnow() + timedelta(days=1)
    start = end - timedelta(days=max(days, 1))

    df = _download_ticker(ticker, start=start, end=end)
    if df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])

    expected_columns = {"date", "close", "volume"}
    missing = expected_columns.difference(df.columns)
    if missing:
        # Ensure all expected columns exist even if yfinance omits volume (e.g. futures).
        for column in missing:
            df[column] = 0.0 if column == "volume" else None

    result = df[["date", "close", "volume"]].copy()
    result["date"] = pd.to_datetime(result["date"])
    result.sort_values("date", inplace=True)
    result.reset_index(drop=True, inplace=True)
    return result


def get_yahoo_data_comprehensive(ticker: str, days: int = 365) -> pd.DataFrame:
    """
    Fetch OHLCV data for the supplied ticker using yfinance.

    Returns a DataFrame with columns: date, open, high, low, close, volume.
    """
    end = datetime.utcnow() + timedelta(days=1)
    start = end - timedelta(days=max(days, 1))

    df = _download_ticker(ticker, start=start, end=end)
    if df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    # Ensure all columns exist
    expected_columns = ["open", "high", "low", "close", "volume"]
    for column in expected_columns:
        if column not in df.columns:
            df[column] = 0.0 if column == "volume" else None

    result = df[["date", "open", "high", "low", "close", "volume"]].copy()
    result["date"] = pd.to_datetime(result["date"])
    result.sort_values("date", inplace=True)
    result.reset_index(drop=True, inplace=True)
    return result
