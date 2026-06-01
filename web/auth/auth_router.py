"""
auth_router.py — 認證 + 收藏 API
在 main.py 中以 app.include_router(auth_router) 掛載。
"""
import json
import re
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .database import get_conn, init_db
from .dependencies import get_current_user, get_optional_user
from .security import create_access_token, hash_password, verify_password

auth_router = APIRouter()
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_templates   = Jinja2Templates(directory=str(TEMPLATE_DIR))

BASE_URL = "https://snowboarding-support-system-jp-production.up.railway.app"

# 初始化 DB（第一次 import 時執行）
init_db()


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
            "SELECT id, type, data, label, created_at FROM favorites WHERE user_id = ? ORDER BY created_at DESC",
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
            conn.execute(
                "INSERT INTO users (email, username, hashed_password) VALUES (?, ?, ?)",
                (body.email.lower().strip(), body.username.strip(), hashed),
            )
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=409, detail="Email 或用戶名稱已被使用")
        raise HTTPException(status_code=500, detail="註冊失敗")
    return {"ok": True, "message": "註冊成功"}


@auth_router.post("/api/auth/login")
async def api_login(body: LoginBody):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, hashed_password FROM users WHERE email = ?",
            (body.email.lower().strip(),)
        ).fetchone()
    if not row or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Email 或密碼錯誤")
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
            "SELECT id, type, data, label, created_at FROM favorites WHERE user_id = ? ORDER BY created_at DESC",
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
        cur = conn.execute(
            "INSERT INTO favorites (user_id, type, data, label) VALUES (?, ?, ?, ?)",
            (current_user["id"], body.type, json.dumps(body.data), body.label),
        )
        fav_id = cur.lastrowid
    return {"ok": True, "id": fav_id}


@auth_router.delete("/api/favorites/{fav_id}")
async def api_delete_favorite(fav_id: int, current_user=Depends(get_current_user)):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE id = ? AND user_id = ?",
            (fav_id, current_user["id"]),
        )
    return {"ok": True}
