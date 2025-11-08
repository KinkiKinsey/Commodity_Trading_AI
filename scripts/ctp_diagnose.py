"""
Simple diagnostics helper for the CTP docker stack.

Run:
    python scripts/ctp_diagnose.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path


COMPOSE_FILE = "docker-compose.ctp.yml"
ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> str:
  result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, shell=False)
  output = (result.stdout or "") + (result.stderr or "")
  return output.strip()


def main():
  print("=== docker compose ps ===")
  print(run(["docker", "compose", "-f", COMPOSE_FILE, "ps"]))

  print("\n=== collector logs (tail 20) ===")
  print(run(["docker", "compose", "-f", COMPOSE_FILE, "logs", "--tail=20", "collector"]))

  print("\n=== kafka topic describe ===")
  print(
      run(
          [
              "docker",
              "compose",
              "-f",
              COMPOSE_FILE,
              "exec",
              "kafka",
              "kafka-topics",
              "--bootstrap-server",
              "kafka:9092",
              "--describe",
              "--topic",
              "ctp_ticks",
          ]
      )
  )

  print("\n=== clickhouse tick count ===")
  print(
      run(
          [
              "docker",
              "compose",
              "-f",
              COMPOSE_FILE,
              "exec",
              "clickhouse",
              "clickhouse-client",
              "-q",
              "SELECT count() FROM ctp.ctp_ticks",
          ]
      )
  )


if __name__ == "__main__":
  main()
