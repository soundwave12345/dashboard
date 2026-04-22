#!/usr/bin/env python3
"""
Placeholder ingest script.

Replace this file with the real ingest/ingest.py when available.
The dashboard invokes it as:
    python ingest/ingest.py <nome_audit> <data> <directory_path>

It expects stdout output for real-time streaming in the dashboard.
"""

import sys
import time


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: ingest.py <nome_audit> <data> <directory_path>")
        sys.exit(1)

    nome, data, dir_path = sys.argv[1], sys.argv[2], sys.argv[3]

    print(f"[INGEST] Avvio ingest per audit: {nome}")
    print(f"[INGEST] Data: {data}")
    print(f"[INGEST] Directory: {dir_path}")
    time.sleep(1)

    for i in range(1, 4):
        print(f"[INGEST] Step {i}/3 — elaborazione...")
        time.sleep(1)

    print(f"[INGEST] Completato con successo per '{nome}'.")


if __name__ == "__main__":
    main()
