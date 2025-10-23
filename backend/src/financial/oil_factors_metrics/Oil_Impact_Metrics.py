"""
Oil Impact Metrics Calculator - EXACT COPY from Quant Impact Agent
================================================================

This module is an EXACT copy of Quant_Impact_Storage_Agent.py but adapted for oil futures.
Uses single beta filtering (no sector beta for commodities).

Key Features:
- EXACT same LLM factor extraction as Quant Impact Agent
- EXACT same date range mapping as Quant Impact Agent  
- EXACT same beta filtering logic (single beta only)
- EXACT same 7 datasets generation
- EXACT same mathematical formulas

Usage:
    from Oil_Impact_Metrics import calculate_oil_impact_metrics
    
    result = calculate_oil_impact_metrics(
        llm_trend_data=trend_json,
        ticker="CLZ25.NYM",
        market_beta=1.2,
        risk_free_rate=0.025
    )
"""

import pandas as pd
import numpy as np
import json
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple
import requests
from datetime import datetime, timedelta
from io import StringIO
from scipy import stats
import re

# Add workspace root to path for Oil_LLM_Source, data_sources imports
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from .Oil_LLM_Source.LLM_Call_Agent import LLMCallAgent
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# FMP API Configuration - Use environment variables
FMP_API_KEY = os.getenv("RINGSHELL_FMP_API_KEY")
if not FMP_API_KEY:
    raise ValueError("RINGSHELL_FMP_API_KEY not found in environment variables")

# =============================================================================
# PYDANTIC MODELS (EXACT SAME AS QUANT IMPACT AGENT)
# =============================================================================

class FactorSet(BaseModel):
    factor_1: str = Field(description="Keyword for the top catalyst")
    factor_2: str = Field(description="Keyword for the second catalyst.")
    factor_3: str = Field(description="Keyword for the third catalyst.")
    factor_4: str = Field(description="Keyword for the fourth catalyst.")
    factor_5: str = Field(description="Keyword for the fifth catalyst.")
    factor_6: str = Field(description="Keyword for the sixth catalyst.")

class FactorPayload(BaseModel):
    ticker: str = Field(description="Ticker symbol in uppercase.")
    macro: FactorSet = Field(description="Macro-level catalyst keywords.")
    micro: FactorSet = Field(description="Company-level catalyst keywords.")

# LangChain parser expects Pydantic v2's model_json_schema; shim it for v1.
FactorSet.model_json_schema = classmethod(lambda cls: cls.schema())
FactorPayload.model_json_schema = classmethod(lambda cls: cls.schema())

parser = PydanticOutputParser(pydantic_object=FactorPayload)

class DateRangePayload(BaseModel):
    ticker: str = Field(description="Ticker symbol in uppercase")
    macro: Dict[str, List[List[str]]] = Field(description="Macro factor to date ranges mapping")
    micro: Dict[str, List[List[str]]] = Field(description="Micro factor to date ranges mapping")

# LangChain parser expects Pydantic v2's model_json_schema; shim it for v1.
DateRangePayload.model_json_schema = classmethod(lambda cls: cls.schema())

date_range_parser = PydanticOutputParser(pydantic_object=DateRangePayload)

# =============================================================================
# EXACT FUNCTIONS FROM QUANT IMPACT AGENT
# =============================================================================

def get_system_instructions(language: str = "English") -> str:
    """Get system instructions with language support."""
    base_instructions = f"""
You are a senior oil market analyst. Given the supplied crude oil market intelligence and historical trends,
identify the TOP 6 most impactful catalysts for MACRO and MICRO factors.

Rules:
- Output EXACTLY 6 factors for MACRO and EXACTLY 6 factors for MICRO (total 12 factors)
- Focus on the MOST IMPORTANT factors only - quality over quantity
- Include expectation/delivery context directly in the factor name
- Examples: "OPEC+ Production Cut Expectation", "Inventory Decline Better Than Expected", "Demand Growth Worse Than Expected"
- Keep each keyword under 60 characters
- Ground every keyword in the provided context or widely known facts; never invent events
- **MACRO factors**: Market-wide events (Fed policy, global demand, geopolitical tensions, currency movements)
- **MICRO factors**: Oil-specific events (OPEC+ decisions, inventory levels, production disruptions, refinery activity)
- Include both positive and negative variants when relevant (e.g., "Supply Disruption" + "Supply Stability")
- **CRITICAL: Include expectation/delivery context:**
  - For expectations: "Event Name Expectation" (e.g., "OPEC+ Cut Expectation")
  - For delivery better than expected: "Event Name Better Than Expected" (e.g., "Inventory Decline Better Than Expected")
  - For delivery worse than expected: "Event Name Worse Than Expected" (e.g., "Demand Growth Worse Than Expected")
  - For delivery meeting expectations: "Event Name" (e.g., "OPEC+ Production Cut")
{parser.get_format_instructions()}
""".strip()
    
    if language.lower() != "english":
        language_instruction = f"\n\nIMPORTANT: Output ALL factor names in {language} language only. Do NOT use English."
        return base_instructions + language_instruction
    else:
        return base_instructions

def _extract_json_payload(raw: str) -> str:
    """Strip markdown fences and clamp to the outermost JSON braces."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]
    return cleaned

def build_factor_prompt(
    ticker: str, 
    read_information: Union[str, Dict[str, Any]],
    language: str = "English"
) -> str:
    """Human prompt body sent to the LLM."""
    if isinstance(read_information, (dict, list)):
        serialized_context = json.dumps(read_information, ensure_ascii=False, indent=2)
    else:
          serialized_context = str(read_information)

    base_prompt = (
        f"Ticker: {ticker}\n\n"
        "Crude oil market intelligence snapshot:\n"
        f"{serialized_context}\n\n"
        "Task: Identify the TOP 6 MOST IMPORTANT MACRO factors and TOP 6 MOST IMPORTANT MICRO factors. "
        "MACRO: market-wide economic/political events (Fed policy, global demand, geopolitical, currency). "
        "MICRO: oil-specific events (OPEC+ decisions, inventory levels, production disruptions, refinery activity). "
        "IMPORTANT: Provide EXACTLY 6 factors for each category. "
        "Include expectation/delivery context directly in factor names (e.g., 'OPEC+ Cut Expectation', 'Inventory Decline Better Than Expected')"
    )
    
    if language.lower() != "english":
        language_instruction = f"\n\nIMPORTANT: Output ALL factor names in {language} language only. Do NOT use English."
        return base_prompt + language_instruction
    else:
        return base_prompt

def generate_stock_factors(
    ticker: str,
    read_information: Union[str, Dict[str, Any]],
    provider: str = "deepseek",
    model_override: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 500,  # Increased to 500 for 6+6=12 factors
    language: str = "English"
) -> FactorPayload:
    """Call the LLM and parse keyword factors via LangChain."""
    prompt = build_factor_prompt(ticker, read_information, language)
    system_instructions = get_system_instructions(language)

    if provider == "deepseek":
        model = model_override or "deepseek-chat"
    else:
        provider = "openai"
        model = model_override or "gpt-4o"

    llm_agent = LLMCallAgent(default_provider=provider, default_model=model)

    if provider == "deepseek":
        raw_response = llm_agent.call_deepseek(
            prompt=prompt,
            system_message=system_instructions,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    else:
        raw_response = llm_agent.call_openai(
            prompt=prompt,
            system_message=system_instructions,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    if not raw_response:
        raise ValueError("Empty response from LLM")

    cleaned = _extract_json_payload(raw_response)
    try:
        return parser.parse(cleaned)
    except Exception as exc:
        raise ValueError(f"LLM response could not be parsed:\n{raw_response}") from exc

def get_date_range_system_instructions(language: str = "English") -> str:
    """Get system instructions for date range mapping."""
    base_instructions = f"""
You are a meticulous financial analyst. Given the intelligence and historical trends,
map each factor to specific date ranges when those events actually occurred.

