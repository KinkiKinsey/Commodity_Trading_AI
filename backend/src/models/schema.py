from typing import List, TypedDict, Annotated, Sequence
import operator

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Literal, NotRequired


class SOCommodity(BaseModel):
    """Structured output for the commodity agent."""

    direction: Annotated[Literal["bullish", "bearish", "neutral"], Field(description="The direction of the commodity market")]
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence score")
    citations: List[str] = Field(description="List of urls")
    chain_of_thought: List[str] = Field(description="Chain of thought for the analysis")


class ChainOfThoughtStep(BaseModel):
    """Structured representation of a reasoning step for the news UI."""

    id: str = Field(..., description="Unique identifier for the step")
    step: int = Field(..., ge=0, description="Ordering index of the step")
    text: str = Field(..., description="Reasoning content in the same language as the headline")
    evidence: str | None = Field(None, description="Optional evidence summary")
    url: str | None = Field(None, description="Optional citation URL")


class NewsSignal(BaseModel):
    """Signal metadata associated with an index buy/sell point."""

    signalId: str = Field(..., description="Unique signal identifier")
    signalType: Literal["buy", "sell"] = Field(..., description="Signal direction")
    price: float = Field(..., description="Trigger price of the signal")
    indexValue: float | None = Field(None, description="Associated index value")
    reasonTag: str | None = Field(None, description="Short label describing the trigger")
    newsId: str | None = Field(None, description="Associated news/event identifier")
    createdAt: str = Field(..., description="ISO timestamp when the signal was generated")


class NewsStreamEvent(BaseModel):
    """Realtime SSE payload for the AI news module."""

    eventId: str = Field(..., description="Unique identifier for the news event (UUID)")
    timestamp: str = Field(..., description="ISO timestamp of the news analysis")
    headline: str = Field(..., max_length=200, description="Headline displayed in the modal")
    summary: str | None = Field(None, max_length=200, description="Short summary used in preview modal")
    direction: Literal["bullish", "bearish", "neutral"] = Field(..., description="Market direction classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from the LLM analysis")
    language: str = Field("zh-CN", description="BCP 47 language tag of the content")
    chain_of_thought: List[ChainOfThoughtStep] = Field(default_factory=list, description="Structured reasoning steps")
    citations: List[str] = Field(default_factory=list, description="List of citation URLs")
    signalTags: List[str] = Field(default_factory=list, description="Tag labels mapped to the signal tooltip")
    complianceStatus: Literal["clean", "masked", "blocked"] = Field("clean", description="Compliance flag for rendering")
    signal: NewsSignal | None = Field(None, description="Optional signal metadata bundled with the event")


class CommodityAgentState(TypedDict):
    """State for commodity agent"""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    news: str
    tool_call_iterations: int = 0
    raw_notes: Annotated[List[str], operator.add] = []
    analysis: SOCommodity


# ## Trend News Agent State and Schema

class TrendNews(BaseModel):
    """Trend news data."""
    content: Annotated[str, Field(description="")]
    date: Annotated[str, Field(description="The ISO 8601 timestamp of the event happened")]
    url: Annotated[str, Field(description="The url of the event")]
    weight: Annotated[float, Field(description="The weight of the event contributes to the trend")]

class SOTrendNews(BaseModel):
    """Structured output for the trend news agent."""
    trend_news: List[TrendNews] = Field(description="The trend news")

class TrendNewsAgentState(TypedDict):
    """State for trend news agent"""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int = 0
    raw_notes: Annotated[List[str], operator.add] = []
    analysis: NotRequired[SOTrendNews]
    payload: NotRequired[str]