"""
RSI Strategy with Textual Analysis for LLM Agents
Usage: 
    from Data_Source.get_price import get_yahoo_data_comprehensive
    df = get_yahoo_data_comprehensive(ticker, days_back)
    result = rsi_strategy(df)
    graph(result)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def rsi_strategy(df, length=14, overbought=70, oversold=30):
    """
    RSI Strategy with Textual Output + Trend Structure Analysis for LLM Agents
    
    Input:
        df: DataFrame with ['date','open','high','low','close']
        length: RSI period (default: 14)
        overbought: RSI upper threshold (default: 70)
        oversold: RSI lower threshold (default: 30)
    
    Output:
        Dictionary with textual_analysis including trend structure
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # === Compute RSI ===
    delta = df['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(length).mean()
    avg_loss = pd.Series(loss).rolling(length).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # === Generate Signals ===
    df['buy_signal'] = (df['rsi'] > oversold) & (df['rsi'].shift(1) <= oversold)
    df['sell_signal'] = (df['rsi'] < overbought) & (df['rsi'].shift(1) >= overbought)

    # === Simulate Positions ===
    df['position'] = 0
    position = 0
    for i in range(len(df)):
        if df.loc[i, 'buy_signal']:
            position = 1
        elif df.loc[i, 'sell_signal']:
            position = -1
        df.loc[i, 'position'] = position

    # === Strategy Returns ===
    df['return'] = df['close'].pct_change() * df['position']
    df['equity'] = (1 + df['return'].fillna(0)).cumprod()

    # === Calculate Key Metrics ===
    current_price = df['close'].iloc[-1]
    current_rsi = df['rsi'].iloc[-1]
    current_position = int(df['position'].iloc[-1])
    
    rsi_mean = df['rsi'].mean()
    rsi_std = df['rsi'].std()
    rsi_zscore = (current_rsi - rsi_mean) / rsi_std if rsi_std > 0 else 0
    rsi_percentile = (df['rsi'] < current_rsi).sum() / len(df) * 100
    
    in_overbought = current_rsi > overbought
    in_oversold = current_rsi < oversold
    zone = 'overbought' if in_overbought else ('oversold' if in_oversold else 'neutral')
    
    distance_to_overbought = overbought - current_rsi
    distance_to_oversold = current_rsi - oversold
    
    rsi_change_5d = current_rsi - df['rsi'].iloc[-6] if len(df) > 5 else 0
    rsi_trend = 'rising' if rsi_change_5d > 2 else ('falling' if rsi_change_5d < -2 else 'flat')
    
    buy_signals = df[df['buy_signal']]
    sell_signals = df[df['sell_signal']]
    avg_rsi_at_buy = buy_signals['rsi'].mean() if len(buy_signals) > 0 else None
    avg_rsi_at_sell = sell_signals['rsi'].mean() if len(sell_signals) > 0 else None
    
    # === TREND STRUCTURE ANALYSIS ===
    if current_position == 1:
        current_phase = "BULLISH"
        opposite_signals = sell_signals
        same_signals = buy_signals
    elif current_position == -1:
        current_phase = "BEARISH"
        opposite_signals = buy_signals
        same_signals = sell_signals
    else:
        current_phase = "NEUTRAL"
        opposite_signals = pd.DataFrame()
        same_signals = pd.DataFrame()
    
    last_buy = buy_signals.iloc[-1] if len(buy_signals) > 0 else None
    last_sell = sell_signals.iloc[-1] if len(sell_signals) > 0 else None
    
    if last_buy is not None and last_sell is not None:
        if buy_signals.index[-1] > sell_signals.index[-1]:
            last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'buy', last_buy['date'], last_buy['close'], last_buy['rsi']
            previous_signal, previous_signal_date, previous_signal_price = 'sell', last_sell['date'], last_sell['close']
        else:
            last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'sell', last_sell['date'], last_sell['close'], last_sell['rsi']
            previous_signal, previous_signal_date, previous_signal_price = 'buy', last_buy['date'], last_buy['close']
        days_since = (df['date'].iloc[-1] - last_signal_date).days
        days_prev_trend = (last_signal_date - previous_signal_date).days
    elif last_buy is not None:
        last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'buy', last_buy['date'], last_buy['close'], last_buy['rsi']
        days_since = (df['date'].iloc[-1] - last_signal_date).days
        previous_signal, previous_signal_date, previous_signal_price, days_prev_trend = None, None, None, None
    elif last_sell is not None:
        last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'sell', last_sell['date'], last_sell['close'], last_sell['rsi']
        days_since = (df['date'].iloc[-1] - last_signal_date).days
        previous_signal, previous_signal_date, previous_signal_price, days_prev_trend = None, None, None, None
    else:
        last_signal, last_signal_date, last_signal_price, last_signal_rsi, days_since = None, None, None, None, None
        previous_signal, previous_signal_date, previous_signal_price, days_prev_trend = None, None, None, None
    
    if last_signal and days_since is not None:
        rsi_change_since_signal = current_rsi - last_signal_rsi
        rsi_momentum_per_day = rsi_change_since_signal / days_since if days_since > 0 else 0
        price_change_since_signal = ((current_price - last_signal_price) / last_signal_price * 100) if last_signal_price else 0
        trend_strength = "STRONG" if abs(rsi_momentum_per_day) > 2 else ("MODERATE" if abs(rsi_momentum_per_day) > 1 else "WEAK")
    else:
        rsi_change_since_signal, rsi_momentum_per_day, price_change_since_signal, trend_strength = 0, 0, 0, "UNKNOWN"
    
    if previous_signal and days_prev_trend:
        if days_prev_trend > 30:
            structure_status, structure_desc = "MAJOR BREAK", f"Breaking {days_prev_trend}-day {previous_signal.upper()} trend"
        elif days_prev_trend > 14:
            structure_status, structure_desc = "MODERATE BREAK", f"Breaking {days_prev_trend}-day {previous_signal.upper()} trend"
        else:
            structure_status, structure_desc = "MINOR BREAK", f"Breaking {days_prev_trend}-day {previous_signal.upper()} trend"
    else:
        structure_status, structure_desc = "NO BREAK", "Continuing current trend or no prior signals"
    
    if last_signal and days_since:
        if days_since >= 7:
            confirmation_status, confirmation_desc = "CONFIRMED", f"Trend confirmed ({days_since} days since {last_signal.upper()} signal)"
        elif days_since >= 3:
            confirmation_status, confirmation_desc = "DEVELOPING", f"Trend developing ({days_since} days, needs {7-days_since} more for confirmation)"
        else:
            confirmation_status, confirmation_desc = "EARLY", f"Early stage ({days_since} days, needs {7-days_since} more for confirmation)"
    else:
        confirmation_status, confirmation_desc = "NONE", "No active trend"
    
    all_signals_list = []
    for _, row in buy_signals.iterrows():
        all_signals_list.append({'date': row['date'], 'type': 'BUY', 'price': row['close'], 'rsi': row['rsi']})
    for _, row in sell_signals.iterrows():
        all_signals_list.append({'date': row['date'], 'type': 'SELL', 'price': row['close'], 'rsi': row['rsi']})
    all_signals_list.sort(key=lambda x: x['date'])
    
    if len(all_signals_list) >= 3:
        last_3 = all_signals_list[-3:]
        pattern_desc = " → ".join([s['type'] for s in last_3])
        if len(last_3) >= 2 and last_3[-2]['type'] == 'BUY' and last_3[-1]['type'] == 'SELL':
            last_trade_return = ((last_3[-1]['price'] - last_3[-2]['price']) / last_3[-2]['price'] * 100)
            last_trade_result = "WIN" if last_trade_return > 0 else "LOSS"
            pattern_context = f"Last 3 signals: {pattern_desc}. Last completed trade: {last_trade_result} ({last_trade_return:+.1f}%)"
        else:
            pattern_context = f"Last 3 signals: {pattern_desc}. Current signal still open"
    else:
        pattern_context = f"Only {len(all_signals_list)} signals in history - insufficient for pattern analysis"
    
    total_trades = len(buy_signals) + len(sell_signals)
    winning_trades = (df['return'] > 0).sum()
    losing_trades = (df['return'] < 0).sum()
    win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
    total_return = (df['equity'].iloc[-1] - 1) * 100
    max_trade_return = df['return'].max() * 100 if len(df['return']) > 0 else 0
    returns = df['return'].dropna()
    sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    # BUILD TEXTUAL ANALYSIS
    position_text = "LONG" if current_position == 1 else ("SHORT" if current_position == -1 else "NEUTRAL")
    
    if last_signal and last_signal_price:
        pnl = ((current_price - last_signal_price) / last_signal_price * 100)
        position_context = f"Currently {position_text}. Last signal was {last_signal.upper()} {days_since} days ago at ${last_signal_price:.2f}. Current price ${current_price:.2f} = {pnl:+.1f}% from signal."
    else:
        position_context = f"Currently {position_text}. No recent signals generated."
    
    if last_signal and days_since and previous_signal and days_prev_trend:
        trend_structure = f"{structure_desc}. Previous {previous_signal.upper()} phase lasted {days_prev_trend} days. "
        trend_structure += f"Current {last_signal.upper()} phase is {days_since} days old ({confirmation_status}). "
        trend_structure += f"RSI momentum: {rsi_momentum_per_day:+.2f} points/day ({trend_strength} momentum). "
        trend_structure += f"RSI has moved {rsi_change_since_signal:+.1f} points since signal (from {last_signal_rsi:.1f} to {current_rsi:.1f}). "
        if structure_status in ["MAJOR BREAK", "MODERATE BREAK"]:
            trend_structure += f"⚠️ This is a {structure_status} - significant trend reversal after extended {previous_signal} period."
        elif confirmation_status == "EARLY":
            trend_structure += f"⚠️ Trend still in early stage - watch for continuation or reversal in next few days."
    elif last_signal and days_since:
        trend_structure = f"Current {last_signal.upper()} signal appeared {days_since} days ago. {confirmation_desc}. RSI momentum: {rsi_momentum_per_day:+.2f} points/day ({trend_strength})."
    else:
        trend_structure = "No active trend detected. Market in consolidation phase."
    
    rsi_context = f"RSI at {current_rsi:.1f} ({zone}), {rsi_zscore:+.2f} standard deviations from mean of {rsi_mean:.1f}. "
    rsi_context += f"This is in the {rsi_percentile:.0f}th percentile of historical RSI values. "
    rsi_context += f"RSI has {rsi_trend} over last 5 days ({rsi_change_5d:+.1f} points)."
    
    if avg_rsi_at_buy and avg_rsi_at_sell:
        reversal_text = f"Historical patterns show buy signals typically trigger at RSI {avg_rsi_at_buy:.1f}, "
        reversal_text += f"while sell signals occur at RSI {avg_rsi_at_sell:.1f}. "
        reversal_text += f"Current RSI is {abs(current_rsi - avg_rsi_at_buy):.1f} points from typical buy zone, "
        reversal_text += f"{abs(avg_rsi_at_sell - current_rsi):.1f} points from typical sell zone."
    else:
        reversal_text = "Insufficient signal history to determine typical reversal levels."
    
    vol_label = "LOW" if rsi_std < 10 else ("HIGH" if rsi_std > 15 else "MODERATE")
    volatility_text = f"RSI standard deviation is {rsi_std:.2f}, indicating {vol_label} volatility "
    volatility_text += "(tight range)." if rsi_std < 10 else ("(wide swings)." if rsi_std > 15 else ".")
    
    volatility_text += f" Current Z-score of {rsi_zscore:.2f} shows RSI is "
    if abs(rsi_zscore) > 2:
        volatility_text += "at EXTREME levels (>2 STD from mean)."
    elif abs(rsi_zscore) > 1:
        volatility_text += "ELEVATED but within 2 standard deviations."
    else:
        volatility_text += "within NORMAL range (±1 STD)."
    
    perf_label = "STRONG" if win_rate > 60 else ("GOOD" if win_rate > 50 else ("MODERATE" if win_rate > 40 else "WEAK"))
    risk_text = f"Strategy shows {perf_label} performance: {win_rate:.1f}% win rate over {total_trades} trades. "
    risk_text += f"Total return: {total_return:+.1f}%, Max single trade: {max_trade_return:+.1f}%, Sharpe: {sharpe_ratio:.2f}."
    
    if in_oversold and rsi_trend == 'rising' and structure_status in ["MAJOR BREAK", "MODERATE BREAK"]:
        recommendation = f"STRONG BUY: RSI oversold and rising + {structure_status} after {days_prev_trend}-day downtrend. High probability reversal forming."
    elif in_oversold and rsi_trend == 'rising':
        recommendation = f"BUY SIGNAL: RSI oversold and rising. Potential bounce opportunity. RSI needs to cross above {oversold} to confirm."
    elif in_overbought and rsi_trend == 'falling' and structure_status in ["MAJOR BREAK", "MODERATE BREAK"]:
        recommendation = f"STRONG SELL: RSI overbought and falling + {structure_status} after {days_prev_trend}-day uptrend. High probability reversal forming."
    elif in_overbought and rsi_trend == 'falling':
        recommendation = f"SELL SIGNAL: RSI overbought and falling. Consider taking profits or shorting."
    elif confirmation_status == "EARLY" and trend_strength == "WEAK":
        recommendation = f"CAUTION: {last_signal.upper()} signal only {days_since} days old with WEAK momentum ({rsi_momentum_per_day:+.2f} pts/day). Trend fragile - needs confirmation."
    elif confirmation_status == "DEVELOPING" and trend_strength in ["MODERATE", "STRONG"]:
        recommendation = f"HOLD: {last_signal.upper()} trend developing with {trend_strength} momentum. {7-days_since} more days needed for full confirmation."
    elif confirmation_status == "CONFIRMED":
        recommendation = f"TREND CONFIRMED: {last_signal.upper()} trend confirmed ({days_since} days). Ride the momentum but watch for reversal signals."
    elif zone == 'neutral' and current_rsi > 55 and rsi_trend == 'rising':
        recommendation = f"NEUTRAL-BULLISH: RSI trending up. Monitor for break above {overbought} or pullback to {oversold}."
    elif zone == 'neutral' and current_rsi < 45 and rsi_trend == 'falling':
        recommendation = f"NEUTRAL-BEARISH: RSI trending down. Watch for break below {oversold} or bounce to {overbought}."
    else:
        recommendation = f"WAIT: RSI in middle range with no clear setup. Distance to oversold: {distance_to_oversold:.1f} points, to overbought: {distance_to_overbought:.1f} points."
    
    if last_signal and confirmation_status == "EARLY":
        next_action = f"Monitor {last_signal.upper()} position closely. Set stop-loss at entry ±3%. Needs {7-days_since} more days above/below thresholds for confirmation. Watch for RSI reversal back to {oversold if last_signal == 'buy' else overbought} indicating failed breakout."
    else:
        next_action = f"Watch for RSI to cross below {oversold} (currently {distance_to_oversold:.1f} points away) for BUY signal, or above {overbought} (currently {distance_to_overbought:.1f} points away) for SELL signal."
    
    textual = {
        'summary': f"RSI at {current_rsi:.1f} ({zone}), {rsi_zscore:+.1f} STD. {trend_strength} {rsi_trend} momentum. {confirmation_status} trend.",
        'position_context': position_context,
        'trend_structure': trend_structure,
        'pattern_context': pattern_context,
        'rsi_interpretation': rsi_context,
        'reversal_analysis': reversal_text,
        'volatility_assessment': volatility_text,
        'risk_metrics': risk_text,
        'recommendation': recommendation,
        'next_action': next_action
    }
    
    print("=" * 80)
    print("RSI STRATEGY - ANALYSIS WITH TREND STRUCTURE")
    print("=" * 80)
    print(f"\n📊 SUMMARY: {textual['summary']}")
    print(f"\n💼 POSITION: {textual['position_context']}")
    print(f"\n🔄 TREND STRUCTURE: {textual['trend_structure']}")
    print(f"\n📋 PATTERN: {textual['pattern_context']}")
    print(f"\n📈 RSI: {textual['rsi_interpretation']}")
    print(f"\n🎯 REVERSALS: {textual['reversal_analysis']}")
    print(f"\n📉 VOLATILITY: {textual['volatility_assessment']}")
    print(f"\n💰 PERFORMANCE: {textual['risk_metrics']}")
    print(f"\n🎯 RECOMMENDATION: {textual['recommendation']}")
    print(f"\n👉 NEXT ACTION: {textual['next_action']}")
    print("=" * 80 + "\n")
    
    textual['_df'] = df
    textual['_overbought'] = overbought
    textual['_oversold'] = oversold
    
    return textual


def graph(result):
    """Display RSI strategy graphs"""
    df = result['_df']
    overbought = result['_overbought']
    oversold = result['_oversold']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13,8), sharex=True, gridspec_kw={'height_ratios':[3,1]})
    
    ax1.plot(df['date'], df['close'], label='Close', color='black')
    ax1.scatter(df.loc[df['buy_signal'], 'date'], df.loc[df['buy_signal'], 'close'],
                marker='^', color='lime', s=100, label='Buy Signal')
    ax1.scatter(df.loc[df['sell_signal'], 'date'], df.loc[df['sell_signal'], 'close'],
                marker='v', color='magenta', s=100, label='Sell Signal')
    ax1.set_title('RSI Strategy')
    ax1.set_ylabel('Price')
    ax1.legend()

    ax2.plot(df['date'], df['rsi'], label='RSI', color='blue')
    ax2.axhline(overbought, color='red', linestyle='--', linewidth=1, label=f'Overbought ({overbought})')
    ax2.axhline(oversold, color='green', linestyle='--', linewidth=1, label=f'Oversold ({oversold})')
    ax2.fill_between(df['date'], overbought, oversold, color='gray', alpha=0.1)
    ax2.set_ylabel('RSI')
    ax2.set_xlabel('Date')
    ax2.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(10,4))
    plt.plot(df['date'], df['equity'], color='red', linewidth=2)
    plt.title('RSI Strategy Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Equity (relative)')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
