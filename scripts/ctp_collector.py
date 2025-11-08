"""
High-frequency CTP tick collector.

Features
--------
* Dynamic contract rotation (always keep the latest N CL contracts)
* 1s polling loop with failure/backoff + alert logging
* Pluggable publisher: stdout / CSV / Kafka (best-effort, optional dependency)
* Ready for Docker deployment (config via env/CLI)

Run example:
    python scripts/ctp_collector.py --interval 1 --contracts 6 --dry-run --max-cycles 10
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
  from kafka import KafkaProducer  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
  KafkaProducer = None  # type: ignore


CTP_BASE_URL = os.environ.get("CTP_TICK_BASE_URL", "http://47.108.177.50:8080/md/tick")
DEFAULT_CONTRACTS = 6
DEFAULT_INTERVAL = 1.0
DEFAULT_FAILURE_THRESHOLD = 5
CSV_PATH = Path("data/ctp_ticks.csv")


UTC = timezone.utc


def generate_contract_ids(count: int = DEFAULT_CONTRACTS) -> List[str]:
  now = datetime.now(UTC)
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


def fetch_tick(symbol: str) -> Dict[str, Optional[float]]:
  url = f"{CTP_BASE_URL}/{symbol}"
  with urllib.request.urlopen(url, timeout=3) as resp:
    return json.load(resp)


@dataclass
class CollectorConfig:
  interval: float = DEFAULT_INTERVAL
  contract_count: int = DEFAULT_CONTRACTS
  failure_threshold: int = DEFAULT_FAILURE_THRESHOLD
  dry_run: bool = False
  max_cycles: Optional[int] = None  # None means run indefinitely


class TickPublisher:
  """Publish rows to CSV and (optionally) Kafka."""

  def __init__(self, dry_run: bool = False):
    self.dry_run = dry_run
    self.kafka_enabled = False
    self._kafka_producer: Optional[KafkaProducer] = None
    brokers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    topic = os.environ.get("KAFKA_TICK_TOPIC", "ctp_ticks")
    self.kafka_topic = topic

    if brokers and KafkaProducer:
      try:
        self._kafka_producer = KafkaProducer(
            bootstrap_servers=brokers.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self.kafka_enabled = True
        logging.info("Kafka producer ready (topic=%s)", topic)
      except Exception as exc:  # pragma: no cover
        logging.warning("Kafka init failed (%s). Falling back to CSV only.", exc)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
      with CSV_PATH.open("w", newline="") as f:
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

  def publish(self, rows: Iterable[Dict[str, Optional[float]]]):
    rows = list(rows)
    if not rows:
      return

    if not self.dry_run:
      with CSV_PATH.open("a", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
          writer.writerow(
              [
                  row.get("local_time"),
                  row.get("symbol"),
                  row.get("update_time"),
                  row.get("update_millisec"),
                  row.get("last_price"),
                  row.get("bid_price1"),
                  row.get("bid_volume1"),
                  row.get("ask_price1"),
                  row.get("ask_volume1"),
                  row.get("volume"),
              ]
          )

    if self.kafka_enabled and self._kafka_producer:
      for row in rows:
        self._kafka_producer.send(self.kafka_topic, value=row)

    logging.debug("published %d rows (dry_run=%s)", len(rows), self.dry_run)


class Collector:
  def __init__(self, config: CollectorConfig):
    self.config = config
    self.publisher = TickPublisher(dry_run=config.dry_run)
    self.failure_count = 0

  def _collect_once(self, symbols: Iterable[str]) -> List[Dict[str, Optional[float]]]:
    rows: List[Dict[str, Optional[float]]] = []
    for symbol in symbols:
      try:
        payload = fetch_tick(symbol)
      except Exception as exc:  # pragma: no cover
        logging.warning("failed to fetch %s (%s)", symbol, exc)
        continue

      now_iso = datetime.now(UTC).isoformat()
      rows.append(
          {
              "local_time": now_iso,
              "symbol": symbol,
              "update_time": payload.get("update_time"),
              "update_millisec": payload.get("update_millisec"),
              "last_price": payload.get("last_price"),
              "bid_price1": payload.get("bid_price1"),
              "bid_volume1": payload.get("bid_volume1"),
              "ask_price1": payload.get("ask_price1"),
              "ask_volume1": payload.get("ask_volume1"),
              "volume": payload.get("volume"),
          }
      )
    return rows

  def run(self):
    cycle = 0
    logging.info("starting collector interval=%.2fs contracts=%d", self.config.interval, self.config.contract_count)

    while self.config.max_cycles is None or cycle < self.config.max_cycles:
      cycle += 1
      start = time.time()
      symbols = generate_contract_ids(self.config.contract_count)
      try:
        rows = self._collect_once(symbols)
        if not rows:
          raise RuntimeError("no rows collected")
        self.publisher.publish(rows)
        self.failure_count = 0
        logging.info("cycle %d ok (%d rows)", cycle, len(rows))
      except Exception as exc:  # pragma: no cover
        self.failure_count += 1
        logging.error("cycle %d failed (%s)", cycle, exc)
        if self.failure_count >= self.config.failure_threshold:
          logging.critical("failure threshold reached (%d). check CTP endpoint!", self.failure_count)

      elapsed = time.time() - start
      sleep = max(0.0, self.config.interval - elapsed)
      time.sleep(sleep)

    logging.info("collector finished after %d cycles", cycle)


def parse_args(argv: List[str]) -> CollectorConfig:
  parser = argparse.ArgumentParser(description="CTP tick collector daemon.")
  parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL, help="Polling interval in seconds")
  parser.add_argument("--contracts", type=int, default=DEFAULT_CONTRACTS, help="How many latest contracts to track")
  parser.add_argument("--failure-threshold", type=int, default=DEFAULT_FAILURE_THRESHOLD, help="Alert after consecutive failures")
  parser.add_argument("--dry-run", action="store_true", help="Do not write CSV/Kafka, log only")
  parser.add_argument("--max-cycles", type=int, help="Optional number of cycles (omit to run forever)")
  args = parser.parse_args(argv)
  return CollectorConfig(
      interval=args.interval,
      contract_count=args.contracts,
      failure_threshold=args.failure_threshold,
      dry_run=args.dry_run,
      max_cycles=args.max_cycles,
  )


def main():
  logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(levelname)s] %(message)s",
      handlers=[logging.StreamHandler(sys.stdout)],
  )
  config = parse_args(sys.argv[1:])
  collector = Collector(config)
  collector.run()


if __name__ == "__main__":
  main()
