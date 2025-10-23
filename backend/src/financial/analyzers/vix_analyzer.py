"""
VIX (Volatility Index) Analysis Module

Analyzes VIX data with z-score analysis and historical context.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.financial.data_sources.get_price import get_yahoo_data


def _calculate_vix_metrics(df: pd.DataFrame, window: int = 252) -> dict:
    """
    Calculate VIX metrics with z-score analysis.
    
    Args:
        df: DataFrame with VIX price data
        window: Rolling window for calculations (default: 252 trading days)
    
    Returns:
        Dictionary with VIX metrics and analysis
    """
    if df.empty:
        return {}
    
    df_work = df.copy()
    
    # Calculate statistics
    df_work["Mean"] = df_work['close'].mean()
    df_work["Std"] = df_work['close'].std()
    df_work["Rolling_Mean"] = df_work['close'].rolling(window=window).mean()
    df_work["Rolling_Std"] = df_work['close'].rolling(window=window).std()
    
    # Add sigma levels
    for i in range(1, 4):
        df_work[f'+{i}σ'] = df_work["Mean"] + i * df_work["Std"]
        df_work[f'-{i}σ'] = df_work["Mean"] - i * df_work["Std"]
    
    # Get latest values
    df_valid = df_work.dropna(subset=['Rolling_Mean', 'Rolling_Std'])
    
    if df_valid.empty:
        return {}
    
    latest_row = df_valid.iloc[-1]
    current_price = latest_row["close"]
    mean = latest_row["Mean"]
    std = latest_row["Std"]
    rolling_mean = latest_row["Rolling_Mean"]
    rolling_std = latest_row["Rolling_Std"]
    
    # Z-scores
    long_term_z_score = (current_price - mean) / std
    short_term_z_score = (current_price - rolling_mean) / rolling_std
    
    # Sentiment mapping
    def map_z_to_sentiment(z):
        if z >= 5:
            return "Irrational Fear (5σ+)"
        elif z >= 3:
            return "Very Fear (3σ+)"
        elif z >= 2:
            return "Fear (2σ+)"
        elif z >= 1:
            return "Moderate Fear (1σ+)"
        elif z >= 0:
            return "Neutral"
        elif z >= -1:
            return "Moderate Greed (-1σ)"
        elif z >= -2:
            return "Greed (-2σ)"
        elif z >= -3:
            return "Very Greedy (-3σ)"
        else:
            return "Irrational Greed (≤ -5σ)"
    
    long_term_sentiment = map_z_to_sentiment(long_term_z_score)
    short_term_sentiment = map_z_to_sentiment(short_term_z_score)
    
    # Historical highs analysis
    current_date = df['date'].max()
    all_time_high = df['close'].max()
    all_time_high_date = df[df['close'] == all_time_high]['date'].iloc[0]
    days_since_ath = (current_date - all_time_high_date).days
    
    # Recent highs
    one_year_ago = current_date - timedelta(days=365)
    two_years_ago = current_date - timedelta(days=730)
    five_years_ago = current_date - timedelta(days=1825)
    
    high_1y = df[df['date'] >= one_year_ago]['close'].max() if len(df[df['date'] >= one_year_ago]) > 0 else 0
    high_2y = df[df['date'] >= two_years_ago]['close'].max() if len(df[df['date'] >= two_years_ago]) > 0 else 0
    high_5y = df[df['date'] >= five_years_ago]['close'].max() if len(df[df['date'] >= five_years_ago]) > 0 else 0
    
    # Percentiles
    percentiles = {
        '25th': df['close'].quantile(0.25),
        '50th': df['close'].quantile(0.50),
        '75th': df['close'].quantile(0.75),
        '90th': df['close'].quantile(0.90),
        '95th': df['close'].quantile(0.95),
        '99th': df['close'].quantile(0.99)
    }
    
    return {
        'current_vix': current_price,
        'current_date': current_date.strftime('%Y-%m-%d'),
        'z_score_analysis': {
            'long_term_z_score': long_term_z_score,
            'short_term_z_score': short_term_z_score,
            'long_term_sentiment': long_term_sentiment,
            'short_term_sentiment': short_term_sentiment
        },
        'statistics': {
            'mean': mean,
            'std': std,
            'rolling_mean': rolling_mean,
            'rolling_std': rolling_std,
            'min': df['close'].min(),
            'max': df['close'].max(),
            'median': df['close'].median()
        },
        'historical_highs': {
            'all_time_high': {
                'price': all_time_high,
                'date': all_time_high_date.strftime('%Y-%m-%d'),
                'days_ago': days_since_ath
            },
            'high_1y': high_1y,
            'high_2y': high_2y,
            'high_5y': high_5y
        },
        'sigma_levels': {
            '+1σ': latest_row['+1σ'],
            '+2σ': latest_row['+2σ'],
            '+3σ': latest_row['+3σ'],
            '-1σ': latest_row['-1σ'],
            '-2σ': latest_row['-2σ'],
            '-3σ': latest_row['-3σ']
        },
        'percentiles': percentiles
    }


def _generate_vix_report(df: pd.DataFrame, metrics: dict) -> str:
    """Generate comprehensive VIX analysis report."""
    if not metrics:
        return "❌ Unable to generate VIX report - no data available"
    
    current_vix = metrics['current_vix']
    z_analysis = metrics['z_score_analysis']
    stats = metrics['statistics']
    highs = metrics['historical_highs']
    sigma_levels = metrics['sigma_levels']
    percentiles = metrics['percentiles']
    
    # Determine volatility status
    z_score = z_analysis['long_term_z_score']
    sentiment = z_analysis['long_term_sentiment']
    
    if z_score >= 2:
        status_emoji = "🔴"
        volatility_status = "EXTREME FEAR"
    elif z_score >= 1:
        status_emoji = "🟠"
        volatility_status = "FEAR"
    elif z_score >= 0:
        status_emoji = "🔵"
        volatility_status = "NEUTRAL"
    elif z_score >= -1:
        status_emoji = "🟡"
        volatility_status = "GREED"
    else:
        status_emoji = "🟢"
        volatility_status = "EXTREME GREED"
    
    # Calculate price changes
    price_1d = ((current_vix - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100 if len(df) >= 2 else 0
    price_1w = ((current_vix - df['close'].iloc[-6]) / df['close'].iloc[-6]) * 100 if len(df) >= 6 else 0
    price_1m = ((current_vix - df['close'].iloc[-21]) / df['close'].iloc[-21]) * 100 if len(df) >= 21 else 0
    
    report = f"""
