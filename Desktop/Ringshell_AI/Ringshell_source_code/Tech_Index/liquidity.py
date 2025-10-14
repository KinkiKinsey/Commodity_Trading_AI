"""
Liquidity Zones (Buyside/Sellside) with Textual Analysis for LLM Agents
Usage: 
    from Data_Source.get_price import get_yahoo_data_comprehensive
    df = get_yahoo_data_comprehensive(ticker, days_back)
    result = liquidity_zones(df)
    graph(result)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def liquidity_zones(df, liq_len=7, liq_margin=2.3, show_buyside=True, show_sellside=True, show_voids=True):
    """
    Liquidity Zones Analysis with Textual Output
    
    Input:
        df: DataFrame with ['date', 'open', 'high', 'low', 'close']
        liq_len: Pivot lookback window (default: 7)
        liq_margin: Zone height scaling factor (default: 2.3)
        show_buyside: Show buyside liquidity (default: True)
        show_sellside: Show sellside liquidity (default: True)
        show_voids: Show liquidity voids/gaps (default: True)
    
    Output:
        Dictionary with textual_analysis
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Detect swing highs and lows
    df['swing_high'] = (
        (df['high'] > df['high'].shift(1)) &
        (df['high'] > df['high'].shift(-1))
    ) * df['high']

    df['swing_low'] = (
        (df['low'] < df['low'].shift(1)) &
        (df['low'] < df['low'].shift(-1))
    ) * df['low']

    # Compute ATR for adaptive margin
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                     abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(10).mean()

    # Identify Buyside & Sellside Liquidity Zones
    liquidity_zones = []

    for i in range(liq_len, len(df)):
        atr = df.loc[i, 'atr']
        
        if show_buyside and not np.isnan(df.loc[i, 'swing_high']):
            price = df.loc[i, 'swing_high']
            top = price + liq_margin * atr
            bottom = price
            start = df.loc[i, 'date']
            end = start + pd.Timedelta(days=10)
            liquidity_zones.append({'type': 'buyside', 'start': start, 'end': end, 'top': top, 'bottom': bottom, 'price': price})

        if show_sellside and not np.isnan(df.loc[i, 'swing_low']):
            price = df.loc[i, 'swing_low']
            top = price
            bottom = price - liq_margin * atr
            start = df.loc[i, 'date']
            end = start + pd.Timedelta(days=10)
            liquidity_zones.append({'type': 'sellside', 'start': start, 'end': end, 'top': top, 'bottom': bottom, 'price': price})

    # Liquidity Voids (large gaps)
    voids = []
    if show_voids:
        df['gap_up'] = (df['low'] - df['high'].shift(2)) > df['atr'] * 2
        df['gap_down'] = (df['high'].shift(2) - df['low']) > df['atr'] * 2

        for i in range(2, len(df)):
            if df.loc[i, 'gap_up']:
                voids.append({'start': df.loc[i-2, 'date'], 'end': df.loc[i, 'date'],
                              'top': df.loc[i, 'low'], 'bottom': df.loc[i-2, 'high'], 'type': 'bullish'})
            elif df.loc[i, 'gap_down']:
                voids.append({'start': df.loc[i-2, 'date'], 'end': df.loc[i, 'date'],
                              'top': df.loc[i-2, 'low'], 'bottom': df.loc[i, 'high'], 'type': 'bearish'})

    # === STATISTICAL ANALYSIS ===
    
    current_price = df['close'].iloc[-1]
    current_high = df['high'].iloc[-1]
    current_low = df['low'].iloc[-1]
    current_atr = df['atr'].iloc[-1]
    
    # Find nearest liquidity zones
    buyside_zones = [z for z in liquidity_zones if z['type'] == 'buyside']
    sellside_zones = [z for z in liquidity_zones if z['type'] == 'sellside']
    
    # Calculate distance to each zone
    for zone in buyside_zones:
        zone['distance'] = zone['bottom'] - current_price
        zone['distance_pct'] = (zone['distance'] / current_price * 100)
    
    for zone in sellside_zones:
        zone['distance'] = current_price - zone['top']
        zone['distance_pct'] = (zone['distance'] / current_price * 100)
    
    # Sort by proximity
    buyside_above = [z for z in buyside_zones if z['bottom'] > current_price]
    buyside_below = [z for z in buyside_zones if z['bottom'] <= current_price]
    sellside_below = [z for z in sellside_zones if z['top'] < current_price]
    sellside_above = [z for z in sellside_zones if z['top'] >= current_price]
    
    buyside_above_sorted = sorted(buyside_above, key=lambda x: x['distance'])
    sellside_below_sorted = sorted(sellside_below, key=lambda x: x['distance'])
    
    nearest_buyside = buyside_above_sorted[0] if len(buyside_above_sorted) > 0 else None
    nearest_sellside = sellside_below_sorted[0] if len(sellside_below_sorted) > 0 else None
    
    # Check if price is currently inside a zone (sweeping liquidity)
    in_buyside_zone = any(z['bottom'] <= current_price <= z['top'] for z in buyside_zones)
    in_sellside_zone = any(z['bottom'] <= current_price <= z['top'] for z in sellside_zones)
    
    swept_buyside = [z for z in buyside_below if current_high >= z['bottom']]
    swept_sellside = [z for z in sellside_above if current_low <= z['top']]
    
    # Void analysis
    unfilled_voids_below = [v for v in voids if v['top'] < current_price and v['type'] == 'bullish']
    unfilled_voids_above = [v for v in voids if v['bottom'] > current_price and v['type'] == 'bearish']
    
    nearest_void_below = sorted(unfilled_voids_below, key=lambda x: current_price - x['top'])[0] if len(unfilled_voids_below) > 0 else None
    nearest_void_above = sorted(unfilled_voids_above, key=lambda x: x['bottom'] - current_price)[0] if len(unfilled_voids_above) > 0 else None
    
    # Price action analysis (last 3 candles)
    last_3 = df.tail(3)
    recent_rejection = False
    rejection_type = None
    
    for _, row in last_3.iterrows():
        body_size = abs(row['close'] - row['open'])
        wick_size = row['high'] - max(row['close'], row['open'])
        lower_wick_size = min(row['close'], row['open']) - row['low']
        
        # Upper rejection (bearish)
        if wick_size > body_size * 2:
            recent_rejection = True
            rejection_type = "BEARISH"
        # Lower rejection (bullish)
        elif lower_wick_size > body_size * 2:
            recent_rejection = True
            rejection_type = "BULLISH"
    
    # === BUILD TEXTUAL ANALYSIS ===
    
    # Liquidity Summary
    if in_buyside_zone or len(swept_buyside) > 0:
        if len(swept_buyside) > 0:
            zone = swept_buyside[-1]
            liquidity_status = f"Price ${current_price:.2f} just SWEPT buyside liquidity zone (${zone['bottom']:.2f}–${zone['top']:.2f})."
        else:
            liquidity_status = f"Price ${current_price:.2f} is INSIDE buyside liquidity zone - liquidity sweep in progress."
    elif in_sellside_zone or len(swept_sellside) > 0:
        if len(swept_sellside) > 0:
            zone = swept_sellside[-1]
            liquidity_status = f"Price ${current_price:.2f} just SWEPT sellside liquidity zone (${zone['bottom']:.2f}–${zone['top']:.2f})."
        else:
            liquidity_status = f"Price ${current_price:.2f} is INSIDE sellside liquidity zone - liquidity sweep in progress."
    else:
        liquidity_status = f"Price ${current_price:.2f} not currently interacting with major liquidity zones."
    
    # Nearest zones
    if nearest_buyside:
        nearest_buyside_text = f"Nearest buyside liquidity: ${nearest_buyside['bottom']:.2f}–${nearest_buyside['top']:.2f} ({nearest_buyside['distance']:+.2f}, {nearest_buyside['distance_pct']:+.1f}% away)."
    else:
        nearest_buyside_text = "No buyside liquidity zones above current price."
    
    if nearest_sellside:
        nearest_sellside_text = f"Nearest sellside liquidity: ${nearest_sellside['bottom']:.2f}–${nearest_sellside['top']:.2f} ({nearest_sellside['distance']:+.2f}, {nearest_sellside['distance_pct']:+.1f}% away)."
    else:
        nearest_sellside_text = "No sellside liquidity zones below current price."
    
    # Void analysis
    if nearest_void_below:
        void_below_text = f"Unfilled void below: ${nearest_void_below['bottom']:.2f}–${nearest_void_below['top']:.2f} (bullish gap - pullback target)."
    else:
        void_below_text = "No unfilled voids below current price."
    
    if nearest_void_above:
        void_above_text = f"Unfilled void above: ${nearest_void_above['bottom']:.2f}–${nearest_void_above['top']:.2f} (bearish gap - rally resistance)."
    else:
        void_above_text = "No unfilled voids above current price."
    
    # Rejection analysis
    if recent_rejection:
        rejection_text = f"{rejection_type} rejection candle detected in last 3 periods - potential reversal signal."
    else:
        rejection_text = "No clear rejection patterns in recent price action."
    
    # Zone balance
    total_buyside = len(buyside_zones)
    total_sellside = len(sellside_zones)
    total_voids = len(voids)
    
    zone_balance = f"Total zones: {total_buyside} buyside, {total_sellside} sellside, {total_voids} voids. "
    if total_buyside > total_sellside * 1.3:
        zone_balance += "More buyside zones - bias toward upside liquidity sweep."
    elif total_sellside > total_buyside * 1.3:
        zone_balance += "More sellside zones - bias toward downside liquidity sweep."
    else:
        zone_balance += "Balanced liquidity structure."
    
    # Recommendation
    if (in_buyside_zone or len(swept_buyside) > 0) and recent_rejection and rejection_type == "BEARISH":
        if nearest_sellside:
            recommendation = f"SHORT BIAS: Buyside liquidity swept + bearish rejection. Target sellside liquidity at ${nearest_sellside['bottom']:.2f}–${nearest_sellside['top']:.2f}."
        else:
            recommendation = f"SHORT BIAS: Buyside liquidity swept + bearish rejection. Watch for downside move."
    elif (in_sellside_zone or len(swept_sellside) > 0) and recent_rejection and rejection_type == "BULLISH":
        if nearest_buyside:
            recommendation = f"LONG BIAS: Sellside liquidity swept + bullish rejection. Target buyside liquidity at ${nearest_buyside['bottom']:.2f}–${nearest_buyside['top']:.2f}."
        else:
            recommendation = f"LONG BIAS: Sellside liquidity swept + bullish rejection. Watch for upside move."
    elif nearest_buyside and nearest_buyside['distance'] < current_atr:
        recommendation = f"APPROACHING RESISTANCE: Buyside liquidity nearby (${nearest_buyside['bottom']:.2f}). Watch for rejection or breakout."
    elif nearest_sellside and nearest_sellside['distance'] < current_atr:
        recommendation = f"APPROACHING SUPPORT: Sellside liquidity nearby (${nearest_sellside['bottom']:.2f}). Watch for bounce or breakdown."
    elif len(unfilled_voids_below) > len(unfilled_voids_above):
        recommendation = f"PULLBACK EXPECTED: {len(unfilled_voids_below)} unfilled voids below - price may retrace to fill gaps."
    elif len(unfilled_voids_above) > len(unfilled_voids_below):
        recommendation = f"RALLY RESISTANCE: {len(unfilled_voids_above)} unfilled voids above - gaps may act as resistance."
    else:
        recommendation = f"NEUTRAL: Price between major liquidity zones. Wait for sweep signal."
    
    # Next Action
    if in_buyside_zone or len(swept_buyside) > 0:
        if nearest_sellside:
            next_action = f"Monitor for reversal after buyside sweep. Target: ${nearest_sellside['bottom']:.2f}–${nearest_sellside['top']:.2f}. Stop above ${current_high + current_atr:.2f}."
        else:
            next_action = f"Monitor for reversal. Set stop above recent high ${current_high:.2f}."
    elif in_sellside_zone or len(swept_sellside) > 0:
        if nearest_buyside:
            next_action = f"Monitor for bounce after sellside sweep. Target: ${nearest_buyside['bottom']:.2f}–${nearest_buyside['top']:.2f}. Stop below ${current_low - current_atr:.2f}."
        else:
            next_action = f"Monitor for bounce. Set stop below recent low ${current_low:.2f}."
    elif nearest_buyside and nearest_buyside['distance'] < current_atr * 2:
        next_action = f"Watch price approach buyside liquidity (${nearest_buyside['bottom']:.2f}). Look for rejection = SHORT, breakout = continue LONG."
    elif nearest_sellside and nearest_sellside['distance'] < current_atr * 2:
        next_action = f"Watch price approach sellside liquidity (${nearest_sellside['top']:.2f}). Look for bounce = LONG, breakdown = continue SHORT."
    else:
        next_action = f"Wait for price to approach liquidity zones. Next targets: buyside ${nearest_buyside['bottom']:.2f if nearest_buyside else 'N/A'}, sellside ${nearest_sellside['top']:.2f if nearest_sellside else 'N/A'}."
    
    textual = {
        'summary': liquidity_status,
        'nearest_buyside': nearest_buyside_text,
        'nearest_sellside': nearest_sellside_text,
        'void_below': void_below_text,
        'void_above': void_above_text,
        'rejection_analysis': rejection_text,
        'zone_balance': zone_balance,
        'recommendation': recommendation,
        'next_action': next_action
    }
    
    print("=" * 80)
    print("LIQUIDITY ZONES - ANALYSIS")
    print("=" * 80)
    print(f"\n🔍 LIQUIDITY SUMMARY: {textual['summary']}")
    print(f"\n⬆️  BUYSIDE: {textual['nearest_buyside']}")
    print(f"\n⬇️  SELLSIDE: {textual['nearest_sellside']}")
    print(f"\n📉 VOID BELOW: {textual['void_below']}")
    print(f"\n📈 VOID ABOVE: {textual['void_above']}")
    print(f"\n🕯️  REJECTION: {textual['rejection_analysis']}")
    print(f"\n⚖️  BALANCE: {textual['zone_balance']}")
    print(f"\n🎯 RECOMMENDATION: {textual['recommendation']}")
    print(f"\n👉 NEXT ACTION: {textual['next_action']}")
    print("=" * 80 + "\n")
    
    textual['_df'] = df
    textual['_liquidity_zones'] = liquidity_zones
    textual['_voids'] = voids
    textual['_liq_len'] = liq_len
    textual['_liq_margin'] = liq_margin
    
    return textual


