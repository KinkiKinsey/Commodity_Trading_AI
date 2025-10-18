from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool, InjectedToolArg
from tavily import TavilyClient
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from typing import List, TypedDict, Annotated, Sequence, Optional
import operator
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, AnyUrl, Field
from langgraph.graph import MessagesState


class SOFoundamentals(BaseModel):
    pass


class Commodity_Agent_State(TypedDict):
    """State for competitor finder subgraph only"""
    foundamentals: SOFoundamentals
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int = 0
    raw_notes: Annotated[List[str], operator.add] = []