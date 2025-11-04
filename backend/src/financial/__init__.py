"""
Financial Analysis Tools Package

Provides comprehensive financial analysis tools for commodity trading and risk assessment.
"""

# Analyzers (direct functions)
from src.financial.analyzers import (
    analyze_contango_backwardation,
    get_macro_risk_analysis,
    analyze_vix,
    analyze_liquidity
)

# LangChain tool interface (for LangGraph agents)
from src.financial.tools import (
    contango_backwardation_analysis,
    macro_risk_analysis,
    vix_volatility_analysis,
    global_liquidity_monitor
)

__all__ = [
    # Analyzer functions
    "analyze_contango_backwardation",
    "get_macro_risk_analysis",
    "analyze_vix",
    "analyze_liquidity",
    # LangChain tools
    "contango_backwardation_analysis",
    "macro_risk_analysis",
    "vix_volatility_analysis",
    "global_liquidity_monitor"
]

__version__ = "1.0.0"

