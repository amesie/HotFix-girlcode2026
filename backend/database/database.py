"""SQLite data-access layer for Verifi.

The only module in the backend that talks to a datastore. Route code
must never see a cursor, a connection, or raw SQL here — if we ever swap
the datastore, only this file changes.

Uses the stdlib ``sqlite3`` module only: no ORM, no hosted database, no
migration framework. Five demo records don't need one, and a 10-hour
hackathon on conference wifi can't afford the setup time.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

# Resolved from __file__, not the current working directory, so the DB
# lands in the same place regardless of where uvicorn was launched from.
_REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = _REPO_ROOT / "data" / "verifi.db"
MARRIAGES_JSON_PATH = _REPO_ROOT / "data" / "synthetic" / "marriages.json"

# Hardcoded fallback so the API works standalone even if marriages.json
# doesn't exist yet or is mid-edit. Keys match the demo ID table in the
# project brief.
_FALLBACK_RECORDS: list[dict[str, Any]] = [
    {
        "id_number": "9001015800083",
        "marital_status": "single",
        "is_deceased": 0,
        "is_blocked": 0,
        "duplicate_of": None,
        "notes": "Clean record, no flags (demo fallback).",
    },
    {
        "id_number": "8505124800086",
        "marital_status": "married",
        "is_deceased": 0,
        "is_blocked": 0,
        "duplicate_of": None,
        "notes": "Fraudulent marriage on record (demo fallback).",
    },
    {
        "id_number": "7712089800081",
        "marital_status": "single",
        "is_deceased": 0,
        "is_blocked": 0,
        "duplicate_of": "7712089800081-DUP",
        "notes": "Duplicate ID on record (demo fallback).",
    },
    {
        "id_number": "6003215800084",
        "marital_status": "single",
        "is_deceased": 1,
        "is_blocked": 0,
        "duplicate_of": None,
        "notes": "Deceased flag (demo fallback).",
    },
    {
        "id_number": "9506306800082",
        "marital_status": "single",
        "is_deceased": 0,
        "is_blocked": 1,
        "duplicate_of": None,
        "notes": "Blocked ID (demo fallback).",
    },
]

# Tracks how the data currently in SQLite got there, for GET /health.
# "json" | "fallback"; set by seed(). Not persisted — recomputed each boot.
_last_seed_source: str | None = None


def mask_id(id_number: str) -> str:
    """Mask an ID number for logs/errors: first 6 and last 2 digits only.

    Never log or echo a full ID number — this product is about identity
    fraud, so leaking IDs in our own logs would be a bad look.
    """
    if len(id_number) <= 8:
        return "*" * len(id_number)
    middle = "*" * (len(id_number) - 8)
    return f"{id_number[:6]}{middle}{id_number[-2:]}"


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    """Open a short-lived connection for a single call.

    sqlite3 connections aren't safe to share across threads, and FastAPI
    runs sync handlers in a threadpool. Rather than keep one connection
    alive with check_same_thread=False plus a lock, we open/close a
    connection per call: at this scale (a handful of rows, a hackathon
    demo) the connect overhead is negligible and it sidesteps thread
    safety entirely.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the schema if it doesn't exist yet. Safe to call every boot."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS identity_records (
                id_number TEXT PRIMARY KEY,
                marital_status TEXT,
                is_deceased INTEGER NOT NULL DEFAULT 0,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                duplicate_of TEXT,
                notes TEXT
            )
            """
        )
    logger.info("Database schema ready at %s", DB_PATH)


def _normalize_record(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Map a marriages.json entry onto our column names.

    The teammate's JSON schema isn't finalized (the file is empty as of
    this writing), so accept both snake_case and camelCase keys rather
    than hard-failing the whole seed over a naming mismatch.
    """
    id_number = raw.get("id_number") or raw.get("idNumber")
    if not id_number:
        return None
    return {
        "id_number": str(id_number),
        "marital_status": raw.get("marital_status") or raw.get("maritalStatus"),
        "is_deceased": int(bool(raw.get("is_deceased") or raw.get("isDeceased") or False)),
        "is_blocked": int(bool(raw.get("is_blocked") or raw.get("isBlocked") or False)),
        "duplicate_of": raw.get("duplicate_of") or raw.get("duplicateOf"),
        "notes": raw.get("notes"),
    }


