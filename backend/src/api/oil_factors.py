from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from src.financial.oil_factors_metrics.oil_factor_api import get_oil_factors

router = APIRouter()


@router.get("/api/oil/factors")
async def get_oil_factor_metrics(
    ticker: str = Query("CLZ25.NYM", min_length=1, max_length=32, description="Oil futures ticker symbol"),
    language: str = Query("Chinese", min_length=2, max_length=16, description="Output language (Chinese or English)"),
    force_refresh: bool = Query(
        False,
        description="Force regeneration of factor metrics instead of using cached results.",
    ),
) -> Dict[str, Any]:
    """
    Return oil factor metrics merged with LLM explanations for the specified ticker.
    """
    try:
        df = await get_oil_factors(ticker=ticker, language=language, force_refresh=force_refresh)
    except Exception as exc:  # pragma: no cover - dependent on external services
        raise HTTPException(status_code=502, detail=f"Failed to compute oil factors: {exc}") from exc

    if df is None or df.empty:
        return {"ticker": ticker, "language": language, "count": 0, "factors": []}

    records = json.loads(df.to_json(orient="records", date_format="iso"))
    return {"ticker": ticker, "language": language, "count": len(records), "factors": records}

