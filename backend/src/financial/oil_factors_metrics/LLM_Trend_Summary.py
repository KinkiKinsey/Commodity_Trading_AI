import pandas as pd
import numpy as np
import requests
import json
import asyncio
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from scipy.signal import argrelextrema
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for Data_Source imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from data_sources.get_price import get_yahoo_data
from data_sources.wti_news import get_wti_news
from DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage
from .Oil_LLM_Source.LLM_Call_Agent import LLMCallAgent

# API Configuration - Use environment variables
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
FMP_API_KEY = os.getenv("RINGSHELL_FMP_API_KEY")

if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
if not FMP_API_KEY:
    raise ValueError("RINGSHELL_FMP_API_KEY not found in environment variables")

def filter_wti_news_by_date_range(wti_news_data, start_date, end_date):
    filtered_news = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    for article in wti_news_data:
        try:
            article_date = datetime.strptime(article['timestamp'][:10], "%Y-%m-%d")
            if start_dt <= article_date <= end_dt:
                filtered_news.append({
                    "title": article["title"],
                    "text": article["text"]
                })
        except:
            continue
    
    return filtered_news


def filter_news_by_date(news_list: list, start_date: str) -> list:
    """
    Filter news articles to only include those on or after start_date.
    Used for incremental updates.
    
    Args:
        news_list: Full news list from Redis (all articles with timestamps)
        start_date: Start date in ISO format (e.g., "2025-08-10T12:00:00" or "2025-08-10")
        
    Returns:
        Filtered news list with only articles >= start_date
    """
    # Parse start date
    if 'T' in start_date:
        start_date = start_date.split('T')[0]  # Extract date part
    
    try:
        cutoff_date = datetime.strptime(start_date, '%Y-%m-%d')
    except:
        print(f"⚠️ Invalid start_date format: {start_date}, using all news")
        return news_list
    
    filtered_news = []
    
    for article in news_list:
        try:
            # Article timestamp format: "2025-10-08 14:30:00" or "2025-10-08T14:30:00"
            article_timestamp = article.get('timestamp', '')
            
            if not article_timestamp:
                continue
            
            # Extract date part (first 10 characters)
            article_date_str = article_timestamp[:10]
            article_date = datetime.strptime(article_date_str, '%Y-%m-%d')
            
            # Keep articles on or after cutoff date
            if article_date >= cutoff_date:
                filtered_news.append(article)
        except Exception as e:
            # If date parsing fails, include the article (conservative approach)
            filtered_news.append(article)
            continue
    
    print(f"📰 Filtered news: {len(filtered_news)}/{len(news_list)} articles since {start_date}")
    
    return filtered_news

def calculate_spy_return_rate(ticker: str, start_date: str, end_date: str) -> float:
    try:
        spy_response = requests.get(
            f"https://financialmodelingprep.com/api/v3/historical-price-full/SPY",
            params={'from': start_date, 'to': end_date, 'apikey': FMP_API_KEY}
        )
        
        if spy_response.status_code == 200:
            spy_data = spy_response.json()
            if 'historical' in spy_data and spy_data['historical']:
                spy_prices = [float(h['close']) for h in reversed(spy_data['historical'])]
                if len(spy_prices) >= 2:
                    return (spy_prices[-1] - spy_prices[0]) / spy_prices[0]
        return 0.0
    except Exception:
        return 0.0

