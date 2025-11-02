"""Trend News Agent Implementation.

This module builds a LangGraph workflow that explains the most recent trend
interval by combining targeted web searches with reflective planning.
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from typing import Dict

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.config import get_stream_writer
from langgraph.graph import START, END, StateGraph

from src.core.utils import get_today_str, firecrawl_search_tbs, think_tool
from src.models.schema import SOTrendNews, TrendNewsAgentState
from src.prompts.templates import (
    TREND_NEWS_AGENT_COMPRESS_PROMPT,
    TREND_NEWS_AGENT_PROMPT,
)

_llm = None
_model_with_tools = None
_compress_model = None
_tools = None
_tools_by_name = None

MAX_TOOL_CALLS = 2


def _format_prompt(template: str, **values: object) -> str:
    """Lightweight template replacement that preserves brace literals.

    Using ``str.replace`` avoids the brace interpretation performed by
    ``str.format``. This prevents runtime errors when payload strings or
    agent messages contain JSON snippets or other brace-heavy content.
    """
    formatted = template
    for key, value in values.items():
        replacement = "" if value is None else str(value)
        formatted = formatted.replace(f"{{{key}}}", replacement)
    return formatted


def _get_tools():
    """Lazily initialize tool registry for the trend agent."""
    global _tools, _tools_by_name
    if _tools is None:
        _tools = [firecrawl_search_tbs, think_tool]
        _tools_by_name = {tool.name: tool for tool in _tools}
    return _tools, _tools_by_name


def _get_model():
    """Lazily initialize the base chat model."""
    global _llm
    if _llm is None:
        _llm = init_chat_model(model="openai:gpt-4.1", temperature=0.0)
    return _llm


def _get_model_with_tools():
    """Bind the chat model with the agent's toolset."""
    global _model_with_tools
    if _model_with_tools is None:
        model = _get_model()
        tools, _ = _get_tools()
        _model_with_tools = model.bind_tools(tools)
    return _model_with_tools


def _get_compress_model():
    """Model configured for high-token structured compression."""
    global _compress_model
    if _compress_model is None:
        _compress_model = init_chat_model(model="openai:gpt-4.1", max_tokens=32000)
    return _compress_model


model_with_tools = _get_model_with_tools()
compress_model = _get_compress_model()


async def llm_call(state: TrendNewsAgentState) -> Dict[str, object]:
    """Analyze current state and decide the next step for the trend agent."""

    tool_call_iterations = state.get("tool_call_iterations", 0)

    prior_messages = list(state.get("messages", []))
    payload = state.get("payload")
    if not payload and prior_messages:
        payload = prior_messages[0].content

    system_message = SystemMessage(
        content=_format_prompt(
            TREND_NEWS_AGENT_PROMPT,
            date=get_today_str(),
            payload=payload or "",
            tool_call_iterations=tool_call_iterations,
            MAX_TOOL_CALLS=MAX_TOOL_CALLS,
        )
    )

    response = await model_with_tools.ainvoke([system_message] + prior_messages)

    return {
        "messages": [response],
        "payload": payload or (prior_messages[0].content if prior_messages else ""),
    }


async def tool_node(state: TrendNewsAgentState) -> Dict[str, object]:
    """Execute the tool calls triggered by the preceding LLM step."""
    tool_calls = state["messages"][-1].tool_calls
    _, tools_by_name = _get_tools()

    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        try:
            observation = await tool.ainvoke(tool_call["args"])
            observations.append(observation)
        except Exception as exc:  # pragma: no cover - defensive logging
            writer = get_stream_writer()
            writer(f"Tool execution failed: {exc}")
            observations.append(f"Tool execution failed: {exc}")

    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
        )
        for observation, tool_call in zip(observations, tool_calls)
    ]

    search_tool_count = sum(
        1 for tc in tool_calls if tc["name"] == "firecrawl_search_tbs"
    )

    return {
        "messages": tool_outputs,
        "tool_call_iterations": state.get("tool_call_iterations", 0)
        + (1 if search_tool_count > 0 else 0),
    }


async def compress_research(state: TrendNewsAgentState) -> Dict[str, object]:
    """Compress gathered evidence into structured causal analysis."""
    from langchain_core.messages import filter_messages

    structured_model = compress_model.with_structured_output(SOTrendNews)

    tool_messages = filter_messages(state["messages"], include_types=["tool"])
    ai_messages = filter_messages(state["messages"], include_types=["ai"])

    tool_contents = "\n\n---\n\n".join(m.content for m in tool_messages)
    last_ai_content = ai_messages[-1].content if ai_messages else ""

    payload = state.get("payload", "")

    messages: list[BaseMessage] = [
        SystemMessage(
            content=_format_prompt(
                TREND_NEWS_AGENT_COMPRESS_PROMPT,
                date=get_today_str(),
                payload=payload,
            )
        ),
        HumanMessage(
            content=(
                f"Payload:\n{payload}\n\n"
                f"Tool Results:\n{tool_contents}\n\n"
                f"AI Analysis:\n{last_ai_content}\n\n"
                "Return the structured trend news list."
            )
        ),
    ]

    result = await structured_model.ainvoke(messages)
    raw_notes = [
        m.content
        for m in filter_messages(state["messages"], include_types=["tool", "ai"])
    ]

    return {"analysis": result, "raw_notes": raw_notes}


def should_continue(state: TrendNewsAgentState) -> str:
    """Decide whether to continue tool usage or finalize."""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls and state.get("tool_call_iterations", 0) < MAX_TOOL_CALLS:
        return "tool_node"
    return "compress_research"


# ===== GRAPH CONSTRUCTION =====

trend_news_graph_builder = StateGraph(TrendNewsAgentState)

trend_news_graph_builder.add_node("llm_call", llm_call)
trend_news_graph_builder.add_node("tool_node", tool_node)
trend_news_graph_builder.add_node("compress_research", compress_research)

trend_news_graph_builder.add_edge(START, "llm_call")

trend_news_graph_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {"tool_node": "tool_node", "compress_research": "compress_research"},
)

trend_news_graph_builder.add_edge("tool_node", "llm_call")
trend_news_graph_builder.add_edge("compress_research", END)

trend_news_agent = trend_news_graph_builder.compile()
