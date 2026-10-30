"""SQLite job store. Each operation uses its own connection."""
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def connect() -> sqlite3.Connection:
    path = Path(os.environ.get("DOCUMENT_DB_PATH", "data/jobs.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with closing(connect()) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT
                )
            """)
            connection.execute(
                "UPDATE jobs SET status = 'failed', error = 'interrupted by server restart' "
                "WHERE status = 'queued'"
            )


def create_job(job_id: str) -> None:
    with closing(connect()) as connection:
        with connection:
            connection.execute(
                "INSERT INTO jobs (id, status, created_at) VALUES (?, ?, ?)",
                (job_id, "queued", datetime.now(timezone.utc).isoformat()),
            )


def finish_job(job_id: str, result: dict | None = None, error: str | None = None) -> None:
    status = "failed" if error else "completed"
    with closing(connect()) as connection:
        with connection:
            connection.execute(
                "UPDATE jobs SET status = ?, result_json = ?, error = ? WHERE id = ?",
                (status, json.dumps(result) if result is not None else None, error, job_id),
            )


def serialize_job(row: sqlite3.Row) -> dict:
    job = {"job_id": row["id"], "status": row["status"], "created_at": row["created_at"]}
    if row["result_json"] is not None:
        job["result"] = json.loads(row["result_json"])
    if row["error"] is not None:
        job["error"] = row["error"]
    return job


def get_job(job_id: str) -> dict | None:
    with closing(connect()) as connection:
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return serialize_job(row) if row is not None else None


def list_jobs(limit: int = 20) -> list[dict]:
    with closing(connect()) as connection:
        rows = connection.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [serialize_job(row) for row in rows]
