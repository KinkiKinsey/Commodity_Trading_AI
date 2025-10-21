"""
Financial Analysis Tools Interface

Main interface for all financial analysis tools.
"""

from src.financial.analyzers import (
    analyze_contango_backwardation,
    get_macro_risk_analysis,
    analyze_vix,
    analyze_liquidity,
)
from src.financial.indicators import (
    bollinger_strategy,
    equal_highs_lows,
    liquidity_zones as liquidity_zones_indicator,
    ml_moving_average,
    optimal_rsi_strategy,
    rsi_strategy,
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


def ml_moving_average_tool(df, window: int = 50, sigma: float = 10.0, mult: float = 2.0, forecast: int = 0) -> dict:
    """Expose ML moving average indicator."""
    return ml_moving_average(df, window=window, sigma=sigma, mult=mult, forecast=forecast)


def bollinger_tool(df, length: int = 20, mult: float = 2.0) -> dict:
    """Expose Bollinger Bands indicator."""
    return bollinger_strategy(df, length=length, mult=mult)


def rsi_tool(df, length: int = 14, overbought: float = 70.0, oversold: float = 30.0) -> dict:
    """Expose classic RSI strategy."""
    return rsi_strategy(df, length=length, overbought=overbought, oversold=oversold)


def optimal_rsi_tool(
    df,
    optimal_length: int = 200,
    rsi_count: int = 30,
    rsi_min: int = 4,
    ma_length: int = 14,
    smoothing_length: int = 10,
    smoothing_mode: str = "Simple Average",
) -> dict:
    """Expose optimal RSI strategy."""
    return optimal_rsi_strategy(
        df,
        optimal_length=optimal_length,
        rsi_count=rsi_count,
        rsi_min=rsi_min,
        ma_length=ma_length,
        smoothing_length=smoothing_length,
        smoothing_mode=smoothing_mode,
    )


def equal_highs_lows_tool(df, threshold: float = 0.01, lookback: int = 50) -> dict:
    """Expose EQH/EQL liquidity indicator."""
    return equal_highs_lows(df, threshold=threshold, lookback=lookback)


def liquidity_zones_tool(
    df,
    liq_len: int = 7,
    liq_margin: float = 2.3,
    show_buyside: bool = True,
    show_sellside: bool = True,
    show_voids: bool = True,
) -> dict:
    """Expose liquidity zones indicator."""
    return liquidity_zones_indicator(
        df,
        liq_len=liq_len,
        liq_margin=liq_margin,
        show_buyside=show_buyside,
        show_sellside=show_sellside,
        show_voids=show_voids,
    )


__all__ = [
    "contango_backwardation_tool",
    "macro_risk_analysis_tool",
    "vix_analysis_tool",
    "liquidity_monitor_tool",
    "ml_moving_average_tool",
    "bollinger_tool",
    "rsi_tool",
    "optimal_rsi_tool",
    "equal_highs_lows_tool",
    "liquidity_zones_tool",
]
