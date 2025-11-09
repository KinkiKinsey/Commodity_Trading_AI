"""
Kafka → ClickHouse consumer for CTP ticks.

Usage:
    python scripts/kafka_to_clickhouse.py \
        --brokers localhost:9094 \
        --topic ctp_ticks \
        --ch-url http://localhost:18123 \
        --ch-user default \
        --ch-password ''
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from kafka import KafkaConsumer  # type: ignore
from urllib.parse import urlparse

try:
  import clickhouse_connect  # type: ignore
except ImportError:
  clickhouse_connect = None  # type: ignore

UTC = timezone.utc


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Consume ticks from Kafka and insert into ClickHouse.")
  parser.add_argument("--brokers", default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094"))
  parser.add_argument("--topic", default=os.environ.get("KAFKA_TICK_TOPIC", "ctp_ticks"))
  parser.add_argument("--group", default="ctp-clickhouse-consumer")
  parser.add_argument("--ch-url", default=os.environ.get("CLICKHOUSE_URL", "http://localhost:18123"))
  parser.add_argument("--ch-user", default=os.environ.get("CLICKHOUSE_USER", "default"))
  parser.add_argument("--ch-password", default=os.environ.get("CLICKHOUSE_PASSWORD", ""))
  parser.add_argument("--batch-size", type=int, default=200)
  parser.add_argument("--flush-interval", type=float, default=2.0)
  return parser.parse_args()


def build_ch_client(args: argparse.Namespace):
  if not clickhouse_connect:
    raise RuntimeError("clickhouse-connect not installed. pip install clickhouse-connect")
  parsed = urlparse(args.ch_url)
  host = parsed.hostname or "localhost"
  port = parsed.port or (parsed.scheme == "https" and 8443 or 18123)
  return clickhouse_connect.get_client(
      host=host,
      port=port,
      username=args.ch_user,
      password=args.ch_password,
  )


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
  exchange_ts = None
  if row.get("update_time") is not None:
    day = datetime.now(UTC).date().isoformat()
    millis = int(row.get("update_millisec") or 0)
    exchange_ts = datetime.fromisoformat(f"{day}T{row['update_time']}") \
        .replace(tzinfo=UTC) \
        .replace(microsecond=millis * 1000)

  local_ts = datetime.fromisoformat(row["local_time"]).replace(tzinfo=None)
  return {
      "symbol": row.get("symbol"),
      "local_ts": local_ts,
      "exchange_ts": exchange_ts,
      "update_time": row.get("update_time"),
      "update_millisec": row.get("update_millisec"),
      "last_price": row.get("last_price"),
      "bid_price1": row.get("bid_price1"),
      "bid_volume1": row.get("bid_volume1"),
      "ask_price1": row.get("ask_price1"),
      "ask_volume1": row.get("ask_volume1"),
      "volume": row.get("volume"),
  }


def flush_rows(client, rows: List[Dict[str, Any]]):
  if not rows:
    return
  columns = [
      "symbol",
      "local_ts",
      "exchange_ts",
      "update_time",
      "update_millisec",
      "last_price",
      "bid_price1",
      "bid_volume1",
      "ask_price1",
      "ask_volume1",
      "volume",
  ]
  data = [
      [row.get(col) for col in columns]
      for row in rows
  ]
  client.insert(
      "ctp.ctp_ticks",
      data,
      column_names=columns,
  )


def main():
  args = parse_args()
  logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
  logging.info("starting consumer topic=%s brokers=%s", args.topic, args.brokers)

  consumer = KafkaConsumer(
      args.topic,
      bootstrap_servers=args.brokers.split(","),
      value_deserializer=lambda m: json.loads(m.decode("utf-8")),
      group_id=args.group,
      enable_auto_commit=True,
      auto_offset_reset="latest",
  )
  ch_client = build_ch_client(args)

  buffer: List[Dict[str, Any]] = []
  last_flush = datetime.now(UTC)

  for msg in consumer:
    try:
      normalized = normalize_row(msg.value)
      buffer.append(normalized)
    except Exception as exc:  # pragma: no cover
      logging.warning("skip invalid row (%s)", exc)
      continue

    elapsed = (datetime.now(UTC) - last_flush).total_seconds()
    if len(buffer) >= args.batch_size or elapsed >= args.flush_interval:
      flush_rows(ch_client, buffer)
      logging.info("inserted %d rows into clickhouse", len(buffer))
      buffer.clear()
      last_flush = datetime.now(UTC)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    logging.info("consumer stopped by user")
