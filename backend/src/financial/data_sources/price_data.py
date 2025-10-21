"""
Price Data Fetching Module

Fetches historical price and volume data from Yahoo Finance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def get_yahoo_data(ticker: str, days: int = 365) -> pd.DataFrame:
    """
    Get historical price data from Yahoo Finance.
    
    Args:
        ticker: Yahoo Finance ticker symbol
                Examples: 'CLZ25.NYM' (Crude Oil Dec 2025)
                         'GC=F' (Gold Futures)
                         'AAPL' (Apple Stock)
                         'BTC-USD' (Bitcoin)
        days: Number of days of historical data (default: 365)
    
    Returns:
        DataFrame with columns: ['date', 'close', 'volume']
        Date is a regular column (not index)
    """
    try:
        print(f"📊 Fetching {days} days of data for {ticker}...")
        
        end_date = datetime.now() + timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        df = yf.download(
            ticker, 
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False
        )
        
        if df.empty:
            print(f"❌ No data available for {ticker}")
            return pd.DataFrame(columns=['date', 'close', 'volume'])
        
        # Clean column names
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df.columns = [col.lower() for col in df.columns]
        
        # Reset index to make date a column
        df = df.reset_index()
        df.columns = ['date' if col.lower() in ['date', 'index'] else col for col in df.columns]
        
        # Select only date, close, volume
        df = df[['date', 'close', 'volume']].copy()
        
        print(f"✅ Retrieved {len(df)} days")
        print(f"   Range: {df['date'].min().date()} → {df['date'].max().date()}")
        print(f"   Latest: ${df['close'].iloc[-1]:.2f}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return pd.DataFrame(columns=['date', 'close', 'volume'])

