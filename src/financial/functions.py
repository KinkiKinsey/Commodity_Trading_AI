"""
Financial Analysis Tools Interface

Main interface for all financial analysis tools.
"""

from src.financial.analyzers import (
    analyze_contango_backwardation,
    get_macro_risk_analysis,
    analyze_vix,
    analyze_liquidity
)


def contango_backwardation_tool(sector: str = "oil") -> dict:
    """
    Analyze futures price curves for contango/backwardation structure.
    
    Args:
        sector: Commodity sector to analyze
                Options: 'oil', 'crude_oil', 'gold', 'natural_gas', 'gas', 'gasoline', 'rbob'
    
    Returns:
        Dictionary containing:
        - summary: Market condition summary with key metrics
        - market_structure: Condition, interpretation, gap statistics
        - contract_analysis: Contract counts and structure distribution
        - price_curve_summary: Front/back month prices and curve steepness
        - trading_implications: Storage plays, roll yield, arbitrage opportunities
        - _df: Pandas DataFrame with detailed contract data
    
    Example:
        >>> result = contango_backwardation_tool("oil")
        >>> print(result['summary'])
        >>> df = result['_df']
    """
    return analyze_contango_backwardation(sector)


def macro_risk_analysis_tool() -> str:
    """
    Get macro economic risk analysis from Redis database.
    
    Returns:
        Comprehensive macro analysis string containing:
        - US GDP Growth analysis
        - Unemployment Rate trends
        - Inflation impact on commodities
        - Business cycle phase identification
        - Risk scenarios (Path 1, 2, 3)
        - Global commodity market implications
        
    Returns None if data is unavailable.
    
    Example:
        >>> analysis = macro_risk_analysis_tool()
        >>> if analysis:
        >>>     print(analysis)
    """
    return get_macro_risk_analysis()


def vix_analysis_tool(days: int = 5000) -> str:
    """
    Analyze VIX (Volatility Index) with z-score analysis.
    
    Args:
        days: Number of days of historical data to analyze (default: 5000)
    
    Returns:
        Comprehensive VIX analysis report string containing:
        - Current VIX level and volatility status
        - Z-score analysis (long-term and short-term)
        - Statistical overview (mean, median, std dev)
        - Price movement analysis (1-day, 1-week, 1-month)
        - Volatility level thresholds
        - Trading implications for options, equity, and portfolio managers
        - Risk factors
    
    Example:
        >>> report = vix_analysis_tool(5000)
        >>> print(report)
    """
    return analyze_vix(days)


def liquidity_monitor_tool(days: int = 180) -> str:
    """
    Analyze global liquidity stress signals.
    
    Monitors:
    - DXY (Dollar Index): USD strength and global funding tightness
    - HYG (High Yield ETF): Credit market stress levels
    - XLF (U.S. Banks): Domestic banking sector health
    - IXG (Global Banks): International banking pressure
    
    Args:
        days: Number of days of historical data to analyze (default: 180)
    
    Returns:
        Comprehensive liquidity analysis report string containing:
        - Composite stress score
        - Key indicators with z-scores
        - Interpretation of liquidity conditions
        - Trading implications for commodity traders
        - Risk management recommendations
        - Risk factors
    
    Example:
        >>> report = liquidity_monitor_tool(180)
        >>> print(report)
    """
    return analyze_liquidity(days)


__all__ = [
    "contango_backwardation_tool",
    "macro_risk_analysis_tool",
    "vix_analysis_tool",
    "liquidity_monitor_tool"
]

