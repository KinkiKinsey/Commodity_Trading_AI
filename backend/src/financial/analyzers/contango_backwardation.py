"""
Contango/Backwardation Analysis Module

Analyzes futures price curves to detect market structure and trading opportunities.
"""

import pandas as pd
import datetime
from src.financial.data_sources.get_price import get_yahoo_data


# Futures month codes (universal standard)
MONTH_CODES = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONTH_MAP = dict(zip(MONTH_CODES, MONTH_NAMES))

# Exchange suffix mapping by commodity
EXCHANGE_SUFFIX_MAP = {
    "CL": ".NYM",   # Crude Oil
    "NG": ".NYM",   # Natural Gas
    "RB": ".NYM",   # Gasoline (RBOB)
    "GC": ".CMX",   # Gold
}

COMMODITY_NAME_MAP = {
    "CL": "Crude Oil",
    "NG": "Natural Gas",
    "RB": "Gasoline (RBOB)",
    "GC": "Gold",
}


def _get_next_contracts(root: str, months_ahead: int = 15) -> list:
    """
    Generate consecutive futures contract tickers.
    
    Args:
        root: Commodity root symbol (e.g., 'CL', 'GC')
        months_ahead: Number of months to generate (default: 15)
    
    Returns:
        List of contract tickers (e.g., ['CLZ25.NYM', 'CLF26.NYM', ...])
    """
    today = datetime.date.today()
    year = today.year
    month = today.month

    suffix = EXCHANGE_SUFFIX_MAP.get(root, "")
    contracts = []
    
    for i in range(months_ahead):
        m = (month + i - 1) % 12
        y = year + (month + i - 1) // 12
        month_code = MONTH_CODES[m]
        ticker = f"{root}{month_code}{str(y)[-2:]}{suffix}"
        contracts.append(ticker)
    
    return contracts


def analyze_contango_backwardation(sector: str = "oil") -> dict:
    """
    Analyze futures price curve for contango/backwardation structure.
    
    Args:
        sector: Commodity sector to analyze
                Options: 'oil', 'crude_oil', 'gold', 'natural_gas', 'gas', 'gasoline', 'rbob'
    
    Returns:
        Dictionary containing:
        - summary: Market condition summary
        - market_structure: Condition, interpretation, gap statistics
        - contract_analysis: Contract counts and structure distribution
        - price_curve_summary: Front/back month prices and curve steepness
        - trading_implications: Storage plays, roll yield, arbitrage opportunities
        - _df: Pandas DataFrame with detailed contract data
    
    Example:
        >>> result = analyze_contango_backwardation("oil")
        >>> print(result['summary'])
        >>> df = result['_df']
    """
    # Map sector to commodity root
    sector = sector.lower()
    if sector in ["oil", "crude_oil"]:
        root = "CL"
    elif sector == "gold":
        root = "GC"
    elif sector in ["natural_gas", "natgas", "gas"]:
        root = "NG"
    elif sector in ["gasoline", "rbob"]:
        root = "RB"
    else:
        raise ValueError("Sector must be one of: 'oil', 'gold', 'natural_gas', 'gasoline'")

    commodity_name = COMMODITY_NAME_MAP[root]
    contract_list = _get_next_contracts(root)

    # Fetch price data for all contracts
    prices = []
    active_contracts = 0

    for ticker in contract_list:
        try:
            df = get_yahoo_data(ticker, days=30)
            if not df.empty:
                last_price = df['close'].iloc[-1]
                last_date = df['date'].iloc[-1]
                prices.append({
                    "contract": ticker,
                    "price": last_price,
                    "last_update": last_date,
                    "status": "active"
                })
                active_contracts += 1
            else:
                prices.append({
                    "contract": ticker,
                    "price": None,
                    "last_update": None,
                    "status": "no_data"
                })
        except Exception as e:
            prices.append({
                "contract": ticker,
                "price": None,
                "last_update": None,
                "status": f"error: {str(e)[:25]}"
            })

    df_curve = pd.DataFrame(prices)

    # Compute price gaps and structure
    df_curve['next_price'] = df_curve['price'].shift(-1)
    df_curve['price_gap'] = df_curve['next_price'] - df_curve['price']
    df_curve['gap_pct'] = (df_curve['price_gap'] / df_curve['price'] * 100).round(2)
    df_curve['structure'] = df_curve['price_gap'].apply(
        lambda x: 'Contango' if x and x > 0 else ('Backwardation' if x and x < 0 else 'Flat')
    )
    df_curve['month'] = df_curve['contract'].str[2:3]
    df_curve['month_name'] = df_curve['month'].map(MONTH_MAP)

    # Calculate metrics
    valid_gaps = df_curve['price_gap'].dropna()
    if len(valid_gaps) > 0:
        avg_gap = valid_gaps.mean()
        max_gap = valid_gaps.max()
        min_gap = valid_gaps.min()
        structure_counts = df_curve['structure'].value_counts().to_dict()
    else:
        avg_gap = max_gap = min_gap = 0
        structure_counts = {}

    # Determine market condition
    if avg_gap > 0.5:
        market_condition = "CONTANGO"
        interpretation = f"Future prices are ${avg_gap:.2f} higher than spot → storage cost or surplus expected."
    elif avg_gap < -0.5:
        market_condition = "BACKWARDATION"
        interpretation = f"Future prices are ${abs(avg_gap):.2f} lower than spot → short-term tightness or demand pressure."
    else:
        market_condition = "FLAT/CONTANGO"
        interpretation = f"Minimal price gaps (${avg_gap:.2f}) → balanced supply-demand environment."

    # Build structured result
    return {
        "summary": f"{commodity_name} futures curve shows {market_condition} with {active_contracts} active contracts. Average gap: ${avg_gap:.2f}.",
        "market_structure": {
            "condition": market_condition,
            "interpretation": interpretation,
            "average_gap": float(avg_gap),
            "max_gap": float(max_gap),
            "min_gap": float(min_gap)
        },
        "contract_analysis": {
            "total_contracts": len(contract_list),
            "active_contracts": active_contracts,
            "structure_distribution": structure_counts
        },
        "price_curve_summary": {
            "front_month": f"{df_curve.iloc[0]['contract']} @ ${df_curve.iloc[0]['price']:.2f}" if df_curve.iloc[0]['price'] else "No data",
            "back_month": f"{df_curve.iloc[-1]['contract']} @ ${df_curve.iloc[-1]['price']:.2f}" if df_curve.iloc[-1]['price'] else "No data",
            "curve_steepness": f"${max_gap:.2f} spread (front → back)" if max_gap else "No spread data"
        },
        "trading_implications": {
            "storage_play": "Favorable for storage" if avg_gap > 1.0 else "Limited storage opportunity",
            "roll_yield": "Negative roll yield expected" if avg_gap > 0 else "Positive roll yield possible",
            "arbitrage": "Potential arbitrage plays" if max_gap > 2.0 else "Limited arbitrage potential"
        },
        "_df": df_curve[['contract', 'price', 'price_gap', 'structure', 'month_name']].copy()
    }

