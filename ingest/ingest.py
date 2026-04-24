#!/usr/bin/env python3
"""
Placeholder ingest script.

Replace this file with the real ingest/ingest.py when available.
The dashboard invokes it as:
    python ingest/ingest.py --all --db <nome_audit> --project-dir <directory_path>

It expects stdout output for real-time streaming in the dashboard.
"""

import argparse
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest placeholder")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--db", required=True, help="Nome audit")
    parser.add_argument("--project-dir", required=True, help="Directory progetto")
    args = parser.parse_args()

    nome = args.db
    dir_path = args.project_dir

    print(f"[INGEST] Avvio ingest per audit: {nome}")
    print(f"[INGEST] Directory: {dir_path}")
    sys.stdout.flush()
    time.sleep(1)

    for i in range(1, 4):
        print(f"[INGEST] Step {i}/3 — elaborazione...")
        sys.stdout.flush()
        time.sleep(1)

    print(f"[INGEST] Completato con successo per '{nome}'.")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