def create_trend_segments_and_price_stats(trend_points, prices, dates, df, filtered_wti_news):
    trend_json = {}
    up_count = down_count = 1

    for i in range(len(trend_points) - 1):
        start = trend_points[i]
        end = trend_points[i + 1]
        
        is_up = prices[end] > prices[start]
        json_label = f"uptrend{up_count}" if is_up else f"downtrend{down_count}"
        
        start_date = pd.to_datetime(dates[start]).strftime("%Y-%m-%d")
        end_date = pd.to_datetime(dates[end]).strftime("%Y-%m-%d")

        filtered_news = filter_wti_news_by_date_range(filtered_wti_news, start_date, end_date)

        trend_prices = prices[start:end+1]
        price_change = prices[end] - prices[start]
        total_return = price_change / prices[start] if prices[start] != 0 else 0
        
        daily_returns = []
        for j in range(start+1, end+1):
            if prices[j-1] != 0:
                daily_return = (prices[j] - prices[j-1]) / prices[j-1]
                daily_returns.append(daily_return)
        
        volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0
        spy_return_rate = calculate_spy_return_rate("SPY", start_date, end_date)

        trend_json[json_label] = {
            "time": {
                "start": start_date,
                "end": end_date
            },
            "news": filtered_news,
            "price_stats": {
                "start_price": float(prices[start]),
                "end_price": float(prices[end]),
                "min_price": float(np.min(trend_prices)),
                "max_price": float(np.max(trend_prices)),
                "total_return": float(total_return),
                "daily_returns": [float(r) for r in daily_returns],
                "volatility": float(volatility),
                "spy_return_rate": float(spy_return_rate),
                "price_change": float(price_change),
                "volume_data": df.iloc[start:end+1]['volume'].tolist() if 'volume' in df.columns else None
            }
        }

        if is_up:
            up_count += 1
        else:
            down_count += 1
    return trend_json

async def deepseek_api_call(prompt: str, model: str = "deepseek-chat") -> str:
    """DeepSeek API call function using Oil_LLM_Source"""
    llm_agent = LLMCallAgent(default_provider="deepseek", default_model=model)
    
    response = await llm_agent.call_deepseek(
        prompt=prompt + "\n\nCRITICAL: Respond ONLY with valid JSON, no text, no Chinese.",
        temperature=0.3,
        max_tokens=4000
    )
    
    return response

def robust_json_parser(response_text: str, expected_keys: list) -> dict:
    """
    Robust JSON parser that handles various LLM response formats.
    Based on Fintegrate AI system with advanced parsing strategies.
    
    Args:
        response_text (str): Raw response from LLM
        expected_keys (list): List of expected trend keys
        
    Returns:
        dict: Parsed JSON or fallback structure
    """
    print(f"🔍 DEBUG: Response length: {len(response_text) if response_text else 0}")
    print(f"🔍 DEBUG: Response content: {repr(response_text[:200])}")
    
    if not response_text or not response_text.strip():
        print("❌ Empty response from LLM!")
        return generate_fallback_structure(expected_keys)
    
    # Check if response is an error message
    if response_text.startswith("Error:") or response_text.startswith("❌"):
        print(f"❌ LLM returned error: {response_text}")
        return generate_fallback_structure(expected_keys)
    
    # Clean the response text
    cleaned_text = response_text.strip()
    
    # Remove markdown code blocks
    cleaned_text = re.sub(r"```json\s*|```", "", cleaned_text)
    cleaned_text = re.sub(r"```\s*", "", cleaned_text)
    
    print(f"🧹 Cleaned response (first 500 chars): {cleaned_text[:500]}")
    
    # ADVANCED JSON REPAIR - Based on Fintegrate AI system
    cleaned_text = advanced_json_repair(cleaned_text)
    
    # Try multiple parsing strategies
    parsing_strategies = [
        # Strategy 1: Direct JSON parsing
        lambda: json.loads(cleaned_text),
        
        # Strategy 2: Extract JSON between braces
        lambda: json.loads(cleaned_text[cleaned_text.find('{'):cleaned_text.rfind('}')+1]),
        
        # Strategy 3: Fix common JSON issues
        lambda: json.loads(cleaned_text.replace("'", '"').replace(",\n}", "\n}").replace(",\n]", "\n]")),
        
        # Strategy 4: Try to extract individual key-value pairs
        lambda: extract_key_value_pairs(cleaned_text, expected_keys),
        
        # Strategy 5: Generate fallback structure
        lambda: generate_fallback_structure(expected_keys)
    ]
    
    for i, strategy in enumerate(parsing_strategies):
        try:
            result = strategy()
            if result:
                print(f"✅ JSON parsing strategy {i+1} succeeded")
                # Validate the structure
                validated_result = validate_json_structure(result, expected_keys)
                return validated_result
        except Exception as e:
            print(f"❌ JSON parsing strategy {i+1} failed: {str(e)}")
            continue
    
    print("❌ All JSON parsing strategies failed, using fallback")
    return generate_fallback_structure(expected_keys)

