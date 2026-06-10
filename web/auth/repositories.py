"""Repository helpers — MOD-103（最小封裝原則）。

僅集中三類重複動作：
1. INSERT ... RETURNING id  → 取代 SQLite 的 cur.lastrowid
2. UPDATE 補 updated_at = NOW()  → 決策 #6 應用層注入（非 DB trigger）
3. dict row 取值（與既有 sqlite3.Row 介面相容，由 dict_row factory 處理）

完整 Repository Pattern refactor 留後續 TASK（SA-SUG-102 auth-layering-refactor）。

對應 SD code-arch.md §3.3 MOD-103。
對應 SA functional-flow.md FUNC-105（query dialect 適配）。
"""
from __future__ import annotations

from typing import Any, Sequence

from psycopg import Connection


def insert_returning_id(
    conn: Connection,
    sql: str,
    params: Sequence[Any],
) -> int:
    """執行 INSERT 並回傳新建 row 的 id。

    取代 SQLite 的 cursor.lastrowid 用法（PG 原生 RETURNING）。

    Args:
        conn: psycopg.Connection（透過 get_conn() 取得）
        sql: 必含 `RETURNING id` clause 的 INSERT 語句
        params: %s placeholder 對應的參數 tuple

    Returns:
        新建 row 的 id（BIGINT）

    Raises:
        psycopg.errors.UniqueViolation: UNIQUE 約束違反（ERR-DB-003）
        RuntimeError: INSERT 未回傳 row（SQL 缺 RETURNING clause 的 bug）

    Example:
        user_id = insert_returning_id(
            conn,
            "INSERT INTO users (email, username, hashed_password, is_verified) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (email, username, hashed, False),
        )
    """
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        raise RuntimeError("INSERT did not return an id — check RETURNING clause")
    # row 是 dict（透過 dict_row factory）
    return row["id"]


def update_with_timestamp(
    conn: Connection,
    table: str,
    set_clause: str,
    where_clause: str,
    params: Sequence[Any],
) -> int:
    """UPDATE 並自動補 updated_at = NOW()。

    決策 #6：應用層手動 SET updated_at（不用 DB trigger）。

    Args:
        conn: psycopg.Connection
        table: 表名（無需 quote — 應由呼叫端確保非使用者輸入）
        set_clause: SET 子句（不含 updated_at — 本函式自動補）
        where_clause: WHERE 子句
        params: SET + WHERE 的 %s 對應參數（按出現順序）

    Returns:
        被影響的 row 數

    Example:
        rows = update_with_timestamp(
            conn,
            table="users",
            set_clause="username = %s",
            where_clause="id = %s",
            params=(new_username, user_id),
        )
    """
    full_sql = (
        f"UPDATE {table} "
        f"SET {set_clause}, updated_at = NOW() "
        f"WHERE {where_clause}"
    )
    cur = conn.execute(full_sql, params)
    return cur.rowcount
