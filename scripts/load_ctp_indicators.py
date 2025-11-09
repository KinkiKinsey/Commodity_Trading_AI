"""
Parse INDEX1.xlsx indicator definitions and sync them into ClickHouse.

The script normalises each Excel row into an indicator record and upserts it
into the `ctp.ctp_indicators` table (created via scripts/clickhouse_init.sql).

Usage example:
    python scripts/load_ctp_indicators.py \
        --xlsx INDEX1.xlsx \
        --ch-url http://localhost:18123 \
        --ch-user default \
        --ch-password ''
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import pandas as pd

try:
    import clickhouse_connect  # type: ignore
except ImportError:  # pragma: no cover - helper script
    clickhouse_connect = None  # type: ignore

UTC = timezone.utc

CATEGORY_HINTS = {
    "BBAND": "volatility",
    "SMC": "structure",
    "BSSIDe": "liquidity",
    "LONGTERM": "trend",
    "MLMA": "trend",
    "OPTIMAL RSI": "momentum",
}


@dataclass
class IndicatorRow:
    indicator_key: str
    label: str
    category: str
    description: str
    code: str
    checksum: str
    source_file: str
    metadata_json: str
    updated_at: datetime

    def to_row(self) -> List[Any]:
        return [
            self.indicator_key,
            self.label,
            self.category,
            self.description,
            self.code,
            self.checksum,
            self.source_file,
            self.metadata_json,
            self.updated_at,
        ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync INDEX1.xlsx indicators into ClickHouse")
    parser.add_argument("--xlsx", default=Path("INDEX1.xlsx"), type=Path, help="Path to the indicator Excel file")
    parser.add_argument("--sheet", default=0, help="Sheet index or name (default: 0)")
    parser.add_argument("--ch-url", default=os.environ.get("CLICKHOUSE_URL", "http://localhost:18123"))
    parser.add_argument("--ch-user", default=os.environ.get("CLICKHOUSE_USER", "default"))
    parser.add_argument("--ch-password", default=os.environ.get("CLICKHOUSE_PASSWORD", ""))
    parser.add_argument("--dry-run", action="store_true", help="Parse and display rows without writing to ClickHouse")
    return parser.parse_args()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "indicator"


def infer_category(label: str) -> str:
    upper = label.upper()
    for hint, category in CATEGORY_HINTS.items():
        if hint.upper() in upper:
            return category
    return "general"


def build_description(code: str) -> str:
    snippet = code.strip().splitlines()[:2]
    if not snippet:
        return "Indicator imported from INDEX1.xlsx"
    preview = " ".join(line.strip() for line in snippet if line.strip())
    if not preview:
        return "Indicator imported from INDEX1.xlsx"
    return f"{preview[:240]}"


def dataframe_to_rows(df: pd.DataFrame, source_file: Path) -> List[IndicatorRow]:
    rows: List[IndicatorRow] = []
    now = datetime.now(UTC)

    for idx, record in df.iterrows():
        label = str(record.get("NAME") or "").strip()
        code = str(record.get("CODE") or "").strip()
        if not label or not code:
            continue

        indicator_key = slugify(label)
        checksum = hashlib.sha256(f"{label}\n{code}".encode("utf-8")).hexdigest()
        description = build_description(code)
        category = infer_category(label)
        metadata = {
            "row_index": int(idx) + 2,  # include header offset for Excel users
            "code_length": len(code),
            "code_preview": code[:200],
        }

        rows.append(
            IndicatorRow(
                indicator_key=indicator_key,
                label=label,
                category=category,
                description=description,
                code=code,
                checksum=checksum,
                source_file=str(source_file),
                metadata_json=json.dumps(metadata, ensure_ascii=False),
                updated_at=now,
            )
        )

    return rows


def build_clickhouse_client(args: argparse.Namespace):
    if clickhouse_connect is None:
        raise RuntimeError("clickhouse-connect is required. Install with `pip install clickhouse-connect`.")

    parsed = urlparse(args.ch_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (parsed.scheme == "https" and 8443 or 18123)
    protocol = "https" if parsed.scheme == "https" else "http"

    return clickhouse_connect.get_client(  # type: ignore[no-untyped-call]
        host=host,
        port=port,
        username=args.ch_user,
        password=args.ch_password,
        interface=protocol,
    )


def fetch_existing_checksums(client) -> Dict[str, str]:
    result = client.query("SELECT indicator_key, checksum FROM ctp.ctp_indicators FINAL")
    return {row[0]: row[1] for row in result.result_rows}


def delete_existing(client, indicator_keys: List[str]) -> None:
    if not indicator_keys:
        return
    for key in indicator_keys:
        client.command(f"ALTER TABLE ctp.ctp_indicators DELETE WHERE indicator_key = '{key}'")


def insert_rows(client, rows: List[IndicatorRow]) -> None:
    if not rows:
        return
    columns = [
        "indicator_key",
        "label",
        "category",
        "description",
        "code",
        "checksum",
        "source_file",
        "metadata_json",
        "updated_at",
    ]
    client.insert("ctp.ctp_indicators", [row.to_row() for row in rows], column_names=columns)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not args.xlsx.exists():
        raise FileNotFoundError(f"Excel file not found: {args.xlsx}")

    logging.info("reading %s (sheet=%s)", args.xlsx, args.sheet)
    df = pd.read_excel(args.xlsx, sheet_name=args.sheet)
    if "NAME" not in df.columns or "CODE" not in df.columns:
        raise ValueError("Expected columns NAME and CODE in the Excel sheet.")

    rows = dataframe_to_rows(df, args.xlsx)
    logging.info("parsed %d indicator rows", len(rows))

    for row in rows:
        logging.debug("indicator %s checksum=%s", row.indicator_key, row.checksum[:8])

    if args.dry_run:
        for row in rows:
            logging.info("DRY-RUN indicator=%s label=%s category=%s", row.indicator_key, row.label, row.category)
        return

    client = build_clickhouse_client(args)
    existing = fetch_existing_checksums(client)

    to_update: List[IndicatorRow] = []
    to_delete: List[str] = []

    for row in rows:
        prev_checksum = existing.get(row.indicator_key)
        if prev_checksum == row.checksum:
            logging.info("skip %s (unchanged)", row.indicator_key)
            continue
        if prev_checksum is not None:
            to_delete.append(row.indicator_key)
        to_update.append(row)

    if not to_update:
        logging.info("no indicator changes detected")
        return

    if to_delete:
        logging.info("deleting %d existing rows", len(to_delete))
        delete_existing(client, to_delete)

    logging.info("inserting %d indicators", len(to_update))
    insert_rows(client, to_update)
    logging.info("sync complete")


if __name__ == "__main__":
    main()
