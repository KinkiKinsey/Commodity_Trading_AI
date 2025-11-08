import argparse
import csv
import json
import os
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


CTP_BASE_URL = os.environ.get("CTP_TICK_BASE_URL", "http://47.108.177.50:8080/md/tick")
OUTPUT_CSV = Path("data/ctp_ticks.csv")


def generate_contract_ids(count: int = 12) -> List[str]:
  """Generate sequential CL contracts starting from current month."""
  now = datetime.utcnow()
  year = now.year
  month = now.month
  ids: List[str] = []
  while len(ids) < count:
    ids.append(f"CL{str(year % 100).zfill(2)}{str(month).zfill(2)}-NYM")
    month += 1
    if month > 12:
      month = 1
      year += 1
  return ids


def fetch_tick(symbol: str) -> dict:
  url = f"{CTP_BASE_URL}/{symbol}"
  with urllib.request.urlopen(url, timeout=3) as resp:
    return json.load(resp)


def ensure_csv_header(path: Path):
  if path.exists():
    return
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(
        [
            "local_time",
            "symbol",
            "update_time",
            "update_millisec",
            "last_price",
            "bid_price1",
            "bid_volume1",
            "ask_price1",
            "ask_volume1",
            "volume",
        ]
    )


def sample_once(symbols: Iterable[str]) -> List[dict]:
  rows = []
  for symbol in symbols:
    data = fetch_tick(symbol)
    rows.append(
        {
            "local_time": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "update_time": data.get("update_time"),
            "update_millisec": data.get("update_millisec"),
            "last_price": data.get("last_price"),
            "bid_price1": data.get("bid_price1"),
            "bid_volume1": data.get("bid_volume1"),
            "ask_price1": data.get("ask_price1"),
            "ask_volume1": data.get("ask_volume1"),
            "volume": data.get("volume"),
        }
    )
  return rows


def append_rows(path: Path, rows: List[dict]):
  with path.open("a", newline="") as f:
    writer = csv.writer(f)
    for row in rows:
      writer.writerow(
          [
              row["local_time"],
              row["symbol"],
              row["update_time"],
              row["update_millisec"],
              row["last_price"],
              row["bid_price1"],
              row["bid_volume1"],
              row["ask_price1"],
              row["ask_volume1"],
              row["volume"],
          ]
      )


def main():
  parser = argparse.ArgumentParser(description="Sample CTP ticks into CSV.")
  parser.add_argument("--samples", type=int, default=10, help="Number of sampling cycles")
  parser.add_argument("--interval", type=float, default=1.0, help="Seconds between cycles")
  parser.add_argument(
      "--symbols",
      type=str,
      nargs="*",
      default=["CL2512-NYM", "CL2601-NYM", "CL2602-NYM", "CL2603-NYM", "CL2604-NYM", "CL2605-NYM"],
      help="Symbols to sample (defaults to latest six contracts)",
  )
  args = parser.parse_args()

  symbols = args.symbols or generate_contract_ids(6)
  ensure_csv_header(OUTPUT_CSV)
  print(f"Sampling symbols {symbols} for {args.samples} cycles (interval {args.interval}s)")

  for idx in range(args.samples):
    start = time.time()
    rows = sample_once(symbols)
    append_rows(OUTPUT_CSV, rows)
    print(f"[{idx+1}/{args.samples}] wrote {len(rows)} rows")
    elapsed = time.time() - start
    time.sleep(max(0.0, args.interval - elapsed))

  print(f"Done. Data appended to {OUTPUT_CSV}")


if __name__ == "__main__":
  main()