Rules:
- **CRITICAL: Provide MAXIMUM 3-5 date ranges per factor** (to avoid truncation)
- Use format: ["YYYY-MM-DD", "YYYY-MM-DD"] for each date range
- Only include the MOST SIGNIFICANT occurrences
- Only use dates that actually exist in the historical data
- If no specific dates are available, provide empty list []
- Focus on major events that would impact price
- Be conservative - only include dates you're confident about
- IMPORTANT: You MUST include macro and micro sections
- IMPORTANT: Keep response concise - MAX 3-5 date ranges per factor
{date_range_parser.get_format_instructions()}
""".strip()
    
    if language.lower() != "english":
        language_instruction = f"\n\nIMPORTANT: Output ALL content in {language} language only. Do NOT use English."
        return base_instructions + language_instruction
    else:
        return base_instructions

def build_date_range_prompt(ticker: str, factor_payload: FactorPayload, read_information: Dict[str, Any], language: str) -> str:
    """Build prompt for date range mapping."""
    # Create factor summary (6 factors each)
    macro_factors = [
        factor_payload.macro.factor_1, factor_payload.macro.factor_2, factor_payload.macro.factor_3,
        factor_payload.macro.factor_4, factor_payload.macro.factor_5, factor_payload.macro.factor_6
    ]
    
    micro_factors = [
        factor_payload.micro.factor_1, factor_payload.micro.factor_2, factor_payload.micro.factor_3,
        factor_payload.micro.factor_4, factor_payload.micro.factor_5, factor_payload.micro.factor_6
    ]
    
    factor_summary = f"Macro factors: {', '.join(macro_factors)}\nMicro factors: {', '.join(micro_factors)}"
    
    # Create trend summary from historical data
    trend_summary = {}
    if 'historical_trends' in read_information:
        for trend_key, trend_data in read_information['historical_trends'].items():
            summary = trend_data.get("summary", {})
            trend_summary[trend_key] = {
                "period": trend_data.get("current", ""),
                "macro_reason": summary.get("macro_reason", ""),
                "micro_reason": summary.get("micro_reason", "")
            }
    
    trend_context = json.dumps(trend_summary, indent=2, ensure_ascii=False)
    
    base_prompt = (
        f"Ticker: {ticker}\n\n"
        f"Factor keywords (macro/micro):\n{factor_summary}\n\n"
        "Historical trend context (with dates and reasons):\n"
        f"{trend_context}\n\n"
        
        "Task: For each factor, map to specific date ranges when those events occurred. "
        "**CRITICAL: Provide MAXIMUM 3-5 date ranges per factor** (most significant only). "
        "Use the historical trend data to identify actual dates. "
        "Return date ranges in format: [\"start_date\", \"end_date\"]. "
        "IMPORTANT: Include macro and micro sections and keep response concise - MAX 3-5 date ranges per factor."
    )
    
    if language.lower() != "english":
        language_instruction = f"\n\nIMPORTANT: Output ALL content in {language} language only. Do NOT use English."
        return base_prompt + language_instruction
    else:
        return base_prompt

def map_factors_to_date_ranges(
    ticker: str,
    factor_payload: FactorPayload,
    read_information: Dict[str, Any],
    provider: str = "deepseek",
    model_override: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4000,  # EXACT COPY from Quant Impact Agent - handles 6+6=12 factors
    language: str = "English"
) -> DateRangePayload:
    """Map factors to date ranges using LLM."""
    prompt = build_date_range_prompt(ticker, factor_payload, read_information, language)
    system_instructions = get_date_range_system_instructions(language)

    if provider == "deepseek":
        model = model_override or "deepseek-chat"
    else:
        provider = "openai"
        model = model_override or "gpt-4o"

    llm_agent = LLMCallAgent(default_provider=provider, default_model=model)

    if provider == "deepseek":
        raw_response = llm_agent.call_deepseek(
            prompt=prompt,
            system_message=system_instructions,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    else:
        raw_response = llm_agent.call_openai(
            prompt=prompt,
            system_message=system_instructions,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    if not raw_response:
        raise ValueError("Empty response from LLM during date range mapping")

    cleaned = raw_response.strip().strip("`")
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]

    # Check if response is complete - EXACT COPY from Quant Impact Agent
    if not cleaned.endswith("}"):
        print(f"⚠️ Response may be truncated. Last 100 chars: {cleaned[-100:]}")
        # Try to fix incomplete JSON
        if '"micro"' not in cleaned:
            cleaned += ', "micro": {}}'
        elif '"macro"' not in cleaned:
            cleaned += ', "macro": {}}'
        else:
            # More aggressive JSON repair for truncated responses
            print("🔧 Attempting advanced JSON repair...")
            # Count open vs close braces
            open_braces = cleaned.count('{')
            close_braces = cleaned.count('}')
            missing_braces = open_braces - close_braces
            
            # Add missing closing braces
            cleaned += '}' * missing_braces
            
            # Ensure proper JSON structure
            if not cleaned.strip().endswith('}'):
                cleaned = cleaned.rstrip() + '}'
            
            print(f"🔧 Added {missing_braces} missing closing braces")

    # COMPLETE JSON REPAIR - NO FALLBACKS (EXACT COPY from Quant Impact Agent)
    # Fix incomplete JSON by completing the structure
    if not cleaned.endswith("}"):
        print(f"⚠️ Truncated response detected. Repairing JSON...")
        
        # Find the last complete factor entry
        lines = cleaned.split('\n')
        repaired_lines = []
        in_micro_section = False
        in_macro_section = False
        
        for line in lines:
            if '"micro"' in line:
                in_micro_section = True
                in_macro_section = False
            elif '"macro"' in line:
                in_macro_section = True
                in_micro_section = False
            
            # If line ends with incomplete factor (missing closing bracket)
            if in_micro_section and line.strip().endswith(':'):
                # Complete the incomplete factor
                line = line.rstrip(':') + ': []'
            elif in_macro_section and line.strip().endswith(':'):
                # Complete the incomplete factor  
                line = line.rstrip(':') + ': []'
            
            repaired_lines.append(line)
        
        # Reconstruct the JSON
        cleaned = '\n'.join(repaired_lines)
        
        # Ensure proper closing
        open_braces = cleaned.count('{')
        close_braces = cleaned.count('}')
        missing_braces = open_braces - close_braces
        
        if missing_braces > 0:
            cleaned += '\n' + '}' * missing_braces
        
        print(f"🔧 JSON repair completed")

    try:
        date_range_result = date_range_parser.parse(cleaned)
        
        # CREATE FACTOR-TIME MAPPING DataFrame (EXACT COPY from Quant Impact Agent)
        factor_time_mapping = []
        
        # Process macro factors
        for factor_name, date_ranges in date_range_result.macro.items():
            for date_range in date_ranges:
                if date_range:  # Skip empty ranges
                    start_date, end_date = date_range
                    factor_time_mapping.append({
                        'factor_name': factor_name,
                        'scope': 'macro',
                        'start_date': start_date,
                        'end_date': end_date,
                        'time_interval': f"{start_date} to {end_date}",
                        'duration_days': (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days if start_date and end_date else 0
                    })
        
        # Process micro factors
        for factor_name, date_ranges in date_range_result.micro.items():
            for date_range in date_ranges:
                if date_range:  # Skip empty ranges
                    start_date, end_date = date_range
                    factor_time_mapping.append({
                        'factor_name': factor_name,
                        'scope': 'micro',
                        'start_date': start_date,
                        'end_date': end_date,
                        'time_interval': f"{start_date} to {end_date}",
                        'duration_days': (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days if start_date and end_date else 0
                    })
        
        # Create DataFrame
        factor_time_df = pd.DataFrame(factor_time_mapping)
        
        print(f"✅ Created factor-time mapping: {len(factor_time_df)} factor-date pairs")
        
        return date_range_result, factor_time_df
        
    except Exception as exc:
        print(f"❌ Raw response: {raw_response}")
        print(f"❌ Cleaned response: {cleaned}")
        raise ValueError(f"Date range mapping response could not be parsed:\n{raw_response}") from exc

def step1_get_factors(ticker: str, read_information: Dict[str, Any], language: str = "English"):
    """Step 1: Get micro + macro factors (no sector)"""
    print(f"🔍 Step 1: Getting MICRO + MACRO factors for {ticker}")
    
    # Generate factors using LLM
    factor_result = generate_stock_factors(
        ticker=ticker, 
        read_information=read_information,
        language=language
    )
    
    # Extract factor lists (6 factors each)
    macro_factors = [
        factor_result.macro.factor_1,
        factor_result.macro.factor_2,
        factor_result.macro.factor_3,
        factor_result.macro.factor_4,
        factor_result.macro.factor_5,
        factor_result.macro.factor_6,
    ]
    
    micro_factors = [
        factor_result.micro.factor_1,
        factor_result.micro.factor_2,
        factor_result.micro.factor_3,
        factor_result.micro.factor_4,
        factor_result.micro.factor_5,
        factor_result.micro.factor_6,
    ]
    
    print(f"✅ Generated {len(macro_factors)} macro factors (controlled to 6)")
    print(f"✅ Generated {len(micro_factors)} micro factors (controlled to 6)")
    
    return {
        "factor_payload": factor_result,
        "macro_factors": macro_factors,
        "micro_factors": micro_factors,
        "read_information": read_information
    }

def step2_get_date_ranges(ticker: str, factor_result: Dict[str, Any], language: str = "English"):
    """Step 2: Map micro + macro factors to date ranges - EXACT COPY from Quant Impact Agent"""
    print(f"🔍 Step 2: Mapping MICRO + MACRO factors to date ranges for {ticker}")
    
    factor_payload = factor_result["factor_payload"]
    read_information = factor_result["read_information"]
    
    # Map factors to date ranges using LLM (returns BOTH date_range_result AND factor_time_df)
    date_range_result, factor_time_df = map_factors_to_date_ranges(
        ticker=ticker,
        factor_payload=factor_payload,
        read_information=read_information,
        language=language
    )
    
    print(f"✅ Mapped macro factors to date ranges")
    print(f"✅ Mapped micro factors to date ranges")
    
    # Return BOTH the date range result AND the factor-time mapping DataFrame
    return date_range_result, factor_time_df

def map_date_range_to_trend_data(start_date: str, end_date: str, historical_trends: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify oil factors into 7 categories:
    1. Supply
    2. Demand  
    3. Geopolitical
    4. Policy
    5. Data
    6. Global Market
    7. Manufacturing/Industrial
    """
    factor_lower = factor_name.lower()
    
    # Supply factors
    if any(keyword in factor_lower for keyword in ['supply', 'production', 'output', 'drilling', 'rig', 'pipeline', 'storage', 'inventory']):
        return 'supply'
    
    # Demand factors
    elif any(keyword in factor_lower for keyword in ['demand', 'consumption', 'usage', 'refining', 'gasoline', 'diesel', 'jet fuel']):
        return 'demand'
    
    # Geopolitical factors
    elif any(keyword in factor_lower for keyword in ['geopolitical', 'war', 'conflict', 'sanctions', 'middle east', 'russia', 'iran', 'venezuela']):
        return 'geopolitical'
    
    # Policy factors
    elif any(keyword in factor_lower for keyword in ['policy', 'opec', 'federal reserve', 'interest rate', 'monetary', 'fiscal', 'regulation']):
        return 'policy'
    
    # Data factors
    elif any(keyword in factor_lower for keyword in ['data', 'report', 'eia', 'api', 'inventory', 'gdp', 'employment', 'inflation']):
        return 'data'
    
    # Global market factors
    elif any(keyword in factor_lower for keyword in ['global', 'market', 'economy', 'recession', 'growth', 'trade', 'currency', 'dollar']):
        return 'global_market'
    
    # Manufacturing/Industrial factors
    elif any(keyword in factor_lower for keyword in ['manufacturing', 'industrial', 'factory', 'production', 'pmi', 'industrial production']):
        return 'manufacturing_industrial'
    
    # Default to global_market if no match
    else:
        return 'global_market'

