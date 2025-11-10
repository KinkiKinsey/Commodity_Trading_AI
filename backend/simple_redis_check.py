#!/usr/bin/env python
"""Simple Redis check without complex imports."""
import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

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
    exists = r.exists(key)
    if exists:
        print(f"✓ {key} EXISTS")
        try:
            value = r.get(key)
            if value:
                print(f"  Size: {len(value)} bytes")
                # Show first 100 chars
                print(f"  Preview: {value[:100]}...")
        except Exception as e:
            print(f"  Error reading: {e}")
    else:
        print(f"✗ {key} NOT FOUND")

print("\n" + "=" * 80)
print("Scanning all Crude_Oil keys in Redis:")
pattern = "Crude_Oil:Future_Contract:*"
cursor = 0
count = 0
all_keys = []
while True:
    cursor, keys = r.scan(cursor, match=pattern, count=100)
    all_keys.extend(keys)
    if cursor == 0:
        break

if all_keys:
    print(f"Found {len(all_keys)} keys:")
    for i, key in enumerate(all_keys[:20], 1):  # Show first 20
        print(f"  {i}. {key}")
    if len(all_keys) > 20:
        print(f"  ... and {len(all_keys) - 20} more")
else:
    print("  No keys found matching pattern!")
