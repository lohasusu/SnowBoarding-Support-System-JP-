"""DEPRECATED: SQLite legacy driver — kept as 14-day emergency rollback path.

DO NOT IMPORT FROM THIS MODULE in new code.

Lifecycle:
- Created: TASK-002 cutover (2026-06-11)
- Retire: T+14 days — by follow-up TASK `remove-sqlite-legacy-path`
- Purpose: 若 PG 在切換後 14 天內發生不可恢復災難（資料毀損 / 連線完全失能 > 1 hr），
  可走 `git revert {pg-migration-merge-commit}` 回滾到 SQLite 部署。
- Reference: SUG-006 + CONST-009 + deploy-env.json _deploymentDecisions.backupRollback.sqliteEmergencyPath

Rollback steps (14 天 window 內):
1. Railway dashboard → 移除 POSTGRES_* env vars
2. git revert {pg-migration-merge-commit}
3. git push → Railway 自動 redeploy SQLite 版本
4. 接受 SQLite ephemeral 缺陷重現作為 emergency tradeoff
"""
# ↓↓↓ 以下為既有 web/auth/database.py 原內容（保留 git history 可讀） ↓↓↓
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