def calculate_beta_filtered_impacts(
    llm_trend_data: Dict[str, Any],
    ticker: str,
    market_beta: float = 1.0,
    risk_free_rate: float = 0.025
) -> Dict[str, Any]:
    """
    Calculate beta-filtered impacts for oil factors
    
    Formula: CLZ25_return - risk_free = beta * (macro_return - risk_free) + alpha
    """
    print(f"🔍 Calculating beta-filtered impacts for {ticker}")
    print(f"   Using market beta: {market_beta:.4f}")
    print(f"   Risk-free rate: {risk_free_rate:.1%} annual")
    
    historical_trends = llm_trend_data.get('historical_trends', {})
    if not historical_trends:
        print("❌ No historical trends found")
        return {"error": "No historical trends found"}
    
    print(f"   Found {len(historical_trends)} historical trend periods")
    
    # Get date range for volatility calculation
    all_dates = []
    for trend_data in historical_trends.values():
        current_period = trend_data.get('current', '')
        if ' to ' in current_period:
            start_date, end_date = current_period.split(' to ')
            all_dates.extend([start_date, end_date])
    
    if not all_dates:
        print("❌ No date ranges found")
        return {"error": "No date ranges found"}
    
    min_date = min(all_dates)
    max_date = max(all_dates)
    
    print(f"   Processing date ranges from {min_date} to {max_date}")
    
    # Calculate annual volatility
    annual_volatility = calculate_annual_volatility(ticker, min_date, max_date)
    volatility_factor = annual_volatility / 15.874
    
    print(f"   🔧 Volatility Factor (vol/15.874): {volatility_factor:.4f}")
    
    # Process each trend period
    factor_impacts = []
    
    for trend_key, trend_data in historical_trends.items():
        current_period = trend_data.get('current', '')
        if ' to ' not in current_period:
            continue
            
        start_date, end_date = current_period.split(' to ')
        
        # Get returns from trend data
        stock_daily_return = trend_data.get('day average_return', 0.0)
        spy_daily_return = trend_data.get('SPY_return_rate', 0.0)
        
        if stock_daily_return is None:
            stock_daily_return = 0.0
        if spy_daily_return is None:
            spy_daily_return = 0.0
        
        # Calculate duration
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days = (end_dt - start_dt).days
        except:
            days = 1
        
        # Calculate risk-free return for this period (daily)
        risk_free_daily = risk_free_rate / 365
        
        # Calculate beta-adjusted macro impact
        real_macro_impact = market_beta * (spy_daily_return - risk_free_daily) + risk_free_daily
        
        # Calculate micro impact (what's left after macro)
        real_micro_impact = stock_daily_return - real_macro_impact
        
        # Apply volatility normalization to micro impact
        if real_micro_impact > 0:
            normalized_micro_impact = real_micro_impact - volatility_factor
        else:
            normalized_micro_impact = real_micro_impact + volatility_factor
        
        # Get factor information from LLM analysis
        summary = trend_data.get('summary', {})
        macro_reason = summary.get('macro_reason', '')
        micro_reason = summary.get('micro_reason', '')
        
        # Classify factors
        macro_category = classify_oil_factors(macro_reason)
        micro_category = classify_oil_factors(micro_reason)
        
        factor_impacts.append({
            "trend_key": trend_key,
            "period": current_period,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "stock_daily_return": stock_daily_return,
            "spy_daily_return": spy_daily_return,
            "risk_free_daily": risk_free_daily,
            "real_macro_impact": real_macro_impact,
            "real_micro_impact": real_micro_impact,
            "normalized_micro_impact": normalized_micro_impact,
            "volatility_factor": volatility_factor,
            "macro_reason": macro_reason,
            "micro_reason": micro_reason,
            "macro_category": macro_category,
            "micro_category": micro_category
        })
    
    print(f"✅ Processed {len(factor_impacts)} trend periods")
    
    return {
        "ticker": ticker,
        "market_beta": market_beta,
        "risk_free_rate": risk_free_rate,
        "annual_volatility": annual_volatility,
        "volatility_factor": volatility_factor,
        "factor_impacts": factor_impacts,
        "data_period": f"{min_date} to {max_date}"
    }