def advanced_json_repair(cleaned_text: str) -> str:
    """
    Advanced JSON repair based on Fintegrate AI system.
    Handles truncated responses and missing braces.
    """
    # Extract JSON between first { and last }
    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")
    if start != -1 and end != -1:
        cleaned_text = cleaned_text[start:end+1]
    
    # Check if response is complete
    if not cleaned_text.endswith("}"):
        print(f"⚠️ Response may be truncated. Last 100 chars: {cleaned_text[-100:]}")
        
        # More aggressive JSON repair for truncated responses
        print("🔧 Attempting advanced JSON repair...")
        # Count open vs close braces
        open_braces = cleaned_text.count('{')
        close_braces = cleaned_text.count('}')
        missing_braces = open_braces - close_braces
        
        # Add missing closing braces
        cleaned_text += '}' * missing_braces
        
        # Ensure proper JSON structure
        if not cleaned_text.strip().endswith('}'):
            cleaned_text = cleaned_text.rstrip() + '}'
        
        print(f"🔧 Added {missing_braces} missing closing braces")
    
    return cleaned_text

def extract_key_value_pairs(text: str, expected_keys: list) -> dict:
    """Extract key-value pairs from text that might not be valid JSON."""
    result = {}
    
    for key in expected_keys:
        print(f"🔍 Looking for key: {key}")
        
        # Multiple patterns to try for new primary driver structure
        patterns = [
            # Pattern 1: "key": { "primary_driver": "...", "driver_level": "...", "driver_type": "..." }
            rf'"{key}"\s*:\s*{{\s*"primary_driver":\s*"([^"]+)",\s*"driver_level":\s*"([^"]+)",\s*"driver_type":\s*"([^"]*)"',
            # Pattern 2: 'key': { 'primary_driver': '...', 'driver_level': '...', 'driver_type': '...' }
            rf"'{key}'\s*:\s*{{\s*'primary_driver':\s*'([^']+)',\s*'driver_level':\s*'([^']+)',\s*'driver_type':\s*'([^']*)'",
            # Pattern 3: "key": "primary_driver": "...", "driver_level": "...", "driver_type": "..."
            rf'"{key}"[^}}]*"primary_driver"\s*:\s*"([^"]+)"[^}}]*"driver_level"\s*:\s*"([^"]+)"[^}}]*"driver_type"\s*:\s*"([^"]*)"',
            # Legacy patterns for macro/micro structure
            rf'"{key}"\s*:\s*{{\s*"macro_reason":\s*"([^"]+)",\s*"micro_reason":\s*"([^"]*)"',
            rf"'{key}'\s*:\s*{{\s*'macro_reason':\s*'([^']+)',\s*'micro_reason':\s*'([^']*)'"
        ]
        
        found = False
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.DOTALL)
            if match:
                print(f"✅ Found key {key} with pattern {i+1}")
                try:
                    if i < 3:  # First 3 patterns for primary driver structure
                        primary_driver = match.group(1)
                        driver_level = match.group(2)
                        driver_type = match.group(3)
                        result[key] = {
                            "primary_driver": primary_driver,
                            "driver_level": driver_level,
                            "driver_type": driver_type
                        }
                    else:  # Legacy patterns for macro/micro structure
                        macro_reason = match.group(1)
                        micro_reason = match.group(2)
                        result[key] = {
                            "macro_reason": macro_reason,
                            "micro_reason": micro_reason
                        }
                    found = True
                    break
                except Exception as e:
                    print(f"❌ Error parsing key {key} with pattern {i+1}: {e}")
                    continue
        
        if not found:
            print(f"⚠️ Could not find key: {key}")
    
    return result

def validate_json_structure(result: dict, expected_keys: list) -> dict:
    """Validate and clean the JSON structure."""
    validated = {}
    
    for key in expected_keys:
        if key in result:
            analysis = result[key]
            
            # Handle new primary driver structure
            if "primary_driver" in analysis:
                validated[key] = {
                    "primary_driver": analysis["primary_driver"],
                    "driver_level": analysis["driver_level"],
                    "driver_type": analysis["driver_type"]
                }
            else:
                # Handle legacy macro/micro structure for backward compatibility
                validated[key] = {
                    "macro_reason": analysis.get("macro_reason", ""),
                    "micro_reason": analysis.get("micro_reason", "")
                }
        else:
            print(f"⚠️ Missing key in result: {key}")
            # Add fallback for missing keys
            validated[key] = {
                "primary_driver": "(Level 6 - Other factors): No clear driver identified [EXPECTATION] [N/A]",
                "driver_level": "6",
                "driver_type": "Other factors"
            }
    
    return validated

