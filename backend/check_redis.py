#!/usr/bin/env python
"""Check what oil factor keys exist in Redis."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.financial.DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage

redis_client = RedisDatabaseStorage()

# Check for CLZ25.NYM keys
ticker = "CLZ25.NYM"
normalized = ticker.replace(".", "_").replace("=", "_")

keys_to_check = [
    f"Crude_Oil:Future_Contract:{normalized}:Queries_DF.csv",
    f"Crude_Oil:Future_Contract:{normalized}:Impact_Metrics.csv",
    f"Crude_Oil:Future_Contract:{normalized}:Factor_Time.csv",
    f"Crude_Oil:Future_Contract:{normalized}:LLM_Trend_Analyst_Result",
]

print(f"Checking Redis keys for {ticker} (normalized: {normalized})")
print("=" * 80)

for key in keys_to_check:
    exists = redis_client.redis_client.exists(key)
    if exists:
        print(f"✓ {key} EXISTS")
        # Try to get size
        try:
            value = redis_client.redis_client.get(key)
            if value:
                print(f"  Size: {len(value)} bytes")
        except:
            pass
    else:
        print(f"✗ {key} NOT FOUND")

print("\n" + "=" * 80)
print("Scanning all Crude_Oil keys in Redis:")
pattern = "Crude_Oil:Future_Contract:*"
cursor = 0
count = 0
while True:
    cursor, keys = redis_client.redis_client.scan(cursor, match=pattern, count=100)
    for key in keys:
        count += 1
        print(f"  {count}. {key}")
    if cursor == 0:
        break

if count == 0:
    print("  No keys found matching pattern!")
