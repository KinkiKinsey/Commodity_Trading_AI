from __future__ import annotations

import asyncio
import hashlib
import os
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Sequence, Tuple
from pathlib import Path

import httpx
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.core.commodity_agent import commodity_agent
from src.models.schema import ChainOfThoughtStep

logger = logging.getLogger(__name__)
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
CHAIN_OF_THOUGHT_LIMIT = int(os.getenv("NEWS_CHAIN_OF_THOUGHT_LIMIT", "6"))
try:
    _cot_timeout_raw = os.getenv("NEWS_CHAIN_OF_THOUGHT_TIMEOUT", "45")
    CHAIN_OF_THOUGHT_TIMEOUT = float(_cot_timeout_raw)
except ValueError:  # pragma: no cover - defensive parsing
    CHAIN_OF_THOUGHT_TIMEOUT = 45.0
if CHAIN_OF_THOUGHT_TIMEOUT <= 0:  # type: ignore[operator]
    CHAIN_OF_THOUGHT_TIMEOUT = None


def _detect_language(text: str) -> str:
    """Lightweight language heuristic to align UI localization."""
    return "zh-CN" if re.search(r"[\u3400-\u9FFF]", text) else "en-US"


def _alpha_api_key() -> str | None:
    return os.getenv("RINGSHELL_ALPHAVANTAGE_API_KEY") or os.getenv("ALPHAVANTAGE_API_KEY")


def _fmp_api_key() -> str | None:
    return os.getenv("RINGSHELL_FMP_API_KEY") or os.getenv("FMP_API_KEY")


async def _fetch_fmp_articles(
    client: httpx.AsyncClient,
    api_key: str,
    limit: int,
    *,
    page: int = 0,
) -> list[dict]:
    size = max(limit * 2, 20)
    try:
        response = await client.get(
            FMP_NEWS_ENDPOINT,
            params={"page": page, "size": size, "apikey": api_key},
            timeout=20.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("FMP news fetch failed: %s", exc)
        return []

    payload = response.json()
    if isinstance(payload, dict):
        content = payload.get("content") or payload.get("items")
        if isinstance(content, list):
            return content
        logger.warning("Unexpected FMP payload keys: %s", list(payload.keys()))
        return []
    if isinstance(payload, list):
        return payload

    logger.warning("Unexpected FMP payload type: %s", type(payload))
    return []


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


def _summarize_text(text: str, limit: int = 200) -> str:
    clean = re.sub(r"\s+", " ", text.strip())
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + "…"


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

    return {
        "eventId": event_id,
        "timestamp": timestamp,
        "headline": title or "Untitled",
        "summary": summary,
        "direction": direction,
        "confidence": round(confidence, 2),
        "language": language,
        "chain_of_thought": [],
        "citations": [url] if url else [],
        "signalTags": [direction],
        "complianceStatus": "clean",
        "signal": None,
    }


def _build_agent_payload(event: dict, article: dict) -> str:
    parts: Sequence[str | None] = (
        f"Headline: {event.get('headline')}",
        f"Summary: {event.get('summary')}",
        article.get("text"),
        article.get("content"),
        article.get("overall_sentiment_label"),
    )
    return "\n".join(part for part in parts if part)


async def _apply_chain_of_thought(event: dict, article: dict) -> dict:
    payload = _build_agent_payload(event, article).strip()
    if not payload:
        return event

    try:
        result = await commodity_agent.ainvoke({"messages": [HumanMessage(content=payload)]})
    except Exception as exc:  # pragma: no cover - LLM/tool failures
        logger.warning("Commodity agent failed for %s: %s", event.get("eventId"), exc)
        return event

    analysis = result.get("analysis")
    if not analysis:
        return event

    chain = list(analysis.chain_of_thought or [])
    if chain:
        steps: list[ChainOfThoughtStep] = [
            ChainOfThoughtStep(
                id=f"{event['eventId']}-step-{idx+1}",
                step=idx + 1,
                text=step,
            )
            for idx, step in enumerate(chain)
        ]
        event["chain_of_thought"] = [step.dict() for step in steps]

    event["direction"] = analysis.direction
    event["confidence"] = float(analysis.confidence)
    if analysis.citations:
        event["citations"] = analysis.citations
    event["signalTags"] = [analysis.direction]

    return event


async def fetch_latest_news(limit: int = 40, days_back: int = 3) -> List[dict]:
    alpha_key = _alpha_api_key()
    fmp_key = _fmp_api_key()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)

    articles: list[dict] = []
    async with httpx.AsyncClient() as client:
        if fmp_key:
            articles = await _fetch_fmp_articles(client, fmp_key, limit)

        if not articles:
            params = {
                "function": "NEWS_SENTIMENT",
                "topics": DEFAULT_TOPICS,
                "sort": "LATEST",
                "time_from": start_date.strftime("%Y%m%dT%H%M"),
                "time_to": end_date.strftime("%Y%m%dT%H%M"),
                "limit": str(max(limit * 3, 20)),
                "apikey": alpha_key or "demo",
            }
            articles = await _fetch_json(client, params)

        if not articles and fmp_key:
            # As a last resort retry FMP once more (Alpha may have failed or returned empty).
            articles = await _fetch_fmp_articles(client, fmp_key, limit)

    articles.sort(key=lambda x: x.get("publishedDate") or x.get("timestamp") or x.get("date") or "", reverse=True)

    seen: set[str] = set()
    processed: list[tuple[dict, dict]] = []
    for article in articles:
        event = _convert_article(article)
        if event["eventId"] in seen:
            continue
        seen.add(event["eventId"])

        processed.append((event, article))
        if len(processed) >= limit:
            break

    events: list[dict] = [event for event, _ in processed]

    chain_count = min(CHAIN_OF_THOUGHT_LIMIT, len(processed))
    if chain_count:
        coroutines = []
        for idx in range(chain_count):
            coro = _apply_chain_of_thought(processed[idx][0], processed[idx][1])
            if CHAIN_OF_THOUGHT_TIMEOUT:
                coro = asyncio.wait_for(coro, timeout=CHAIN_OF_THOUGHT_TIMEOUT)
            coroutines.append(coro)

        enriched = await asyncio.gather(*coroutines, return_exceptions=True)
        for idx, outcome in enumerate(enriched):
            if isinstance(outcome, Exception):
                logger.warning(
                    "Commodity agent timed out after %.1fs for %s",
                    CHAIN_OF_THOUGHT_TIMEOUT or 0.0,
                    processed[idx][0].get("eventId"),
                )
                continue
            events[idx] = outcome

    return events