def generate_fallback_structure(expected_keys: list) -> dict:
    """Generate fallback structure when all parsing fails."""
    print("🔄 Generating fallback structure...")
    fallback = {}
    
    for key in expected_keys:
        fallback[key] = {
            "primary_driver": "(Level 6 - Other factors): Unable to identify primary driver [EXPECTATION] [N/A]",
            "driver_level": "6",
            "driver_type": "Other factors"
        }
    
    return fallback

def create_llm_prompt(ticker, batch_keys, trend_json, language: str = "English"):
    news_content = []
    
    for key in batch_keys:
        trend_data = trend_json[key]
        time_info = trend_data["time"]
        news_items = trend_data.get("news", [])
        
        trend_type = "uptrend" if "uptrend" in key else "downtrend"
        news_summary = f"{trend_type.upper()} from {time_info['start']} to {time_info['end']}:\n"
        
        for j, item in enumerate(news_items[:2]):
            news_summary += f"{j+1}. {item['title']}\n   {item['text'][:150]}...\n\n"
        
        news_content.append(news_summary)

    prompt = f"""You are a financial analyst analyzing WTI news to identify the SINGLE PRIMARY DRIVER that impacts crude oil prices for {ticker} future contracts.

TASK: Identify the ONE primary driver using the CRUDE OIL IMPACT HIERARCHY below. Focus purely on crude oil market fundamentals, NOT WTI-specific references.

**CRUDE OIL IMPACT HIERARCHY (Priority Order - Most Direct to Least Direct):**

**Level 0-1: Physical Supply and Demand Shocks (HIGHEST PRIORITY)**
- **Supply Disruptions**: OPEC+ production cuts, wars/geopolitical tensions (Middle East conflict, Ukraine war), natural disasters, refinery outages
- **Demand Surges**: Global economic expansion, seasonal effects (summer driving, winter heating), post-crisis recoveries (China reopening)
- **Inventory Levels**: EIA/IEA inventory reports (falling = tightening), Strategic Petroleum Reserve (SPR) purchases

**Level 2-3: Financial & Market Mechanisms (Indirect but Amplifying)**
- **Futures Market Positioning**: Speculative positioning, backwardation/contango signals
- **Currency & Inflation Effects**: USD strength/weakness, interest rates, inflation hedging demand

**Level 4-5: Macroeconomic & Policy-Level Drivers (Strategic Influences)**
- **Fiscal & Monetary Stimulus**: Central bank policy, quantitative easing, fiscal stimulus
- **Energy & Climate Policy**: ESG constraints, carbon taxes, emission caps, investment restrictions
- **Geopolitical Strategy**: Sanctions (Iran, Venezuela, Russia), regional tensions, Strait of Hormuz risks

**Level 6: Sentiment & Expectation-Based Drivers (Behavioral and Long-Term)**
- **Market Sentiment**: Risk-on/risk-off investor mood, momentum-based buying, OPEC discipline expectations
- **Substitution & Correlation**: Natural gas prices, shipping costs, logistics bottlenecks
- **Long-Term Expectations**: Anticipation of future undersupply, forward curve movements

**DRIVER IDENTIFICATION RULES:**
- Analyze ALL available factors from the news data
- Apply the hierarchy to determine which level each factor belongs to
- Identify the HIGHEST-LEVEL factor that's actually present and driving the price
- Return ONLY the single primary driver based on this hierarchy
- If multiple factors exist at the same level, choose the most significant one
- If no higher-level factors exist, move down the hierarchy

**CLASSIFICATION REQUIREMENTS:**
- **CRITICAL: ALWAYS classify the primary driver with TWO labels:**
  1. **[EXPECTATION/DELIVERY]**: When news/events are anticipated vs actually delivered/announced
  2. **[LESS_THAN_EXPECTATION/BETTER_THAN_EXPECTATION/N/A]**: For DELIVERY events, how did it compare to expectations?
- **EXPECTATION**: When news/events are anticipated but not yet delivered (use N/A for second label)
- **DELIVERY**: When news/events are actually delivered/announced
  - **LESS_THAN_EXPECTATION**: ONLY use for data-related events (inventory reports, production data, economic indicators) that were disappointing
  - **BETTER_THAN_EXPECTATION**: ONLY use for data-related events (inventory reports, production data, economic indicators) that exceeded expectations
  - **N/A**: Use for all other delivery events (announcements, geopolitical events, weather, regulatory actions, etc.)

Return JSON with this EXACT structure for each trend key:
{{
  "trend_key": {{
    "primary_driver": "(Level X - Factor Type): Brief description [EXPECTATION/DELIVERY] [LESS_THAN_EXPECTATION/BETTER_THAN_EXPECTATION/N/A]",
    "driver_level": "X",
    "driver_type": "Factor Type"
  }}
}}

Trend keys to analyze: {batch_keys}

WTI news data to extract crude oil impact factors from:
{chr(10).join(news_content)}

IMPORTANT: Respond with ONLY the JSON object. Example formats:
{{
  "uptrend1": {{
    "primary_driver": "(Level 0-1 - Supply Disruptions): OPEC+ announces 1M barrel/day production cut [DELIVERY] [N/A]",
    "driver_level": "0-1",
    "driver_type": "Supply Disruptions"
  }},
  "downtrend2": {{
    "primary_driver": "(Level 0-1 - Inventory Levels): EIA reports 8.7M barrel inventory build [DELIVERY] [LESS_THAN_EXPECTATION]",
    "driver_level": "0-1",
    "driver_type": "Inventory Levels"
  }},
  "uptrend3": {{
    "primary_driver": "(Level 4-5 - Geopolitical Strategy): New sanctions on Russian oil exports announced [EXPECTATION] [N/A]",
    "driver_level": "4-5",
    "driver_type": "Geopolitical Strategy"
  }}
}}

No additional text, no explanations, just the JSON."""
    
    # Add language instruction if not English
    if language.lower() != "english":
        language_instruction = f"""

**CRITICAL LANGUAGE REQUIREMENT:**
- Output ALL content (primary_driver descriptions) in {language} language ONLY
- Do NOT use English
- Translate all factor descriptions to {language}
- Keep the JSON structure and keys in English, but all VALUES in {language}
"""
        prompt += language_instruction
    
    return prompt