# VIX (Volatility Index) Analysis Report

## 📊 Current Market Status
{status_emoji} **Current VIX Level**: {current_vix:.2f} ({volatility_status})
📅 **Analysis Date**: {metrics['current_date']}
📈 **Data Points**: {len(df)} trading days

## 🎯 Z-Score Analysis
**Long-term Z-Score**: {z_analysis['long_term_z_score']:.2f}
**Short-term Z-Score**: {z_analysis['short_term_z_score']:.2f}
**Long-term Sentiment**: {z_analysis['long_term_sentiment']}
**Short-term Sentiment**: {z_analysis['short_term_sentiment']}

## 📊 Statistical Overview
• **Mean VIX**: {stats['mean']:.2f}
• **Median VIX**: {stats['median']:.2f}
• **Standard Deviation**: {stats['std']:.2f}
• **Min VIX**: {stats['min']:.2f}
• **Max VIX**: {stats['max']:.2f}

## 📈 Price Movement Analysis
• **1-Day Change**: {price_1d:+.2f}%
• **1-Week Change**: {price_1w:+.2f}%
• **1-Month Change**: {price_1m:+.2f}%

## 🎯 Volatility Level Thresholds
• **+1σ**: {sigma_levels['+1σ']:.2f} (Moderate Fear)
• **+2σ**: {sigma_levels['+2σ']:.2f} (Fear)
• **+3σ**: {sigma_levels['+3σ']:.2f} (Very Fear)
• **-1σ**: {sigma_levels['-1σ']:.2f} (Moderate Greed)
• **-2σ**: {sigma_levels['-2σ']:.2f} (Greed)
• **-3σ**: {sigma_levels['-3σ']:.2f} (Very Greed)

## 💼 Trading Implications
### For Options Traders:
- **Current Z-Score**: {z_score:.2f}
- **Strategy**: {'Buy premium' if z_score < 0 else 'Sell premium'} based on mean reversion

### For Equity Traders:
- **Sentiment Gauge**: {sentiment}
- **Contrarian Signal**: {'Buy fear' if z_score > 1 else 'Sell greed' if z_score < -1 else 'Neutral positioning'}

### For Portfolio Managers:
- **Risk Assessment**: VIX {z_score:.2f}σ from mean indicates {volatility_status.lower()} environment
- **Hedging Strategy**: {'Increase hedges' if z_score < -1 else 'Reduce hedges' if z_score > 1 else 'Maintain current hedges'}

## ⚠️ Risk Factors
- **Historical Context**: VIX all-time high was {highs['all_time_high']['price']:.2f} ({highs['all_time_high']['days_ago']} days ago)
- **Mean Reversion**: VIX tends to revert to {stats['mean']:.2f} (long-term average)
- **Volatility Clustering**: High VIX periods often persist

---
*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report


def analyze_vix(days: int = 5000) -> str:
    """
    Analyze VIX (Volatility Index) with z-score analysis and historical context.
    
    Args:
        days: Number of days of historical data to analyze (default: 5000)
    
    Returns:
        Comprehensive VIX analysis report string
    
    Example:
        >>> report = analyze_vix(5000)
        >>> print(report)
    """
    try:
        vix_df = get_yahoo_data("^VIX", days)
        
        if vix_df.empty:
            return "❌ Failed to retrieve VIX data"
        
        metrics = _calculate_vix_metrics(vix_df)
        
        if not metrics:
            return "❌ Unable to calculate VIX metrics - insufficient data"
        
        return _generate_vix_report(vix_df, metrics)
        
    except Exception as e:
        return f"❌ Error in VIX analysis: {str(e)}"

