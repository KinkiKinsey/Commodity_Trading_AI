import os
import sys
import asyncio
import datetime
from datetime import timedelta
from typing import List, Tuple

# Optional .env loader for local/dev; Render will inject env vars
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

import yfinance as yf
import pandas as pd

# Local modules
from oil_factors_metrics.oil_factor_api import get_oil_factors

MONTH_CODES = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']  # Jan..Dec


def generate_contracts(root: str, suffix: str, months_ahead: int = 24) -> List[str]:
    today = datetime.date.today()
    year = today.year
    month = today.month
    out: List[str] = []
    for i in range(months_ahead):
        m = (month + i - 1) % 12
        y = year + (month + i - 1) // 12
        month_code = MONTH_CODES[m]
        out.append(f"{root}{month_code}{str(y)[-2:]}{suffix}")
    return out


def has_recent_data(ticker: str, days: int = 10) -> bool:
    end = datetime.date.today() + timedelta(days=1)
    start = end - timedelta(days=days)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
    return not df.empty


async def run_oil_metrics_batch(tickers: List[str], language: str = "Chinese") -> dict:
    tasks = [get_oil_factors(t, language=language, force_refresh=False) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = {}
    os.makedirs("outputs", exist_ok=True)
    for t, r in zip(tickers, results):
        if isinstance(r, Exception):
            print(f"❌ {t}: {r}")
        else:
            queries_df: pd.DataFrame = r
            print(f"✅ {t}: queries_df rows={len(queries_df)} | cols={list(queries_df.columns)}")
            out[t] = queries_df
            try:
                csv_path = os.path.join("outputs", f"queries_df_{t.replace('.', '_').replace('=', '_')}.csv")
                queries_df.to_csv(csv_path, index=False)
                print(f"💾 Saved: {csv_path}")
            except Exception as save_err:
                print(f"⚠️ Failed to save CSV for {t}: {save_err}")
    return out


async def main() -> int:
    # Define sector mapping (WTI on NYMEX)
    root, suffix = ("CL", ".NYM")

    # 1) Generate next 24 months of contracts from today
    contracts = generate_contracts(root, suffix, months_ahead=24)
    print(f"Total generated (24 months): {len(contracts)}")

    # 2) Filter by availability on Yahoo Finance (recent data)
    available: List[str] = []
    for t in contracts:
        try:
            if has_recent_data(t, days=10):
                available.append(t)
        except Exception as e:
            print(f"⚠️ Skipping {t}: {e}")

    if not available:
        print("❌ No available contracts found with recent Yahoo data.")
        return 1

    print(f"Available on Yahoo (data in last 10 days): {len(available)}")
    print(available)

    # 3) Run oil factor metrics for the available contracts twice (simple two passes)
    await run_oil_metrics_batch(available, language=os.getenv("OIL_FACTORS_LANGUAGE", "Chinese"))
    print("\n🔁 Running second pass on all available tickers...")
    await run_oil_metrics_batch(available, language=os.getenv("OIL_FACTORS_LANGUAGE", "Chinese"))

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(130)