def calculate_impact_metrics(beta_filtered_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate impact metrics from beta-filtered results
    """
    print(f"🔍 Calculating impact metrics for {beta_filtered_result['ticker']}")
    
    factor_impacts = beta_filtered_result['factor_impacts']
    
    # Aggregate by category
    category_metrics = {}
    
    # Process macro categories
    macro_categories = {}
    for impact in factor_impacts:
        category = impact['macro_category']
        if category not in macro_categories:
            macro_categories[category] = []
        macro_categories[category].append(impact)
    
    # Process micro categories  
    micro_categories = {}
    for impact in factor_impacts:
        category = impact['micro_category']
        if category not in micro_categories:
            micro_categories[category] = []
        micro_categories[category].append(impact)
    
    # Calculate metrics for each category
    def calculate_category_metrics(category_name: str, impacts: List[Dict], impact_type: str):
        if not impacts:
            return None
        
        # Calculate weighted averages (using duration as weights)
        total_duration = sum(impact['days'] for impact in impacts)
        
        if impact_type == 'macro':
            weighted_sum = sum(impact['days'] * impact['real_macro_impact'] for impact in impacts)
        else:
            weighted_sum = sum(impact['days'] * impact['normalized_micro_impact'] for impact in impacts)
        
        weighted_mean = weighted_sum / total_duration if total_duration > 0 else 0
        
        # Calculate weighted variance
        if impact_type == 'macro':
            weighted_variance_sum = sum(impact['days'] * (impact['real_macro_impact'] - weighted_mean)**2 for impact in impacts)
        else:
            weighted_variance_sum = sum(impact['days'] * (impact['normalized_micro_impact'] - weighted_mean)**2 for impact in impacts)
        
        weighted_variance = weighted_variance_sum / total_duration if total_duration > 0 else 0
        
        # Calculate risk-reward ratio
        risk_reward_ratio = abs(weighted_mean) / np.sqrt(weighted_variance) if weighted_variance > 0 else 0
        
        # Calculate compound return
        avg_duration = total_duration / len(impacts) if len(impacts) > 0 else 1
        compound_return = (1 + weighted_mean) ** avg_duration - 1
        
        return {
            "category": category_name,
            "scope": impact_type,
            "trend_count": len(impacts),
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "weighted_mean": weighted_mean,
            "weighted_variance": weighted_variance,
            "risk_reward_ratio": risk_reward_ratio,
            "compound_return": compound_return,
            "volatility": np.sqrt(weighted_variance)
        }
    
    # Calculate metrics for all categories
    all_metrics = []
    
    for category, impacts in macro_categories.items():
        metrics = calculate_category_metrics(category, impacts, 'macro')
        if metrics:
            all_metrics.append(metrics)
    
    for category, impacts in micro_categories.items():
        metrics = calculate_category_metrics(category, impacts, 'micro')
        if metrics:
            all_metrics.append(metrics)
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(all_metrics)
    
    print(f"✅ Generated {len(all_metrics)} category metrics")
    
    return {
        "ticker": beta_filtered_result['ticker'],
        "market_beta": beta_filtered_result['market_beta'],
        "risk_free_rate": beta_filtered_result['risk_free_rate'],
        "annual_volatility": beta_filtered_result['annual_volatility'],
        "volatility_factor": beta_filtered_result['volatility_factor'],
        "summary_df": summary_df,
        "category_metrics": all_metrics
    }

def calculate_trend_weighted_score(summary_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate trend-weighted scores for each factor"""
    total_trends = summary_df['trend_count'].sum()
    summary_df['trend_weight_score'] = summary_df['trend_count'] / total_trends
    summary_df['score_weighted_mean'] = summary_df['trend_weight_score'] * summary_df['weighted_mean']
    summary_df['score_weighted_variance'] = summary_df['trend_weight_score'] * summary_df['weighted_variance']
    return summary_df

def calculate_macro_micro_risk_share(summary_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate Macro vs Micro Risk Share Index"""
    macro_contributions = summary_df[summary_df['scope'] == 'macro']['score_weighted_variance'].sum()
    micro_contributions = summary_df[summary_df['scope'] == 'micro']['score_weighted_variance'].sum()
    total_contributions = macro_contributions + micro_contributions
    
    if total_contributions == 0:
        return {"macro_risk_share": 0.0, "micro_risk_share": 0.0, "risk_environment": "No risk data available"}
    
    macro_risk_share = (macro_contributions / total_contributions) * 100
    micro_risk_share = (micro_contributions / total_contributions) * 100
    
    return {
        "macro_risk_share": macro_risk_share,
        "micro_risk_share": micro_risk_share,
        "risk_environment": f"Current risk environment is {micro_risk_share:.1f}% micro-driven, {macro_risk_share:.1f}% macro-driven."
    }

def calculate_factor_volatility_separated(summary_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate Factor Volatility DataFrames with HIGH/LOW classification"""
    volatility_df = summary_df.copy()
    volatility_df['volatility'] = np.sqrt(volatility_df['weighted_variance'])
    volatility_df['score_weighted_volatility'] = np.sqrt(volatility_df['score_weighted_variance'])
    
    macro_volatility_df = volatility_df[volatility_df['scope'] == 'macro'].copy()
    micro_volatility_df = volatility_df[volatility_df['scope'] == 'micro'].copy()
    
    if not macro_volatility_df.empty:
        macro_volatility_median = macro_volatility_df['volatility'].median()
        macro_volatility_df['volatility_level'] = macro_volatility_df['volatility'].apply(
            lambda x: 'HIGH' if x > macro_volatility_median else 'LOW'
        )
    
    if not micro_volatility_df.empty:
        micro_volatility_median = micro_volatility_df['volatility'].median()
        micro_volatility_df['volatility_level'] = micro_volatility_df['volatility'].apply(
            lambda x: 'HIGH' if x > micro_volatility_median else 'LOW'
        )
    
    return macro_volatility_df, micro_volatility_df

def calculate_risk_reward_ratio(summary_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Risk-Reward Ratio for each factor"""
    impact_metrics_df = summary_df.copy()
    impact_metrics_df['risk_reward_ratio'] = np.abs(impact_metrics_df['weighted_mean']) / np.sqrt(impact_metrics_df['weighted_variance'])
    impact_metrics_df['risk_reward_ratio'] = impact_metrics_df['risk_reward_ratio'].replace([np.inf, -np.inf], 0)
    impact_metrics_df['risk_reward_ratio'] = impact_metrics_df['risk_reward_ratio'].fillna(0)
    
    # Return with average_duration and total_duration included
    return impact_metrics_df[['factor', 'scope', 'trend_count', 'weighted_mean', 'weighted_variance', 'risk_reward_ratio', 'average_duration', 'total_duration']]

def calculate_final_impact_separated(summary_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate Final Impact using compound formula"""
    impact_df = summary_df.copy()
    impact_df['final_impact'] = (1 + impact_df['weighted_mean']) ** impact_df['average_duration'] - 1
    
    macro_total_impact_df = impact_df[impact_df['scope'] == 'macro'][['factor', 'final_impact']].sort_values('final_impact', ascending=False)
    micro_total_impact_df = impact_df[impact_df['scope'] == 'micro'][['factor', 'final_impact']].sort_values('final_impact', ascending=False)
    
    return macro_total_impact_df, micro_total_impact_df

def generate_7_datasets(impact_metrics_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the 7 datasets using Quant Impact Agent format"""
    print(f"🔍 Generating 7 datasets for {impact_metrics_result['ticker']}")
    
    summary_df = impact_metrics_result['summary_df']
    
    if summary_df.empty:
        print("❌ No data to generate datasets")
        return {"error": "No data available"}
    
    # Use Quant Impact Risk Analysis pipeline
    enhanced_df = calculate_trend_weighted_score(summary_df.copy())
    risk_share_index = calculate_macro_micro_risk_share(enhanced_df)
    macro_volatility_df, micro_volatility_df = calculate_factor_volatility_separated(enhanced_df)
    impact_metrics_df = calculate_risk_reward_ratio(enhanced_df)
    macro_total_impact_df, micro_total_impact_df = calculate_final_impact_separated(enhanced_df)
    
    # 7. Factor Risk Reward DataFrame
    factor_risk_reward_df = enhanced_df.groupby(['scope', 'factor']).agg({
        'weighted_mean': 'mean',
        'weighted_variance': 'mean',
        'average_duration': 'mean',
        'trend_count': 'sum'
    }).reset_index()
    
    factor_risk_reward_df['final_impact'] = (1 + factor_risk_reward_df['weighted_mean']) ** factor_risk_reward_df['average_duration'] - 1
    factor_risk_reward_df = factor_risk_reward_df.rename(columns={
        'factor': 'factor_name',
        'final_impact': 'max_compound_return'
    })
    factor_risk_reward_df['min_compound_return'] = factor_risk_reward_df['max_compound_return']
    factor_risk_reward_df = factor_risk_reward_df.sort_values('max_compound_return', ascending=False)
    
    print(f"✅ Generated 7 datasets:")
    print(f"   📊 Risk Share Index: macro={risk_share_index['macro_risk_share']:.1f}%, micro={risk_share_index['micro_risk_share']:.1f}%")
    print(f"   📊 Macro Volatility: {len(macro_volatility_df)} factors")
    print(f"   📊 Micro Volatility: {len(micro_volatility_df)} factors")
    print(f"   📊 Impact Metrics: {len(impact_metrics_df)} factors")
    print(f"   📊 Macro Total Impact: {len(macro_total_impact_df)} factors")
    print(f"   📊 Micro Total Impact: {len(micro_total_impact_df)} factors")
    print(f"   📊 Factor Risk Reward: {len(factor_risk_reward_df)} factors")
    
    return {
        "risk_share_index": risk_share_index,
        "macro_volatility_df": macro_volatility_df,
        "micro_volatility_df": micro_volatility_df,
        "impact_metrics_df": impact_metrics_df,
        "macro_total_impact_df": macro_total_impact_df,
        "micro_total_impact_df": micro_total_impact_df,
        "factor_risk_reward_df": factor_risk_reward_df
    }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def step3_beta_filtering(
    ticker: str,
    step2_result: DateRangePayload,
    read_information: Dict[str, Any],
    market_beta: float = 1.0,
    risk_free_rate: float = 0.025
) -> Dict[str, Any]:
    """Step 3: Beta filtering - Get 600 days data once, calculate beta, then filter each trend"""
    print(f"🔍 Step 3: Beta filtering for {ticker}")
    print(f"   Using market beta: {market_beta:.4f}")
    print(f"   Risk-free rate: {risk_free_rate:.1%} annual")
    
    # Extract factor date ranges
    macro_date_ranges = step2_result.macro
    micro_date_ranges = step2_result.micro
    
    # Get historical trend data
    historical_trends = read_information.get('historical_trends', {})
    
    if not historical_trends:
        return {"error": "No historical trends found in LLM data"}
    
    print(f"   Found {len(historical_trends)} historical trend periods")
    
    # Step 1: Get 600 days of data once
    print(f"   📊 Fetching 600 days of data for beta calculation...")
    from data_sources.get_price import get_yahoo_data
    
    price_data = get_yahoo_data(ticker, 600)
    spy_data = get_yahoo_data("SPY", 600)
    
    if price_data.empty or spy_data.empty:
        return {"error": "Failed to fetch 600 days of price data"}
    
    print(f"   ✅ Retrieved {len(price_data)} days of price data")
    print(f"   ✅ Retrieved {len(spy_data)} days of SPY data")
    
    # Step 2: Calculate daily returns
    price_data['daily_return'] = price_data['close'].pct_change()
    spy_data['daily_return'] = spy_data['close'].pct_change()
    
    # Step 3: Merge data and calculate beta
    merged_data = pd.merge(
        price_data[['date', 'daily_return']], 
        spy_data[['date', 'daily_return']], 
        on='date', 
        suffixes=('_stock', '_spy')
    )
    
    # Calculate beta from 600-day data
    correlation = merged_data['daily_return_stock'].corr(merged_data['daily_return_spy'])
    stock_std = merged_data['daily_return_stock'].std()
    spy_std = merged_data['daily_return_spy'].std()
    calculated_beta = correlation * (stock_std / spy_std) if spy_std > 0 else market_beta
    
    print(f"   📈 Calculated beta: {calculated_beta:.4f}")
    print(f"   📊 Using beta: {market_beta:.4f} (provided)")
    
    # Step 4: Process each trend period using the 600-day data
    factor_impacts = []
    processed_periods = 0
    
    for trend_key, trend_data in historical_trends.items():
        try:
            # Extract trend period dates
            current_period = trend_data.get('current', '')
            if not current_period:
                continue
                
            # Parse dates (format: "2024-03-22 to 2024-04-04")
            if ' to ' in current_period:
                start_date, end_date = current_period.split(' to ')
                start_date = start_date.strip()
                end_date = end_date.strip()
            else:
                continue
            
            # Filter the 600-day data for this trend period
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            trend_data_filtered = merged_data[
                (merged_data['date'] >= start_dt) & 
                (merged_data['date'] <= end_dt)
            ].copy()
            
            if len(trend_data_filtered) < 2:
                print(f"   ⚠️ Insufficient data for {current_period} ({len(trend_data_filtered)} days)")
                continue
            
            # Calculate risk-free daily rate
            risk_free_daily = risk_free_rate / 252
            
            # Calculate real macro and micro impacts using the provided beta
            trend_data_filtered['real_macro_impact'] = market_beta * (trend_data_filtered['daily_return_spy'] - risk_free_daily) + risk_free_daily
            trend_data_filtered['real_micro_impact'] = trend_data_filtered['daily_return_stock'] - trend_data_filtered['real_macro_impact']
            
            # Calculate volatility factor for this trend period
            annual_volatility = trend_data_filtered['daily_return_stock'].std() * np.sqrt(252)
            volatility_factor = annual_volatility / 15.874
            
            # Normalize micro impact
            trend_data_filtered['normalized_micro_impact'] = np.where(
                trend_data_filtered['real_micro_impact'] >= 0,
                trend_data_filtered['real_micro_impact'] - volatility_factor,
                trend_data_filtered['real_micro_impact'] + volatility_factor
            )
            
            # Store factor impact data
            factor_impacts.append({
                'trend_key': trend_key,
                'period': current_period,
                'start_date': start_date,
                'end_date': end_date,
                'daily_data': trend_data_filtered,
                'annual_volatility': annual_volatility,
                'volatility_factor': volatility_factor,
                'macro_date_ranges': macro_date_ranges,
                'micro_date_ranges': micro_date_ranges
            })
            
            processed_periods += 1
            
        except Exception as e:
            print(f"   ⚠️ Error processing {trend_key}: {e}")
            continue
    
    print(f"✅ Processed {processed_periods} trend periods")
    
    if not factor_impacts:
        return {"error": "No valid trend periods processed"}
    
    # Calculate overall volatility
    all_volatilities = [impact['annual_volatility'] for impact in factor_impacts]
    overall_volatility = np.mean(all_volatilities) if all_volatilities else 0.0
    overall_volatility_factor = overall_volatility / 15.874
    
    # Calculate weighted averages (using duration as weights)
    def calculate_weighted_averages(factor_results: Dict[str, List[Dict]]) -> Dict[str, Dict[str, float]]:
        """Calculate weighted averages for each factor"""
        weighted_results = {}
        
        for factor_name, impacts in factor_results.items():
            if not impacts:
                continue
                
            total_duration = sum(impact['days'] for impact in impacts)
            weighted_macro_sum = sum(impact['days'] * impact['real_macro_impact'] for impact in impacts)
            weighted_micro_sum = sum(impact['days'] * impact['real_micro_impact'] for impact in impacts)
            weighted_normalized_micro_sum = sum(impact['days'] * impact['normalized_micro_impact'] for impact in impacts)
            
            weighted_results[factor_name] = {
                "weighted_macro_impact": weighted_macro_sum / total_duration if total_duration > 0 else 0,
                "weighted_micro_impact": weighted_micro_sum / total_duration if total_duration > 0 else 0,
                "weighted_normalized_micro_impact": weighted_normalized_micro_sum / total_duration if total_duration > 0 else 0,
                "total_duration": total_duration,
                "periods": len(impacts)
            }
        
        return weighted_results
    
    # Group impacts by factor (from macro_date_ranges and micro_date_ranges)
    macro_results = {}
    micro_results = {}
    
    for impact in factor_impacts:
        macro_date_ranges = impact['macro_date_ranges']
        micro_date_ranges = impact['micro_date_ranges']
        daily_data = impact['daily_data']
        
        # Process macro factors
        for factor_name, date_ranges in macro_date_ranges.items():
            if factor_name not in macro_results:
                macro_results[factor_name] = []
            
            for date_range in date_ranges:
                if len(date_range) != 2:
                    continue
                start_date, end_date = date_range
                
                # Filter daily_data for this date range
                mask = (daily_data['date'] >= start_date) & (daily_data['date'] <= end_date)
                period_data = daily_data[mask]
                
                if len(period_data) < 2:
                    continue
                
                days = len(period_data)
                real_macro_impact = period_data['real_macro_impact'].mean()
                real_micro_impact = period_data['real_micro_impact'].mean()
                normalized_micro_impact = period_data['normalized_micro_impact'].mean()
                
                macro_results[factor_name].append({
                    'days': days,
                    'real_macro_impact': real_macro_impact,
                    'real_micro_impact': real_micro_impact,
                    'normalized_micro_impact': normalized_micro_impact
                })
        
        # Process micro factors
        for factor_name, date_ranges in micro_date_ranges.items():
            if factor_name not in micro_results:
                micro_results[factor_name] = []
            
            for date_range in date_ranges:
                if len(date_range) != 2:
                    continue
                start_date, end_date = date_range
                
                # Filter daily_data for this date range
                mask = (daily_data['date'] >= start_date) & (daily_data['date'] <= end_date)
                period_data = daily_data[mask]
                
                if len(period_data) < 2:
                    continue
                
                days = len(period_data)
                real_macro_impact = period_data['real_macro_impact'].mean()
                real_micro_impact = period_data['real_micro_impact'].mean()
                normalized_micro_impact = period_data['normalized_micro_impact'].mean()
                
                micro_results[factor_name].append({
                    'days': days,
                    'real_macro_impact': real_macro_impact,
                    'real_micro_impact': real_micro_impact,
                    'normalized_micro_impact': normalized_micro_impact
                })
    
    macro_weighted = calculate_weighted_averages(macro_results)
    micro_weighted = calculate_weighted_averages(micro_results)
    
    return {
        'ticker': ticker,
        'factor_impacts': factor_impacts,
        'annual_volatility': overall_volatility,
        'volatility_factor': overall_volatility_factor,
        'processed_periods': processed_periods,
        'calculated_beta': calculated_beta,
        'used_beta': market_beta,
        'risk_free_rate': risk_free_rate,
        'macro_results': macro_results,
        'micro_results': micro_results,
        'macro_weighted': macro_weighted,
        'micro_weighted': micro_weighted
    }

def step4_impact_metrics(step3_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 4: Generate final impact metrics in Quant Agent format - EXACT COPY from Quant Impact Agent
    
    Args:
        step3_result: Beta filtering results from Step 3 (with macro_weighted and micro_weighted)
    
    Returns:
        dict: Final aggregated metrics matching Quant Agent format
    """
    print(f"🔍 Step 4: Generating impact metrics for {step3_result['ticker']}")
    
    # Extract data from step3_result
    macro_weighted = step3_result.get('macro_weighted', {})
    micro_weighted = step3_result.get('micro_weighted', {})
    market_beta = step3_result['used_beta']
    risk_free_rate = step3_result['risk_free_rate']
    
    # Convert to Quant Agent format
    aggregated_metrics = {
        "macro": {},
        "micro": {}
    }
    
    # Process macro factors
    print(f"\n   Processing {len(macro_weighted)} macro factors...")
    
    for factor_name, factor_data in macro_weighted.items():
        # Calculate variance from the weighted impacts
        macro_impact = factor_data['weighted_macro_impact']
        total_duration = factor_data['total_duration']
        periods = factor_data['periods']
        
        # Estimate variance (10% of absolute impact as variance estimate)
        estimated_variance = abs(macro_impact) * 0.1
        
        aggregated_metrics["macro"][factor_name] = {
            "weighted_mean": macro_impact,
            "weighted_variance": estimated_variance,
            "total_duration": total_duration,
            "periods": periods
        }
        
        print(f"   ✅ {factor_name}: μ={macro_impact:.4f}, σ²={estimated_variance:.4f}")
    
    # Process micro factors
    print(f"\n   Processing {len(micro_weighted)} micro factors...")
    
    for factor_name, factor_data in micro_weighted.items():
        # Calculate variance from the weighted impacts
        micro_impact = factor_data['weighted_micro_impact']
        total_duration = factor_data['total_duration']
        periods = factor_data['periods']
        
        # Estimate variance (15% of absolute impact as variance estimate)
        estimated_variance = abs(micro_impact) * 0.15
        
        aggregated_metrics["micro"][factor_name] = {
            "weighted_mean": micro_impact,
            "weighted_variance": estimated_variance,
            "total_duration": total_duration,
            "periods": periods
        }
        
        print(f"   ✅ {factor_name}: μ={micro_impact:.4f}, σ²={estimated_variance:.4f}")
    
    # Generate summary DataFrame in Quant Agent format
    summary_data = []
    
    for scope, factors in aggregated_metrics.items():
        for factor_name, factor_data in factors.items():
            summary_data.append({
                "scope": scope,
                "factor": factor_name,
                "trend_count": factor_data["periods"],
                "weighted_mean": factor_data["weighted_mean"],
                "weighted_variance": factor_data["weighted_variance"],
                "average_duration": factor_data["total_duration"] / factor_data["periods"] if factor_data["periods"] > 0 else 0,
                "total_duration": factor_data["total_duration"]
            })
    
    if not summary_data:
        return {"error": "No factor impact data generated"}
    
    summary_df = pd.DataFrame(summary_data)
    print(f"\n✅ Generated {len(summary_df)} factor impact records")
    
    return {
        'ticker': step3_result['ticker'],
        'market_beta': market_beta,
        'risk_free_rate': risk_free_rate,
        'aggregated_metrics': aggregated_metrics,
        'summary_df': summary_df
    }

def generate_impact_summary_schema(summary_df: pd.DataFrame, language: str = "English") -> Dict[str, Any]:
    """Generate impact summary schema - EXACT COPY from Quant Impact Agent"""
    print(f"🔍 Generating impact summary schema...")
    
    # Create factor summary
    factor_summary = summary_df.groupby('factor_name').agg({
        'weighted_mean': 'mean',
        'weighted_variance': 'mean',
        'compound_return': 'mean',
        'risk_reward_ratio': 'mean',
        'average_duration': 'mean'
    }).reset_index()
    
    # Convert to JSON for LLM
    factor_json = factor_summary.to_json(orient='records', indent=2)
    
    # LLM prompt for schema generation
    prompt = f"""
Ticker: CLZ25.NYM
Factor impact data:
{factor_json}

Task: Generate a comprehensive impact summary schema for oil futures factors.
Focus on: supply, demand, geopolitical, policy, data, global market, manufacturing/industrial factors.
Return JSON with factor categories and descriptions.
"""
    
    system_message = f"""
You are a senior oil market analyst. Generate a comprehensive impact summary schema for oil futures factors.
Focus on these 7 categories: supply, demand, geopolitical, policy, data, global market, manufacturing/industrial.
Return structured JSON with factor categories and descriptions.
{language} language only.
"""
    
    try:
        llm_agent = LLMCallAgent(default_provider="deepseek", default_model="deepseek-chat")
        response = llm_agent.call_deepseek(
            prompt=prompt,
            system_message=system_message,
            max_tokens=1000,
            temperature=0.1
        )
        
        # Parse response
        cleaned = response.strip().strip("`")
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
        
        schema_result = json.loads(cleaned)
        print(f"✅ Generated impact summary schema")
        return schema_result
        
    except Exception as e:
        print(f"⚠️ Error generating schema: {e}")
        # Return default schema
        return {
            "supply": "Supply factors affecting oil production and availability",
            "demand": "Demand factors affecting oil consumption and usage",
            "geopolitical": "Geopolitical factors affecting oil markets",
            "policy": "Policy factors affecting oil markets",
            "data": "Data factors affecting oil markets",
            "global_market": "Global market factors affecting oil",
            "manufacturing_industrial": "Manufacturing and industrial factors affecting oil"
        }

def convert_schema_to_compound_datasets(schema_result: Dict[str, Any], summary_df: pd.DataFrame) -> pd.DataFrame:
    """Convert schema to compound datasets - EXACT COPY from Quant Impact Agent"""
    print(f"🔍 Converting schema to compound datasets...")
    
    # Create factor risk reward dataframe
    factor_risk_reward_data = []
    
    for factor_name in summary_df['factor_name'].unique():
        factor_data = summary_df[summary_df['factor_name'] == factor_name]
        
        # Calculate compound metrics
        avg_weighted_mean = factor_data['weighted_mean'].mean()
        avg_weighted_variance = factor_data['weighted_variance'].mean()
        avg_compound_return = factor_data['compound_return'].mean()
        avg_risk_reward_ratio = factor_data['risk_reward_ratio'].mean()
        avg_duration = factor_data['average_duration'].mean()
        
        # Determine factor category (simplified mapping)
        category = "other"
        for cat, desc in schema_result.items():
            if isinstance(desc, str) and any(keyword in factor_name.lower() for keyword in desc.lower().split()):
                category = cat
                break
        
        factor_risk_reward_data.append({
            'factor_name': factor_name,
            'category': category,
            'avg_weighted_mean': avg_weighted_mean,
            'avg_weighted_variance': avg_weighted_variance,
            'avg_compound_return': avg_compound_return,
            'avg_risk_reward_ratio': avg_risk_reward_ratio,
            'avg_duration': avg_duration,
            'total_occurrences': len(factor_data)
        })
    
    factor_risk_reward_df = pd.DataFrame(factor_risk_reward_data)
    print(f"✅ Generated {len(factor_risk_reward_df)} factor risk reward records")
    
    return factor_risk_reward_df

def quant_impact_risk_analysis(summary_df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate 6 risk metrics - EXACT COPY from Quant Impact Agent"""
    print(f"🔍 Generating 6 risk metrics...")
    
    # 1. Risk Share Index
    macro_impact = summary_df[summary_df['scope'] == 'macro']['weighted_mean'].abs().sum()
    micro_impact = summary_df[summary_df['scope'] == 'micro']['weighted_mean'].abs().sum()
    total_impact = macro_impact + micro_impact
    
    risk_share_index = {
        'macro_share': macro_impact / total_impact if total_impact > 0 else 0,
        'micro_share': micro_impact / total_impact if total_impact > 0 else 0,
        'risk_environment': f"Current risk environment is {micro_impact/total_impact*100:.1f}% micro-driven, {macro_impact/total_impact*100:.1f}% macro-driven." if total_impact > 0 else "No risk data available"
    }
    
    # 2. Macro Volatility DF
    macro_volatility_df = summary_df[summary_df['scope'] == 'macro'][['factor', 'weighted_variance', 'trend_count', 'average_duration']].copy()
    macro_volatility_df = macro_volatility_df.rename(columns={'factor': 'factor_name'})
    
    # 3. Micro Volatility DF
    micro_volatility_df = summary_df[summary_df['scope'] == 'micro'][['factor', 'weighted_variance', 'trend_count', 'average_duration']].copy()
    micro_volatility_df = micro_volatility_df.rename(columns={'factor': 'factor_name'})
    
    # 4. Impact Metrics DF
    impact_metrics_df = summary_df[['factor', 'scope', 'trend_count', 'weighted_mean', 'weighted_variance']].copy()
    impact_metrics_df = impact_metrics_df.rename(columns={'factor': 'factor_name'})
    
    # 5. Macro Total Impact DF
    macro_total_impact_df = summary_df[summary_df['scope'] == 'macro'].copy()
    macro_total_impact_df['final_impact'] = macro_total_impact_df['weighted_mean'] * macro_total_impact_df['average_duration']
    macro_total_impact_df = macro_total_impact_df[['factor', 'final_impact']].rename(columns={'factor': 'factor_name'})
    macro_total_impact_df = macro_total_impact_df.sort_values('final_impact', ascending=False)
    
    # 6. Micro Total Impact DF
    micro_total_impact_df = summary_df[summary_df['scope'] == 'micro'].copy()
    micro_total_impact_df['final_impact'] = micro_total_impact_df['weighted_mean'] * micro_total_impact_df['average_duration']
    micro_total_impact_df = micro_total_impact_df[['factor', 'final_impact']].rename(columns={'factor': 'factor_name'})
    micro_total_impact_df = micro_total_impact_df.sort_values('final_impact', ascending=False)
    
    print(f"✅ Generated 6 risk metrics")
    
    return risk_share_index, macro_volatility_df, micro_volatility_df, impact_metrics_df, macro_total_impact_df, micro_total_impact_df

# =============================================================================
# INTEGRATED FUNCTION - ONE CALL DOES EVERYTHING
# =============================================================================

def filter_llm_trends_by_date(llm_trend_json: Dict[str, Any], incremental_since_date: str) -> Dict[str, Any]:
    """
    Filter LLM trends to only include those after incremental_since_date.
    
    Args:
        llm_trend_json: Full LLM trend JSON from Redis
        incremental_since_date: ISO date string (e.g., "2025-10-07T21:38:14")
        
    Returns:
        Filtered LLM trend JSON with only trends after the incremental date
    """
    try:
        cutoff_date = pd.to_datetime(incremental_since_date.split('T')[0])  # Extract date part
        
        # Create filtered structure
        filtered_trends = {
            "current_trends": {},
            "historical_trends": {}
        }
        
        # Get the llm_summary section
        llm_summary = llm_trend_json.get('llm_summary', llm_trend_json)
        
        # Filter current trends
        for trend_name, trend_data in llm_summary.get('current_trends', {}).items():
            trend_start = pd.to_datetime(trend_data['time']['start'])
            if trend_start >= cutoff_date:
                filtered_trends['current_trends'][trend_name] = trend_data
        
        # Filter historical trends
        for trend_name, trend_data in llm_summary.get('historical_trends', {}).items():
            trend_start = pd.to_datetime(trend_data['time']['start'])
            if trend_start >= cutoff_date:
                filtered_trends['historical_trends'][trend_name] = trend_data
        
        # Create filtered result maintaining original structure
        filtered_result = llm_trend_json.copy()
        filtered_result['llm_summary'] = filtered_trends
        
        print(f"   📅 Filtered trends from {cutoff_date.strftime('%Y-%m-%d')} onwards")
        print(f"   📊 Current trends: {len(filtered_trends['current_trends'])}")
        print(f"   📊 Historical trends: {len(filtered_trends['historical_trends'])}")
        
        return filtered_result
        
    except Exception as e:
        print(f"   ⚠️ Error filtering trends by date: {e}")
        print(f"   📋 Returning original trends (no filtering)")
        return llm_trend_json
def get_oil_impact_from_existing_trends(
    llm_trend_json: Dict[str, Any],
    ticker: str = "CLZ25.NYM",
    risk_free_rate: float = 0.025,
    language: str = "English",
    beta_calculation_days: int = 600,
    incremental_since: str = None
) -> Dict[str, Any]:
    """
    🚀 USE EXISTING LLM TREND JSON - NO REGENERATION!
    
    This function:
    1. Calculates market beta from historical data
    2. Uses EXISTING llm_trend_json (no regeneration)
    3. Extracts macro/micro factors using LLM
    4. Maps factors to date ranges using LLM
    5. Calculates beta-filtered impacts
    6. Generates 7 impact datasets
    
    Args:
        llm_trend_json: EXISTING LLM trend JSON from Redis (already have it!)
        ticker: Oil futures ticker (default: CLZ25.NYM)
        risk_free_rate: Annual risk-free rate (default: 0.025)
        language: Language for LLM responses (default: "English")
        beta_calculation_days: Days to use for beta calculation (default: 600)
        incremental_since: ISO date string for incremental filtering (default: None)
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - ticker: Ticker symbol
        - meta_info: Metadata (including calculated beta)
        - datasets: All 7 datasets
        - summary_df: Summary dataframe
    
    Usage:
        from Oil_Impact_Metrics import get_oil_impact_from_existing_trends
        
        # You already have llm_trend_json from Redis!
        result = get_oil_impact_from_existing_trends(llm_trend_json)
        
        if result['status'] == 'success':
            datasets = result['datasets']
    """
    print(f"\n{'='*100}")
    print(f"🚀 OIL IMPACT ANALYSIS - USING EXISTING LLM TREND JSON")
    print(f"{'='*100}")
    print(f"📊 Ticker: {ticker}")
    print(f"💰 Risk-Free Rate: {risk_free_rate:.1%}")
    print(f"🌍 Language: {language}")
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")
    
    try:
        import time
        start_time = time.time()
        
        # Extract trend data from Redis structure
        if 'llm_summary' in llm_trend_json:
            read_information = llm_trend_json['llm_summary']
            print(f"✅ Extracted trend data from Redis structure")
        else:
            read_information = llm_trend_json
            print(f"✅ Using trend data directly")
        
        # Apply incremental filtering if specified
        if incremental_since:
            print(f"\n🔄 INCREMENTAL MODE: Filtering trends from {incremental_since} onwards")
            llm_trend_json = filter_llm_trends_by_date(llm_trend_json, incremental_since)
            read_information = llm_trend_json['llm_summary']
            print(f"✅ Applied incremental filtering to trends")
        
        # =================================================================
        # PHASE 0: Calculate Market Beta from Historical Data
        # =================================================================
        print(f"\n{'='*80}")
        print(f"📈 PHASE 0: Calculating Market Beta from Historical Data")
        print(f"{'='*80}")
        phase0_start = time.time()
        
        from data_sources.get_price import get_yahoo_data
        
        print(f"   Fetching {beta_calculation_days} days of {ticker} and SPY data...")
        df_ticker = get_yahoo_data(ticker, beta_calculation_days)
        df_spy = get_yahoo_data("SPY", beta_calculation_days)
        
        if df_ticker.empty or df_spy.empty:
            return {
                "status": "error",
                "ticker": ticker,
                "error": "Failed to fetch price data for beta calculation"
            }
        
        # Calculate daily returns
        df_ticker['date'] = pd.to_datetime(df_ticker['date'])
        df_spy['date'] = pd.to_datetime(df_spy['date'])
        df_ticker['return'] = df_ticker['close'].pct_change()
        df_spy['return'] = df_spy['close'].pct_change()
        
        # Merge on date
        merged = pd.merge(
            df_ticker[['date', 'return']],
            df_spy[['date', 'return']],
            on='date',
            suffixes=('_ticker', '_spy')
        ).dropna()
        
        # Calculate beta using covariance
        covariance = merged['return_ticker'].cov(merged['return_spy'])
        spy_variance = merged['return_spy'].var()
        market_beta = covariance / spy_variance if spy_variance > 0 else 1.0
        
        # Also calculate correlation for reference
        correlation = merged['return_ticker'].corr(merged['return_spy'])
        
        phase0_time = time.time() - phase0_start
        
        print(f"   ✅ Beta Calculation Complete:")
        print(f"      Days Used: {len(merged)}")
        print(f"      Correlation: {correlation:.4f}")
        print(f"      ✨ Calculated Beta: {market_beta:.4f}")
        print(f"✅ Phase 0 complete in {phase0_time:.2f} seconds\n")
        
        # =================================================================
        # PHASE 1: Extract Macro/Micro Factors using LLM
        # =================================================================
        print(f"\n{'='*80}")
        print(f"🧠 PHASE 1: Extracting MACRO + MICRO Factors using LLM")
        print(f"{'='*80}")
        phase1_start = time.time()
        
        step1_result = step1_get_factors(
            ticker=ticker,
            read_information=read_information,
            language=language
        )
        
        phase1_time = time.time() - phase1_start
        print(f"✅ Phase 1 complete in {phase1_time:.2f} seconds")
        
        # =================================================================
        # PHASE 2: Map Factors to Date Ranges using LLM
        # =================================================================
        print(f"\n{'='*80}")
        print(f"🗓️ PHASE 2: Mapping Factors to Date Ranges using LLM")
        print(f"{'='*80}")
        phase2_start = time.time()
        
        step2_result, factor_time_df = step2_get_date_ranges(
            ticker=ticker,
            factor_result=step1_result,
            language=language
        )
        
        phase2_time = time.time() - phase2_start
        print(f"✅ Phase 2 complete in {phase2_time:.2f} seconds")
        
        # Show factor-time mapping summary
        if not factor_time_df.empty:
            print(f"   📅 Factor-Time Mappings:")
            print(f"      Total date ranges: {len(factor_time_df)}")
            print(f"      Macro ranges: {len(factor_time_df[factor_time_df['scope']=='macro'])}")
            print(f"      Micro ranges: {len(factor_time_df[factor_time_df['scope']=='micro'])}")
        
        # =================================================================
        # PHASE 3: Beta Filtering (Math - No LLM)
        # =================================================================
        print(f"\n{'='*80}")
        print(f"📐 PHASE 3: Beta Filtering (CAPM Calculations)")
        print(f"{'='*80}")
        phase3_start = time.time()
        
        step3_result = step3_beta_filtering(
            ticker=ticker,
            step2_result=step2_result,
            read_information=read_information,
            market_beta=market_beta,
            risk_free_rate=risk_free_rate
        )
        
        if "error" in step3_result:
            return {
                "status": "error",
                "ticker": ticker,
                "error": f"Phase 3 failed: {step3_result['error']}"
            }
        
        phase3_time = time.time() - phase3_start
        print(f"✅ Phase 3 complete in {phase3_time:.2f} seconds")
        
        # =================================================================
        # PHASE 4: Calculate Impact Metrics (Math - No LLM)
        # =================================================================
        print(f"\n{'='*80}")
        print(f"📊 PHASE 4: Calculating Impact Metrics")
        print(f"{'='*80}")
        phase4_start = time.time()
        
        step4_result = step4_impact_metrics(step3_result)
        
        if "error" in step4_result:
            return {
                "status": "error",
                "ticker": ticker,
                "error": f"Phase 4 failed: {step4_result['error']}"
            }
        
        phase4_time = time.time() - phase4_start
        print(f"✅ Phase 4 complete in {phase4_time:.2f} seconds")
        
        # =================================================================
        # PHASE 5: Generate 7 Datasets
        # =================================================================
        print(f"\n{'='*80}")
        print(f"📈 PHASE 5: Generating 7 Impact Datasets")
        print(f"{'='*80}")
        phase5_start = time.time()
        
        impact_metrics_result = {
            "ticker": ticker,
            "market_beta": market_beta,
            "risk_free_rate": risk_free_rate,
            "annual_volatility": step3_result.get('annual_volatility', 0),
            "volatility_factor": step3_result.get('volatility_factor', 0),
            "summary_df": step4_result['summary_df']
        }
        
        datasets = generate_7_datasets(impact_metrics_result)
        
        if "error" in datasets:
            return {
                "status": "error",
                "ticker": ticker,
                "error": f"Phase 5 failed: {datasets.get('error', 'Unknown error')}"
            }
        
        phase5_time = time.time() - phase5_start
        print(f"✅ Phase 5 complete in {phase5_time:.2f} seconds")
        
        # =================================================================
        # COMPLETION
        # =================================================================
        total_time = time.time() - start_time
        
        meta_info = {
            "ticker": ticker,
            "status": "success",
            "calculated_beta": market_beta,
            "beta_correlation": correlation,
            "beta_calculation_days": len(merged),
            "risk_free_rate": risk_free_rate,
            "total_periods": len(step4_result['summary_df']),
            "annual_volatility": step3_result.get('annual_volatility', 0),
            "volatility_factor": step3_result.get('volatility_factor', 0),
            "generated_date": datetime.now().isoformat(),
            "data_source": "oil_impact_metrics_existing_trends",
            "timing": {
                "phase0_beta_calculation": phase0_time,
                "phase1_factor_extraction": phase1_time,
                "phase2_date_mapping": phase2_time,
                "phase3_beta_filtering": phase3_time,
                "phase4_impact_metrics": phase4_time,
                "phase5_datasets": phase5_time,
                "total": total_time
            }
        }
        
        print(f"\n{'='*100}")
        print(f"✅ OIL IMPACT ANALYSIS COMPLETED!")
        print(f"{'='*100}")
        print(f"📈 Calculated Beta: {market_beta:.4f} (correlation: {correlation:.4f})")
        print(f"⏱️ Total Time: {total_time:.2f} seconds")
        print(f"   Phase 0 (Beta Calculation): {phase0_time:.2f}s")
        print(f"   Phase 1 (Factor Extraction - LLM): {phase1_time:.2f}s")
        print(f"   Phase 2 (Date Mapping - LLM): {phase2_time:.2f}s")
        print(f"   Phase 3 (Beta Filtering): {phase3_time:.2f}s")
        print(f"   Phase 4 (Impact Metrics): {phase4_time:.2f}s")
        print(f"   Phase 5 (Generate Datasets): {phase5_time:.2f}s")
        print(f"\n📊 Risk Environment: {datasets['risk_share_index']['risk_environment']}")
        print(f"{'='*100}\n")
        
        return {
            "status": "success",
            "ticker": ticker,
            "meta_info": meta_info,
            "datasets": datasets,
            "summary_df": step4_result['summary_df'],
            "factor_time_df": factor_time_df  # Shows all factor-date mappings
        }
        
    except Exception as e:
        print(f"\n❌ Error in oil impact analysis: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "ticker": ticker,
            "error": str(e)
        }