async def analyze_manual_news(text: str, headline: str | None = None, summary: str | None = None) -> dict:
    """Run the commodity agent against an arbitrary news snippet."""
    body = text.strip()
    if not body:
        raise ValueError("News text must not be empty.")

    language = _detect_language(body)
    headline_value = headline.strip() if headline else _summarize_text(body, 96) or "Untitled Insight"
    summary_value = summary.strip() if summary else _summarize_text(body, 220)

    event_id = f"manual-{hashlib.sha1(body.encode('utf-8'), usedforsecurity=False).hexdigest()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    direction, confidence = _infer_sentiment(body)

    event: dict = {
        "eventId": event_id,
        "timestamp": timestamp,
        "headline": headline_value,
        "summary": summary_value,
        "direction": direction,
        "confidence": round(confidence, 2),
        "language": language,
        "chain_of_thought": [],
        "citations": [],
        "signalTags": [direction],
        "complianceStatus": "clean",
        "signal": None,
    }

    try:
        result = await commodity_agent.ainvoke({"messages": [HumanMessage(content=body)]})
    except Exception as exc:  # pragma: no cover - LLM/tool failures
        logger.warning("Manual commodity analysis failed: %s", exc)
        return event

    analysis = result.get("analysis")
    if not analysis:
        return event

    chain = list(analysis.chain_of_thought or [])
    if chain:
        event["chain_of_thought"] = [
            ChainOfThoughtStep(
                id=f"{event_id}-step-{idx + 1}",
                step=idx + 1,
                text=step,
            ).dict()
            for idx, step in enumerate(chain)
        ]

    event["direction"] = analysis.direction
    event["confidence"] = float(analysis.confidence)
    event["signalTags"] = [analysis.direction]
    if analysis.citations:
        event["citations"] = analysis.citations

    return event
