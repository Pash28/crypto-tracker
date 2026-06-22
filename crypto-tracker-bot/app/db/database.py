from decimal import Decimal
from pathlib import Path
from typing import Any

import aiosqlite

from app.db.models import SCHEMA_SQL, Alert


class DatabaseError(RuntimeError):
    pass


class Database:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.execute("PRAGMA journal_mode = WAL")
        await self._connection.commit()

    async def init(self) -> None:
        conn = self._conn
        await conn.executescript(SCHEMA_SQL)
        await conn.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def upsert_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
    ) -> None:
        try:
            await self._conn.execute(
                """
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (telegram_id, username, first_name),
            )
            await self._conn.commit()
        except aiosqlite.Error as exc:
            raise DatabaseError("Could not save user data.") from exc

    async def create_alert(
        self,
        user_id: int,
        ticker: str,
        coin_id: str,
        direction: str,
        target_price: Decimal,
    ) -> int:
        try:
            cursor = await self._conn.execute(
                """
                INSERT INTO alerts (user_id, ticker, coin_id, direction, target_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, ticker, coin_id, direction, str(target_price)),
            )
            await self._conn.commit()
            return int(cursor.lastrowid)
        except aiosqlite.Error as exc:
            raise DatabaseError("Could not create alert.") from exc

    async def list_user_alerts(self, user_id: int) -> list[Alert]:
        try:
            cursor = await self._conn.execute(
                """
                SELECT id, user_id, ticker, coin_id, direction, target_price, active
                FROM alerts
                WHERE user_id = ? AND active = 1
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [_alert_from_row(row) for row in rows]
        except aiosqlite.Error as exc:
            raise DatabaseError("Could not load alerts.") from exc

    async def get_active_alerts(self) -> list[Alert]:
        try:
            cursor = await self._conn.execute(
                """
                SELECT id, user_id, ticker, coin_id, direction, target_price, active
                FROM alerts
                WHERE active = 1
                ORDER BY created_at ASC
                """
            )
            rows = await cursor.fetchall()
            return [_alert_from_row(row) for row in rows]
        except aiosqlite.Error as exc:
            raise DatabaseError("Could not load active alerts.") from exc

    async def deactivate_alert(self, alert_id: int) -> None:
        try:
            await self._conn.execute(
                """
                UPDATE alerts
                SET active = 0, triggered_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (alert_id,),
            )
            await self._conn.commit()
        except aiosqlite.Error as exc:
            raise DatabaseError("Could not deactivate alert.") from exc

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        try:
            cursor = await self._conn.execute(
                "DELETE FROM alerts WHERE id = ? AND user_id = ? AND active = 1",
                (alert_id, user_id),
            )
            await self._conn.commit()
            return cursor.rowcount > 0
        except aiosqlite.Error as exc:
            raise DatabaseError("Could not delete alert.") from exc

    @property
    def _conn(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise DatabaseError("Database is not connected.")
        return self._connection


def _alert_from_row(row: Any) -> Alert:
    return Alert(
        id=int(row["id"]),
        user_id=int(row["user_id"]),
        ticker=str(row["ticker"]),
        coin_id=str(row["coin_id"]),
        direction=str(row["direction"]),
        target_price=Decimal(str(row["target_price"])),
        active=bool(row["active"]),
    )
