"""
Bollinger Bands Strategy with Textual Analysis for LLM Agents
Usage: 
    from Data_Source.get_price import get_yahoo_data_comprehensive
    df = get_yahoo_data_comprehensive(ticker, days_back)
    result = bollinger_strategy(df)
    graph(result)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def bollinger_strategy(df, length=20, mult=2.0):
    """
    Bollinger Bands with Textual Analysis
    
    Input:
        df: DataFrame with ['date', 'close']
        length: Moving average period (default: 20)
        mult: Standard deviation multiplier (default: 2.0)
    
    Output:
        Dictionary with textual_analysis
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Bollinger Bands Calculation
    df['basis'] = df['close'].rolling(window=length).mean()
    df['stdev'] = df['close'].rolling(window=length).std()
    df['upper'] = df['basis'] + mult * df['stdev']
    df['lower'] = df['basis'] - mult * df['stdev']

    # Entry Signals
    df['buy_signal'] = (df['close'] > df['lower']) & (df['close'].shift(1) <= df['lower'].shift(1))
    df['sell_signal'] = (df['close'] < df['upper']) & (df['close'].shift(1) >= df['upper'].shift(1))

    # Track Position
    df['position'] = 0
    position = 0
    for i in range(len(df)):
        if df.loc[i, 'buy_signal']:
            position = 1
        elif df.loc[i, 'sell_signal']:
            position = -1
        df.loc[i, 'position'] = position

    # Strategy Returns
    df['return'] = df['close'].pct_change() * df['position']
    df['equity'] = (1 + df['return']).cumprod()

    # === STATISTICAL ANALYSIS ===
    
    current_price = df['close'].iloc[-1]
    current_basis = df['basis'].iloc[-1]
    current_stdev = df['stdev'].iloc[-1]
    current_upper = df['upper'].iloc[-1]
    current_lower = df['lower'].iloc[-1]
    
    distance_to_upper_pct = ((current_upper - current_price) / current_price * 100)
    distance_to_lower_pct = ((current_price - current_lower) / current_price * 100)
    distance_from_basis_pct = ((current_price - current_basis) / current_basis * 100) if current_basis > 0 else 0
    
    band_width = current_upper - current_lower
    percent_b_pct = ((current_price - current_lower) / band_width * 100) if band_width > 0 else 50
    price_in_std = ((current_price - current_basis) / current_stdev) if current_stdev > 0 else 0
    
    bandwidth = (band_width / current_basis * 100) if current_basis > 0 else 0
    avg_bandwidth = ((df['upper'] - df['lower']) / df['basis'] * 100).mean()
    
    is_squeeze = bandwidth < avg_bandwidth * 0.75
    is_expansion = bandwidth > avg_bandwidth * 1.25
    
    recent_df = df.tail(30)
    upper_touches = ((recent_df['high'] >= recent_df['upper']) | (recent_df['close'] >= recent_df['upper'])).sum()
    lower_touches = ((recent_df['low'] <= recent_df['lower']) | (recent_df['close'] <= recent_df['lower'])).sum()
    
    winning_days = (df['return'] > 0).sum()
    losing_days = (df['return'] < 0).sum()
    win_rate = (winning_days / (winning_days + losing_days) * 100) if (winning_days + losing_days) > 0 else 0
    total_return = (df['equity'].iloc[-1] - 1) * 100
    returns = df['return'].dropna()
    sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    # === BUILD TEXTUAL ANALYSIS ===
    
    if percent_b_pct > 100:
        position_status = "ABOVE UPPER BAND"
    elif percent_b_pct < 0:
        position_status = "BELOW LOWER BAND"
    elif percent_b_pct > 80:
        position_status = "NEAR UPPER BAND"
    elif percent_b_pct < 20:
        position_status = "NEAR LOWER BAND"
    else:
        position_status = "MID-RANGE"
    
    summary = f"{position_status}. Price ${current_price:.2f}, Basis ${current_basis:.2f}, %B: {percent_b_pct:.1f}%."
    position_context = f"Current: ${current_price:.2f}. Moving Mean (Basis): ${current_basis:.2f} ({distance_from_basis_pct:+.1f}%). Upper: ${current_upper:.2f} ({distance_to_upper_pct:+.1f}%), Lower: ${current_lower:.2f} ({distance_to_lower_pct:+.1f}%)."
    std_analysis = f"Moving Std: ${current_stdev:.2f}. Bandwidth: {bandwidth:.2f}% (Avg: {avg_bandwidth:.2f}%). Price is {price_in_std:+.2f}σ from mean."
    
    percentb_interpretation = f"%B: {percent_b_pct:.1f}%. "
    if percent_b_pct > 100:
        percentb_interpretation += f"${abs(current_upper - current_price):.2f} above upper band."
    elif percent_b_pct < 0:
        percentb_interpretation += f"${abs(current_price - current_lower):.2f} below lower band."
    elif percent_b_pct > 80:
        percentb_interpretation += "Approaching upper band."
    elif percent_b_pct < 20:
        percentb_interpretation += "Approaching lower band."
    else:
        percentb_interpretation += "Within normal range."
    
    if is_squeeze:
        volatility_state = f"SQUEEZE: Bandwidth {bandwidth:.2f}% is {((bandwidth/avg_bandwidth - 1) * 100):.1f}% below average. Low volatility."
    elif is_expansion:
        volatility_state = f"EXPANSION: Bandwidth {bandwidth:.2f}% is {((bandwidth/avg_bandwidth - 1) * 100):.1f}% above average. High volatility."
    else:
        volatility_state = f"NORMAL: Bandwidth {bandwidth:.2f}%. Standard volatility."
    
    if upper_touches > lower_touches * 1.5:
        band_interaction = f"{upper_touches} upper touches vs {lower_touches} lower - uptrend bias."
    elif lower_touches > upper_touches * 1.5:
        band_interaction = f"{lower_touches} lower touches vs {upper_touches} upper - downtrend bias."
    else:
        band_interaction = f"{upper_touches} upper, {lower_touches} lower touches - balanced."
    
    perf_label = "STRONG" if win_rate > 60 else ("GOOD" if win_rate > 50 else ("MODERATE" if win_rate > 40 else "WEAK"))
    performance_metrics = f"{perf_label}: {win_rate:.1f}% win rate, {total_return:+.1f}% return, Sharpe {sharpe_ratio:.2f}."
    
    textual = {
        'summary': summary,
        'position_context': position_context,
        'std_analysis': std_analysis,
        'percentb_interpretation': percentb_interpretation,
        'volatility_state': volatility_state,
        'band_interaction': band_interaction,
        'performance_metrics': performance_metrics
    }
    
    print("=" * 80)
    print("BOLLINGER BANDS - ANALYSIS")
    print("=" * 80)
    print(f"\n📊 SUMMARY: {textual['summary']}")
    print(f"\n💼 POSITION: {textual['position_context']}")
    print(f"\n📊 STD ANALYSIS: {textual['std_analysis']}")
    print(f"\n📈 %B: {textual['percentb_interpretation']}")
    print(f"\n📉 VOLATILITY: {textual['volatility_state']}")
    print(f"\n🔄 BANDS: {textual['band_interaction']}")
    print(f"\n💰 PERFORMANCE: {textual['performance_metrics']}")
    print("=" * 80 + "\n")
    
    textual['_df'] = df
    textual['_length'] = length
    textual['_mult'] = mult
    
    return textual


def graph(result):
    """Display Bollinger Bands chart"""
    df = result['_df']
    length = result['_length']
    mult = result['_mult']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13,8), sharex=True, gridspec_kw={'height_ratios': [3,1]})

    ax1.plot(df['date'], df['close'], label='Close', color='black')
    ax1.plot(df['date'], df['basis'], label='Basis (SMA)', color='blue', linewidth=1.2)
    ax1.plot(df['date'], df['upper'], label='Upper Band', color='red', linestyle='--')
    ax1.plot(df['date'], df['lower'], label='Lower Band', color='green', linestyle='--')

    ax1.scatter(df.loc[df['buy_signal'], 'date'], df.loc[df['buy_signal'], 'close'],
                marker='^', color='lime', s=100, label='Buy Signal')
    ax1.scatter(df.loc[df['sell_signal'], 'date'], df.loc[df['sell_signal'], 'close'],
                marker='v', color='magenta', s=100, label='Sell Signal')

    ax1.set_title(f'Bollinger Bands (Length={length}, Mult={mult})')
    ax1.set_ylabel('Price')
    ax1.legend()

    ax2.plot(df['date'], df['equity'], color='red', label='Equity')
    ax2.set_ylabel('Equity')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

