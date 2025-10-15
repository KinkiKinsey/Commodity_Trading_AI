"""
Oil Factor Metrics API - Simple Wrapper
========================================
Single function to get oil factor metrics with automatic incremental updates.

Usage:
------
from oil_factor_api import get_oil_factors

# Simple call:
impact_df, factor_time_df = await get_oil_factors("CLZ25.NYM")

# With language:
impact_df, factor_time_df = await get_oil_factors("CLZ25.NYM", language="Chinese")

# Force refresh:
impact_df, factor_time_df = await get_oil_factors("CLZ25.NYM", force_refresh=True)

Returns:
--------
- impact_metrics_df: DataFrame with impact metrics (12-20 factors)
- factor_time_df: DataFrame with factor date ranges (60-80 intervals)

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
from typing import Tuple
import pandas as pd
from get_factor_metrics import get_factor_metrics


async def get_oil_factors(
    ticker: str = "CLZ25.NYM",
    language: str = "Chinese",
    force_refresh: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get oil factor impact metrics and time ranges.
    
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
        Tuple[pd.DataFrame, pd.DataFrame]:
            - impact_metrics_df: Impact metrics for each factor
                Columns: factor, scope, trend_count, weighted_mean, 
                        weighted_variance, risk_reward_ratio, etc.
            
            - factor_time_df: Date ranges for each factor
                Columns: factor_name, scope, start_date, end_date, 
                        duration_days, time_interval
    
    Example:
        >>> import asyncio
        >>> impact_df, time_df = asyncio.run(get_oil_factors("CLZ25.NYM"))
        >>> print(f"Factors: {len(impact_df)}")
        >>> print(impact_df.head())
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
    
    # Return clean output
    return impact_metrics_df, factor_time_df


def get_oil_factors_sync(
    ticker: str = "CLZ25.NYM",
    language: str = "Chinese",
    force_refresh: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Synchronous wrapper for get_oil_factors.
    Use this if you're NOT in an async context.
    
    Args:
        ticker (str): Oil futures ticker
        language (str): Output language
        force_refresh (bool): Force regeneration
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (impact_metrics_df, factor_time_df)
    
    Example:
        >>> impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")
    """
    return asyncio.run(get_oil_factors(ticker, language, force_refresh))


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("🚀 Oil Factor Metrics API - Example Usage\n")
    
    # Example 1: Simple call
    print("Example 1: Simple async call")
    print("-"*60)
    impact_df, time_df = asyncio.run(get_oil_factors("CLZ25.NYM"))
    print(f"✅ Got {len(impact_df)} factors and {len(time_df)} time intervals\n")
    
    # Example 2: With parameters
    print("Example 2: With custom parameters")
    print("-"*60)
    impact_df, time_df = get_oil_factors_sync(
        ticker="CLZ25.NYM",
        language="English",
        force_refresh=False
    )
    print(f"✅ Got {len(impact_df)} factors\n")
    
    # Show preview
    print("📊 Impact Metrics Preview:")
    print(impact_df.head())
    
    print("\n📅 Factor Time Preview:")
    print(time_df.head())

