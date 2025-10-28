from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Set

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ..news.service import fetch_latest_news

router = APIRouter()

HEARTBEAT_INTERVAL = float(os.getenv("NEWS_STREAM_HEARTBEAT", "10"))
POLL_INTERVAL = float(os.getenv("NEWS_STREAM_POLL_INTERVAL", "180"))
INITIAL_BATCH = int(os.getenv("NEWS_STREAM_INITIAL_BATCH", "20"))
NEWS_LIMIT = int(os.getenv("NEWS_STREAM_LIMIT", "60"))


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
