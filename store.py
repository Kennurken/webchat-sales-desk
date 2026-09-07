import csv
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class LeadRecord:
    id: int
    created_at: str
    visitor_name: str
    email: str
    channel: str
    interest: str
    budget: str
    status: str


class LeadStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                visitor_name TEXT NOT NULL,
                email TEXT NOT NULL,
                channel TEXT NOT NULL,
                interest TEXT NOT NULL,
                budget TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new'
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                step TEXT NOT NULL,
                visitor_name TEXT,
                email TEXT,
                channel TEXT,
                interest TEXT,
                budget TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def get_session(self, session_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM chat_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None

    def upsert_session(self, session_id: str, **fields) -> None:
        existing = self.get_session(session_id)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO chat_sessions (
                    session_id, step, visitor_name, email, channel, interest, budget, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    fields.get("step", "ask_name"),
                    fields.get("visitor_name"),
                    fields.get("email"),
                    fields.get("channel"),
                    fields.get("interest"),
                    fields.get("budget"),
                    now,
                ),
            )
        else:
            merged = {**existing, **fields, "updated_at": now}
            self._conn.execute(
                """
                UPDATE chat_sessions SET
                    step = ?, visitor_name = ?, email = ?, channel = ?,
                    interest = ?, budget = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (
                    merged["step"],
                    merged.get("visitor_name"),
                    merged.get("email"),
                    merged.get("channel"),
                    merged.get("interest"),
                    merged.get("budget"),
                    merged["updated_at"],
                    session_id,
                ),
            )
        self._conn.commit()

    def clear_session(self, session_id: str) -> None:
        self._conn.execute(
            "DELETE FROM chat_sessions WHERE session_id = ?",
            (session_id,),
        )
        self._conn.commit()

    def add_lead(
        self,
        *,
        visitor_name: str,
        email: str,
        channel: str,
        interest: str,
        budget: str,
    ) -> LeadRecord:
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cursor = self._conn.execute(
            """
            INSERT INTO leads (
                created_at, visitor_name, email, channel, interest, budget, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'new')
            """,
            (
                created_at,
                visitor_name.strip(),
                email.strip().lower(),
                channel.strip(),
                interest.strip(),
                budget.strip(),
            ),
        )
        self._conn.commit()
        return LeadRecord(
            id=int(cursor.lastrowid),
            created_at=created_at,
            visitor_name=visitor_name.strip(),
            email=email.strip().lower(),
            channel=channel.strip(),
            interest=interest.strip(),
            budget=budget.strip(),
            status="new",
        )

    def list_recent(self, limit: int = 50) -> list[LeadRecord]:
        rows = self._conn.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            LeadRecord(
                id=row["id"],
                created_at=row["created_at"],
                visitor_name=row["visitor_name"],
                email=row["email"],
                channel=row["channel"],
                interest=row["interest"],
                budget=row["budget"],
                status=row["status"],
            )
            for row in rows
        ]

    def export_csv(self, csv_path: Path) -> int:
        leads = list(reversed(self.list_recent(10_000)))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "id",
                    "created_at",
                    "visitor_name",
                    "email",
                    "channel",
                    "interest",
                    "budget",
                    "status",
                ],
            )
            writer.writeheader()
            for lead in leads:
                writer.writerow(
                    {
                        "id": lead.id,
                        "created_at": lead.created_at,
                        "visitor_name": lead.visitor_name,
                        "email": lead.email,
                        "channel": lead.channel,
                        "interest": lead.interest,
                        "budget": lead.budget,
                        "status": lead.status,
                    }
                )
        return len(leads)

    def close(self) -> None:
        self._conn.close()
