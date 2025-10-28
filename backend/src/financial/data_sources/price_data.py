"""
Alpha Vantage based price data fetching helpers with caching and retry support.

Features:
    * in-memory cache for repeat requests within a TTL window
    * Alpha Vantage daily time series with graceful degradation when OHLC is unavailable
    * fallback to commodity endpoints (WTI/Brent) when standard symbols are not supported
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict

import pandas as pd
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

CACHE_TTL_SECONDS = int(os.getenv("PRICE_CACHE_TTL", "300"))
_CACHE: Dict[str, dict] = {}

ALPHAVANTAGE_API_KEY = (
    os.getenv("RINGSHELL_ALPHAVANTAGE_API_KEY")
    or os.getenv("ALPHAVANTAGE_API_KEY")
    or os.getenv("RINGSHELL_FMP_API_KEY")  # backward compatibility
    or os.getenv("FMP_API_KEY")
)

ALPHAVANTAGE_ENDPOINT = "https://www.alphavantage.co/query"

# Mapping from Yahoo style tickers to Alpha Vantage symbols
ALPHA_TICKER_MAP: Dict[str, str] = {
    "CLZ25.NYM": "CL",
    "CL=F": "CL",
    "BZ=F": "BZ",
    "GC=F": "GC",
    "DX-Y.NYB": "DX-Y.NYB",
    "WTICO/USD": "WTICO/USD",
}


def _cache_key(ticker: str, days: int, variant: str) -> str:
    return f"{ticker.upper()}|{days}|{variant}"


def _get_cache(key: str) -> pd.DataFrame | None:
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["timestamp"] > CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return entry["df"].copy()


def _set_cache(key: str, df: pd.DataFrame) -> None:
    _CACHE[key] = {"timestamp": time.time(), "df": df.copy()}


def _alpha_symbol(ticker: str) -> str:
    return ALPHA_TICKER_MAP.get(ticker.upper(), ticker)


def _request_alpha(params: dict) -> dict:
    try:
        response = requests.get(ALPHAVANTAGE_ENDPOINT, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:  # pragma: no cover - network issues
        print(f"[warn] alpha vantage request failed: {exc}")
        return {}


def _parse_time_series_daily(payload: dict, days: int) -> pd.DataFrame:
    series = payload.get("Time Series (Daily)")
    if not series:
        return pd.DataFrame()

    rows = []
    for date_str, values in series.items():
        try:
            rows.append(
                {
                    "date": datetime.strptime(date_str, "%Y-%m-%d"),
                    "open": float(values.get("1. open", values.get("1. Open", 0.0))),
                    "high": float(values.get("2. high", values.get("2. High", 0.0))),
                    "low": float(values.get("3. low", values.get("3. Low", 0.0))),
                    "close": float(values.get("4. close", values.get("4. Close", 0.0))),
                    "volume": float(values.get("5. volume", values.get("5. Volume", 0.0)) or 0.0),
                }
            )
        except (TypeError, ValueError):
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df.sort_values("date", inplace=True)
    cutoff = datetime.now() - timedelta(days=days + 5)
    df = df[df["date"] >= cutoff]
    df.reset_index(drop=True, inplace=True)
    return df


def _parse_commodity_series(payload: dict, days: int) -> pd.DataFrame:
    data = payload.get("data") or []
    if not isinstance(data, list):
        return pd.DataFrame()

    rows = []
    last_close = None
    for item in data:
        date_str = item.get("date") or item.get("timestamp")
        value = item.get("value") or item.get("price")
        if not date_str or value is None:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            close = float(value)
        except (ValueError, TypeError):
            continue

        open_price = last_close if last_close is not None else close
        high = max(open_price, close)
        low = min(open_price, close)
        rows.append(
            {
                "date": dt,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": float("nan"),
            }
        )
        last_close = close

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df.sort_values("date", inplace=True)
    cutoff = datetime.now() - timedelta(days=days + 5)
    df = df[df["date"] >= cutoff]
    df.reset_index(drop=True, inplace=True)
    return df


def _fetch_alpha_vantage(ticker: str, days: int) -> pd.DataFrame:
    if not ALPHAVANTAGE_API_KEY:
        raise RuntimeError("Alpha Vantage API key missing. Set ALPHAVANTAGE_API_KEY in environment.")

    symbol = _alpha_symbol(ticker)

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY,
        "outputsize": "full",
    }

    payload = _request_alpha(params)
    if "Note" in payload:
        print(f"[warn] alpha vantage notice: {payload['Note']}")

    df = _parse_time_series_daily(payload, days)
    if not df.empty:
        return df

    # Commodity fallback (WTI, Brent, etc.)
    commodity_function = None
    if symbol in {"CL", "WTICO/USD", "WTI"}:
        commodity_function = "WTI"
    elif symbol in {"BZ", "BRENT"}:
        commodity_function = "BRENT"

    if commodity_function:
        commodity_payload = _request_alpha({"function": commodity_function, "apikey": ALPHAVANTAGE_API_KEY})
        df = _parse_commodity_series(commodity_payload, days)
        if not df.empty:
            return df

    return pd.DataFrame()


def _normalise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["date"] = df["date"].dt.tz_localize(timezone.utc).dt.tz_convert(None)
    return df


def get_yahoo_data(ticker: str, days: int = 365, *, force_refresh: bool = False) -> pd.DataFrame:
    cache_key = _cache_key(ticker, days, "close")
    if not force_refresh:
        cached = _get_cache(cache_key)
        if cached is not None:
            return cached

    df = _fetch_alpha_vantage(ticker, days)
    if df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])

    df = _normalise_dataframe(df)
    df["volume"] = df["volume"].fillna(0.0)
    result = df[["date", "close", "volume"]].tail(500).reset_index(drop=True)
    _set_cache(cache_key, result)
    return result


def get_yahoo_data_comprehensive(ticker: str, days: int = 365, *, force_refresh: bool = False) -> pd.DataFrame:
    cache_key = _cache_key(ticker, days, "ohlcv")
    if not force_refresh:
        cached = _get_cache(cache_key)
        if cached is not None:
            return cached

    df = _fetch_alpha_vantage(ticker, days)
    if df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    df = _normalise_dataframe(df)
    for column in ("open", "high", "low", "close"):
        df[column] = df[column].astype(float)
    df["volume"] = df["volume"].fillna(0.0)

    result = df[["date", "open", "high", "low", "close", "volume"]].tail(500).reset_index(drop=True)
    _set_cache(cache_key, result)
    return result
