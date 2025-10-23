"""
Trend News Agent - Test ML Moving Average
"""

# from src.financial.indicators import ml_moving_average
# from src.financial.data_sources.get_price import get_yahoo_data_comprehensive


# def test_ml_moving_average():
#     """Test ML Moving Average with real data"""
#     
#     print("🔍 Fetching data for TSLA...")
#     df = get_yahoo_data_comprehensive("TSLA", days=1300)
#     
#     print(f"\n📊 Running ML Moving Average analysis...")
#     print(f"   Data points: {len(df)}")
#     print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
#     print(f"   Latest price: ${df['close'].iloc[-1]:.2f}\n")
#     
#     result = ml_moving_average(df, window=100, sigma=0.01, mult=2.0, forecast=0)
#     
#     print("\n" + "="*80)
#     print("📋 COMPLETE RESULT STRUCTURE")
#     print("="*80)
#     
#     for key, value in result.items():
#         if key.startswith('_'):
#             if key == '_df':
#                 print(f"\n{key}: DataFrame with {len(value)} rows and columns {list(value.columns)}")
#             else:
#                 print(f"\n{key}: {value}")
#         elif key == 'time_intervals':
#             print(f"\n{key}:")
#             for interval in value:
#                 print(f"  - {interval}")
#         else:
#             print(f"\n{key}:")
#             print(f"  {value}")
#     
#     print("\n" + "="*80)
#     print("✅ Test completed!")
#     print("="*80)
#     
#     return result

mock_payload = """{
  "ticker": "TSLA",
  "time_intervals": [
    {"start_date": "2022-08-26", "end_date": "2023-01-25", "trend": "BEARISH"},
    {"start_date": "2023-01-26", "end_date": "2023-04-19", "trend": "BULLISH"},
    {"start_date": "2023-04-20", "end_date": "2023-06-07", "trend": "BEARISH"},
    {"start_date": "2023-06-08", "end_date": "2023-06-23", "trend": "BULLISH"},
    {"start_date": "2023-06-26", "end_date": "2023-06-30", "trend": "BEARISH"},
    {"start_date": "2023-07-03", "end_date": "2023-07-19", "trend": "BULLISH"},
    {"start_date": "2023-07-20", "end_date": "2023-08-28", "trend": "BEARISH"},
    {"start_date": "2023-08-29", "end_date": "2023-10-18", "trend": "BULLISH"},
    {"start_date": "2023-10-19", "end_date": "2023-11-01", "trend": "BEARISH"},
    {"start_date": "2023-11-02", "end_date": "2023-11-08", "trend": "BULLISH"},
    {"start_date": "2023-11-09", "end_date": "2023-11-13", "trend": "BEARISH"},
    {"start_date": "2023-11-14", "end_date": "2024-01-24", "trend": "BULLISH"},
    {"start_date": "2024-01-25", "end_date": "2024-02-14", "trend": "BEARISH"},
    {"start_date": "2024-02-15", "end_date": "2024-04-12", "trend": "BULLISH"},
    {"start_date": "2024-04-15", "end_date": "2024-04-23", "trend": "BEARISH"},
    {"start_date": "2024-04-24", "end_date": "2024-07-23", "trend": "BULLISH"},
    {"start_date": "2024-07-24", "end_date": "2024-11-05", "trend": "BEARISH"},
    {"start_date": "2024-11-06", "end_date": "2024-12-26", "trend": "BULLISH"},
    {"start_date": "2024-12-27", "end_date": "2025-03-21", "trend": "BEARISH"},
    {"start_date": "2025-03-24", "end_date": "2025-04-03", "trend": "BULLISH"},
    {"start_date": "2025-04-04", "end_date": "2025-04-24", "trend": "BEARISH"},
    {"start_date": "2025-04-25", "end_date": "2025-06-04", "trend": "BULLISH"},
    {"start_date": "2025-06-05", "end_date": "2025-06-20", "trend": "BEARISH"},
    {"start_date": "2025-06-23", "end_date": "2025-10-09", "trend": "BULLISH"},
    {"start_date": "2025-10-10", "end_date": "2025-10-22", "trend": "BEARISH"}
  ]
}"""






if __name__ == "__main__":
    print("Hello World")