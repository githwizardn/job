"""SQLite — ვაკანსიების ისტორია, აპლიკაციების tracking."""
import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

from models import Job

DB_PATH = Path("jobs.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    fp          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    title       TEXT NOT NULL,
    url         TEXT NOT NULL,
    company     TEXT,
    location    TEXT,
    posted      TEXT,
    deadline    TEXT,
    salary      TEXT,
    remote      INTEGER DEFAULT 0,
    description TEXT,
    geo_status  TEXT,
    score       INTEGER DEFAULT 0,
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL,
    applied     INTEGER DEFAULT 0,
    favorite    INTEGER DEFAULT 0,
    note        TEXT
);
CREATE INDEX IF NOT EXISTS idx_first_seen ON jobs(first_seen DESC);
CREATE INDEX IF NOT EXISTS idx_score      ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_applied    ON jobs(applied);
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def fingerprint(job: Job) -> str:
    key = f"{job.url}|{job.title}|{job.company}".lower().strip()
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def upsert(conn, jobs: Iterable[Job], score_fn=None) -> list[Job]:
    """
    ჩაწერს ვაკანსიებს. აბრუნებს მხოლოდ *ახლებს* (რაც არ გვინახავს).
    უკვე ნანახებს განაახლებს last_seen-ს.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new: list[Job] = []

    for j in jobs:
        fp = fingerprint(j)
        existing = conn.execute("SELECT 1 FROM jobs WHERE fp = ?", (fp,)).fetchone()
        if existing:
            conn.execute("UPDATE jobs SET last_seen = ? WHERE fp = ?", (now, fp))
            continue

        sc = score_fn(j) if score_fn else 0
        conn.execute(
            """
            INSERT INTO jobs (
                fp, source, title, url, company, location,
                posted, deadline, salary, remote, description,
                geo_status, score, first_seen, last_seen
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                fp, j.source, j.title, j.url, j.company, j.location,
                j.posted, j.deadline, j.salary, int(j.remote), j.description,
                j.geo_status, sc, now, now,
            ),
        )
        new.append(j)

    conn.commit()
    return new


def get_jobs(
    conn,
    only_new_hours: Optional[int] = None,
    only_applied: Optional[int] = None,
    only_favorite: Optional[int] = None,
    source: Optional[str] = None,
    limit: int = 500,
) -> list[dict]:
    q = "SELECT * FROM jobs WHERE 1=1"
    args: list = []

    if only_new_hours:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=only_new_hours)
        ).isoformat(timespec="seconds")
        q += " AND first_seen >= ?"
        args.append(cutoff)

    if only_applied is not None:
        q += " AND applied = ?"
        args.append(only_applied)

    if only_favorite is not None:
        q += " AND favorite = ?"
        args.append(only_favorite)

    if source:
        q += " AND source = ?"
        args.append(source)

    q += " ORDER BY score DESC, first_seen DESC LIMIT ?"
    args.append(limit)

    return [dict(r) for r in conn.execute(q, args).fetchall()]

def mark_applied(conn, fp: str, applied: bool = True) -> None:
    conn.execute("UPDATE jobs SET applied = ? WHERE fp = ?", (int(applied), fp))
    conn.commit()


def toggle_favorite(conn, fp: str) -> None:
    conn.execute("UPDATE jobs SET favorite = 1 - favorite WHERE fp = ?", (fp,))
    conn.commit()


def set_note(conn, fp: str, note: str) -> None:
    conn.execute("UPDATE jobs SET note = ? WHERE fp = ?", (note, fp))
    conn.commit()


def stats(conn) -> dict:
    row = conn.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN applied = 1 THEN 1 ELSE 0 END) as applied,
            SUM(CASE WHEN favorite = 1 THEN 1 ELSE 0 END) as favorite,
            SUM(CASE WHEN first_seen >= datetime('now', '-24 hours') THEN 1 ELSE 0 END) as last_24h
        FROM jobs
        """
    ).fetchone()
    return dict(row) if row else {"total": 0, "applied": 0, "favorite": 0, "last_24h": 0}
    row = conn.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN applied = 1 THEN 1 ELSE 0 END) as applied,
            SUM(CASE WHEN first_seen >= datetime('now', '-24 hours') THEN 1 ELSE 0 END) as last_24h
        FROM jobs
        """
    ).fetchone()
    return dict(row) if row else {"total": 0, "applied": 0, "last_24h": 0}