"""
Machine Learning Moving Average (Gaussian RBF) with Textual Analysis for LLM Agents
Usage: 
    from Data_Source.get_price import get_yahoo_data_comprehensive
    df = get_yahoo_data_comprehensive(ticker, days_back)
    result = ml_moving_average(df)
    graph(result)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection


def rbf_kernel(x1, x2, l):
    """Gaussian RBF kernel"""
    return np.exp(-((x1 - x2)**2) / (2 * (l**2)))


def ml_moving_average(df, window=50, sigma=10, mult=2.0, forecast=0):
    """
    Machine Learning Moving Average with Textual Analysis
    
    Input:
        df: DataFrame with ['date', 'close']
        window: Training window size (default: 50)
        sigma: RBF kernel bandwidth (default: 10)
        mult: Envelope multiplier (default: 2.0)
        forecast: Forecast periods ahead (default: 0)
    
    Output:
        Dictionary with textual_analysis
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    n = len(df)
    prices = df['close'].values
    out = np.full(n, np.nan)

    # Core GPR loop
    for i in range(window, n):
        X_train = np.arange(window)
        y_train = prices[i - window:i]
        mean = np.mean(y_train)
        y_train_c = y_train - mean

        # Kernel matrix
        K_train = np.zeros((window, window))
        for a in range(window):
            for b in range(window):
                K_train[a, b] = rbf_kernel(X_train[a], X_train[b], sigma)
        K_inv = np.linalg.pinv(K_train + 1e-6 * np.eye(window))

        # Test kernel vector
        x_test = np.arange(window + forecast)
        K_star = np.array([rbf_kernel(x, X_train, sigma) for x in x_test])
        K_row = K_star[-1] @ K_inv

        # Predicted value
        out[i] = np.dot(K_row, y_train_c) + mean

    # Envelope (dynamic MAE bands)
    mae = pd.Series(np.abs(df['close'] - pd.Series(out))).rolling(window).mean() * mult
    upper = out + mae
    lower = out - mae

    # Trend detection
    trend = np.full(n, np.nan)
    for i in range(1, n):
        if df['close'][i] > upper[i] and out[i] > out[i - 1]:
            trend[i] = 1
        elif df['close'][i] < lower[i] and out[i] < out[i - 1]:
            trend[i] = 0
        else:
            trend[i] = trend[i - 1] if i > 0 else 0

    # Save outputs
    df['ML_MA'] = out
    df['upper'] = upper
    df['lower'] = lower
    df['trend'] = trend

    # STATISTICAL ANALYSIS
    valid_idx = ~np.isnan(out)
    valid_df = df[valid_idx].copy()
    
    if len(valid_df) == 0:
        print("ERROR: Insufficient data")
        return None
    
    current_price = valid_df['close'].iloc[-1]
    current_ml_ma = valid_df['ML_MA'].iloc[-1]
    current_upper = valid_df['upper'].iloc[-1]
    current_lower = valid_df['lower'].iloc[-1]
    current_trend_value = valid_df['trend'].iloc[-1]
    current_trend = int(current_trend_value) if not np.isnan(current_trend_value) else 0
    
    distance_to_upper = current_upper - current_price
    distance_to_lower = current_price - current_lower
    band_width = current_upper - current_lower
    price_position_pct = ((current_price - current_lower) / band_width * 100) if band_width > 0 else 50
    
    ml_ma_change_5d = current_ml_ma - valid_df['ML_MA'].iloc[-6] if len(valid_df) > 5 else 0
    ml_ma_slope = "rising" if ml_ma_change_5d > 0 else ("falling" if ml_ma_change_5d < 0 else "flat")
    
    above_ml_ma = current_price > current_ml_ma
    distance_from_ml_ma = current_price - current_ml_ma
    distance_from_ml_ma_pct = (distance_from_ml_ma / current_ml_ma * 100) if current_ml_ma > 0 else 0
    
    bullish_periods = (valid_df['trend'] == 1).sum()
    bearish_periods = (valid_df['trend'] == 0).sum()
    total_valid_periods = len(valid_df)
    bullish_pct = (bullish_periods / total_valid_periods * 100) if total_valid_periods > 0 else 0
    bearish_pct = (bearish_periods / total_valid_periods * 100) if total_valid_periods > 0 else 0
    
    trend_shifts = np.where(np.diff(valid_df['trend'].fillna(0)) != 0)[0] + 1
    num_trend_shifts = len(trend_shifts)
    
    if len(trend_shifts) > 0:
        last_shift_idx = trend_shifts[-1]
        last_shift_date = valid_df.iloc[last_shift_idx]['date']
        days_since_shift = (valid_df['date'].iloc[-1] - last_shift_date).days
        prev_trend_value = valid_df['trend'].iloc[last_shift_idx - 1] if last_shift_idx > 0 else None
        previous_trend = int(prev_trend_value) if prev_trend_value is not None and not np.isnan(prev_trend_value) else None
        shift_from = "BEARISH" if previous_trend == 0 else "BULLISH"
        shift_to = "BULLISH" if current_trend == 1 else "BEARISH"
    else:
        days_since_shift, shift_from, shift_to = None, None, None
    
    band_width_pct = (band_width / current_price * 100) if current_price > 0 else 0
    avg_band_width = valid_df['upper'] - valid_df['lower']
    avg_band_width_pct = (avg_band_width.mean() / valid_df['close'].mean() * 100)
    
    expanding = band_width_pct > avg_band_width_pct * 1.1
    contracting = band_width_pct < avg_band_width_pct * 0.9
    
    # BUILD TEXTUAL ANALYSIS
    trend_text = "BULLISH" if current_trend == 1 else "BEARISH"
    
    if current_price > current_upper:
        position_status = "ABOVE UPPER BAND"
        position_desc = f"Price ${current_price:.2f} is ${abs(distance_to_upper):.2f} above upper band (${current_upper:.2f}) - strong bullish breakout."
    elif current_price < current_lower:
        position_status = "BELOW LOWER BAND"
        position_desc = f"Price ${current_price:.2f} is ${abs(distance_to_lower):.2f} below lower band (${current_lower:.2f}) - strong bearish breakdown."
    elif price_position_pct > 70:
        position_status = "NEAR UPPER BAND"
        position_desc = f"Price at {price_position_pct:.1f}% of band width - approaching upper band (${current_upper:.2f})."
    elif price_position_pct < 30:
        position_status = "NEAR LOWER BAND"
        position_desc = f"Price at {price_position_pct:.1f}% of band width - approaching lower band (${current_lower:.2f})."
    else:
        position_status = "MID-RANGE"
        position_desc = f"Price at {price_position_pct:.1f}% of band width - within normal range."
    
    if days_since_shift is not None:
        if days_since_shift < 7:
            trend_structure = f"Recent trend shift: {shift_from} → {shift_to} {days_since_shift} days ago (EARLY stage). ML MA is {ml_ma_slope} ({ml_ma_change_5d:+.2f} over 5 days). Price is {'above' if above_ml_ma else 'below'} ML MA by {abs(distance_from_ml_ma_pct):.2f}%."
        elif days_since_shift < 14:
            trend_structure = f"Trend shift: {shift_from} → {shift_to} {days_since_shift} days ago (DEVELOPING). ML MA {ml_ma_slope} ({ml_ma_change_5d:+.2f} over 5 days). Trend gaining momentum."
        else:
            trend_structure = f"Established {shift_to} trend ({days_since_shift} days since shift from {shift_from}). ML MA {ml_ma_slope}. Strong directional move."
    else:
        trend_structure = f"No recent trend shifts detected. Market in {trend_text} mode. ML MA {ml_ma_slope}."
    
    ml_ma_context = f"ML Moving Average at ${current_ml_ma:.2f}, {ml_ma_slope} with {ml_ma_change_5d:+.2f} change over 5 days. Price is {'ABOVE' if above_ml_ma else 'BELOW'} ML MA by ${abs(distance_from_ml_ma):.2f} ({abs(distance_from_ml_ma_pct):.1f}%). Current trend: {trend_text}."
    
    if expanding:
        volatility_context = f"Bands EXPANDING: Width ${band_width:.2f} ({band_width_pct:.2f}%) is above average ({avg_band_width_pct:.2f}%). High volatility - expect larger moves."
    elif contracting:
        volatility_context = f"Bands CONTRACTING: Width ${band_width:.2f} ({band_width_pct:.2f}%) is below average ({avg_band_width_pct:.2f}%). Low volatility - potential breakout coming."
    else:
        volatility_context = f"Bands NORMAL: Width ${band_width:.2f} ({band_width_pct:.2f}%) near average ({avg_band_width_pct:.2f}%). Standard volatility."
    
    trend_dist = f"Historical: {bullish_pct:.1f}% bullish, {bearish_pct:.1f}% bearish over {total_valid_periods} days. Total shifts: {num_trend_shifts}."
    
    if current_trend == 1 and above_ml_ma and ml_ma_slope == "rising":
        if current_price > current_upper:
            recommendation = f"STRONG BULLISH: Above upper band + bullish trend + rising ML MA. Momentum continuation."
        else:
            recommendation = f"BULLISH: Above ML MA in bullish trend. Follow the trend."
    elif current_trend == 0 and not above_ml_ma and ml_ma_slope == "falling":
        if current_price < current_lower:
            recommendation = f"STRONG BEARISH: Below lower band + bearish trend + falling ML MA. Downside momentum."
        else:
            recommendation = f"BEARISH: Below ML MA in bearish trend. Downtrend in progress."
    elif current_trend == 1 and ml_ma_slope == "falling":
        recommendation = f"CAUTION: Bullish trend but ML MA losing momentum. Watch for reversal."
    elif current_trend == 0 and ml_ma_slope == "rising":
        recommendation = f"CAUTION: Bearish trend but ML MA gaining momentum. Potential bottom."
    elif days_since_shift and days_since_shift < 3:
        recommendation = f"EARLY TREND CHANGE: Shifted to {shift_to} {days_since_shift} days ago. Wait for confirmation."
    else:
        recommendation = f"NEUTRAL: Mid-range. ML MA {ml_ma_slope}. No strong bias."
    
    if current_trend == 1:
        next_action = f"Monitor bullish trend. Watch for break below lower band (${current_lower:.2f}) or ML MA (${current_ml_ma:.2f}) for reversal."
    else:
        next_action = f"Monitor bearish trend. Watch for break above upper band (${current_upper:.2f}) or ML MA (${current_ml_ma:.2f}) for reversal."
    
    textual = {
        'summary': f"{trend_text} trend. Price ${current_price:.2f}, ML MA ${current_ml_ma:.2f} ({ml_ma_slope}). {position_status}.",
        'position_context': position_desc,
        'trend_structure': trend_structure,
        'ml_ma_interpretation': ml_ma_context,
        'band_analysis': volatility_context,
        'trend_distribution': trend_dist,
        'recommendation': recommendation,
        'next_action': next_action
    }
    
    print("=" * 80)
    print("ML MOVING AVERAGE (Gaussian RBF) - ANALYSIS")
    print("=" * 80)
    print(f"\n📊 SUMMARY: {textual['summary']}")
    print(f"\n💼 POSITION: {textual['position_context']}")
    print(f"\n🔄 TREND STRUCTURE: {textual['trend_structure']}")
    print(f"\n📈 ML MA: {textual['ml_ma_interpretation']}")
    print(f"\n📉 BANDS: {textual['band_analysis']}")
    print(f"\n📊 DISTRIBUTION: {textual['trend_distribution']}")
    print(f"\n🎯 RECOMMENDATION: {textual['recommendation']}")
    print(f"\n👉 NEXT ACTION: {textual['next_action']}")
    print("=" * 80 + "\n")
    
    # SIMPLE TIME INTERVALS JSON
    time_intervals = []
    
    # Track periods
    current_period_start = 0
    current_trend_type = None
    
    for i in range(len(valid_df)):
        trend_val = valid_df['trend'].iloc[i]
        trend_type = 'BULLISH' if trend_val == 1 else 'BEARISH'
        
        if current_trend_type != trend_type:
            # End previous period
            if current_trend_type is not None and i > current_period_start:
                period = {
                    'start_date': valid_df.iloc[current_period_start]['date'].strftime('%Y-%m-%d'),
                    'end_date': valid_df.iloc[i-1]['date'].strftime('%Y-%m-%d'),
                    'trend': current_trend_type
                }
                time_intervals.append(period)
            
            # Start new period
            current_period_start = i
            current_trend_type = trend_type
    
    # Add final period
    if current_trend_type is not None and len(valid_df) > current_period_start:
        period = {
            'start_date': valid_df.iloc[current_period_start]['date'].strftime('%Y-%m-%d'),
            'end_date': valid_df.iloc[-1]['date'].strftime('%Y-%m-%d'),
            'trend': current_trend_type
        }
        time_intervals.append(period)

    textual['_df'] = df
    textual['_window'] = window
    textual['_sigma'] = sigma
    textual['time_intervals'] = time_intervals
    
    return textual