async def process_single_llm_batch(batch_keys, trend_json, ticker, batch_id, language: str = "English"):
    """Process a single LLM batch - Same as Stock Trend Modular"""
    
    print(f"🧠 Batch {batch_id}: Processing LLM batch {batch_keys}")
    
    batch_prompt = create_llm_prompt(ticker, batch_keys, trend_json, language=language)
    
    print(f"📡 Batch {batch_id}: Calling LLM API for batch {batch_keys}...")
    
    try:
        response_text = await deepseek_api_call(batch_prompt, model="deepseek-chat")
        print(f"✅ Batch {batch_id}: DeepSeek API call successful")
        print(f"📝 Raw response length: {len(response_text)} characters")
        print(f"📝 Raw response preview: {response_text[:200]}...")
        
        # Check if response indicates API failure
        if response_text.startswith("Error:"):
            print(f"⚠️ Batch {batch_id}: DeepSeek API returned error, using fallback analysis")
            response_text = ""  # This will trigger fallback structure
    except Exception as e:
        print(f"❌ Batch {batch_id}: Error calling DeepSeek API: {str(e)}")
        response_text = ""
    
    # Use robust JSON parser
    parsed = robust_json_parser(response_text, batch_keys)
    
    # Process results for this batch
    batch_output = {}
    for key in batch_keys:
        match = re.match(r"(uptrend|downtrend)(\d+)", key)
        arrow = f"↑{match.group(2)}" if match and match.group(1) == "uptrend" else \
                f"↓{match.group(2)}" if match else None
        
        summary = parsed.get(key, {
            "primary_driver": "(Level 6 - Other factors): Unable to identify primary driver [EXPECTATION] [N/A]",
            "driver_level": "6",
            "driver_type": "Other factors"
        })
        
        if key in parsed:
            print(f"✅ Batch {batch_id}: Found analysis for {key}")
        else:
            print(f"⚠️ Batch {batch_id}: LLM skipped trend key: {key}")

        price_stats = trend_json[key].get("price_stats", {})
        start_date = trend_json[key]["time"]["start"]
        end_date = trend_json[key]["time"]["end"]
        
        duration = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
        
        start_price = price_stats["start_price"]
        end_price = price_stats["end_price"]
        slope = (end_price - start_price) / duration
        
        daily_returns = price_stats["daily_returns"]
        week_avg_return = sum(daily_returns[:5]) / len(daily_returns[:5])
        month_avg_return = sum(daily_returns[:20]) / len(daily_returns[:20])

        # Handle new primary driver structure
        if "primary_driver" in summary:
            # New hierarchy-based structure
            summary_data = {
                "primary_driver": summary["primary_driver"],
                "driver_level": summary["driver_level"],
                "driver_type": summary["driver_type"]
            }
        else:
            # Legacy macro/micro structure for backward compatibility
            summary_data = {
                "macro_reason": summary.get("macro_reason", ""),
                "micro_reason": summary.get("micro_reason", "")
            }

        batch_output[key] = {
            "time": trend_json[key]["time"],
            "summary": summary_data,
            "symbol": arrow,
            "day average_return": price_stats["total_return"],
            "week average return": week_avg_return,
            "month average return": month_avg_return,
            "return rate variance": price_stats["volatility"] ** 2,
            "How Long it Take": float(duration),
            "Slope of stock trend": float(slope),
            "Max Return": price_stats["max_price"],
            "Estimate_price": end_price,
            "SPY_return_rate": price_stats["spy_return_rate"],
            "current": f"{start_date} to {end_date}" 
        }
    
    print(f"✅ Batch {batch_id}: Batch complete: {len(batch_keys)} trends processed")
    return batch_output

