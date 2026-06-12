"""API-101: GET /api/db/healthz — DB 健康檢查 + migration 狀態.

對應 SD api-spec.md §2 API-101。
對應 SA functional-flow.md FUNC-101（pool 就緒）+ FUNC-103/104（migration 已套用）。

Response 範例（200 ok）:
    {
      "status": "ok",
      "db": {"connected": true, "pool": {"min": 2, "max": 10, "open": 2, "in_use": 0}},
      "migration": {"current": "20260610_120100", "head": "20260610_120100", "up_to_date": true}
    }

Response 範例（503 down）:
    {"status": "down", "db": {"connected": false, "error": "ERR-DB-001"}, "migration": null}
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

healthz_router = APIRouter(tags=["healthz"])


def _read_pool_stats() -> dict | None:
    """讀 psycopg_pool 統計。回 None 表示 pool 未就緒。"""
    try:
        from web.auth.database import get_pool
        pool = get_pool()
        # psycopg_pool 的 stats key（每個 release 略有不同）
        stats = pool.get_stats()
        return {
            "min": int(os.environ.get("POSTGRES_POOL_MIN", "2")),
            "max": int(os.environ.get("POSTGRES_POOL_MAX", "10")),
            # psycopg_pool stats: pool_size = open conns; pool_available = idle
            "open": stats.get("pool_size", 0),
            "in_use": stats.get("pool_size", 0) - stats.get("pool_available", 0),
        }
    except Exception:
        return None


def _read_alembic_current(conn) -> str | None:
    """從 alembic_version 表讀目前版本。表不存在則回 None。"""
    try:
        cur = conn.execute("SELECT version_num FROM alembic_version LIMIT 1")
        row = cur.fetchone()
        if row is None:
            return None
        # row 是 dict（dict_row factory）
        return row.get("version_num") if isinstance(row, dict) else row[0]
    except Exception:
        return None


def _read_alembic_head() -> str:
    """從 migrations/versions/ 取最新 revision id（檔名前綴）。"""
    versions_dir = Path(__file__).resolve().parent.parent.parent / "migrations" / "versions"
    if not versions_dir.is_dir():
        return ""
    revisions = []
    for f in versions_dir.glob("*.py"):
        if f.name.startswith("__"):
            continue
        # 檔名前綴 = revision id（如 20260610_120100_xxx.py）
        parts = f.stem.split("_", 2)
        if len(parts) >= 2:
            revisions.append(f"{parts[0]}_{parts[1]}")
    if not revisions:
        return ""
    return sorted(revisions)[-1]


@healthz_router.get("/api/db/healthz", summary="DB 健康檢查 + migration 狀態")
async def db_healthz():
    """API-101 — 給 Tester / Deployer 在 production cutover 確認狀態用。

    不需認證（healthcheck 端點任何狀態下都可達）。
    """
    pool_stats = _read_pool_stats()

    # 嘗試取連線
    from web.auth.database import get_conn
    try:
        with get_conn() as conn:
            current = _read_alembic_current(conn)
    except Exception as exc:
        # 對應 ERR-DB-001 / ERR-DB-002
        err_id = "ERR-DB-002" if "Timeout" in type(exc).__name__ else "ERR-DB-001"
        body = {
            "status": "down",
            "db": {"connected": False, "error": err_id},
            "migration": None,
        }
        return JSONResponse(body, status_code=503)

    head = _read_alembic_head()
    up_to_date = (current is not None and current == head)
    status_str = "ok" if up_to_date else "degraded"

    body = {
        "status": status_str,
        "db": {
            "connected": True,
            "pool": pool_stats or {
                "min": int(os.environ.get("POSTGRES_POOL_MIN", "2")),
                "max": int(os.environ.get("POSTGRES_POOL_MAX", "10")),
                "open": 0,
                "in_use": 0,
            },
        },
        "migration": {
            "current": current,
            "head": head,
            "up_to_date": up_to_date,
        },
    }
    return JSONResponse(body, status_code=200)
