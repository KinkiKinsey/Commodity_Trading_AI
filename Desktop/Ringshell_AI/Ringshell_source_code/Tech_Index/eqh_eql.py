"""
Equal Highs/Lows (EQH/EQL) Indicator with Textual Analysis for LLM Agents
Usage: 
    from Data_Source.get_price import get_yahoo_data_comprehensive
    df = get_yahoo_data_comprehensive(ticker, days_back)
    result = equal_highs_lows(df)
    graph(result)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def equal_highs_lows(df, threshold=0.01):
    """
    Equal Highs/Lows Detection with Price Position Analysis
    
    Input:
        df: DataFrame with ['date', 'high', 'low', 'close']
        threshold: Price tolerance (default: 0.01 = 1%)
    
    Output:
        Dictionary with textual_analysis
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Detect Equal Highs (EQH)
    eqh_list = []
    for i in range(1, len(df)):
        if abs(df.loc[i, 'high'] - df.loc[i - 1, 'high']) / df.loc[i, 'high'] < threshold:
            eqh_list.append({
                'date': df.loc[i, 'date'],
                'price': df.loc[i, 'high'],
                'type': 'EQH'
            })
    
    # Detect Equal Lows (EQL)
    eql_list = []
    for i in range(1, len(df)):
        if abs(df.loc[i, 'low'] - df.loc[i - 1, 'low']) / df.loc[i, 'low'] < threshold:
            eql_list.append({
                'date': df.loc[i, 'date'],
                'price': df.loc[i, 'low'],
                'type': 'EQL'
            })
    
    # Save to dataframe
    df['EQH'] = np.nan
    df['EQL'] = np.nan
    
    for eqh in eqh_list:
        idx = df[df['date'] == eqh['date']].index
        if len(idx) > 0:
            df.loc[idx[0], 'EQH'] = eqh['price']
    
    for eql in eql_list:
        idx = df[df['date'] == eql['date']].index
        if len(idx) > 0:
            df.loc[idx[0], 'EQL'] = eql['price']
    
    # === STATISTICAL ANALYSIS ===
    
    current_price = df['close'].iloc[-1]
    
    # Calculate average high and low
    lookback_period = 50
    recent_df = df.tail(lookback_period)
    
    avg_high = recent_df['high'].mean()
    avg_low = recent_df['low'].mean()
    avg_range = avg_high - avg_low
    avg_mid = (avg_high + avg_low) / 2
    
    # Price position in range
    if avg_range > 0:
        price_in_range_pct = ((current_price - avg_low) / avg_range * 100)
    else:
        price_in_range_pct = 50
    
    # Distance from averages
    dist_from_avg_high = current_price - avg_high
    dist_from_avg_high_pct = (dist_from_avg_high / avg_high * 100)
    dist_from_avg_low = current_price - avg_low
    dist_from_avg_low_pct = (dist_from_avg_low / avg_low * 100)
    
    # Valuation
    if price_in_range_pct > 70:
        valuation = "EXPENSIVE"
    elif price_in_range_pct < 30:
        valuation = "CHEAP"
    else:
        valuation = "FAIR VALUE"
    
    # Recent EQH/EQL
    recent_period = 30
    cutoff_date = df['date'].iloc[-1] - pd.Timedelta(days=recent_period)
    
    recent_eqh = [eq for eq in eqh_list if eq['date'] >= cutoff_date]
    recent_eql = [eq for eq in eql_list if eq['date'] >= cutoff_date]
    
    # EQH/EQL above and below
    eqh_above = [eq for eq in recent_eqh if eq['price'] > current_price]
    eql_below = [eq for eq in recent_eql if eq['price'] <= current_price]
    
    # Nearest levels
    nearest_eqh_above = min(eqh_above, key=lambda x: x['price'] - current_price) if len(eqh_above) > 0 else None
    nearest_eql_below = max(eql_below, key=lambda x: x['price']) if len(eql_below) > 0 else None
    
    # Average EQH/EQL
    avg_eqh = np.mean([eq['price'] for eq in recent_eqh]) if len(recent_eqh) > 0 else None
    avg_eql = np.mean([eq['price'] for eq in recent_eql]) if len(recent_eql) > 0 else None
    
    # EQ position
    if avg_eqh and avg_eql:
        eq_mid = (avg_eqh + avg_eql) / 2
        eq_range = avg_eqh - avg_eql
        if eq_range > 0:
            eq_position_pct = ((current_price - avg_eql) / eq_range * 100)
        else:
            eq_position_pct = 50
    else:
        eq_mid = None
        eq_position_pct = None
    
    # Balance
    if len(recent_eqh) > len(recent_eql) * 1.5:
        balance = "RESISTANCE HEAVY"
    elif len(recent_eql) > len(recent_eqh) * 1.5:
        balance = "SUPPORT HEAVY"
    else:
        balance = "BALANCED"
    
    # === BUILD TEXTUAL ANALYSIS ===
    
    summary = f"{valuation}. At {price_in_range_pct:.1f}% of range. {len(recent_eqh)} EQH, {len(recent_eql)} EQL."
    
    position_context = f"Current: ${current_price:.2f}. Avg High: ${avg_high:.2f} ({dist_from_avg_high_pct:+.1f}%), Avg Low: ${avg_low:.2f} ({dist_from_avg_low_pct:+.1f}%), Mid: ${avg_mid:.2f}. Position: {price_in_range_pct:.1f}% of {lookback_period}-day range."
    
    valuation_detail = f"{valuation} zone. Price {dist_from_avg_high_pct:+.1f}% from avg high, {dist_from_avg_low_pct:+.1f}% from avg low."
    
    if eq_mid:
        eq_context = f"EQ Levels: Avg EQH ${avg_eqh:.2f}, Avg EQL ${avg_eql:.2f}, Mid ${eq_mid:.2f}. Price at {eq_position_pct:.1f}% of EQ range."
    else:
        eq_context = "Insufficient EQH/EQL detected."
    
    liquidity_situation = f"{len(eqh_above)} EQH above current price (resistance liquidity), {len(eql_below)} EQL below current price (support liquidity)."
    
    balance_desc = f"{len(recent_eqh)} Equal Highs, {len(recent_eql)} Equal Lows in last {recent_period} days. {balance}."
    
    if nearest_eqh_above:
        dist = nearest_eqh_above['price'] - current_price
        dist_pct = (dist / current_price * 100)
        eqh_text = f"${nearest_eqh_above['price']:.2f} (+${dist:.2f}, +{dist_pct:.1f}%)"
    else:
        eqh_text = "None above"
    
    if nearest_eql_below:
        dist = current_price - nearest_eql_below['price']
        dist_pct = (dist / current_price * 100)
        eql_text = f"${nearest_eql_below['price']:.2f} (-${dist:.2f}, -{dist_pct:.1f}%)"
    else:
        eql_text = "None below"
    
    textual = {
        'summary': summary,
        'position_context': position_context,
        'valuation': valuation_detail,
        'eq_levels': eq_context,
        'liquidity_situation': liquidity_situation,
        'balance': balance_desc,
        'nearest_eqh': eqh_text,
        'nearest_eql': eql_text
    }
    
    print("=" * 80)
    print("EQUAL HIGHS/LOWS (EQH/EQL) - PRICE POSITION ANALYSIS")
    print("=" * 80)
    print(f"\n📊 SUMMARY: {textual['summary']}")
    print(f"\n💼 POSITION: {textual['position_context']}")
    print(f"\n💰 VALUATION: {textual['valuation']}")
    print(f"\n📊 EQ LEVELS: {textual['eq_levels']}")
    print(f"\n💧 LIQUIDITY: {textual['liquidity_situation']}")
    print(f"\n⚖️  BALANCE: {textual['balance']}")
    print(f"\n⬆️  Nearest EQH: {textual['nearest_eqh']}")
    print(f"\n⬇️  Nearest EQL: {textual['nearest_eql']}")
    print("=" * 80 + "\n")
    
    textual['_df'] = df
    textual['_eqh_list'] = eqh_list
    textual['_eql_list'] = eql_list
    textual['_threshold'] = threshold
    textual['_avg_high'] = avg_high
    textual['_avg_low'] = avg_low
    
    return textual


