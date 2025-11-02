import asyncio
from langchain_core.messages import HumanMessage
from src.core.commodity_agent import commodity_agent

async def main():
    res = await commodity_agent.ainvoke({'messages':[HumanMessage(content='Headline: {foo}\nSummary: {bar}')]} )
    print(res['analysis'].direction, len(res['analysis'].chain_of_thought))

asyncio.run(main())
