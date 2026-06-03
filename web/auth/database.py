"""SQLite 資料庫初始化與連線。"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "snowtrip.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL DEFAULT '',
                is_verified BOOLEAN NOT NULL DEFAULT 0,
                google_id TEXT UNIQUE,
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                data TEXT NOT NULL,
                label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP DEFAULT NULL
            );
        """)
        # 安全遷移：舊 DB 可能缺少新欄位
        _migrations = [
            "ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN google_id TEXT",
            "ALTER TABLE users ADD COLUMN avatar_url TEXT",
        ]
        for sql in _migrations:
            try:
                conn.execute(sql)
            except Exception:
                pass  # 欄位已存在
