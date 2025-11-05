"""
Global Liquidity Monitor Module

Analyzes global liquidity stress signals using DXY, HYG, XLF, and IXG.
"""

import pandas as pd
import numpy as np
import datetime
from src.financial.data_sources.get_price import get_yahoo_data


def analyze_liquidity(days: int = 180) -> str:
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
        Comprehensive liquidity analysis report string
    
    Example:
        >>> report = analyze_liquidity(180)
        >>> print(report)
    """
    tickers = {
        "DXY": "DX-Y.NYB",   # Dollar Index
        "HYG": "HYG",        # High-Yield Credit ETF
        "XLF": "XLF",        # U.S. Financial Sector
        "IXG": "IXG"         # Global Financials
    }

    data = {}
    print("📡 Fetching global liquidity indicators from Yahoo Finance...\n")

    for name, symbol in tickers.items():
        try:
            df = get_yahoo_data(symbol, days)
            if df.empty:
                raise ValueError("No data retrieved.")
            # Ensure df is properly structured before calculating returns
            if 'close' not in df.columns:
                raise ValueError(f"No 'close' column found for {symbol}")
            df = df.copy()  # Avoid SettingWithCopyWarning
            df["returns"] = df["close"].pct_change(fill_method=None) * 100
            data[name] = df
            print(f"✅ {name} ({symbol}) data loaded: {len(df)} rows")
        except Exception as e:
            print(f"❌ Failed to load {name}: {e}")
            return f"❌ Error in liquidity monitor: {str(e)}"

    # Compute z-scores and trends
    metrics = {}
    for k, df in data.items():
        last = df["close"].iloc[-1]
        z = (last - df["close"].mean()) / df["close"].std()
        change_7d = (last - df["close"].iloc[-7]) / df["close"].iloc[-7] * 100 if len(df) > 7 else np.nan
        metrics[k] = {"latest": last, "zscore": z, "change_7d": change_7d}

    # Build composite stress score
    # DXY ↑ (stress), HYG ↓, XLF ↓, IXG ↓ → global tightening
    stress_score = (
        (metrics["DXY"]["zscore"] * +1) +
        (metrics["HYG"]["zscore"] * -1) +
        (metrics["XLF"]["zscore"] * -1) +
        (metrics["IXG"]["zscore"] * -1)
    )

    # Interpretation logic
    if stress_score > 3:
        condition = "🚨 Global Liquidity Stress (Pre-Black-Swan Risk)"
        interpretation = (
            "Strong USD and sharp decline in credit & financial sectors suggest global dollar tightening. "
            "Liquidity stress is spreading through credit and banking channels. Commodities vulnerable."
        )
    elif stress_score > 1:
        condition = "⚠️ Liquidity Tightening Phase"
        interpretation = (
            "Moderate liquidity contraction. Dollar gaining, credit spreads widening, "
            "and financial equities under pressure — early warning signs of funding stress."
        )
    else:
        condition = "🟢 Stable Liquidity Environment"
        interpretation = (
            "Dollar stable, credit and financial sectors holding up. "
            "No systemic liquidity stress currently visible."
        )

    # Generate report
    report = f"""
# 🌍 Global Liquidity & Funding Stress Monitor
📅 Date: {datetime.date.today().strftime("%Y-%m-%d")}
📈 Period Analyzed: {days} days

## 🔢 Composite Stress Score: {stress_score:.2f}
**Condition:** {condition}

### 💰 Key Indicators:
| Indicator | Latest | Z-Score | 7D Change (%) | Interpretation |
|------------|--------|----------|----------------|----------------|
| DXY (Dollar Index) | {metrics['DXY']['latest']:.2f} | {metrics['DXY']['zscore']:+.2f} | {metrics['DXY']['change_7d']:+.2f}% | High = USD tightness |
| HYG (High Yield ETF) | {metrics['HYG']['latest']:.2f} | {metrics['HYG']['zscore']:+.2f} | {metrics['HYG']['change_7d']:+.2f}% | Low = Credit stress |
| XLF (U.S. Banks) | {metrics['XLF']['latest']:.2f} | {metrics['XLF']['zscore']:+.2f} | {metrics['XLF']['change_7d']:+.2f}% | Low = Domestic liquidity squeeze |
| IXG (Global Banks) | {metrics['IXG']['latest']:.2f} | {metrics['IXG']['zscore']:+.2f} | {metrics['IXG']['change_7d']:+.2f}% | Low = Global banking pressure |

---

### 🧠 Interpretation:
{interpretation}

### 📈 Simplified Logic:
> If DXY ↑, HYG ↓, XLF ↓, and IXG ↓ → global liquidity is tightening,  
> signaling a **pre-Black-Swan environment** for commodities and risk assets.

### 💼 Trading Implications:

#### For Commodity Traders:
- **Liquidity Environment**: {condition.split(' ', 1)[1] if ' ' in condition else condition}
- **Commodity Risk**: {'High' if stress_score > 1 else 'Moderate' if stress_score > 0 else 'Low'} - {'Commodities vulnerable to liquidity squeeze' if stress_score > 1 else 'Normal commodity market functioning'}
- **Strategy**: {'Defensive positioning' if stress_score > 1 else 'Normal risk management'} recommended

#### For Risk Management:
- **Stress Level**: {stress_score:.2f} (Scale: >3 = Crisis, >1 = Warning, <1 = Normal)
- **Key Risk**: {'Global dollar funding stress' if stress_score > 1 else 'Normal market conditions'}
- **Monitoring**: {'Watch for credit spread widening' if stress_score > 1 else 'Standard market monitoring'}

### ⚠️ Risk Factors:
- **Dollar Strength**: DXY at {metrics['DXY']['latest']:.2f} ({'Elevated' if metrics['DXY']['zscore'] > 1 else 'Normal' if metrics['DXY']['zscore'] > -1 else 'Low'} level)
- **Credit Conditions**: HYG at {metrics['HYG']['latest']:.2f} ({'Stressed' if metrics['HYG']['zscore'] < -1 else 'Normal' if metrics['HYG']['zscore'] > -1 else 'Strong'})
- **Banking Sector**: {'Under pressure' if (metrics['XLF']['zscore'] < -1 or metrics['IXG']['zscore'] < -1) else 'Stable'}
- **Liquidity Risk**: {'High' if stress_score > 2 else 'Moderate' if stress_score > 0 else 'Low'}

---
*Report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Methodology: Composite stress score based on DXY, HYG, XLF, IXG z-scores*
"""
    
    return report