async def summarize_news_trends_with_llm(trend_json: dict, ticker: str, language: str = "English") -> dict:
    """Summarize news trends for each trend segment using LLM - Same as Stock Trend Modular"""
    
    trend_keys = [k for k in trend_json if "news" in trend_json[k] and trend_json[k]["news"]]
    
    if not trend_keys:
        return {}
    
    print(f"🚀 Starting analysis for {ticker}")
    print(f"📊 Total trends to process: {len(trend_keys)}")
    print(f"📊 Trend keys: {trend_keys}")
    print("=" * 60)
    
    # Use batch size of 4 like Stock Trend Modular
    clean_output = {}
    i = 0
    
    while i < len(trend_keys):
        batch_size = min(4, len(trend_keys) - i)
        batch_keys = trend_keys[i:i+batch_size]
        batch_id = i // 4 + 1
        i += batch_size
        
        print(f"📦 Processing batch {batch_id}: {batch_keys}")
        
        # Process this batch
        batch_result = await process_single_llm_batch(batch_keys, trend_json, ticker, batch_id, language=language)
        clean_output.update(batch_result)
        
        print(f"✅ Batch {batch_id} complete: {len(batch_keys)} trends processed")
    
    print(f"\n🎉 Analysis complete!")
    print(f"📊 Final results: {len(clean_output)} trends processed")
    print(f"📋 Processed keys: {list(clean_output.keys())}")
    print("=" * 60)
    
    return clean_output

