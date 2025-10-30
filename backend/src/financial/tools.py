"""
LangChain Tool Wrappers for Financial Analysis Tools

This module exposes financial analysis tools as LangChain tools for use with LangGraph agents.
"""

from langchain_core.tools import tool
from src.financial.analyzers import (
    analyze_contango_backwardation,
    get_macro_risk_analysis,
    analyze_vix,
    analyze_liquidity
)
from src.financial.DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage


@tool
def contango_backwardation_analysis(sector: str = "oil") -> str:
    """
    Analyze futures price curves to detect market structure (contango vs backwardation).
    
    This tool analyzes commodity futures contracts to identify:
    - Market structure (Contango, Backwardation, or Flat)
    - Price gaps between contract months
    - Trading implications (storage plays, roll yield, arbitrage)
    - Supply/demand imbalances
    
    Args:
        sector: Commodity sector to analyze. Options:
                - "oil" or "crude_oil": Crude Oil futures (CL contracts)
                - "gold": Gold futures (GC contracts)
                - "natural_gas" or "gas": Natural Gas futures (NG contracts)
                - "gasoline" or "rbob": Gasoline futures (RB contracts)
    
    Returns:
        Comprehensive market structure analysis including:
        - Market condition summary
        - Active contract count
        - Price curve analysis
        - Trading implications
    
    Example:
        >>> result = contango_backwardation_analysis("oil")
        >>> # Returns detailed analysis of oil futures curve
    """
    result = analyze_contango_backwardation(sector)
    
    # Convert dict result to formatted string for LLM consumption
    summary = f"""
# Contango/Backwardation Analysis: {sector.upper()}

## Market Summary
{result['summary']}

## Market Structure
- Condition: {result['market_structure']['condition']}
- Interpretation: {result['market_structure']['interpretation']}
- Average Gap: ${result['market_structure']['average_gap']:.2f}
- Max Gap: ${result['market_structure']['max_gap']:.2f}
- Min Gap: ${result['market_structure']['min_gap']:.2f}

## Contract Analysis
- Total Contracts: {result['contract_analysis']['total_contracts']}
- Active Contracts: {result['contract_analysis']['active_contracts']}
- Structure Distribution: {result['contract_analysis']['structure_distribution']}

## Price Curve
- Front Month: {result['price_curve_summary']['front_month']}
- Back Month: {result['price_curve_summary']['back_month']}
- Curve Steepness: {result['price_curve_summary']['curve_steepness']}

## Trading Implications
- Storage Play: {result['trading_implications']['storage_play']}
- Roll Yield: {result['trading_implications']['roll_yield']}
- Arbitrage: {result['trading_implications']['arbitrage']}
"""
    return summary.strip()


@tool
def macro_risk_analysis() -> str:
    """
    Get comprehensive macro economic risk analysis for commodity markets.
    
    This tool retrieves pre-computed macro economic analysis focusing on:
    - US GDP Growth trends and trajectory
    - Unemployment Rate and labor market conditions
    - Inflation levels and impact on commodities
    - Business cycle phase identification
    - Three risk path scenarios for commodity markets
    - Global economic implications
    
    The analysis is updated regularly and stored in a Redis database.
    
    Returns:
        Comprehensive macro analysis text containing economic indicators,
        risk scenarios, and commodity market implications.
        Returns None if data is unavailable.
    
    Example:
        >>> analysis = macro_risk_analysis()
        >>> # Returns detailed macro economic analysis
    """
    analysis = get_macro_risk_analysis()
    
    if analysis is None:
        return "⚠️ Macro risk analysis is currently unavailable. The database may be updating or the service may be temporarily down."
    
    return analysis


@tool
def vix_volatility_analysis(days: int = 5000) -> str:
    """
    Analyze VIX (Volatility Index) to assess market fear and greed levels.
    
    This tool performs comprehensive VIX analysis including:
    - Current VIX level and volatility status (Fear/Greed)
    - Z-score analysis (long-term and short-term sentiment)
    - Historical context (all-time highs, percentiles)
    - Statistical overview (mean, median, standard deviation)
    - Price movement analysis (1-day, 1-week, 1-month changes)
    - Trading implications for options, equity, and portfolio managers
    - Risk factors and mean reversion expectations
    
    The VIX is often called the "fear gauge" and measures expected market volatility.
    
    Args:
        days: Number of days of historical VIX data to analyze (default: 5000)
              Larger values provide better long-term context
    
    Returns:
        Comprehensive VIX analysis report with volatility status,
        z-score analysis, and trading implications.
    
    Example:
        >>> report = vix_volatility_analysis(5000)
        >>> # Returns detailed VIX analysis with market sentiment
    """
    return analyze_vix(days)


@tool
def global_liquidity_monitor(days: int = 180) -> str:
    """
    Monitor global liquidity stress signals to detect funding crises.
    
    This tool analyzes four key global liquidity indicators:
    - DXY (Dollar Index): USD strength and global funding tightness
    - HYG (High Yield ETF): Credit market stress levels
    - XLF (U.S. Banks): Domestic banking sector health
    - IXG (Global Banks): International banking pressure
    
    The tool computes a composite stress score to identify:
    - Pre-Black-Swan risk environments
    - Liquidity tightening phases
    - Stable liquidity conditions
    
    High stress scores indicate potential commodity market vulnerability.
    
    Args:
        days: Number of days of historical data to analyze (default: 180)
              6 months is typically sufficient for liquidity analysis
    
    Returns:
        Comprehensive liquidity analysis report with:
        - Composite stress score
        - Individual indicator z-scores
        - Interpretation of liquidity conditions
        - Trading implications for commodity traders
        - Risk management recommendations
    
    Example:
        >>> report = global_liquidity_monitor(180)
        >>> # Returns global liquidity stress analysis
    """
    return analyze_liquidity(days)


@tool
def oil_metrics_list_available_tickers() -> str:
    """
    List tickers that already have oil metrics stored in Redis.
    
    Output:
        A newline-separated list of ticker keys detected in Redis. These are storage keys
        used by the system (e.g., CLZ25_NYM). They correspond to original Yahoo tickers
        like CLZ25.NYM.
    """
    storage = RedisDatabaseStorage()
    r = storage.redis_client
    base_prefix = "Crude_Oil:Future_Contract:"
    # Detect presence via Queries_DF.csv (canonical merged output)
    keys = r.keys(f"{base_prefix}*:*Queries_DF.csv")
    seen = set()
    for k in keys:
        parts = k.split(":")
        if len(parts) >= 4:
            seen.add(parts[2])
    if not seen:
        return ""
    # Return one per line
    return "\n".join(sorted(seen))


@tool
def oil_metrics_fetch_queries_csv(ticker: str) -> str:
    """
    Fetch the stored Queries DF for a ticker from Redis and return as CSV text.
    
    Args:
        ticker: Yahoo futures ticker (e.g., "CLZ25.NYM").
                This will be mapped to the storage key format used in Redis.
    
    Returns:
        CSV string of the Queries DataFrame. Empty string if not found.
    """
    if not ticker or not isinstance(ticker, str):
        return ""
    storage_key = ticker.replace('.', '_').replace('=', '_')
    key = f"Crude_Oil:Future_Contract:{storage_key}:Queries_DF.csv"
    storage = RedisDatabaseStorage()
    data = storage.redis_client.get(key)
    return data or ""


# Export all tools
__all__ = [
    "contango_backwardation_analysis",
    "macro_risk_analysis",
    "vix_volatility_analysis",
    "global_liquidity_monitor",
    "oil_metrics_list_available_tickers",
    "oil_metrics_fetch_queries_csv",
]

