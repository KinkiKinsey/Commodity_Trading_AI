"""
Oil Factor Metrics API - Simple Wrapper
========================================
Single function to get oil factor metrics with automatic incremental updates.

Usage:
------
from oil_factor_api import get_oil_factors

# Simple call:
queries_df = await get_oil_factors("CLZ25.NYM")

# With language:
queries_df = await get_oil_factors("CLZ25.NYM", language="Chinese")

# Force refresh:
queries_df = await get_oil_factors("CLZ25.NYM", force_refresh=True)

Returns:
--------
- queries_df: DataFrame with merged impact metrics, time ranges, and LLM trends
              Contains all factor information in one unified DataFrame

Features:
---------
✅ Smart caching (14-day freshness check)
✅ Automatic incremental updates when stale
✅ LLM-based factor merging
✅ Weighted average updates
✅ Multi-language support (English/Chinese)
✅ WTI + General news combined
"""

import asyncio
import pandas as pd
from .get_factor_metrics import get_factor_metrics
from .create_queries_df import create_queries_df
from DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage


async def get_oil_factors(
    ticker: str = "CLZ25.NYM",
    language: str = "Chinese",
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Get oil factor queries DataFrame with merged impact metrics, time ranges, and LLM trend analysis.
    
    Simple wrapper that handles all complexity internally:
    - Fetches WTI + General news
    - Creates LLM trend analysis
    - Generates impact metrics
    - Auto-updates when cache is stale (>14 days)
    - Merges new data with existing data
    
    Args:
        ticker (str): Oil futures ticker (default: "CLZ25.NYM")
                     Examples: "CLZ25.NYM", "CLH26.NYM", "CL=F"
        
        language (str): Output language (default: "Chinese")
                       Options: "English", "Chinese"
        
        force_refresh (bool): Force regeneration (default: False)
                             True = Bypass cache, generate fresh data
    
    Returns:
        pd.DataFrame: Queries DataFrame containing:
            - All Impact_Metrics columns (factor, scope, trend_count, weighted_mean, 
              weighted_variance, risk_reward_ratio, average_duration, total_duration)
            - All Factor_Time columns (start_date, end_date, duration_days, time_interval)
            - LLM trend columns (driver_type, AI_Reason)
            One row per factor-time range combination
    
    Example:
        >>> import asyncio
        >>> queries_df = await get_oil_factors("CLZ25.NYM")
        >>> print(f"Total queries: {len(queries_df)}")
        >>> print(queries_df.head())
    """
    
    # Call the main function
    result = await get_factor_metrics(
        ticker=ticker,
        language=language,
        force_refresh=force_refresh
    )
    
    # Check status
    if result['status'] != 'success':
        raise Exception(f"Failed to get oil factors: {result.get('error', 'Unknown error')}")
    
    # Extract DataFrames
    impact_metrics_df = result['impact_metrics_df']
    factor_time_df = result['factor_time_df']
    
    # Generate queries_df by merging with LLM trend summary
    storage_key = ticker.replace('.', '_').replace('=', '_')
    redis_client = RedisDatabaseStorage()
    llm_key = f"Crude_Oil:Future_Contract:{storage_key}:LLM_Trend_Analyst_Result"
    llm_trend_json = redis_client.get_json(llm_key)
    
    if llm_trend_json and 'llm_summary' in llm_trend_json:
        queries_df = create_queries_df(
            impact_metrics_df=impact_metrics_df,
            factor_time_df=factor_time_df,
            llm_trend_summary=llm_trend_json
        )
        
        # Store queries_df in Redis (same folder/location as other outputs)
        queries_csv_key = f"Crude_Oil:Future_Contract:{storage_key}:Queries_DF.csv"
        queries_csv_data = queries_df.to_csv(index=False)
        redis_client.redis_client.set(queries_csv_key, queries_csv_data)
        redis_client.redis_client.expire(queries_csv_key, 86400 * 7)  # 7 days expiry
    else:
        queries_df = pd.DataFrame()
    
    # Return only queries_df for simplified API
    return queries_df


def get_oil_factors_sync(
    ticker: str = "CLZ25.NYM",
    language: str = "Chinese",
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Synchronous wrapper for get_oil_factors.
    Use this if you're NOT in an async context.
    
    Args:
        ticker (str): Oil futures ticker
        language (str): Output language
        force_refresh (bool): Force regeneration
    
    Returns:
        pd.DataFrame: Queries DataFrame with merged impact metrics, time ranges, and LLM trends
    
    Example:
        >>> queries_df = get_oil_factors_sync("CLZ25.NYM")
        >>> print(f"Total queries: {len(queries_df)}")
    """
    return asyncio.run(get_oil_factors(ticker, language, force_refresh))


# # =============================================================================
# # EXAMPLE USAGE
# # =============================================================================

#     print("🚀 Oil Factor Metrics API - Example Usage\n")
    
#     # Example 1: Simple call
#     print("Example 1: Simple async call")
#     print("-"*60)
#     queries_df = asyncio.run(get_oil_factors("CLZ25.NYM"))
#     print(f"✅ Got {len(queries_df)} factor-time range queries\n")
    
#     # Example 2: With parameters
#     print("Example 2: With custom parameters")
#     print("-"*60)
#     queries_df = get_oil_factors_sync(
#         ticker="CLZ25.NYM",
#         language="English",
#         force_refresh=False
#     )
#     print(f"✅ Got {len(queries_df)} queries\n")
    
#     # Show preview
#     print("📊 Queries DataFrame Preview:")
#     print(queries_df.head())

