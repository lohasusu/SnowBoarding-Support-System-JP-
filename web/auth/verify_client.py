"""
verify_client.py — SnowTrip Japan 登入驗證工具

CLI 用途（維運/除錯）：
    python verify_client.py --token <jwt>
    python verify_client.py --email <email>

API 端點：
    GET /api/auth/verify                  ← 讀 access_token cookie
    GET /api/auth/verify?token=<jwt>      ← 明確帶 token
    GET /api/auth/verify?email=<email>    ← 查用戶狀態

TASK-002 變更（FUNC-105）：
- SQL placeholder `?` → `%s`
- 移除 `bool(d.get("is_verified", 1))` adapter — PG 原生 BOOLEAN
- NFR-002 保證：回傳 JSON 結構不變
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── path setup（CLI 模式執行時需要）────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent          # web/auth/
_WEB  = _HERE.parent                             # web/
_ROOT = _WEB.parent                              # snowboarding_support/
for _p in (_WEB, _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fastapi import APIRouter, Cookie, Query
from fastapi.responses import JSONResponse

verify_router = APIRouter(tags=["auth"])


# ── 核心驗證邏輯 ───────────────────────────────────────────────────────────────

def verify_token_info(token: str) -> dict:
    """
    驗證 JWT token，回傳完整狀態 dict。
    {valid, user, issued_at, expires_at, auth_method, error}
    """
    try:
        try:
            from auth.security import decode_token
            from auth.database import get_conn
        except ImportError:
            from security import decode_token   # type: ignore
            from database import get_conn       # type: ignore

        payload = decode_token(token)
        if not payload:
            return {"valid": False, "user": None, "error": "Token 無效或已過期"}

        user_id = payload.get("sub")
        if not user_id:
            return {"valid": False, "user": None, "error": "Token 格式錯誤（缺少 sub）"}

        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, email, username, is_verified, google_id FROM users WHERE id = %s",
                (int(user_id),),
            ).fetchone()

        if not row:
            return {"valid": False, "user": None, "error": "使用者不存在（已刪除？）"}

        d = dict(row)
        exp = payload.get("exp")
        iat = payload.get("iat")

        return {
            "valid": True,
            "user": {
                "id":          d["id"],
                "email":       d["email"],
                "username":    d["username"],
                # TASK-002 FUNC-105: PG 原生 BOOLEAN — 移除 bool() adapter
                "is_verified": bool(d.get("is_verified")) if d.get("is_verified") is not None else True,
            },
            "issued_at":   _ts(iat),
            "expires_at":  _ts(exp),
            "auth_method": "google" if d.get("google_id") else "password",
            "error":       None,
        }
    except Exception as exc:
        return {"valid": False, "user": None, "error": f"驗證例外：{exc}"}


def verify_email_info(email: str) -> dict:
    """查詢 email 對應的帳號狀態。"""
    try:
        try:
            from auth.database import get_conn
        except ImportError:
            from database import get_conn  # type: ignore

        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, email, username, is_verified, google_id, created_at FROM users WHERE email = %s",
                (email.lower().strip(),),
            ).fetchone()

        if not row:
            return {"found": False, "user": None, "error": "找不到此 Email 的帳號"}

        d = dict(row)
        return {
            "found": True,
            "user": {
                "id":          d["id"],
                "email":       d["email"],
                "username":    d["username"],
                # TASK-002 FUNC-105: PG 原生 BOOLEAN — 移除 bool() adapter
                "is_verified": bool(d.get("is_verified")) if d.get("is_verified") is not None else True,
                "auth_method": "google" if d.get("google_id") else "password",
                "created_at":  d.get("created_at").isoformat() if d.get("created_at") else None,
            },
            "error": None,
        }
    except Exception as exc:
        return {"found": False, "user": None, "error": f"查詢例外：{exc}"}


def _ts(epoch: int | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


# ── FastAPI 端點 ───────────────────────────────────────────────────────────────

@verify_router.get("/api/auth/verify", summary="驗證登入 token 或查詢用戶狀態")
async def api_verify(
    access_token: str | None = Cookie(default=None),
    token: str | None        = Query(default=None, description="明確帶入 JWT"),
    email: str | None        = Query(default=None, description="查詢 email 帳號狀態"),
):
    """
    維運 API：確認 JWT 有效性或查詢帳號狀態。

    - 帶 `?token=<jwt>` 或使用 cookie：回傳 token 驗證結果
    - 帶 `?email=<email>`：回傳帳號是否存在及驗證狀態
    - 兩者都不帶：讀取 access_token cookie
    """
    if email:
        return verify_email_info(email)
    t = token or access_token
    if not t:
        return JSONResponse(
            {"valid": False, "error": "請提供 token 參數或登入 cookie"},
            status_code=400,
        )
    return verify_token_info(t)


# ── CLI 入口 ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SnowTrip Japan 登入驗證工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python verify_client.py --token eyJhbGci...
  python verify_client.py --email user@example.com
        """,
    )
    parser.add_argument("--token", metavar="JWT",   help="驗證 JWT token")
    parser.add_argument("--email", metavar="EMAIL", help="查詢 email 帳號狀態")
    args = parser.parse_args()

    if args.email:
        result = verify_email_info(args.email)
    elif args.token:
        result = verify_token_info(args.token)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("valid") or result.get("found") else 1)
