import httpx
import os
from langchain_core.tools import tool


CTP_BASE_URL = os.getenv("CTP_SERVICE_URL", "http://ctp-service:8080")


async_client = httpx.AsyncClient(base_url=CTP_BASE_URL, timeout=30.0)


@tool
async def check_ctp_status() -> dict:
    """
    Check connectivity and configuration of the CTP service.
    """
    try:
        resp = await async_client.get("/health")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"CTP service unreachable: {e}"}


@tool
async def md_subscribe(instrument_ids: list[str]) -> dict:
    """
    Subscribe to market data for a list of instruments.
    """
    try:
        resp = await async_client.post("/md/subscribe", json={"instrument_ids": instrument_ids})
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to subscribe: {e}"}


@tool
async def md_unsubscribe(instrument_ids: list[str]) -> dict:
    """
    Unsubscribe market data for a list of instruments.
    """
    try:
        resp = await async_client.post("/md/unsubscribe", json={"instrument_ids": instrument_ids})
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to unsubscribe: {e}"}


@tool
async def md_tick(instrument_id: str) -> dict:
    """
    Get a test tick for a subscribed instrument.
    """
    try:
        resp = await async_client.get(f"/md/tick/{instrument_id}")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to fetch tick: {e}"}


# No order placement tool (info-only)


@tool
async def list_orders() -> dict:
    try:
        resp = await async_client.get("/orders")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to list orders: {e}"}


# No order replace tool (info-only)


# No order cancel tool (info-only)


@tool
async def list_positions() -> dict:
    try:
        resp = await async_client.get("/positions")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to list positions: {e}"}


@tool
async def list_trades() -> dict:
    try:
        resp = await async_client.get("/trades")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to list trades: {e}"}


@tool
async def get_instrument(instrument_id: str) -> dict:
    try:
        resp = await async_client.get(f"/instruments/{instrument_id}")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to get instrument: {e}"}