async def get_llm_trend_summary(ticker: str, days: int = 365, force_refresh: bool = False, incremental_since: str = None, language: str = "English") -> dict:
    try:
        redis_client = RedisDatabaseStorage()
        
        storage_key = ticker.replace('.', '_').replace('=', '_')
        llm_key = f"Crude_Oil:Future_Contract:{storage_key}:LLM_Trend_Analyst_Result"
        existing_analysis = redis_client.get_json(llm_key)
        
        # Check if we should use cached data (not force refresh and data is fresh)
        if not force_refresh and existing_analysis and not existing_analysis.get('error'):
            analysis_date_str = existing_analysis.get('analysis_date', '')
            if analysis_date_str:
                try:
                    analysis_date = datetime.strptime(analysis_date_str, "%Y-%m-%d %H:%M:%S")
                    hours_since_analysis = (datetime.now() - analysis_date).total_seconds() / 3600
                    
                    # Use cached data if less than 24 hours old
                    if hours_since_analysis < 24:
                        print(f"📋 Using cached analysis (age: {hours_since_analysis:.1f} hours)")
                        return existing_analysis.get('llm_summary', {})
                    else:
                        print(f"🔄 Analysis is {hours_since_analysis:.1f} hours old, refreshing...")
                except:
                    print("⚠️ Could not parse analysis date, refreshing...")
            else:
                print("⚠️ No analysis date found, refreshing...")
        elif force_refresh:
            print("🔄 Force refresh requested, updating analysis...")
        else:
            print("📊 No existing analysis found, creating new analysis...")
        
        df = get_yahoo_data(ticker, days)
        if df.empty:
            return {"error": f"No price data available for {ticker}"}
        
        dates = df['date'].values
        prices = df['close'].values
        actual_start_date = pd.to_datetime(dates[0])
        actual_end_date = pd.to_datetime(dates[-1])
        
        # Fetch all WTI news from Redis (auto-updates if needed)
        print(f"📰 Fetching WTI news from database...")
        wti_news_data = get_wti_news(days_back=max(days, (actual_end_date - actual_start_date).days + 30))
        print(f"✅ Retrieved {len(wti_news_data)} total articles from database")
        
        # Check if incremental mode
        if incremental_since:
            print(f"🔄 INCREMENTAL MODE: Filtering news since {incremental_since}")
            filtered_wti_news = filter_news_by_date(wti_news_data, incremental_since)
            
            if not filtered_wti_news or len(filtered_wti_news) == 0:
                print(f"⚠️ No new news found since {incremental_since}")
                return None  # Signal no new data to process
            
            print(f"✅ Using {len(filtered_wti_news)} NEW articles for trend creation")
        else:
            # Full mode: filter by price date range
            print(f"📰 FULL MODE: Using all news in price date range")
            filtered_wti_news = []
            for article in wti_news_data:
                try:
                    article_date = datetime.strptime(article['timestamp'][:10], "%Y-%m-%d")
                    if actual_start_date.date() <= article_date.date() <= actual_end_date.date():
                        filtered_wti_news.append(article)
                except:
                    continue
            print(f"✅ Using {len(filtered_wti_news)} articles for trend creation")
        
        df['Date'] = pd.to_datetime(df['date'])
        df['Price'] = df['close']
        
        prices = df['Price'].values
        dates = df['Date'].values
        
        order = 5
        local_min = argrelextrema(prices, np.less, order=order)[0]
        local_max = argrelextrema(prices, np.greater, order=order)[0]
        extrema = np.sort(np.concatenate((local_min, local_max)))

        trend_points = []
        if len(extrema) == 0 or extrema[0] != 0:
            trend_points.append(0)

        for idx in extrema:
            prev = trend_points[-1]
            if (prices[idx] > prices[prev] and prices[prev] == min(prices[prev], prices[idx])) or \
               (prices[idx] < prices[prev] and prices[prev] == max(prices[prev], prices[idx])):
                trend_points.append(idx)
        
        trend_points.append(len(prices) - 1)
        
        trend_json = create_trend_segments_and_price_stats(trend_points, prices, dates, df, filtered_wti_news)
        llm_summary_json = await summarize_news_trends_with_llm(trend_json, ticker, language=language)
        
        sorted_trends = sorted(llm_summary_json.items(), 
                             key=lambda x: pd.to_datetime(x[1]['time']['start']), 
                             reverse=True)
        
        current_trends = {}
        historical_trends = {}
        
        if sorted_trends:
            current_trend_name, current_trend_data = sorted_trends[0]
            current_trends[current_trend_name] = current_trend_data
            
            for trend_name, trend_data in sorted_trends[1:]:
                historical_trends[trend_name] = trend_data
        
        formatted_result = {
            "ticker": ticker,
            "current_trends": current_trends,
            "historical_trends": historical_trends
        }
        
        llm_result_data = {
            "ticker": ticker,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trends_count": len(llm_summary_json),
            "llm_summary": formatted_result,
            "analysis_period_days": days,
            "price_data_range": f"{actual_start_date.strftime('%Y-%m-%d')} to {actual_end_date.strftime('%Y-%m-%d')}"
        }
        
        # LLM Trend Analysis: Simple storage (no versioning)
        # Just store the latest analysis (replaces previous)
        redis_client.store_json(llm_result_data, llm_key)
        print("📦 LLM Analysis: Stored latest analysis")
        
        return formatted_result
        
    except Exception as e:
        import traceback
        error_msg = f"LLM trend summary failed: {str(e)}"
        print(f"💥 ERROR: {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}