def _load_from_json() -> list[dict[str, Any]] | None:
    """Return normalized records from marriages.json, or None on any problem.

    None covers "missing", "empty", "malformed", and "no usable records"
    alike — the caller (seed()) decides whether to fall back to demo data
    or keep whatever is already in SQLite.
    """
    if not MARRIAGES_JSON_PATH.exists():
        logger.warning("marriages.json not found at %s; using fallback demo data", MARRIAGES_JSON_PATH)
        return None

    try:
        raw_text = MARRIAGES_JSON_PATH.read_text(encoding="utf-8").strip()
        if not raw_text:
            logger.warning("marriages.json is empty; using fallback demo data")
            return None
        data = json.loads(raw_text)
    except (OSError, json.JSONDecodeError) as exc:
        # The teammate may be editing this file live while we're running.
        # Never let a bad file take the API down mid-demo.
        logger.error("marriages.json is malformed, keeping existing data: %s", exc)
        return None

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("records") or data.get("marriages") or []
    else:
        items = []

    if not isinstance(items, list):
        logger.error("marriages.json has an unexpected shape; using fallback demo data")
        return None

    records = [r for r in (_normalize_record(item) for item in items if isinstance(item, dict)) if r]
    if not records:
        logger.warning("marriages.json parsed but contained no usable records")
        return None
    return records


def _upsert(records: list[dict[str, Any]]) -> None:
    """Insert or update records, keyed by id_number. Always parameterised."""
    with _connection() as conn:
        conn.executemany(
            """
            INSERT INTO identity_records
                (id_number, marital_status, is_deceased, is_blocked, duplicate_of, notes)
            VALUES (:id_number, :marital_status, :is_deceased, :is_blocked, :duplicate_of, :notes)
            ON CONFLICT(id_number) DO UPDATE SET
                marital_status = excluded.marital_status,
                is_deceased = excluded.is_deceased,
                is_blocked = excluded.is_blocked,
                duplicate_of = excluded.duplicate_of,
                notes = excluded.notes
            """,
            records,
        )


def _count_records() -> int:
    with _connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM identity_records").fetchone()
        return int(row["n"])


def seed() -> None:
    """Idempotent upsert from marriages.json, falling back to demo data.

    Safe to call on every boot and again via reseed(): ON CONFLICT DO
    UPDATE means re-running never duplicates rows.
    """
    global _last_seed_source
    records = _load_from_json()
    if records:
        _upsert(records)
        _last_seed_source = "json"
        logger.info("Seeded %d record(s) from marriages.json", len(records))
        return

    # JSON missing/empty/malformed. If we already have data from a prior
    # successful seed this session, leave it alone rather than nuking a
    # working demo because the teammate is mid-edit on the file.
    if _count_records() == 0:
        _upsert(_FALLBACK_RECORDS)
        _last_seed_source = "fallback"
        logger.warning(
            "Seeded %d fallback demo record(s) (no usable marriages.json)",
            len(_FALLBACK_RECORDS),
        )


def reseed() -> None:
    """Force a re-read of marriages.json without restarting the server."""
    logger.info("Reseed requested")
    seed()


def get_records_for_id(id_number: str) -> list[dict[str, Any]]:
    """Look up records for a single ID number. Empty list if not found."""
    with _connection() as conn:
        rows = conn.execute(
            "SELECT * FROM identity_records WHERE id_number = ?",
            (id_number,),
        ).fetchall()
    return [dict(row) for row in rows]


def all_records() -> list[dict[str, Any]]:
    """Return every record. Small demo dataset only — no pagination needed."""
    with _connection() as conn:
        rows = conn.execute("SELECT * FROM identity_records").fetchall()
    return [dict(row) for row in rows]


def health() -> dict[str, Any]:
    """Snapshot for GET /health: datasource, seed source, record count."""
    return {
        "datasource": "sqlite",
        "seededFrom": _last_seed_source or "fallback",
        "recordCount": _count_records(),
    }
