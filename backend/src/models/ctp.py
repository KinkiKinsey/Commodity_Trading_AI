from __future__ import annotations

from datetime import datetime
from typing import Literal, List

from pydantic import BaseModel, Field

from .pricing import PriceBar, RangeMetadata, PricingMetadata


SupportedInterval = Literal["1m", "5m", "15m", "1h"]


class CtpKlineResponse(BaseModel):
    symbol: str = Field(..., description="CTP instrument identifier, e.g. CL2512-NYM")
    interval: SupportedInterval
    range: RangeMetadata
    bars: List[PriceBar]
    metadata: PricingMetadata
