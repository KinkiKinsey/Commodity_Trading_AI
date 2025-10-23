"""
Test Suite for Financial Analysis Tools

Tests all functions from analyzers, indicators, and data_sources modules.
"""

import pytest
import pandas as pd

# Import from analyzers
from src.financial.analyzers import (
    analyze_contango_backwardation,
    get_macro_risk_analysis,
    analyze_vix,
    analyze_liquidity
)

# Import from indicators
from src.financial.indicators import (
    bollinger_strategy,
    equal_highs_lows,
    liquidity_zones,
    ml_moving_average,
    optimal_rsi_strategy,
    rsi_strategy
)

# Import from data_sources
from src.financial.data_sources import (
    get_yahoo_data
)
from src.financial.data_sources.get_price import get_yahoo_data_comprehensive


# ========================
# DATA SOURCES TESTS
# ========================

def test_get_yahoo_data():
    """Test Yahoo Finance data fetching."""
    print("\n\n=== Testing get_yahoo_data ===")
    
    # Test with a liquid commodity futures contract
    df = get_yahoo_data("CL=F", days=30)  # Crude Oil Futures
    
    assert isinstance(df, pd.DataFrame), "Result should be a DataFrame"
    assert not df.empty, "DataFrame should not be empty"
    assert 'close' in df.columns, "DataFrame should have 'close' column"
    assert 'volume' in df.columns, "DataFrame should have 'volume' column"
    
    print(f"✅ Fetched {len(df)} rows of data")
    print(f"📊 Columns: {list(df.columns)}")
    print(f"📈 Latest close: {df['close'].iloc[-1]:.2f}")


# ========================
# ANALYZERS TESTS
# ========================

def test_analyze_contango_backwardation():
    """Test contango/backwardation analysis."""
    print("\n\n=== Testing analyze_contango_backwardation ===")
    
    result = analyze_contango_backwardation("oil")
    
    # Validate result structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'summary' in result, "Result should contain 'summary' key"
    assert 'market_structure' in result, "Result should contain 'market_structure' key"
    assert '_df' in result, "Result should contain '_df' key"
    
    print(f"✅ Analysis completed")
    print(f"📊 Summary: {result['summary']}")
    print(f"📈 Market Condition: {result['market_structure']['condition']}")
    print(f"📋 Active Contracts: {result['contract_analysis']['active_contracts']}")


def test_get_macro_risk_analysis():
    """Test macro risk analysis."""
    print("\n\n=== Testing get_macro_risk_analysis ===")
    
    result = get_macro_risk_analysis()
    
    # Skip test if Redis data not available
    if result is None:
        pytest.skip("No macro analysis data available in Redis")
    
    assert isinstance(result, str), "Result should be a string"
    assert len(result) > 0, "Result should not be empty"
    
    print(f"✅ Macro analysis retrieved")
    print(f"📊 Analysis Preview (first 500 chars):")
    print(result[:500] + "...")


def test_analyze_vix():
    """Test VIX analysis."""
    print("\n\n=== Testing analyze_vix ===")
    
    # Test with smaller dataset for faster testing
    result = analyze_vix(days=1000)
    
    assert isinstance(result, str), "Result should be a string"
    assert len(result) > 0, "Result should not be empty"
    assert "VIX" in result, "Result should mention VIX"
    
    print(f"✅ VIX analysis completed")
    print(f"📊 Analysis Preview (first 500 chars):")
    print(result[:500] + "...")


def test_analyze_liquidity():
    """Test liquidity monitor."""
    print("\n\n=== Testing analyze_liquidity ===")
    
    # Test with smaller dataset for faster testing
    result = analyze_liquidity(days=180)
    
    assert isinstance(result, str), "Result should be a string"
    assert len(result) > 0, "Result should not be empty"
    assert "Liquidity" in result, "Result should mention Liquidity"
    
    print(f"✅ Liquidity analysis completed")
    print(f"📊 Analysis Preview (first 500 chars):")
    print(result[:500] + "...")


# ========================
# INDICATORS TESTS
# ========================

@pytest.fixture
def sample_df():
    """Create sample price data for indicator testing (OHLCV data)."""
    df = get_yahoo_data_comprehensive("CL=F", days=100)  # Crude Oil Futures - Full OHLCV
    return df


def test_bollinger_strategy(sample_df):
    """Test Bollinger Bands strategy."""
    print("\n\n=== Testing bollinger_strategy ===")
    
    result = bollinger_strategy(sample_df, length=20, mult=2.0)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert '_df' in result, "Result should contain '_df' key"  # Fixed: Use _df
    
    print(f"✅ Bollinger strategy calculated")
    print(f"📊 Result keys: {list(result.keys())}")


def test_equal_highs_lows(sample_df):
    """Test EQH/EQL liquidity indicator."""
    print("\n\n=== Testing equal_highs_lows ===")
    
    result = equal_highs_lows(sample_df, threshold=0.01)  # Fixed: No lookback parameter
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert '_df' in result, "Result should contain '_df' key"  # Fixed: Use _df
    
    print(f"✅ EQH/EQL calculated")
    print(f"📊 Result keys: {list(result.keys())}")


def test_liquidity_zones(sample_df):
    """Test liquidity zones indicator."""
    print("\n\n=== Testing liquidity_zones ===")
    
    result = liquidity_zones(
        sample_df,
        liq_len=7,
        liq_margin=2.3,
        show_buyside=True,
        show_sellside=True,
        show_voids=True
    )
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert '_df' in result, "Result should contain '_df' key"  # Fixed: Use _df
    
    print(f"✅ Liquidity zones calculated")
    print(f"📊 Result keys: {list(result.keys())}")


def test_ml_moving_average(sample_df):
    """Test ML moving average (RBF)."""
    print("\n\n=== Testing ml_moving_average ===")
    
    result = ml_moving_average(sample_df, window=50, sigma=10.0, mult=2.0, forecast=0)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert '_df' in result, "Result should contain '_df' key"  # Fixed: Use _df
    
    print(f"✅ ML moving average calculated")
    print(f"📊 Result keys: {list(result.keys())}")


def test_optimal_rsi_strategy(sample_df):
    """Test optimal RSI strategy."""
    print("\n\n=== Testing optimal_rsi_strategy ===")
    
    result = optimal_rsi_strategy(
        sample_df,
        optimal_length=200,
        rsi_count=30,
        rsi_min=4,
        ma_length=14,
        backup_length=14,  # Fixed: Use backup_length instead of smoothing_length
        ml_mode="Simple Average"  # Fixed: Use ml_mode instead of smoothing_mode
    )
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert '_df' in result, "Result should contain '_df' key"  # Fixed: Use _df
    
    print(f"✅ Optimal RSI strategy calculated")
    print(f"📊 Result keys: {list(result.keys())}")


def test_rsi_strategy(sample_df):
    """Test classic RSI strategy."""
    print("\n\n=== Testing rsi_strategy ===")
    
    result = rsi_strategy(sample_df, length=14, overbought=70.0, oversold=30.0)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert '_df' in result, "Result should contain '_df' key"  # Fixed: Use _df
    
    print(f"✅ RSI strategy calculated")
    print(f"📊 Result keys: {list(result.keys())}")
