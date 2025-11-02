"""
Quick sanity check for the FMP news endpoint.

Usage
-----
    # Activate your backend virtualenv first
    python backend/scripts/test_fmp_news.py --api-key <FMP_KEY> --limit 5

If --api-key is omitted, the script will look for one of the following
environment variables (in this order):
    - RINGSHELL_FMP_API_KEY
    - FMP_API_KEY

The script exits with code 0 when the API responds with at least one article,
otherwise it prints a diagnostic message and exits with code 1.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import requests


FMP_NEWS_ENDPOINT = "https://financialmodelingprep.com/api/v3/fmp/articles"


def resolve_api_key(explicit_key: str | None) -> str:
    if explicit_key:
        return explicit_key

    env_key = os.getenv("RINGSHELL_FMP_API_KEY") or os.getenv("FMP_API_KEY")
    if not env_key:
        raise SystemExit(
            "No API key found. Provide --api-key or set RINGSHELL_FMP_API_KEY/FMP_API_KEY."
        )
    return env_key


def fetch_fmp_news(api_key: str, *, page: int, limit: int, symbol: str | None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "apikey": api_key,
        "page": page,
        "size": limit,
    }
    if symbol:
        params["symbol"] = symbol

    response = requests.get(FMP_NEWS_ENDPOINT, params=params, timeout=20)
    response.raise_for_status()

    payload = response.json()
    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("content")
        if isinstance(items, list):
            return items
        raise SystemExit(f"Unexpected dict payload structure: {list(payload.keys())}")

    if isinstance(payload, list):
        return payload

    raise SystemExit(f"Unexpected payload type: {type(payload)!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanity check for FMP news endpoint.")
    parser.add_argument("--api-key", dest="api_key", help="FMP API key (optional, falls back to env)")
    parser.add_argument("--page", type=int, default=0, help="Page index to request (default: 0)")
    parser.add_argument("--limit", type=int, default=5, help="Number of articles to fetch (default: 5)")
    parser.add_argument("--symbol", help="Optional symbol filter, e.g. CL")
    args = parser.parse_args()

    api_key = resolve_api_key(args.api_key)

    try:
        articles = fetch_fmp_news(api_key, page=args.page, limit=args.limit, symbol=args.symbol)
    except requests.HTTPError as exc:
        print(f"[ERROR] HTTP {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(f"[ERROR] Request failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not articles:
        print("[WARN] Request succeeded but returned no articles.")
        raise SystemExit(1)

    print(f"[OK] Retrieved {len(articles)} article(s) from FMP.")
    print("-" * 80)
    for idx, article in enumerate(articles, start=1):
        title = article.get("title") or article.get("headline") or "<no title>"
        published = article.get("publishedDate") or article.get("date")
        url = article.get("url")
        print(f"{idx}. {title}")
        print(f"   Published: {published}")
        if url:
            print(f"   URL      : {url}")
        summary = article.get("summary") or article.get("text")
        if summary:
            trimmed = summary.strip().splitlines()[0][:200]
            print(f"   Summary  : {trimmed}{'…' if len(summary) > len(trimmed) else ''}")
        print("-" * 80)


if __name__ == "__main__":
    main()
