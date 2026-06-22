from dataclasses import dataclass
from decimal import Decimal

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    coin_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('above', 'below')),
    target_price TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    triggered_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alerts_active_coin_id
ON alerts(active, coin_id);

CREATE INDEX IF NOT EXISTS idx_alerts_user_active
ON alerts(user_id, active);
"""


@dataclass(frozen=True, slots=True)
class Alert:
    id: int
    user_id: int
    ticker: str
    coin_id: str
    direction: str
    target_price: Decimal
    active: bool
