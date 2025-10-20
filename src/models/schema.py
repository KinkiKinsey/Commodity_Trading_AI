from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool, InjectedToolArg
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from typing import List, TypedDict, Annotated, Sequence, Optional
import operator
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, AnyUrl, Field
from langgraph.graph import MessagesState
from typing_extensions import Literal

class SOCommodity(BaseModel):
    direction: Annotated[Literal["bullish", "bearish", "neutral"], Field(description="The direction of the commodity market")]
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence score")
    citations: List[str] = Field(description="List of urls")
    chain_of_thought: List[str] = Field(description="Chain of thought for the analysis")

class CommodityAgentState(TypedDict):
    """State for commodity agent"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    news: str
    tool_call_iterations: int = 0
    raw_notes: Annotated[List[str], operator.add] = []
    analysis: SOCommodity