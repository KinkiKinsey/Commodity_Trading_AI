"""
Price data fetching helpers with lightweight caching and retry support.

Features:
    * in-memory cache for repeat requests within a TTL window
    * automatic retries with backoff when Yahoo rate limits
    * fallbacks to ticker.history and the public chart API
"""



from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict

import pandas as pd
import requests
import yfinance as yf


CACHE_TTL_SECONDS = int(os.getenv("PRICE_CACHE_TTL", "300"))
_CACHE: Dict[str, dict] = {}
_HTTP_SESSION: requests.Session | None = None

try:
    from yfinance.exceptions import YFRateLimitError  # type: ignore
except Exception:  # pragma: no cover - fallback for older yfinance
    try:
        from yfinance.shared._exceptions import YFRateLimitError  # type: ignore
    except Exception:
        class YFRateLimitError(Exception):  # type: ignore
            """Fallback YFRateLimitError when yfinance API changes."""


def _get_http_session() -> requests.Session:
    global _HTTP_SESSION
    if _HTTP_SESSION is None:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": os.getenv(
                    "YFINANCE_USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
                )
            }
        )
        _HTTP_SESSION = session
    return _HTTP_SESSION


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


def _download_ohlc(ticker: str, start: datetime, end: datetime, interval: str = "1d") -> pd.DataFrame:
    return yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )


def _fallback_history(ticker: str, days: int, interval: str = "1d") -> pd.DataFrame:
    try:
        period = f"{max(days, 5)}d"
        ticker_obj = yf.Ticker(ticker)
        return ticker_obj.history(period=period, interval=interval, auto_adjust=False)
    except Exception:
        return pd.DataFrame()


def _fallback_chart_api(ticker: str, start: datetime, end: datetime, interval: str = "1d") -> pd.DataFrame:
    session = _get_http_session()
    params = {
        "period1": int(start.timestamp()),
        "period2": int(end.timestamp()),
        "interval": interval,
    }
    try:
        response = session.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("chart", {}).get("result")
        if not result:
            return pd.DataFrame()
        primary = result[0]
        timestamps = primary.get("timestamp") or []
        indicators = primary.get("indicators", {}).get("quote", [{}])[0]
        if not timestamps or not indicators:
            return pd.DataFrame()
        df = pd.DataFrame(
            {
                "open": indicators.get("open"),
                "high": indicators.get("high"),
                "low": indicators.get("low"),
                "close": indicators.get("close"),
                "volume": indicators.get("volume"),
            },
            index=pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None),
        )
        df.index.name = "date"
        return df.reset_index().dropna(how="all")
    except Exception:
        return pd.DataFrame()


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    df = df.copy()
    df.columns = [str(col).lower() for col in df.columns]
    df = df.reset_index()
    df.columns = [str(col).lower() for col in df.columns]
    if "date" in df.columns and "index" in df.columns:
        df.drop(columns=["index"], inplace=True)
    elif "index" in df.columns:
        df.rename(columns={"index": "date"}, inplace=True)
    df.columns = [str(col).lower() for col in df.columns]
    if "date" not in df.columns and df.columns:
        df.rename(columns={df.columns[0]: "date"}, inplace=True)
    return df


def get_yahoo_data(ticker: str, days: int = 365, *, force_refresh: bool = False) -> pd.DataFrame:
    cache_key = _cache_key(ticker, days, "close")
    if not force_refresh:
        cached = _get_cache(cache_key)
        if cached is not None:
            return cached

    end_date = datetime.now(timezone.utc) + timedelta(days=1)
    start_date = end_date - timedelta(days=days)

    df = pd.DataFrame()
    for attempt in range(3):
        sleep_seconds = 1 + attempt
        try:
            df = _download_ohlc(ticker, start_date, end_date)
            if df.empty:
                df = _fallback_history(ticker, days)
            if df.empty:
                df = _fallback_chart_api(ticker, start_date, end_date)
            if not df.empty:
                break
        except YFRateLimitError as exc:
            sleep_seconds = 60 * (attempt + 1)
            print(f"[warn] yahoo close rate limited for {ticker} (attempt {attempt + 1}): {exc}")
        except Exception as exc:
            print(f"[warn] yahoo close fetch attempt {attempt + 1} failed for {ticker}: {exc}")
        if attempt < 2:
            time.sleep(sleep_seconds)

    if df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])

    df = _normalise_columns(df)
    for column in ("close", "volume"):
        if column not in df.columns:
            df[column] = float("nan")

    df = df[["date", "close", "volume"]].copy()
    df.dropna(subset=["close"], inplace=True)
    df = df.tail(500).reset_index(drop=True)
    _set_cache(cache_key, df)
    return df


def get_yahoo_data_comprehensive(ticker: str, days: int = 365, *, force_refresh: bool = False) -> pd.DataFrame:
    cache_key = _cache_key(ticker, days, "ohlcv")
    if not force_refresh:
        cached = _get_cache(cache_key)
        if cached is not None:
            return cached

    end_date = datetime.now(timezone.utc) + timedelta(days=1)
    start_date = end_date - timedelta(days=days)

    df = pd.DataFrame()
    for attempt in range(3):
        sleep_seconds = 1 + attempt
        try:
            df = _download_ohlc(ticker, start_date, end_date)
            if df.empty:
                df = _fallback_history(ticker, days)
            if df.empty:
                df = _fallback_chart_api(ticker, start_date, end_date)
            if not df.empty:
                break
        except YFRateLimitError as exc:
            sleep_seconds = 60 * (attempt + 1)
            print(f"[warn] yahoo ohlcv rate limited for {ticker} (attempt {attempt + 1}): {exc}")
        except Exception as exc:
            print(f"[warn] yahoo ohlcv fetch attempt {attempt + 1} failed for {ticker}: {exc}")
        if attempt < 2:
            time.sleep(sleep_seconds)

    if df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    df = _normalise_columns(df)
    for column in ("open", "high", "low", "close", "volume"):
        if column not in df.columns:
            df[column] = float("nan")

    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df.dropna(subset=["open", "high", "low", "close"], inplace=True)
    df = df.tail(500).reset_index(drop=True)
    _set_cache(cache_key, df)
    return df
