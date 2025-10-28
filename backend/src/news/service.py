from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List
from pathlib import Path

import httpx
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

POSITIVE_KEYWORDS = (
    "surge",
    "gain",
    "optimis",
    "support",
    "bull",
    "rebound",
    "rally",
    "strength",
)
NEGATIVE_KEYWORDS = (
    "drop",
    "risk",
    "concern",
    "loss",
    "fear",
    "slump",
    "bear",
    "weak",
    "decline",
)

NEWS_ENDPOINT = "https://www.alphavantage.co/query"
FMP_NEWS_ENDPOINT = "https://financialmodelingprep.com/api/v3/fmp/articles"
DEFAULT_TOPICS = os.getenv("ALPHAVANTAGE_TOPICS", "energy,commodities,financial_markets")


def _alpha_api_key() -> str | None:
    return os.getenv("RINGSHELL_ALPHAVANTAGE_API_KEY") or os.getenv("ALPHAVANTAGE_API_KEY")


def _fmp_api_key() -> str | None:
    return os.getenv("RINGSHELL_FMP_API_KEY") or os.getenv("FMP_API_KEY")


async def _fetch_json(client: httpx.AsyncClient, params: dict) -> list[dict]:
    response = await client.get(NEWS_ENDPOINT, params=params, timeout=20.0)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403}:
            raise RuntimeError(
                "AlphaVantage API authentication failed. Set ALPHAVANTAGE_API_KEY or RINGSHELL_ALPHAVANTAGE_API_KEY in your environment."
            ) from exc
        raise
    data = response.json()
    if isinstance(data, dict):
        if "feed" in data:
            return data["feed"] or []
        if "items" in data:
            return data["items"] or []
        if "news" in data:
            return data["news"] or []
    if isinstance(data, list):
        return data
    return []


def _normalise_timestamp(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y%m%dT%H%M%S", "%Y%m%dT%H%M"):
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        else:
            return datetime.now(timezone.utc).isoformat()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _make_event_id(*parts: str) -> str:
    raw = "|".join(part or "" for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8"), usedforsecurity=False).hexdigest()
    return f"fmp-{digest}"


def _infer_sentiment(text: str) -> tuple[str, float]:
    lower = text.lower()
    if any(word in lower for word in POSITIVE_KEYWORDS):
        return "bullish", 0.65
    if any(word in lower for word in NEGATIVE_KEYWORDS):
        return "bearish", 0.65
    return "neutral", 0.5


def _convert_article(article: dict) -> dict:
    title = (
        article.get("title")
        or article.get("news_title")
        or article.get("headline")
        or article.get("summary")
        or ""
    )
    raw_text = (
        article.get("summary")
        or article.get("text")
        or article.get("content")
        or article.get("overall_sentiment_label")
        or ""
    )
    plain_text = re.sub(r"<[^>]+>", "", raw_text) if raw_text else raw_text
    combined_source = plain_text or raw_text or ""
    combined = f"{title} {combined_source}".strip()
    label = (article.get("overall_sentiment_label") or "").lower()
    score = 0.0
    try:
        score = float(article.get("overall_sentiment_score", 0.0))
    except (TypeError, ValueError):
        score = 0.0

    if label == "bullish":
        direction = "bullish"
        confidence = min(0.9, max(0.5, abs(score)))
    elif label == "bearish":
        direction = "bearish"
        confidence = min(0.9, max(0.5, abs(score)))
    else:
        direction, confidence = _infer_sentiment(combined)

    timestamp = _normalise_timestamp(
        article.get("time_published")
        or article.get("publishedDate")
        or article.get("timestamp")
        or article.get("date")
    )
    url = article.get("url") or article.get("link") or article.get("source")
    event_id = _make_event_id(timestamp, title, url or (article.get("authors") or article.get("source")))
    summary = (plain_text[:280] + "...") if plain_text and len(plain_text) > 280 else (plain_text or None)
    summary = summary.strip() if summary else None
    language = article.get("language") or "en"

    chain_text = summary or title or "No summary provided."

    return {
        "eventId": event_id,
        "timestamp": timestamp,
        "headline": title or "Untitled",
        "summary": summary,
        "direction": direction,
        "confidence": round(confidence, 2),
        "language": language,
        "chain_of_thought": [
            {
                "id": f"{event_id}-step-1",
                "step": 1,
                "text": chain_text,
            }
        ],
        "citations": [url] if url else [],
        "signalTags": [direction],
        "complianceStatus": "clean",
        "signal": None,
    }


async def fetch_latest_news(limit: int = 40, days_back: int = 3) -> List[dict]:
    alpha_key = _alpha_api_key()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)

    params = {
        "function": "NEWS_SENTIMENT",
        "topics": DEFAULT_TOPICS,
        "sort": "LATEST",
        "time_from": start_date.strftime("%Y%m%dT%H%M"),
        "time_to": end_date.strftime("%Y%m%dT%H%M"),
        "limit": str(max(limit * 3, 20)),
        "apikey": alpha_key or "demo",
    }

    async with httpx.AsyncClient() as client:
        articles = await _fetch_json(client, params)
        if not articles:
            fmp_key = _fmp_api_key()
            if fmp_key:
                size = max(limit * 2, 20)
                try:
                    response = await client.get(
                        FMP_NEWS_ENDPOINT,
                        params={"page": 0, "size": size, "apikey": fmp_key},
                        timeout=20.0,
                    )
                    response.raise_for_status()
                except httpx.HTTPError:
                    articles = []
                else:
                    payload = response.json()
                    if isinstance(payload, dict):
                        content = payload.get("content") or payload.get("items")
                        articles = content if isinstance(content, list) else []
                    elif isinstance(payload, list):
                        articles = payload
                    else:
                        articles = []

    articles.sort(key=lambda x: x.get("publishedDate") or x.get("timestamp") or x.get("date") or "", reverse=True)

    seen: set[str] = set()
    events: list[dict] = []
    for article in articles:
        event = _convert_article(article)
        if event["eventId"] in seen:
            continue
        seen.add(event["eventId"])
        events.append(event)
        if len(events) >= limit:
            break

    return events
