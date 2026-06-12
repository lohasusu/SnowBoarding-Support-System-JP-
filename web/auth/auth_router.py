"""
auth_router.py — 認證 + 收藏 API
在 main.py 中以 app.include_router(auth_router) 掛載。

TASK-002 變更（FUNC-105 SQLite → PG dialect 適配）：
- SQL placeholder: `?` → `%s`
- INSERT cursor.lastrowid → INSERT ... RETURNING id + cur.fetchone()["id"]
- UPDATE 補 SET updated_at = NOW()（決策 #6 應用層注入）
- 移除 `init_db()` 呼叫 — schema 改由 Alembic migration 管理（FUNC-103/104）
- 移除 ISO 字串時間字典序比較 — 改 PG TIMESTAMPTZ 原生比較（用 datetime 物件）
- NFR-002 保證：HTTP / Response / Cookie 外部行為完全不變
"""
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse as _Redirect, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .database import get_conn
from .dependencies import get_current_user, get_optional_user
from .security import create_access_token, hash_password, verify_password
from .email_service import send_verification_email

auth_router = APIRouter()
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_templates   = Jinja2Templates(directory=str(TEMPLATE_DIR))

BASE_URL = "https://snowboarding-support-system-jp-production.up.railway.app"

# TASK-002: 移除 init_db() — schema 改由 Alembic migration 管理（FUNC-103/104）
# DB schema 由 web/db_bootstrap.py.on_startup() 在 FastAPI lifespan 中經 advisory lock 套用


def _ctx(request: Request, **kw) -> dict:
    return {
        "base_url": BASE_URL,
        "canonical_url": BASE_URL + str(request.url.path),
        **kw,
    }


# ── 頁面路由 ──────────────────────────────────────────────────────────────────

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, access_token: str | None = Cookie(default=None)):
    from .dependencies import get_optional_user as _opt
    user = get_optional_user(access_token)
    if user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/profile")
    return _templates.TemplateResponse(request, "auth/login.html", _ctx(request))


@auth_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return _templates.TemplateResponse(request, "auth/register.html", _ctx(request))


@auth_router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, current_user=Depends(get_current_user)):
    with get_conn() as conn:
        favs = conn.execute(
            "SELECT id, type, data, label, created_at FROM favorites WHERE user_id = %s ORDER BY created_at DESC",
            (current_user["id"],)
        ).fetchall()
    favorites = [dict(f) for f in favs]
    for f in favorites:
        try:
            f["data"] = json.loads(f["data"])
        except Exception:
            pass
    return _templates.TemplateResponse(request, "profile.html", _ctx(request, user=current_user, favorites=favorites))


# ── API: 認證 ─────────────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    email: str
    username: str
    password: str


class LoginBody(BaseModel):
    email: str
    password: str


@auth_router.post("/api/auth/register")
async def api_register(body: RegisterBody):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="密碼至少 8 個字元")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", body.email):
        raise HTTPException(status_code=400, detail="Email 格式不正確")
    hashed = hash_password(body.password)
    try:
        with get_conn() as conn:
            # TASK-002 FUNC-105: lastrowid → RETURNING id
            cur = conn.execute(
                "INSERT INTO users (email, username, hashed_password, is_verified) "
                "VALUES (%s, %s, %s, FALSE) RETURNING id",
                (body.email.lower().strip(), body.username.strip(), hashed),
            )
            user_id = cur.fetchone()["id"]
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            conn.execute(
                "INSERT INTO email_verification_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, token, expires_at),
            )
    except HTTPException:
        raise
    except Exception as e:
        # psycopg.errors.UniqueViolation → ERR-DB-003 → 409
        # 既有 NFR-002 行為：訊息維持中文「Email 或用戶名稱已被使用」
        emsg = str(e)
        if "unique" in emsg.lower() or "UniqueViolation" in type(e).__name__:
            raise HTTPException(status_code=409, detail="Email 或用戶名稱已被使用")
        raise HTTPException(status_code=500, detail="註冊失敗")
    sent = await send_verification_email(body.email.lower().strip(), body.username.strip(), token)
    if sent:
        message = "帳號建立成功，驗證信已寄出，請在 24 小時內點擊信中連結"
    else:
        message = "帳號建立成功，但寄信失敗，請至登入頁點選「重寄驗證信」"
    return {"ok": True, "message": message}


