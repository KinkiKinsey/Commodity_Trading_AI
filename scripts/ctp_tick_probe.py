import json
import sys
import time
import urllib.request
from typing import List, Dict, Any


def fetch_tick(symbol: str) -> Dict[str, Any]:
  url = f"http://47.108.177.50:8080/md/tick/{symbol}"
  with urllib.request.urlopen(url, timeout=3) as resp:
    return json.load(resp)


def main():
  symbol = sys.argv[1] if len(sys.argv) > 1 else "CL2512-NYM"
  count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
  interval = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

  print(f"Sampling {symbol} for {count} ticks (interval {interval}s)...")
  rows: List[Dict[str, Any]] = []
  for i in range(count):
    start = time.time()
    data = fetch_tick(symbol)
    now = time.strftime("%H:%M:%S", time.localtime())
    rows.append(
        {
            "local_time": now,
            "update_time": data.get("update_time"),
            "update_millisec": data.get("update_millisec"),
            "last_price": data.get("last_price"),
        }
    )
    print(rows[-1])
    elapsed = time.time() - start
    sleep = max(0.0, interval - elapsed)
    time.sleep(sleep)

  print("\nSummary:")
  for row in rows:
    print(
        f"{row['local_time']} -> update {row['update_time']}.{row['update_millisec']:03d} price {row['last_price']}"
    )


if __name__ == "__main__":
  main()
