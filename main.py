from src.core.commodity_agent import commodity_agent
from langchain_core.messages import HumanMessage
import asyncio


async def commodity_agent():
    res = await commodity_agent.ainvoke({
        "messages": [HumanMessage(content="""
        美国总统特朗普：如果印度不限制购买俄罗斯石油，将继续支付“巨额”关税。
        """)]
    })
    print(res)


if __name__ == "__main__":
    asyncio.run(commodity_agent())