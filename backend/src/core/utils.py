from dotenv import load_dotenv
import os
import requests
from firecrawl import FirecrawlApp
from langgraph.config import get_stream_writer
from langchain_core.tools import tool
from datetime import datetime

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")


@tool(parse_docstring=True)
def firecrawl_search(query: str) -> str:
    """Tool for searching the web using Firecrawl.

    Args:
        query: The query to search for.

    Returns:
        Formatted string containing search results with URLs and summaries.
    """
    app = FirecrawlApp()
    writer = get_stream_writer()
    writer(f"TOOL USE: Searching for {query}...")
    search_result = app.search(
        query,
        limit=3,
        scrape_options = {
        "onlyMainContent": False,
        "maxAge": 1,
        "parsers": [],
        "formats": [
        "markdown",
        "summary"
        ]}
    )
    results = []
    for item in search_result.web:
        if hasattr(item, 'summary'):
            results.append({
                "url": item.metadata.url,
                "summary": item.summary
            })
    
    if not results:
        return "No search results found."
    
    formatted_output = "\n\n---\n\n".join([
        f"**Source:** {item['url']}\n\n**Summary:**\n{item['summary']}"
        for item in results
    ])
    return formatted_output


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    writer = get_stream_writer()
    writer(f"Thinking: {reflection}")
    return f"Reflection recorded: {reflection}"
