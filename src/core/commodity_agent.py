from typing import List, Dict, Any, TypedDict, Annotated, Literal
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, BaseMessage
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from src.models.schema import Chemical_Industry_State, SOFoundamentals

_llm = None
_model_with_tools = None
_compress_model = None
_tools = None
_tools_by_name = None


### Tools ###
@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """
    Tool for strategic reflection on research progress and decision-making

    Args:
        reflection: Detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded
    """
    return f"Reflection recorded: {reflection}"

@tool(parse_docstring=True)
def get_stats(args: Dict[str, Any]) -> str:
    """
    Tool for getting statistics on research progress and decision-making

    Args:
        args: Dictionary containing the following keys:
            - "statistics": Detailed statistics on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that statistics were recorded
    """
    statistics = {
        "RSI": "100",
        "MA": "200",
        "MACD": "300",
        "Stochastic": "400",
        "RSI_Signal": "500",
        "MA_Signal": "600",
        "MACD_Signal": "700",
    }
    return f"Statistics recorded: {statistics}"


def get_llm():
    global _llm
    if _llm is None:
        _llm = init_chat_model(model="gpt-4o-mini", temperature=0)
    return _llm


def _get_compress_model():
    global _compress_model
    if _compress_model is None:
        _compress_model = init_chat_model(model="openai:gpt-4.1", max_tokens=32000)
    return _compress_model

def _get_tools():
    global _tools, _tools_by_name
    if _tools is None:
        tavily_search = TavilySearch(max_results=3, search_depth="basic")
        _tools = [tavily_search, think_tool, get_stats]
        _tools_by_name = {tool.name: tool for tool in _tools}
    return _tools, _tools_by_name

def _get_model_with_tools():
    global _model_with_tools
    if _model_with_tools is None:
        model = get_llm()
        tools, _ = _get_tools()
        _model_with_tools = model.bind_tools(tools)
    return _model_with_tools


async def tool_node(state: Chemical_Industry_State) -> Dict:
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
            # Use rate limiter for Tavily search
            if tool_call["name"] == "tavily_search":
                observation = await rate_limiter.execute_with_limit(
                    "tavily",
                    tool.ainvoke,
                    tool_call["args"]
                )
            else:
                observation = await tool.ainvoke(tool_call["args"])
            
            observations.append(observation)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            observations.append(f"Tool execution failed: {str(e)}")
            
    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) for observation, tool_call in zip(observations, tool_calls)
    ]
    
    # Only increment counter for actual search tools, not think_tool
    search_tool_count = sum(1 for tc in tool_calls if tc["name"] == "tavily_search")
    
    return {
        "messages": tool_outputs, 
        "tool_call_iterations": state.get("tool_call_iterations", 0) + (1 if search_tool_count > 0 else 0)
    }


async def get_foundamentals(state: Chemical_Industry_State) -> Dict:
    """Extract competitors from search results and AI analysis."""
    from langchain_core.messages import filter_messages
    
    # Use rate-limited model for extraction
    structured_model = compress_model.with_structured_output(SOFoundamentals)
    
    # Extract content we need
    tool_contents = [m.content for m in filter_messages(state["messages"], include_types=["tool"])]
    search_context = "\n---\n".join(tool_contents[-3:])  # Last 3 searches only
    
    # Get the last AI message content (the final analysis/summary)
    ai_messages = filter_messages(state["messages"], include_types=["ai"])
    last_ai_content = ai_messages[-1].content if ai_messages else "No AI analysis available"
    
    # Simplified, focused prompt
    messages = [
        SystemMessage(content=f"Extract competitors for {state['tenant'].tenant_name} from the search results and AI analysis below. Focus on direct competitors that customers would actually compare when making purchasing decisions."),
        HumanMessage(content=f"Target Company Information:\n{state['tenant'].model_dump_json(indent=2)}\n\nSearch Results:\n{search_context}\n\nAI Analysis:\n{last_ai_content}\n\nReturn structured competitor list.")
    ]
    
    result = await structured_model.ainvoke(messages)
    raw_notes = [m.content for m in filter_messages(state["messages"], include_types=["tool", "ai"])]
    
    return {
        "tenant": state['tenant'], 
        "foundamentals": result.foundamentals, 
        "raw_notes": raw_notes
    }


def should_continue(state: Chemical_Industry_State) -> Literal["tool_node", "extract_competitors"]:
    """Determine whether to continue research or provide final answer.
    
    Determines whether the agent should continue the research loop or provide
    a final answer based on whether the LLM made tool calls.
    
    Returns:
        "tool_node": Continue to tool execution
        "extract_competitors": Stop and extract research
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM makes a tool call, continue to tool execution
    if last_message.tool_calls:
        return "tool_node"
    # Otherwise, we have a final answer
    return "extract_competitors"

model_with_tools = _get_model_with_tools()
compress_model = _get_compress_model()