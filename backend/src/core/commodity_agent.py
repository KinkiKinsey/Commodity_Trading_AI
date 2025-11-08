
"""Research Agent Implementation.

This module implements a research agent that can perform iterative web searches
and synthesis to answer complex research questions.
"""

from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any, TypedDict, Annotated, Literal
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, BaseMessage
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import logging
from langgraph.config import get_stream_writer
from src.prompts.templates import COMMODITY_AGENT_PROMPT, COMMODITY_AGENT_COMPRESS_PROMPT
from src.models.schema import CommodityAgentState, SOCommodity
from src.core.utils import firecrawl_search, think_tool, get_today_str, get_eia_crude_inventory


_llm = None
_model_with_tools = None
_compress_model = None
_tools = None
_tools_by_name = None
MAX_TOOL_CALLS = 2


def _escape_braces(text: str | None) -> str:
    if not text:
        return ""
    return text.replace("{", "{{").replace("}", "}}")
def _get_tools():
    global _tools, _tools_by_name
    if _tools is None:
        _tools = [firecrawl_search, think_tool, get_eia_crude_inventory]
        _tools_by_name = {tool.name: tool for tool in _tools}
    return _tools, _tools_by_name

def _get_model():
    global _llm
    if _llm is None:
        _llm = init_chat_model(model="openai:gpt-4.1", temperature=0.0)
    return _llm

def _get_model_with_tools():
    global _model_with_tools
    if _model_with_tools is None:
        model = _get_model()
        tools, _ = _get_tools()
        _model_with_tools = model.bind_tools(tools)
    return _model_with_tools

def _get_compress_model():
    global _compress_model
    if _compress_model is None:
        _compress_model = init_chat_model(model="openai:gpt-4.1", max_tokens=32000)
    return _compress_model

    
async def llm_call(state: CommodityAgentState) -> Dict:
    """Analyze current state and decide on next actions.
    
    The model analyzes the current conversation state and decides whether to:
    1. Call search tools to gather more information
    2. Provide a final answer based on gathered information
    
    Returns updated state with the model's response.
    """

    tool_call_iterations = state.get("tool_call_iterations", 0)
        
    # Execute OpenAI call (rate limiting is handled by RateLimitedLLM wrapper)
    initial_messages = state.get("messages", [])
    initial_content = initial_messages[0].content if initial_messages else ""

    prompt = (
        COMMODITY_AGENT_PROMPT
        .replace("{date}", get_today_str())
        .replace("{tool_call_iterations}", str(tool_call_iterations))
        .replace("{MAX_TOOL_CALLS}", str(MAX_TOOL_CALLS))
    )

    response = await _get_model_with_tools().ainvoke(
        [SystemMessage(content=prompt)] + initial_messages
    )

    return {"messages": [response], "news": _escape_braces(initial_content)}

async def tool_node(state: CommodityAgentState) -> Dict:
    """Execute all tool calls from the previous LLM response.
    
    Executes all tool calls from the previous LLM responses.
    Returns updated state with tool execution results.
    """
    tool_calls = state["messages"][-1].tool_calls
    _, tools_by_name = _get_tools()
    
    # Execute all tool calls
    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        
        try:
            observation = await tool.ainvoke(tool_call["args"])
            observations.append(observation)
        except Exception as e:
            writer = get_stream_writer()
            writer(f"Tool execution failed: {e}")
            observations.append(f"Tool execution failed: {str(e)}")
            
    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) for observation, tool_call in zip(observations, tool_calls)
    ]
    
    # Only increment counter for firecrawl_search, not think_tool or get_eia_crude_inventory
    search_tool_count = sum(1 for tc in tool_calls if tc["name"] == "firecrawl_search")
    
    return {
        "messages": tool_outputs, 
        "tool_call_iterations": state.get("tool_call_iterations", 0) + (1 if search_tool_count > 0 else 0)
    }

async def compress_research(state: CommodityAgentState) -> Dict:
    """Extract competitors from search results and AI analysis."""
    from langchain_core.messages import filter_messages
    
    # Use rate-limited model for extraction
    structured_model = _get_compress_model().with_structured_output(SOCommodity)
    
    # Extract content we need
    tool_contents = [m.content for m in filter_messages(state["messages"], include_types=["tool"])]
    # search_context = "\n---\n".join(tool_contents[-3:])  # Last 3 searches only
    
    # Get the last AI message content (the final analysis/summary)
    ai_messages = filter_messages(state["messages"], include_types=["ai"])
    last_ai_content = ai_messages[-1].content if ai_messages else "No AI analysis available"
    
    # Simplified, focused prompt
    messages = [
        SystemMessage(
            content=COMMODITY_AGENT_COMPRESS_PROMPT
            .replace("{date}", get_today_str())
            .replace("{news}", _escape_braces(state.get("news", "")))
        ),
        HumanMessage(content=f"Search Results:\n{tool_contents}\n\nAI Analysis:\n{last_ai_content}\n\nReturn structured commodity analysis."),
    ]
    
    result = await structured_model.ainvoke(messages)
    raw_notes = [m.content for m in filter_messages(state["messages"], include_types=["tool", "ai"])]
    
    return {
        "analysis": result, 
        "raw_notes": raw_notes
    }

def should_continue(state: CommodityAgentState) -> Literal["tool_node", "compress_research"]:
    """Determine whether to continue research or provide final answer.
    
    Determines whether the agent should continue the research loop or provide
    a final answer based on whether the LLM made tool calls.
    
    Returns:
        "tool_node": Continue to tool execution
        "compress_research": Stop and extract research
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM makes a tool call, continue to tool execution
    if last_message.tool_calls and state.get("tool_call_iterations", 0) < MAX_TOOL_CALLS:
        return "tool_node"
    # Otherwise, we have a final answer
    return "compress_research"

# ===== GRAPH CONSTRUCTION =====

# Build the commodity agent workflow
commodity_graph_builder = StateGraph(CommodityAgentState)

# Add nodes to the graph
commodity_graph_builder.add_node("llm_call", llm_call)
commodity_graph_builder.add_node("tool_node", tool_node)
commodity_graph_builder.add_node("compress_research", compress_research)

# Add edges to connect nodes
commodity_graph_builder.add_edge(START, "llm_call")
commodity_graph_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        "compress_research": "compress_research"
    }
)
commodity_graph_builder.add_edge("tool_node", "llm_call")
commodity_graph_builder.add_edge("compress_research", END)

# Compile the commodity agent
commodity_agent = commodity_graph_builder.compile()
