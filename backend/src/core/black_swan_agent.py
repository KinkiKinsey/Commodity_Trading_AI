from src.financial.tools import (
    vix_volatility_analysis,           
    global_liquidity_monitor,         
    contango_backwardation_analysis    
)
from src.core.utils import firecrawl_search, think_tool, get_today_str
from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import ToolCallLimitMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
import uuid
from pydantic import BaseModel, Field
from typing import List, Annotated
from typing_extensions import Literal

_checkpointer = MemorySaver()

_deepagent_model = init_chat_model(model="openai:gpt-4.1", temperature=0.0, max_tokens=32000)
_subagent_model = init_chat_model(model="openai:gpt-4.1", temperature=0.0, max_tokens=32000)

search_limiter = ToolCallLimitMiddleware(
    tool_name="firecrawl_search",
    thread_limit=20,
    run_limit=10,
    exit_behavior="end"
)


class BlackSwanEvent(BaseModel):
    """Individual black swan event with probability classification."""
    event: Annotated[str, Field(description="Description of the potential black swan event.")]
    probability: Annotated[Literal["low", "medium", "high"], Field(description="Probability classification of the event occurring: low, medium, or high.")]
    impact: Annotated[str, Field(description="Brief description of the potential impact if the event occurs.")]


class SOBlackSwanAnalysis(BaseModel):
    """Structured output for the black swan analysis."""
    black_swan_score: Annotated[float, Field(ge=0.0, le=100.0, description="The score of the black swan event, 0-100, 100 is the highest risk.")]
    analysis: Annotated[str, Field(description="The analysis of the economic situation.")]
    citations: Annotated[List[str], Field(description="List of URLs of the sources used for the analysis.")]
    potential_black_swan_events: Annotated[List[BlackSwanEvent], Field(description="List of potential black swan events with their probability and impact.")]


class SONewsAnalysis(BaseModel):
    """Structured output for the news analysis."""
    news_analysis: Annotated[str, Field(description="The analysis of the news.")]
    citations: Annotated[List[str], Field(description="List of URLs of the sources used for the analysis.")]





MACRO_AGENT_PROMPT = f"""你是宏观金融分析专家。分析市场指标（VIX波动率、全球流动性、原油库存、期货升贴水）以评估系统性风险。今天日期是 {get_today_str()}。

<Task>
任务要求：
1. 系统性地调用各项分析工具
2. 识别市场异常和风险信号
3. 提供清晰的风险评估结论
</Task>

<Available Tools>
1. **vix_volatility_analysis**: VIX波动率分析工具
2. **global_liquidity_monitor**: 全球流动性监测工具
3. **contango_backwardation_analysis**: 原油期货升贴水分析工具
</Available Tools>
"""

NEWS_AGENT_PROMPT = f"""你是金融新闻分析专家。搜索并综合最新新闻，识别新兴金融威胁和市场异常。今天日期是 {get_today_str()}。

<Task>
重要提示：你的搜索工具调用次数有限（最多3-4次），请高效使用：
1. 先搜索最关键的主题（如"黑天鹅事件"、"金融风险"、"市场异常"）
2. 基于初步结果，有针对性地深入搜索
3. **在搜索限制到达前，必须总结已收集的所有信息**
4. 即使信息不完整，也要基于现有信息提供分析报告
</Task>

<Available Tools>
1. **firecrawl_search**: 网络搜索工具，用于获取最新金融新闻和市场信息
2. **think_tool**: 用于策略性反思和规划的思考工具

**CRITICAL: 策略性使用 think_tool**:
- **在开始时**: 评估哪些主题最相关，制定搜索策略
- **在每次搜索前**: 规划下一个搜索的关键词和方向
- **在每次搜索后**: 反思发现的内容，决定下一步行动
</Available Tools>

<Output Format>
你的最终输出必须包含：
- **news_analysis**: 综合所有搜索结果的新闻分析，识别潜在威胁和异常事件
- **citations**: 所有参考来源的 URL 列表
</Output Format>
"""

BLACK_SWAN_DEEP_AGENT_PROMPT = f"""你是黑天鹅事件检测系统的协调者。协调宏观分析和新闻分析，检测潜在黑天鹅事件。聚焦尾部风险和离群场景。今天日期是 {get_today_str()}。

<Task>
重要：使用 task() 工具委托给专业 subagent：
- 使用 **macro-agent** 进行市场指标分析（VIX、流动性、期货升贴水等）
- 使用 **news-agent** 搜索和综合最新金融新闻及市场异常

等待所有 subagent 完成后，综合分析结果，形成完整的黑天鹅风险评估报告。
</Task>

<Available Subagents>
1. **macro-agent**: 分析市场指标（VIX波动率、全球流动性、原油库存、期货升贴水）以评估系统性风险和市场异常信号
2. **news-agent**: 搜索并综合最新金融新闻，识别新兴市场威胁、极端事件和黑天鹅风险因素。注意：搜索次数有限，需高效使用
</Available Subagents>

<Output Format>
你的最终输出必须包含：
- **black_swan_score**: 黑天鹅事件风险评分（0-100，100为最高风险）
- **analysis**: 综合宏观和新闻分析的经济局势分析
- **citations**: 所有参考来源的 URL 列表
- **potential_black_swan_events**: 潜在黑天鹅事件列表，每个事件包含：
  - **event**: 事件描述
  - **probability**: 发生可能性分类（"low", "medium", "high"）
  - **impact**: 如果事件发生的潜在影响描述
</Output Format>
"""


_macro_agent_graph = create_agent(
    model=_subagent_model,
    tools=[vix_volatility_analysis, global_liquidity_monitor, contango_backwardation_analysis],
    system_prompt=MACRO_AGENT_PROMPT
)

_macro_subagent = CompiledSubAgent(
    name="macro-agent",
    description="分析市场指标（VIX波动率、全球流动性、原油库存、期货升贴水）以评估系统性风险和市场异常信号",
    runnable=_macro_agent_graph
)

_news_agent_graph = create_agent(
    model=_subagent_model,
    tools=[firecrawl_search, think_tool],
    system_prompt=NEWS_AGENT_PROMPT,
    middleware=[search_limiter],
    response_format=SONewsAnalysis
)

_news_subagent = CompiledSubAgent(
    name="news-agent",
    description="搜索并综合最新金融新闻，识别新兴市场威胁、极端事件和黑天鹅风险因素。注意：搜索次数有限，需高效使用",
    runnable=_news_agent_graph
)


black_swan_agent = create_deep_agent(
    model=_deepagent_model,
    subagents=[_macro_subagent, _news_subagent],
    system_prompt=BLACK_SWAN_DEEP_AGENT_PROMPT,
    checkpointer=_checkpointer,
    response_format=SOBlackSwanAnalysis
)

if __name__ == "__main__":
    # 使用 uuid 生成独立的 thread_id
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    # macro_result = _macro_agent_graph.invoke(
    #     {"messages": [HumanMessage(content="分析当前经济状况")]},
    #     config=config
    # )
    result = black_swan_agent.invoke(
        {"messages": [HumanMessage(content="分析当前的黑天鹅情况，并给出分析报告。")]},
        config=config
    )
    
    print("\n" + "="*80)
    print("黑天鹅分析结果:")
    print("="*80)
    for msg in result.get("messages", []):
        if hasattr(msg, "content"):
            print(msg.content)
            print("-"*80)