def graph(result):
    """Display ML Moving Average chart"""
    df = result['_df']
    window = result['_window']
    sigma = result['_sigma']
    
    # Only plot data where ML_MA is valid (not NaN)
    valid_mask = ~df['ML_MA'].isna()
    valid_df = df[valid_mask].copy()
    
    if len(valid_df) == 0:
        print("No valid ML_MA data to plot")
        return
    
    x = mdates.date2num(valid_df['date'])
    y = valid_df['ML_MA'].values
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    colors = ['#3179f5' if t == 1 else '#e91e63' for t in valid_df['trend'][1:]]

    fig, ax = plt.subplots(figsize=(14,6))
    # Plot close price for the same valid period
    ax.plot(valid_df['date'], valid_df['close'], color='gray', alpha=0.4, label='Close')

    lc = LineCollection(segments, colors=colors, linewidth=2.2)
    ax.add_collection(lc)

    ax.fill_between(valid_df['date'], valid_df['lower'], valid_df['upper'], color='blue', alpha=0.07)

    shift_points = np.where(np.diff(valid_df['trend']) != 0)[0] + 1
    if len(shift_points) > 0:
        valid_shift_points = shift_points[shift_points < len(colors)]
        if len(valid_shift_points) > 0:
            ax.scatter(valid_df.iloc[valid_shift_points]['date'], valid_df['ML_MA'].iloc[valid_shift_points],
                       color=[colors[i] if i < len(colors) else colors[-1] for i in valid_shift_points],
                       edgecolor='black', s=60, zorder=5, label='Trend Shift')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)

    ax.set_title(f"Machine Learning Moving Average (Window={window}, Sigma={sigma})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    plt.tight_layout()
    plt.show()

