#!/usr/bin/env python3
"""FUNC-106: SQLite → PostgreSQL 一次性匯入腳本.

用法:
    python scripts/migrate_sqlite_to_postgres.py --sqlite-path /path/to/snowtrip.db

對應 SD code-arch.md §5 規格。
AC-056: SQLite 檔不存在 → exit 0 + 訊息「無 SQLite 資料需匯入」
       FK 違反 → log warning + skip + 繼續

PG 連線資訊讀 env vars（同 MOD-101）。
不依賴 web.auth.database — 為一次性工具，可獨立執行。
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _build_dsn() -> str:
    """從 env vars 構造 PG DSN（同 MOD-101 _build_dsn_from_env）。"""
    import os
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return dsn
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")
    sslmode = os.environ.get("POSTGRES_SSL_MODE", "disable")
    if not all([host, user, password, db]):
        raise RuntimeError(
            "Missing required PostgreSQL env vars "
            "(POSTGRES_HOST/USER/PASSWORD/DB) or DATABASE_URL"
        )
    return (
        f"host={host} port={port} user={user} password={password} "
        f"dbname={db} sslmode={sslmode}"
    )


def _read_sqlite_rows(sqlite_path: Path, table: str) -> list[dict]:
    """讀 SQLite 表全部 row。"""
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _insert_users(pg_conn, rows: list[dict]) -> int:
    """匯入 users 表 — 用 OVERRIDING SYSTEM VALUE 保留歷史 id。"""
    n_ok = 0
    for r in rows:
        # SQLite is_verified 為 0/1 → PG BOOLEAN
        is_verified = bool(r.get("is_verified", 0))
        # SQLite created_at 為 ISO 字串 → PG TIMESTAMPTZ
        created_at = r.get("created_at")
        # backfill updated_at = created_at
        updated_at = created_at
        try:
            pg_conn.execute(
                "INSERT INTO users (id, email, username, hashed_password, "
                "is_verified, google_id, avatar_url, created_at, updated_at, deleted_at) "
                "OVERRIDING SYSTEM VALUE "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)",
                (
                    r["id"], r["email"], r["username"],
                    r.get("hashed_password", ""), is_verified,
                    r.get("google_id"), r.get("avatar_url"),
                    created_at, updated_at,
                ),
            )
            n_ok += 1
        except Exception as exc:
            print(f"[WARN] users id={r.get('id')} insert failed: {exc}", file=sys.stderr)
    return n_ok


def _insert_favorites(pg_conn, rows: list[dict]) -> int:
    n_ok = 0
    for r in rows:
        created_at = r.get("created_at")
        updated_at = created_at
        try:
            pg_conn.execute(
                "INSERT INTO favorites (id, user_id, type, data, label, "
                "created_at, updated_at, deleted_at) "
                "OVERRIDING SYSTEM VALUE "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)",
                (
                    r["id"], r["user_id"], r["type"], r["data"],
                    r.get("label"), created_at, updated_at,
                ),
            )
            n_ok += 1
        except Exception as exc:
            print(f"[WARN] favorites id={r.get('id')} insert failed: {exc}", file=sys.stderr)
    return n_ok


def _insert_tokens(pg_conn, rows: list[dict]) -> int:
    n_ok = 0
    for r in rows:
        # SQLite 無 created_at → backfill = expires_at - 24h
        expires_at = r.get("expires_at")
        # 由 PG 端解析 ISO 字串時加 INTERVAL
        try:
            pg_conn.execute(
                "INSERT INTO email_verification_tokens (id, user_id, token, "
                "expires_at, used_at, created_at, updated_at, deleted_at) "
                "OVERRIDING SYSTEM VALUE "
                "VALUES (%s, %s, %s, %s, %s, "
                "(%s::timestamptz - INTERVAL '24 hours'), "
                "(%s::timestamptz - INTERVAL '24 hours'), NULL)",
                (
                    r["id"], r["user_id"], r["token"],
                    expires_at, r.get("used_at"),
                    expires_at, expires_at,
                ),
            )
            n_ok += 1
        except Exception as exc:
            print(f"[WARN] tokens id={r.get('id')} insert failed: {exc}", file=sys.stderr)
    return n_ok


def _reset_identity(pg_conn, table: str) -> None:
    """Reset IDENTITY 起始值避免後續 INSERT 衝突歷史 id。"""
    pg_conn.execute(
        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
        f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
    )


def main(sqlite_path: Path) -> int:
    if not sqlite_path.exists():
        print(f"[INFO] SQLite file not found at {sqlite_path}")
        print("[INFO] 無 SQLite 資料需匯入. exit 0")
        return 0

    print(f"[INFO] SQLite file: {sqlite_path}")
    print(f"[INFO] PostgreSQL: from env vars (POSTGRES_HOST/USER/DB or DATABASE_URL)")

    try:
        from psycopg import connect
    except ImportError:
        print("[ERROR] psycopg not installed — pip install 'psycopg[binary]'")
        return 1

    users = _read_sqlite_rows(sqlite_path, "users")
    favorites = _read_sqlite_rows(sqlite_path, "favorites")
    tokens = _read_sqlite_rows(sqlite_path, "email_verification_tokens")
    print(f"[INFO] Reading users... {len(users)} rows")
    print(f"[INFO] Reading favorites... {len(favorites)} rows")
    print(f"[INFO] Reading email_verification_tokens... {len(tokens)} rows")

    dsn = _build_dsn()
    with connect(dsn) as conn:
        with conn.cursor() as cur:
            print("[INFO] Inserting users (with OVERRIDING SYSTEM VALUE)...")
            u_ok = _insert_users(cur, users)
            print(f"[INFO] users {u_ok}/{len(users)} ok")
            print("[INFO] Inserting favorites...")
            f_ok = _insert_favorites(cur, favorites)
            print(f"[INFO] favorites {f_ok}/{len(favorites)} ok")
            print("[INFO] Inserting email_verification_tokens...")
            t_ok = _insert_tokens(cur, tokens)
            print(f"[INFO] tokens {t_ok}/{len(tokens)} ok")
            print("[INFO] Resetting IDENTITY sequences...")
            _reset_identity(cur, "users")
            _reset_identity(cur, "favorites")
            _reset_identity(cur, "email_verification_tokens")
        conn.commit()

    print(
        f"[INFO] Verifying counts: SQLite {len(users)}/{len(favorites)}/{len(tokens)} "
        f"vs PG {u_ok}/{f_ok}/{t_ok}"
    )
    if u_ok == len(users) and f_ok == len(favorites) and t_ok == len(tokens):
        print("[INFO] MATCH — Done. exit 0")
        return 0
    else:
        print("[WARN] Count mismatch — see [WARN] lines above. exit 0 (skipped rows tolerated)")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SQLite → PostgreSQL one-shot import (TASK-002 FUNC-106)",
    )
    parser.add_argument(
        "--sqlite-path", required=True, type=Path,
        help="Path to existing SQLite snowtrip.db file",
    )
    args = parser.parse_args()
    sys.exit(main(args.sqlite_path))