@auth_router.post("/api/auth/login")
async def api_login(body: LoginBody):
    # body.email 可以是 email 或 username — 以是否含 "@" 判定
    raw = body.email.strip()
    if "@" in raw:
        # 視為 email（保留大小寫不敏感）
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, hashed_password, is_verified FROM users WHERE email = %s",
                (raw.lower(),),
            ).fetchone()
    else:
        # 視為 username（schema 為大小寫敏感）
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, hashed_password, is_verified FROM users WHERE username = %s",
                (raw,),
            ).fetchone()
    if not row or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Email/使用者名稱 或密碼錯誤")
    # is_verified 為 PG 原生 BOOLEAN（不再是 SQLite 的 0/1 整數）
    if not row["is_verified"]:
        raise HTTPException(status_code=403, detail="請先驗證您的 Email 後再登入。未收到信？請點選下方「重寄驗證信」")
    token = create_access_token({"sub": str(row["id"])})
    resp  = JSONResponse({"ok": True, "message": "登入成功"})
    resp.set_cookie(
        key="access_token", value=token,
        httponly=True, max_age=60 * 60 * 24 * 7,
        samesite="lax", secure=False,
    )
    return resp


@auth_router.post("/api/auth/logout")
async def api_logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    return resp


@auth_router.get("/api/auth/verify-email")
async def api_verify_email(token: str):
    # TASK-002 FUNC-105: 改用 datetime 物件比較（PG TIMESTAMPTZ 原生）
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, user_id, expires_at, used_at FROM email_verification_tokens WHERE token = %s",
            (token,)
        ).fetchone()
    if not row:
        return _Redirect(url="/login?error=invalid_token")
    if row["used_at"]:
        return _Redirect(url="/login?error=token_used")
    # row["expires_at"] 為 psycopg 回傳的 datetime（含 tz）
    if row["expires_at"] < now:
        return _Redirect(url="/login?error=token_expired")
    with get_conn() as conn:
        # TASK-002 FUNC-105: UPDATE 補 updated_at = NOW() (決策 #6)
        conn.execute(
            "UPDATE users SET is_verified = TRUE, updated_at = NOW() WHERE id = %s",
            (row["user_id"],),
        )
        conn.execute(
            "UPDATE email_verification_tokens SET used_at = %s, updated_at = NOW() WHERE id = %s",
            (now, row["id"]),
        )
    return _Redirect(url="/login?verified=1")


class ResendVerificationBody(BaseModel):
    email: str


@auth_router.post("/api/auth/resend-verification")
async def api_resend_verification(body: ResendVerificationBody):
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, username, is_verified FROM users WHERE email = %s",
            (body.email.lower().strip(),)
        ).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="找不到此 Email 的帳號")
    if user["is_verified"]:
        return {"ok": True, "message": "此帳號已完成驗證"}
    # 廢棄舊 token + 發新 token
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        conn.execute(
            "UPDATE email_verification_tokens "
            "SET used_at = %s, updated_at = NOW() "
            "WHERE user_id = %s AND used_at IS NULL",
            (now, user["id"]),
        )
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        conn.execute(
            "INSERT INTO email_verification_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user["id"], token, expires_at),
        )
    sent = await send_verification_email(body.email.lower().strip(), user["username"], token)
    return {"ok": True, "message": "驗證信已重新寄出" if sent else "寄信失敗，請稍後再試"}


@auth_router.get("/api/auth/me")
async def api_me(current_user=Depends(get_current_user)):
    return {"ok": True, "user": {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
    }}


# ── API: 收藏 ─────────────────────────────────────────────────────────────────

class FavoriteBody(BaseModel):
    type: str   # 'ski' or 'flight'
    data: dict
    label: str = ""


@auth_router.get("/api/favorites")
async def api_get_favorites(current_user=Depends(get_current_user)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, type, data, label, created_at FROM favorites WHERE user_id = %s ORDER BY created_at DESC",
            (current_user["id"],)
        ).fetchall()
    result = []
    for r in rows:
        item = dict(r)
        try:
            item["data"] = json.loads(item["data"])
        except Exception:
            pass
        result.append(item)
    return {"ok": True, "data": result}


@auth_router.post("/api/favorites")
async def api_add_favorite(body: FavoriteBody, current_user=Depends(get_current_user)):
    if body.type not in ("ski", "flight"):
        raise HTTPException(status_code=400, detail="type 必須是 ski 或 flight")
    with get_conn() as conn:
        # TASK-002 FUNC-105: lastrowid → RETURNING id
        cur = conn.execute(
            "INSERT INTO favorites (user_id, type, data, label) VALUES (%s, %s, %s, %s) RETURNING id",
            (current_user["id"], body.type, json.dumps(body.data), body.label),
        )
        fav_id = cur.fetchone()["id"]
    return {"ok": True, "id": fav_id}


@auth_router.delete("/api/favorites/{fav_id}")
async def api_delete_favorite(fav_id: int, current_user=Depends(get_current_user)):
    # [IRREVERSIBLE REUSE]: hard delete — 由 SUG-004 + CONST-005 維持既有行為
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE id = %s AND user_id = %s",
            (fav_id, current_user["id"]),
        )
    return {"ok": True}
