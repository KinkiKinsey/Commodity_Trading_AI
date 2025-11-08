"""
Lightweight client for the proprietary `/md/tick/{instrument_id}` endpoint.

Provides a synchronous helper used by the FastAPI layer to obtain the latest
quote for a given instrument and raise clear exceptions when the upstream
service fails or returns malformed data.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")


class TickApiError(RuntimeError):
    """Raised when the md/tick upstream cannot be reached or returns bad data."""


def _base_url() -> str:
    raw = os.getenv("MD_TICK_BASE_URL", "http://47.108.177.50:8080")
    return raw.rstrip("/")


def _build_url(instrument_id: str) -> str:
    if not instrument_id:
        raise ValueError("instrument_id must not be empty")
    return f"{_base_url()}/md/tick/{instrument_id}"


def fetch_md_tick(instrument_id: str) -> Dict[str, Any]:
    """
    Fetch the latest tick data for the provided instrument identifier.

    Raises:
        TickApiError: when the request fails, response is not JSON, or `ok` flag is false.
    """

    url = _build_url(instrument_id)
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network instability
        raise TickApiError(f"md/tick request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise TickApiError("md/tick response is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise TickApiError("md/tick response must be a JSON object")
    if not payload.get("ok"):
        raise TickApiError(f"md/tick response indicates failure: {payload}")

    return payload
