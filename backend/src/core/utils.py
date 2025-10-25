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
        sources=[{"type": "news"}],
        scrape_options={
            "onlyMainContent": True,
            "maxAge": 1,
            "parsers": [],
            "formats": ["summary"],
        }
    )
    results = []
    
    # Process news results only (since we're using news sources)
    if hasattr(search_result, 'news') and search_result.news:
        for item in search_result.news:
            # Extract URL and date from metadata
            metadata = getattr(item, 'metadata', None)
            url = None
            date = None
            
            if metadata:
                metadata_dict = metadata.model_dump() if hasattr(metadata, 'model_dump') else metadata.dict()
                url = metadata_dict.get('url') or metadata_dict.get('source_url')
                date = metadata_dict.get('published_time') or metadata_dict.get('modified_time')
            
            results.append({
                "url": url,
                "summary": getattr(item, 'summary', ''),
                "date": date
            })
    
    if not results:
        return "No search results found."
    
    formatted_output = "\n\n---\n\n".join([
        f"**URL:** {item['url']}\n**Summary:** {item['summary']}\n**Date:** {item['date']}"
        for item in results
    ])
    return formatted_output


@tool(parse_docstring=True)
def firecrawl_search_tbs(query: str, tbs: str) -> str:
    """Tool for searching news using Firecrawl with time-based search parameter.

    Args:
        query: The query to search for.
        tbs: Time-based search parameter. Supports predefined ranges (qdr:h, qdr:d, qdr:w, qdr:m, qdr:y) and custom ranges (cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY).

    Returns:
        Formatted string containing search results with URLs, summaries, and dates.
    """
    app = FirecrawlApp()
    writer = get_stream_writer()
    writer(f"TOOL USE: Searching for {query} with time filter {tbs}...")
    
    search_result = app.search(
        query,
        limit=3,
        sources=[{"type": "news"}],
        tbs=tbs,
        scrape_options={
            "onlyMainContent": False,
            "maxAge": 1,
            "parsers": [],
            "formats": ["markdown", "summary"],
        }
    )
    
    results = []
    
    # Process news results only (since we're using news sources)
    if hasattr(search_result, 'news') and search_result.news:
        for item in search_result.news:
            # Extract URL and date from metadata
            metadata = getattr(item, 'metadata', None)
            url = None
            date = None
            
            if metadata:
                metadata_dict = metadata.model_dump() if hasattr(metadata, 'model_dump') else metadata.dict()
                url = metadata_dict.get('url') or metadata_dict.get('source_url')
                date = metadata_dict.get('published_time') or metadata_dict.get('modified_time')
            
            results.append({
                "url": url,
                "summary": getattr(item, 'summary', ''),
                "date": date
            })
    
    if not results:
        return "No search results found."
    
    formatted_output = "\n\n---\n\n".join([
        f"**URL:** {item['url']}\n**Summary:** {item['summary']}\n**Date:** {item['date']}"
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