def graph(result):
    """Display Equal Highs/Lows chart"""
    df = result['_df']
    eqh_list = result['_eqh_list']
    eql_list = result['_eql_list']
    avg_high = result['_avg_high']
    avg_low = result['_avg_low']
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.plot(df['date'], df['close'], color='black', linewidth=1.5, label='Close Price')
    
    ax.axhline(avg_high, color='red', linestyle=':', alpha=0.5, linewidth=2, label=f'Avg High (${avg_high:.2f})')
    ax.axhline(avg_low, color='green', linestyle=':', alpha=0.5, linewidth=2, label=f'Avg Low (${avg_low:.2f})')
    
    ax.fill_between(df['date'], avg_high, df['high'].max(), color='red', alpha=0.05)
    ax.fill_between(df['date'], avg_low, df['low'].min(), color='green', alpha=0.05)
    
    for eq in eqh_list:
        ax.axhline(eq['price'], color='orange', linestyle='--', alpha=0.6, linewidth=1)
        ax.scatter(eq['date'], eq['price'], color='orange', marker='^', s=100, zorder=5)
    
    for eq in eql_list:
        ax.axhline(eq['price'], color='brown', linestyle='--', alpha=0.6, linewidth=1)
        ax.scatter(eq['date'], eq['price'], color='brown', marker='v', s=100, zorder=5)
    
    if len(eqh_list) > 0:
        ax.scatter([], [], color='orange', marker='^', s=100, label=f'EQH ({len(eqh_list)})')
    if len(eql_list) > 0:
        ax.scatter([], [], color='brown', marker='v', s=100, label=f'EQL ({len(eql_list)})')
    
    ax.set_title("Equal Highs/Lows with Average High/Low")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.legend()
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

