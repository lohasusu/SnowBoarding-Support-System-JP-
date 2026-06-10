"""PostgreSQL 連線層 — MOD-101 postgres_db.

替換既有 SQLite 實作（TASK-001 brownfield）；介面語意保留：
- get_conn() 仍是 context manager，with 區塊內可 execute SQL
- 唯一可見差異：conn 物件型別為 psycopg.Connection，placeholder 改用 %s
- row 物件為 dict-like（透過 row_factory），與既有 sqlite3.Row 介面相容

對應 SD code-arch.md §3.1 MOD-101。
對應 SA functional-flow.md FUNC-101（pool 就緒）/ FUNC-102（pool 關閉）。
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# 模組級 pool — 由 init_pool() 啟動，close_pool() 關閉
_pool: ConnectionPool | None = None


def _build_dsn_from_env() -> str:
    """從 env vars 構造 PostgreSQL DSN。

    優先順序：DATABASE_URL → 個別 POSTGRES_*。
    依 service-contract.yaml + parameter-plan.md 12 個 parameter。

    Raises:
        RuntimeError: 缺必要 env vars 時拋出（不洩漏 password — NFR-011 / ERR-SYS-006）
    """
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return dsn

    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")
    sslmode = os.environ.get("POSTGRES_SSL_MODE", "disable")

    missing = [k for k, v in {
        "POSTGRES_HOST": host,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": db,
    }.items() if not v]
    if missing:
        # ERR-SYS-006: 不在訊息中洩漏 password 值（NFR-011）
        raise RuntimeError(
            f"[ERR-SYS-006] Missing required PostgreSQL env vars: "
            f"{', '.join(missing)}. "
            "Set them in .env (dev) or Railway dashboard (prod), "
            "or provide DATABASE_URL as a fallback."
        )

    return (
        f"host={host} port={port} user={user} password={password} "
        f"dbname={db} sslmode={sslmode}"
    )


def init_pool() -> None:
    """FastAPI startup 時呼叫 — 啟動 connection pool。

    Raises:
        RuntimeError: env vars 缺失（ERR-SYS-006）
        psycopg.OperationalError: 連線失敗（ERR-DB-001）— 阻擋 app 啟動
    """
    global _pool
    if _pool is not None:
        return  # 重複初始化保護（FastAPI lifespan reload 場景）

    dsn = _build_dsn_from_env()
    min_size = int(os.environ.get("POSTGRES_POOL_MIN", "2"))
    max_size = int(os.environ.get("POSTGRES_POOL_MAX", "10"))
    timeout_ms = int(os.environ.get("POSTGRES_POOL_TIMEOUT_MS", "5000"))
    timeout_s = timeout_ms / 1000.0

    _pool = ConnectionPool(
        conninfo=dsn,
        min_size=min_size,
        max_size=max_size,
        timeout=timeout_s,  # 從 pool 取連線的最大等待秒數
        kwargs={"row_factory": dict_row},
        open=False,  # 顯式延後 open（避免 deprecation warning + 利於測試）
    )
    _pool.open(wait=True, timeout=30.0)  # 啟動時測試最小連線


def close_pool() -> None:
    """FastAPI shutdown 時呼叫 — 釋放 pool。"""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_pool() -> ConnectionPool:
    """取回模組級 pool 物件（供 healthz endpoint 讀 stats 用）。

    Raises:
        RuntimeError: pool 未初始化
    """
    if _pool is None:
        raise RuntimeError("pool not initialized — call init_pool() at app startup")
    return _pool


@contextmanager
def get_conn() -> Iterator[Connection]:
    """取得一個 PostgreSQL connection（從 pool 借）。

    用法（與既有 SQLite 完全相同）：
        with get_conn() as conn:
            cur = conn.execute("SELECT ... WHERE id = %s", (123,))
            row = cur.fetchone()

    Note:
        - placeholder 為 %s（不再是 ?）— FUNC-105 全替換
        - row 物件為 dict（透過 dict_row factory）
        - 離開 with 自動 commit（psycopg 預設 autocommit=False，with 區塊 exit 觸發 commit）
        - 例外則 ROLLBACK
    """
    if _pool is None:
        raise RuntimeError("pool not initialized — call init_pool() at app startup")
    with _pool.connection() as conn:
        yield conn