def graph(result):
    """Display Liquidity Zones chart"""
    df = result['_df']
    liquidity_zones = result['_liquidity_zones']
    voids = result['_voids']
    
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_title("Buyside & Sellside Liquidity Zones")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")

    # Candles
    width = 0.4
    for _, row in df.iterrows():
        color = '#00c176' if row['close'] >= row['open'] else '#ff4d4d'
        ax.plot([row['date'], row['date']], [row['low'], row['high']], color='black', linewidth=1)
        ax.add_patch(
            plt.Rectangle(
                (mdates.date2num(row['date']) - width/2, min(row['open'], row['close'])),
                width, abs(row['close'] - row['open']),
                facecolor=color, edgecolor='black', linewidth=0.5
            )
        )

    # Draw Liquidity Zones
    for zone in liquidity_zones:
        color = '#4caf50' if zone['type'] == 'buyside' else '#f23645'
        alpha = 0.2
        ax.fill_between(
            [zone['start'], zone['end']],
            zone['bottom'], zone['top'],
            color=color, alpha=alpha
        )
        ax.text(zone['start'], zone['top'],
                f"{zone['type'].capitalize()}",
                color=color, fontsize=8, va='bottom')

    # Draw Liquidity Voids
    for v in voids:
        color = '#aaffaa' if v['type'] == 'bullish' else '#ffaaaa'
        ax.fill_between([v['start'], v['end']],
                        v['bottom'], v['top'],
                        color=color, alpha=0.3)
        ax.text(v['start'], v['top'], f"{v['type'].capitalize()} Void",
                color=color, fontsize=8, va='bottom')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

