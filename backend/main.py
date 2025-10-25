from src.core.commodity_agent import commodity_agent
from src.core.trend_news_agent import trend_news_agent
from langchain_core.messages import HumanMessage
import asyncio


async def run_commodity_agent():
    res = await commodity_agent.ainvoke({
        "messages": [HumanMessage(content="""
       	崔东树：全国新能源乘用车库存持续回落 行业库存总体压力改善
        """)]
    })
    print(res)

async def run_trend_news_agent():
    res = await trend_news_agent.ainvoke({
        "messages": [HumanMessage(content="""{
  "ticker": "TSLA",
  "time_intervals": [
    {"start_date": "2022-08-26", "end_date": "2023-01-25", "trend": "BEARISH"},
    {"start_date": "2023-01-26", "end_date": "2023-04-19", "trend": "BULLISH"},
    {"start_date": "2023-04-20", "end_date": "2023-06-07", "trend": "BEARISH"},
    {"start_date": "2023-06-08", "end_date": "2023-06-23", "trend": "BULLISH"},
    {"start_date": "2023-06-26", "end_date": "2023-06-30", "trend": "BEARISH"},
    {"start_date": "2023-07-03", "end_date": "2023-07-19", "trend": "BULLISH"},
    {"start_date": "2023-07-20", "end_date": "2023-08-28", "trend": "BEARISH"},
    {"start_date": "2023-08-29", "end_date": "2023-10-18", "trend": "BULLISH"},
    {"start_date": "2023-10-19", "end_date": "2023-11-01", "trend": "BEARISH"},
    {"start_date": "2023-11-02", "end_date": "2023-11-08", "trend": "BULLISH"},
    {"start_date": "2023-11-09", "end_date": "2023-11-13", "trend": "BEARISH"},
    {"start_date": "2023-11-14", "end_date": "2024-01-24", "trend": "BULLISH"},
    {"start_date": "2024-01-25", "end_date": "2024-02-14", "trend": "BEARISH"},
    {"start_date": "2024-02-15", "end_date": "2024-04-12", "trend": "BULLISH"},
    {"start_date": "2024-04-15", "end_date": "2024-04-23", "trend": "BEARISH"},
    {"start_date": "2024-04-24", "end_date": "2024-07-23", "trend": "BULLISH"},
    {"start_date": "2024-07-24", "end_date": "2024-11-05", "trend": "BEARISH"},
    {"start_date": "2024-11-06", "end_date": "2024-12-26", "trend": "BULLISH"},
    {"start_date": "2024-12-27", "end_date": "2025-03-21", "trend": "BEARISH"},
    {"start_date": "2025-03-24", "end_date": "2025-04-03", "trend": "BULLISH"},
    {"start_date": "2025-04-04", "end_date": "2025-04-24", "trend": "BEARISH"},
    {"start_date": "2025-04-25", "end_date": "2025-06-04", "trend": "BULLISH"},
    {"start_date": "2025-06-05", "end_date": "2025-06-20", "trend": "BEARISH"},
    {"start_date": "2025-06-23", "end_date": "2025-10-09", "trend": "BULLISH"},
    {"start_date": "2025-10-10", "end_date": "2025-10-22", "trend": "BEARISH"}
  ]
}""")]
    })
    print(res)



if __name__ == "__main__":
    asyncio.run(run_commodity_agent())