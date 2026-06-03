"""
oauth_router.py — Google OAuth 2.0 登入
需要設定環境變數: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
"""
import os
import secrets
from pathlib import Path

import httpx
from fastapi import APIRouter, Cookie, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .database import get_conn
from .security import create_access_token, hash_password

oauth_router = APIRouter()

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
BASE_URL             = os.getenv("BASE_URL", "https://snowboarding-support-system-jp-production.up.railway.app")
REDIRECT_URI         = f"{BASE_URL}/api/auth/google/callback"


@oauth_router.get("/api/auth/google/login")
async def google_login():
    if not GOOGLE_CLIENT_ID:
        return JSONResponse({"ok": False, "error": "Google 登入尚未設定，請聯繫管理員"}, status_code=503)
    state = secrets.token_urlsafe(16)
    params = (
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid+email+profile"
        f"&state={state}"
        f"&access_type=offline"
    )
    resp = RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}")
    resp.set_cookie("oauth_state", state, httponly=True, max_age=300, samesite="lax", secure=False)
    return resp


@oauth_router.get("/api/auth/google/callback")
async def google_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    oauth_state: str = Cookie(default=None),
):
    if error:
        return RedirectResponse(url=f"/login?error=google_denied")
    if not code or state != oauth_state:
        return RedirectResponse(url="/login?error=oauth_state_mismatch")

    # 1. Exchange code for tokens
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if token_resp.status_code != 200:
        return RedirectResponse(url="/login?error=google_token_failed")
    access_token = token_resp.json().get("access_token", "")

    # 2. Get user info
    async with httpx.AsyncClient(timeout=10.0) as client:
        info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if info_resp.status_code != 200:
        return RedirectResponse(url="/login?error=google_userinfo_failed")
    info = info_resp.json()
    g_id     = info.get("sub", "")
    g_email  = info.get("email", "").lower().strip()
    g_name   = info.get("name", g_email.split("@")[0])
    g_avatar = info.get("picture", "")

    # 3. Upsert user
    with get_conn() as conn:
        existing_by_gid = conn.execute(
            "SELECT id FROM users WHERE google_id=?", (g_id,)
        ).fetchone()
        if existing_by_gid:
            user_id = existing_by_gid["id"]
        else:
            existing_by_email = conn.execute(
                "SELECT id FROM users WHERE email=?", (g_email,)
            ).fetchone()
            if existing_by_email:
                # Link Google to existing account
                user_id = existing_by_email["id"]
                conn.execute(
                    "UPDATE users SET google_id=?, avatar_url=?, is_verified=1 WHERE id=?",
                    (g_id, g_avatar, user_id)
                )
            else:
                # New user
                cur = conn.execute(
                    "INSERT INTO users (email, username, hashed_password, is_verified, google_id, avatar_url) "
                    "VALUES (?, ?, '', 1, ?, ?)",
                    (g_email, g_name, g_id, g_avatar)
                )
                user_id = cur.lastrowid

    jwt_token = create_access_token({"sub": str(user_id)})
    resp = RedirectResponse(url="/plan", status_code=302)
    resp.set_cookie(
        key="access_token", value=jwt_token,
        httponly=True, max_age=60 * 60 * 24 * 7,
        samesite="lax", secure=False,
    )
    resp.delete_cookie("oauth_state")
    return resp
