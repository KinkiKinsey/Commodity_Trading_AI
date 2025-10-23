"""
Financial Analysis Tools Package

Provides comprehensive financial analysis tools for commodity trading and risk assessment.
"""

# Standard Python function interface

# from src.financial.functions import (
#     contango_backwardation_tool,
#     macro_risk_analysis_tool,
#     vix_analysis_tool,
#     liquidity_monitor_tool
# )

# LangChain tool interface (for LangGraph agents)
from src.financial.tools import (
    contango_backwardation_analysis,
    macro_risk_analysis,
    vix_volatility_analysis,
    global_liquidity_monitor,
    oil_factor_analysis
)

__all__ = [
    # Standard functions
    "contango_backwardation_tool",
    "macro_risk_analysis_tool",
    "vix_analysis_tool",
    "liquidity_monitor_tool",
    # LangChain tools
    "contango_backwardation_analysis",
    "macro_risk_analysis",
    "vix_volatility_analysis",
    "global_liquidity_monitor",
    "oil_factor_analysis"

]

__version__ = "1.0.0"

