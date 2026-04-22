"""Database management module for audit dashboard."""

import os
import sqlite3
from datetime import datetime
from typing import Optional


MASTER_DB = "audit_master.db"
AUDITS_DIR = "audits"


def get_master_connection() -> sqlite3.Connection:
    """Return a connection to the master database, creating tables if needed."""
    conn = sqlite3.connect(MASTER_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_audit TEXT NOT NULL UNIQUE,
            data_creazione TEXT NOT NULL,
            directory_path TEXT NOT NULL,
            db_path TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def list_audits() -> list[dict]:
    """Return all registered audits from the master database."""
    conn = get_master_connection()
    try:
        rows = conn.execute(
            "SELECT id, nome_audit, data_creazione, directory_path, db_path "
            "FROM audits ORDER BY data_creazione DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def register_audit(nome_audit: str, directory_path: str, db_path: str) -> int:
    """Insert a new audit into the master database. Returns the new id."""
    conn = get_master_connection()
    try:
        cur = conn.execute(
            "INSERT INTO audits (nome_audit, data_creazione, directory_path, db_path) "
            "VALUES (?, ?, ?, ?)",
            (nome_audit, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             directory_path, db_path),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Audit '{nome_audit}' already exists.")
    finally:
        conn.close()


def delete_audit(nome_audit: str) -> None:
    """Remove an audit record from the master database."""
    conn = get_master_connection()
    try:
        conn.execute("DELETE FROM audits WHERE nome_audit = ?", (nome_audit,))
        conn.commit()
    finally:
        conn.close()


def create_audit_directories(nome_audit: str) -> tuple[str, str]:
    """Create directory and SQLite file for a new audit.

    Returns (directory_path, db_path).
    Raises FileExistsError if the directory already exists.
    """
    dir_path = os.path.join(AUDITS_DIR, nome_audit)
    db_path = os.path.join(dir_path, f"{nome_audit}.db")

    if os.path.exists(dir_path):
        raise FileExistsError(f"Directory '{dir_path}' already exists.")

    os.makedirs(dir_path, exist_ok=False)

    # Initialise the per-audit database with placeholder tables
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    return dir_path, db_path


def get_audit_db_path(nome_audit: str) -> Optional[str]:
    """Look up the db_path for a given audit name."""
    conn = get_master_connection()
    try:
        row = conn.execute(
            "SELECT db_path FROM audits WHERE nome_audit = ?", (nome_audit,)
        ).fetchone()
        return row["db_path"] if row else None
    finally:
        conn.close()


# ── Helpers for placeholder data ──────────────────────────────────────────

def seed_placeholder_data(db_path: str) -> None:
    """Insert sample findings so the pie charts have something to show."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    count = cur.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
    if count > 0:
        conn.close()
        return

    samples = [
        ("Access Control", "High", "Admin panel exposed without auth"),
        ("Access Control", "Medium", "Stale service account found"),
        ("Cryptography", "High", "TLS 1.0 still enabled"),
        ("Cryptography", "Low", "Self-signed cert in staging"),
        ("Data Protection", "High", "PII stored unencrypted"),
        ("Data Protection", "Medium", "Backup retention too long"),
        ("Network", "Medium", "Unnecessary port 22 open"),
        ("Network", "Low", "ICMP flood not rate-limited"),
        ("Compliance", "Low", "Policy doc outdated"),
        ("Compliance", "Medium", "Missing audit log for deletes"),
    ]
    cur.executemany(
        "INSERT INTO findings (category, severity, description) VALUES (?, ?, ?)",
        samples,
    )
    conn.commit()
    conn.close()


def get_findings_by_category(db_path: str) -> list[dict]:
    """Return (category, count) pairs."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT category, COUNT(*) as count FROM findings GROUP BY category"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_findings_by_severity(db_path: str) -> list[dict]:
    """Return (severity, count) pairs."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT severity, COUNT(*) as count FROM findings GROUP BY severity"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
