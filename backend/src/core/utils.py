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


@tool(parse_docstring=True)
def get_eia_crude_inventory(weeks: int = 12) -> str:
    """Tool for fetching EIA crude oil inventory data from official API.
    
    Retrieves US commercial crude oil stocks (excluding SPR) from EIA's weekly petroleum status report.
    Data is reported in thousands of barrels and typically updated every Wednesday.
    
    Args:
        weeks: Number of recent weeks of data to retrieve (default: 12, max: 52)
    
    Returns:
        Formatted string with weekly inventory data including date, stock level, and week-over-week change.
    """
    api_key = os.getenv('EIA_API_KEY')
    if not api_key:
        return "Error: EIA_API_KEY not found in environment variables. Please set your EIA API key."
    
    # Validate and cap weeks parameter
    weeks = min(max(1, weeks), 52)
    
    # EIA API v2 endpoint for Weekly U.S. Ending Stocks of Crude Oil (Excluding SPR)
    # Series: WCESTUS1 = U.S. Ending Stocks excluding SPR of Crude Oil (Thousand Barrels)
    url = f"https://api.eia.gov/v2/petroleum/stoc/wstk/data/?api_key={api_key}&frequency=weekly&data[0]=value&facets[series][]=WCESTUS1&sort[0][column]=period&sort[0][direction]=desc&offset=0&length={weeks}"
    
    writer = get_stream_writer()
    writer(f"TOOL USE: Fetching EIA crude oil inventory data (last {weeks} weeks)...")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # EIA API v2 response structure: data.response.data
        response_data = data.get('response', {})
        inventory_records = response_data.get('data', [])
        
        if not inventory_records:
            return "No inventory data available from EIA."
        
        # Format output with week-over-week changes
        results = []
        results.append(f"**EIA Weekly Crude Oil Inventory (US Commercial Stocks)**")
        results.append(f"Unit: Thousand Barrels | Recent {len(inventory_records)} weeks\n")
        
        for i, record in enumerate(inventory_records):
            # API v2 format: {"period": "2024-10-18", "value": 123456.7, ...}
            date_str = record.get('period', '')
            inventory_raw = record.get('value')
            
            if not date_str or inventory_raw is None:
                continue
            
            # Convert to float (API may return string)
            try:
                inventory = float(inventory_raw)
            except (ValueError, TypeError):
                continue
            
            # Calculate week-over-week change
            if i < len(inventory_records) - 1:
                prev_inventory_raw = inventory_records[i + 1].get('value')
                if prev_inventory_raw:
                    try:
                        prev_inventory = float(prev_inventory_raw)
                        change = inventory - prev_inventory
                        change_pct = (change / prev_inventory) * 100
                        change_str = f" ({change:+,.0f}K, {change_pct:+.2f}%)"
                    except (ValueError, TypeError):
                        change_str = ""
                else:
                    change_str = ""
            else:
                change_str = ""
            
            results.append(f"{date_str}: {inventory:,.0f}K{change_str}")
        
        return "\n".join(results)
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching EIA data: {str(e)}"
    except (KeyError, IndexError, ValueError) as e:
        return f"Error parsing EIA response: {str(e)}"