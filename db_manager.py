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


def get_all_findings(db_path: str) -> list[dict]:
    """Return all rows from the findings table."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM findings").fetchall()
    conn.close()
    return [dict(r) for r in rows]
