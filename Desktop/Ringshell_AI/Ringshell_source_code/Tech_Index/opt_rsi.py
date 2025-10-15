"""
Optimal RSI Strategy with ML and Textual Analysis for LLM Agents
Usage: 
    from Data_Source.get_price import get_yahoo_data_comprehensive
    df = get_yahoo_data_comprehensive(ticker, days_back)
    result = optimal_rsi_strategy(df)
    graph(result)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def pine_sma(series, length):
    return pd.Series(series).rolling(length).mean()


def pine_rma(series, length):
    if length > len(series):
        return np.array([np.nan] * len(series))
    alpha = 1 / length
    rma = [np.nan] * len(series)
    rma[length - 1] = np.mean(series[:length])
    for i in range(length, len(series)):
        rma[i] = alpha * series[i] + (1 - alpha) * rma[i - 1]
    return np.array(rma)


def pine_rsi(close, length):
    delta = np.diff(close, prepend=close[0])
    up = np.where(delta > 0, delta, 0)
    down = np.where(delta < 0, -delta, 0)
    rs = pine_rma(up, length) / pine_rma(down, length)
    return 100 - 100 / (1 + rs)


def rational_quadratic(src, lookback=8, relative_weight=8.0, start=25, eps=1e-9):
    w_sum, y_sum = 0.0, 0.0
    n = len(src)
    if n == 0:
        return np.nan
    for i in range(min(start, n)):
        w = (1 + (i**2 / (2 * (lookback**2) * relative_weight))) ** (-relative_weight)
        y_sum += src[i] * w
        w_sum += w
    return y_sum / (w_sum + eps)


def get_optimal_rsi_length(close, optimal_length=200, rsi_count=30, rsi_min=4, 
                           ma_length=14, backup_length=14, use_rational_quadratic=True):
    src = np.array(close)
    if use_rational_quadratic:
        src = np.array([rational_quadratic(src[:i+1]) for i in range(len(src))])
    
    cross_profits = np.zeros(rsi_count)
    max_testable_length = min(rsi_min + rsi_count, len(close) - ma_length - 1)
    if max_testable_length < rsi_min:
        return backup_length, 0.0
    
    actual_count = min(rsi_count, max_testable_length - rsi_min + 1)
    
    for i in range(actual_count):
        L = rsi_min + i
        if L >= len(close):
            break
            
        rsi = pine_rsi(src, L)
        rsi_ma = pine_sma(rsi, ma_length)
        cross_type = 0
        cross_close = 0
        total_profit, cross_count = 0, 0
        
        for a in range(1, min(optimal_length, len(close))):
            if np.isnan(rsi[a]) or np.isnan(rsi_ma[a]):
                continue
                
            co = (rsi[a-1] < rsi_ma[a-1]) and (rsi[a] > rsi_ma[a])
            cu = (rsi[a-1] > rsi_ma[a-1]) and (rsi[a] < rsi_ma[a])
            if co:
                if cross_type != 0:
                    total_profit += cross_close / close[a]
                    cross_count += 1
                cross_close = close[a]
                cross_type = 1
            elif cu:
                if cross_type != 0:
                    total_profit += close[a] / cross_close
                    cross_count += 1
                cross_close = close[a]
                cross_type = -1
        cross_profits[i] = total_profit / max(cross_count, 1)

    best_idx = np.argmax(cross_profits[:actual_count])
    best_percent = cross_profits[best_idx]
    best_length = rsi_min + best_idx if best_percent > -100000 else backup_length

    return best_length, best_percent


def knn_average(rsi_fast, rsi_slow, k=3, exp=False):
    distances = np.abs(rsi_slow - rsi_fast)
    idx_sorted = np.argsort(distances)
    idx_knn = idx_sorted[:k]
    vals = (rsi_fast[idx_knn] + rsi_slow[idx_knn]) / 2
    if exp:
        weights = np.exp(-distances[idx_knn])
        return np.sum(vals * weights) / np.sum(weights)
    else:
        return np.mean(vals)


def apply_ml_to_rsi(opt_rsi, ma_length=14, ml_mode="Simple Average", ml_length=10, 
                    k=3, fast_length=1, slow_length=5, same_regime=False):
    if ml_mode == "None":
        return opt_rsi[-1] if len(opt_rsi) > 0 else np.nan

    opt_rsi = np.array(opt_rsi)
    
    if len(opt_rsi) < ma_length:
        return opt_rsi[-1] if len(opt_rsi) > 0 else np.nan
    
    rsi_ma = pine_sma(opt_rsi, ma_length)
    
    if pd.isna(rsi_ma.iloc[-1]):
        return opt_rsi[-1]
    
    rsi_bull = opt_rsi[-1] >= rsi_ma.iloc[-1]

    if ml_mode == "Simple Average":
        rsi_data = []
        
        for i in range(min(ml_length, len(opt_rsi))):
            if i == 0:
                if len(opt_rsi) >= ma_length:
                    sma_temp = np.mean(opt_rsi[-ma_length:])
                else:
                    sma_temp = np.mean(opt_rsi)
            else:
                start_idx = max(0, len(opt_rsi) - i - ma_length)
                end_idx = len(opt_rsi) - i
                if end_idx > start_idx:
                    sma_temp = np.mean(opt_rsi[start_idx:end_idx])
                else:
                    continue
            
            temp_bull = opt_rsi[len(opt_rsi) - 1 - i] > sma_temp
            if not same_regime or temp_bull == rsi_bull:
                rsi_data.append(opt_rsi[len(opt_rsi) - 1 - i])
                
        return np.mean(rsi_data) if len(rsi_data) > 0 else opt_rsi[-1]

    else:
        if len(opt_rsi) < max(fast_length, slow_length):
            return opt_rsi[-1]
            
        rsi_fast = pine_sma(opt_rsi, fast_length).values
        rsi_slow = pine_sma(opt_rsi, slow_length).values
        
        valid_length = min(ml_length, len(opt_rsi))
        recent_fast = rsi_fast[-valid_length:]
        recent_slow = rsi_slow[-valid_length:]
        
        mask = ~(np.isnan(recent_fast) | np.isnan(recent_slow))
        recent_fast = recent_fast[mask]
        recent_slow = recent_slow[mask]
        
        if len(recent_fast) == 0:
            return opt_rsi[-1]
            
        return knn_average(recent_fast, recent_slow, k, exp=("Exponential" in ml_mode))


def optimal_rsi_strategy(df, optimal_length=200, rsi_count=30, rsi_min=4,
                         ma_length=14, backup_length=14, ml_mode="Simple Average",
                         use_rational_quadratic=True):
    """
    Machine Learning Optimal RSI Strategy with Textual Output + Trend Structure for LLM Agents
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    close = df['close'].values

    # Step 1: Find optimal RSI length
    rsi_length, best_percent = get_optimal_rsi_length(
        close, optimal_length, rsi_count, rsi_min, ma_length, backup_length, use_rational_quadratic
    )
    df['OptimalLength'] = rsi_length

    # Step 2: Compute RSI and RSI_MA
    rsi = pine_rsi(close, rsi_length)
    df['RSI'] = rsi
    df['RSI_MA'] = pine_sma(rsi, ma_length)

    # Step 3: ML smoothing
    smoothed_values = []
    for i in range(len(rsi)):
        smoothed_values.append(apply_ml_to_rsi(rsi[:i+1], ma_length, ml_mode))
    df['RSI_Smoothed'] = smoothed_values

    # Step 4: Generate Signals
    df['BullCross'] = (df['RSI_Smoothed'] > df['RSI_MA']) & (df['RSI_Smoothed'].shift(1) <= df['RSI_MA'].shift(1))
    df['BearCross'] = (df['RSI_Smoothed'] < df['RSI_MA']) & (df['RSI_Smoothed'].shift(1) >= df['RSI_MA'].shift(1))
    df['Signal'] = np.where(df['BullCross'], 1, np.where(df['BearCross'], -1, 0))

    # Simulate positions
    df['position'] = 0
    position = 0
    for i in range(len(df)):
        if df.loc[i, 'BullCross']:
            position = 1
        elif df.loc[i, 'BearCross']:
            position = -1
        df.loc[i, 'position'] = position

    # Calculate returns
    df['return'] = df['close'].pct_change() * df['position']
    df['equity'] = (1 + df['return'].fillna(0)).cumprod()

    # === STATISTICAL ANALYSIS ===
    current_price = df['close'].iloc[-1]
    current_rsi = df['RSI_Smoothed'].iloc[-1]
    current_rsi_ma = df['RSI_MA'].iloc[-1]
    current_position = int(df['position'].iloc[-1])
    
    rsi_mean = df['RSI_Smoothed'].mean()
    rsi_std = df['RSI_Smoothed'].std()
    rsi_zscore = (current_rsi - rsi_mean) / rsi_std if rsi_std > 0 else 0
    rsi_percentile = (df['RSI_Smoothed'] < current_rsi).sum() / len(df) * 100
    
    overbought = 70
    oversold = 30
    in_overbought = current_rsi > overbought
    in_oversold = current_rsi < oversold
    zone = 'overbought' if in_overbought else ('oversold' if in_oversold else 'neutral')
    
    distance_to_overbought = overbought - current_rsi
    distance_to_oversold = current_rsi - oversold
    
    rsi_change_5d = current_rsi - df['RSI_Smoothed'].iloc[-6] if len(df) > 5 else 0
    rsi_trend = 'rising' if rsi_change_5d > 2 else ('falling' if rsi_change_5d < -2 else 'flat')
    
    above_ma = current_rsi > current_rsi_ma
    rsi_ma_distance = current_rsi - current_rsi_ma
    
    bull_crosses = df[df['BullCross']]
    bear_crosses = df[df['BearCross']]
    avg_rsi_at_bull = bull_crosses['RSI_Smoothed'].mean() if len(bull_crosses) > 0 else None
    avg_rsi_at_bear = bear_crosses['RSI_Smoothed'].mean() if len(bear_crosses) > 0 else None
    
    # === TREND STRUCTURE ANALYSIS ===
    last_bull = bull_crosses.iloc[-1] if len(bull_crosses) > 0 else None
    last_bear = bear_crosses.iloc[-1] if len(bear_crosses) > 0 else None
    
    if last_bull is not None and last_bear is not None:
        if bull_crosses.index[-1] > bear_crosses.index[-1]:
            last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'bull', last_bull['date'], last_bull['close'], last_bull['RSI_Smoothed']
            previous_signal, previous_signal_date, previous_signal_price = 'bear', last_bear['date'], last_bear['close']
        else:
            last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'bear', last_bear['date'], last_bear['close'], last_bear['RSI_Smoothed']
            previous_signal, previous_signal_date, previous_signal_price = 'bull', last_bull['date'], last_bull['close']
        days_since = (df['date'].iloc[-1] - last_signal_date).days
        days_prev_trend = (last_signal_date - previous_signal_date).days
    elif last_bull is not None:
        last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'bull', last_bull['date'], last_bull['close'], last_bull['RSI_Smoothed']
        days_since = (df['date'].iloc[-1] - last_signal_date).days
        previous_signal, previous_signal_date, previous_signal_price, days_prev_trend = None, None, None, None
    elif last_bear is not None:
        last_signal, last_signal_date, last_signal_price, last_signal_rsi = 'bear', last_bear['date'], last_bear['close'], last_bear['RSI_Smoothed']
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
            confirmation_status, confirmation_desc = "CONFIRMED", f"Trend confirmed ({days_since} days since {last_signal.upper()} cross)"
        elif days_since >= 3:
            confirmation_status, confirmation_desc = "DEVELOPING", f"Trend developing ({days_since} days, needs {7-days_since} more for confirmation)"
        else:
            confirmation_status, confirmation_desc = "EARLY", f"Early stage ({days_since} days, needs {7-days_since} more for confirmation)"
    else:
        confirmation_status, confirmation_desc = "NONE", "No active trend"
    
    all_signals_list = []
    for _, row in bull_crosses.iterrows():
        all_signals_list.append({'date': row['date'], 'type': 'BULL', 'price': row['close'], 'rsi': row['RSI_Smoothed']})
    for _, row in bear_crosses.iterrows():
        all_signals_list.append({'date': row['date'], 'type': 'BEAR', 'price': row['close'], 'rsi': row['RSI_Smoothed']})
    all_signals_list.sort(key=lambda x: x['date'])
    
    if len(all_signals_list) >= 3:
        last_3 = all_signals_list[-3:]
        pattern_desc = " → ".join([s['type'] for s in last_3])
        if len(last_3) >= 2 and last_3[-2]['type'] == 'BULL' and last_3[-1]['type'] == 'BEAR':
            last_trade_return = ((last_3[-1]['price'] - last_3[-2]['price']) / last_3[-2]['price'] * 100)
            last_trade_result = "WIN" if last_trade_return > 0 else "LOSS"
            pattern_context = f"Last 3 signals: {pattern_desc}. Last completed trade: {last_trade_result} ({last_trade_return:+.1f}%)"
        else:
            pattern_context = f"Last 3 signals: {pattern_desc}. Current signal still open"
    else:
        pattern_context = f"Only {len(all_signals_list)} signals - insufficient for pattern analysis"
    
    total_signals = len(bull_crosses) + len(bear_crosses)
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
        position_context = f"Currently {position_text}. Last signal was {last_signal.upper()} CROSS {days_since} days ago at ${last_signal_price:.2f}. Current price ${current_price:.2f} = {pnl:+.1f}% from signal."
    else:
        position_context = f"Currently {position_text}. No recent signals generated."
    
    if last_signal and days_since and previous_signal and days_prev_trend:
        trend_structure = f"{structure_desc}. Previous {previous_signal.upper()} phase lasted {days_prev_trend} days. "
        trend_structure += f"Current {last_signal.upper()} phase is {days_since} days old ({confirmation_status}). "
        trend_structure += f"RSI momentum: {rsi_momentum_per_day:+.2f} points/day ({trend_strength} momentum). "
        trend_structure += f"RSI has moved {rsi_change_since_signal:+.1f} points since cross (from {last_signal_rsi:.1f} to {current_rsi:.1f}). "
        if structure_status in ["MAJOR BREAK", "MODERATE BREAK"]:
            trend_structure += f"⚠️ This is a {structure_status} - significant trend reversal after extended {previous_signal} period."
        elif confirmation_status == "EARLY":
            trend_structure += f"⚠️ Trend still in early stage - watch for continuation or reversal in next few days."
    elif last_signal and days_since:
        trend_structure = f"Current {last_signal.upper()} cross appeared {days_since} days ago. {confirmation_desc}. RSI momentum: {rsi_momentum_per_day:+.2f} points/day ({trend_strength})."
    else:
        trend_structure = "No active trend detected. Market in consolidation phase."
    
    rsi_context = f"ML-Optimized RSI at {current_rsi:.1f} ({zone}), using optimal length of {rsi_length} periods. "
    rsi_context += f"RSI is {rsi_zscore:+.2f} standard deviations from mean of {rsi_mean:.1f}. "
    rsi_context += f"Currently {'ABOVE' if above_ma else 'BELOW'} RSI MA ({current_rsi_ma:.1f}) by {abs(rsi_ma_distance):.1f} points. "
    rsi_context += f"RSI has been {rsi_trend} over last 5 days ({rsi_change_5d:+.1f} points)."
    
    if avg_rsi_at_bull and avg_rsi_at_bear:
        reversal_text = f"Historical patterns show bull crosses typically occur at RSI {avg_rsi_at_bull:.1f}, "
        reversal_text += f"while bear crosses occur at RSI {avg_rsi_at_bear:.1f}. "
        reversal_text += f"Current RSI is {abs(current_rsi - avg_rsi_at_bull):.1f} points from typical bull zone, "
        reversal_text += f"{abs(avg_rsi_at_bear - current_rsi):.1f} points from typical bear zone."
    else:
        reversal_text = "Insufficient signal history to determine typical crossover levels."
    
    vol_label = "LOW" if rsi_std < 10 else ("HIGH" if rsi_std > 15 else "MODERATE")
    volatility_text = f"RSI standard deviation is {rsi_std:.2f}, indicating {vol_label} volatility. "
    volatility_text += f"ML optimization selected length {rsi_length} with performance score {best_percent:.4f}. "
    if abs(rsi_zscore) > 2:
        volatility_text += f"Z-score of {rsi_zscore:.2f} shows EXTREME levels (>2 STD)."
    elif abs(rsi_zscore) > 1:
        volatility_text += f"Z-score of {rsi_zscore:.2f} is ELEVATED (>1 STD)."
    else:
        volatility_text += f"Z-score of {rsi_zscore:.2f} is within NORMAL range."
    
    perf_label = "STRONG" if win_rate > 60 else ("GOOD" if win_rate > 50 else ("MODERATE" if win_rate > 40 else "WEAK"))
    risk_text = f"Strategy shows {perf_label} performance: {win_rate:.1f}% win rate over {total_signals} crossover signals. "
    risk_text += f"Total return: {total_return:+.1f}%, Max single trade: {max_trade_return:+.1f}%, Sharpe: {sharpe_ratio:.2f}."
    
    if above_ma and rsi_trend == 'rising' and structure_status in ["MAJOR BREAK", "MODERATE BREAK"]:
        recommendation = f"STRONG BULLISH: RSI above MA and rising + {structure_status} after {days_prev_trend}-day downtrend. High probability continuation."
    elif above_ma and rsi_trend == 'rising':
        recommendation = f"BULLISH: RSI above MA and rising. Momentum is positive. Watch for bear cross as exit signal."
    elif not above_ma and rsi_trend == 'falling' and structure_status in ["MAJOR BREAK", "MODERATE BREAK"]:
        recommendation = f"STRONG BEARISH: RSI below MA and falling + {structure_status} after {days_prev_trend}-day uptrend. High probability continuation."
    elif not above_ma and rsi_trend == 'falling':
        recommendation = f"BEARISH: RSI below MA and falling. Momentum is negative. Watch for bull cross as entry signal."
    elif confirmation_status == "EARLY" and trend_strength == "WEAK":
        recommendation = f"CAUTION: {last_signal.upper()} cross only {days_since} days old with WEAK momentum ({rsi_momentum_per_day:+.2f} pts/day). Trend fragile - needs confirmation."
    elif confirmation_status == "DEVELOPING" and trend_strength in ["MODERATE", "STRONG"]:
        recommendation = f"HOLD: {last_signal.upper()} trend developing with {trend_strength} momentum. {7-days_since} more days needed for full confirmation."
    elif confirmation_status == "CONFIRMED":
        recommendation = f"TREND CONFIRMED: {last_signal.upper()} trend confirmed ({days_since} days). Ride the momentum but watch for reversal signals."
    elif above_ma and rsi_trend == 'falling':
        recommendation = f"CAUTION: RSI above MA but losing momentum. Potential bear cross coming."
    elif not above_ma and rsi_trend == 'rising':
        recommendation = f"WATCH: RSI below MA but gaining strength. Potential bull cross setup forming."
    else:
        recommendation = f"NEUTRAL: RSI near MA ({abs(rsi_ma_distance):.1f} pts away) with flat momentum. Wait for clear crossover."
    
    if last_signal and confirmation_status == "EARLY":
        next_action = f"Monitor {last_signal.upper()} position closely. Set stop-loss at entry ±3%. Needs {7-days_since} more days for confirmation. Watch for RSI crossing back {'below' if last_signal == 'bull' else 'above'} MA indicating failed breakout."
    else:
        next_action = f"Watch for RSI to cross {'below' if above_ma else 'above'} RSI MA (currently {abs(rsi_ma_distance):.1f} points {'above' if above_ma else 'below'}) for signal reversal."
    
    textual = {
        'summary': f"Optimal RSI at {current_rsi:.1f} ({zone}), {rsi_zscore:+.1f} STD. {trend_strength} {rsi_trend} momentum. {confirmation_status} trend. Length {rsi_length}.",
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
    print("OPTIMAL RSI STRATEGY - ML ANALYSIS WITH TREND STRUCTURE")
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
    textual['_rsi_length'] = rsi_length
    textual['_best_percent'] = best_percent
    
    return textual


def graph(result):
    """Display Optimal RSI charts"""
    df = result['_df']
    rsi_length = result['_rsi_length']
    best_percent = result['_best_percent']
    
    plt.figure(figsize=(14,6))
    plt.plot(df['date'], df['RSI_Smoothed'], label='RSI (ML Smoothed)', color='purple', linewidth=2)
    plt.plot(df['date'], df['RSI_MA'], label='RSI MA', color='yellow', linewidth=1.5)
    plt.axhline(70, color='gray', linestyle='--', alpha=0.5, label='Overbought (70)')
    plt.axhline(30, color='gray', linestyle='--', alpha=0.5, label='Oversold (30)')
    plt.scatter(df.loc[df['BullCross'],'date'], df.loc[df['BullCross'],'RSI_Smoothed'], 
                color='green', s=80, label='Bull Cross', zorder=5)
    plt.scatter(df.loc[df['BearCross'],'date'], df.loc[df['BearCross'],'RSI_Smoothed'], 
                color='red', s=80, label='Bear Cross', zorder=5)
    plt.title(f"Machine Learning Optimal RSI (Length={rsi_length}, Performance={best_percent:.4f})")
    plt.xlabel('Date')
    plt.ylabel('RSI')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    plt.figure(figsize=(10,4))
    plt.plot(df['date'], df['equity'], color='purple', linewidth=2)
    plt.title('Optimal RSI Strategy Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Equity (relative)')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
