from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..news.service import fetch_latest_news, analyze_manual_news
from ..news.translator import translate_items

logger = logging.getLogger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL = float(os.getenv("NEWS_STREAM_HEARTBEAT", "10"))
POLL_INTERVAL = float(os.getenv("NEWS_STREAM_POLL_INTERVAL", "180"))
INITIAL_BATCH = int(os.getenv("NEWS_STREAM_INITIAL_BATCH", "20"))
NEWS_LIMIT = int(os.getenv("NEWS_STREAM_LIMIT", "60"))
TRANSLATION_MAX_ITEMS = int(os.getenv("NEWS_TRANSLATION_MAX_ITEMS", "40"))


class TranslationItem(BaseModel):
    id: str = Field(..., min_length=1, max_length=128)
    text: str = Field(..., min_length=1, max_length=8_000)


class TranslationPayload(BaseModel):
    target_locale: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]+)*$")
    items: list[TranslationItem] = Field(default_factory=list, max_items=TRANSLATION_MAX_ITEMS)


class AnalyzeNewsPayload(BaseModel):
    text: str = Field(..., min_length=20, max_length=8000)
    headline: str | None = Field(None, max_length=512)
    summary: str | None = Field(None, max_length=800)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sse_event(data: dict, *, event: str | None = None) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    if event:
        return f"event: {event}\ndata: {payload}\n\n"
    return f"data: {payload}\n\n"


async def _news_event_stream(request: Request):
    seen: Set[str] = set()
    last_poll = 0.0
    initial_sent = False

    while True:
        if await request.is_disconnected():
            break

        now = time.monotonic()
        should_poll = (now - last_poll) >= POLL_INTERVAL or not initial_sent

        if should_poll:
            try:
                events = await fetch_latest_news(limit=NEWS_LIMIT)
            except Exception as exc:
                yield _sse_event({"timestamp": _now_iso(), "error": str(exc)}, event="heartbeat")
            else:
                fresh_events = []
                for event in events:
                    event_id = event.get("eventId")
                    if not event_id or event_id in seen:
                        continue
                    fresh_events.append(event)
                if fresh_events:
                    if not initial_sent:
                        to_send = fresh_events[:INITIAL_BATCH]
                        initial_sent = True
                    else:
                        to_send = fresh_events
                    for event in fresh_events:
                        event_id = event.get("eventId")
                        if event_id:
                            seen.add(event_id)
                    for item in to_send:
                        yield _sse_event(item)
                last_poll = now

        yield _sse_event({"timestamp": _now_iso()}, event="heartbeat")
        await asyncio.sleep(HEARTBEAT_INTERVAL)


@router.get("/api/news/stream")
async def stream_news(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _news_event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/api/news/latest")
async def latest_news(limit: int = 40) -> JSONResponse:
    events = await fetch_latest_news(limit=min(max(limit, 1), NEWS_LIMIT))
    return JSONResponse(events)


@router.post("/api/news/translate")
async def translate_news(payload: TranslationPayload) -> JSONResponse:
    # Translation disabled - return original text to avoid OpenAI blocking
    if not payload.items:
        return JSONResponse({"translations": {}}, status_code=200)

    unique_items: Dict[str, str] = {}
    for item in payload.items:
        if item.id not in unique_items:
            unique_items[item.id] = item.text

    # Return original text without translation
    return JSONResponse({"translations": unique_items})


@router.post("/api/news/analyze")
async def analyze_news(payload: AnalyzeNewsPayload) -> JSONResponse:
    event = await analyze_manual_news(payload.text, payload.headline, payload.summary)
    return JSONResponse(event)
