"""
tests/test_auth.py
執行: cd snowboarding_support && pytest web/auth/tests/ -v
"""
import pytest
import sqlite3
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path


# ── 測試用 in-memory DB fixture ──────────────────────────────────────────────

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """用臨時 SQLite 取代正式 DB。"""
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("web.auth.database.DB_PATH", db_file)
    from web.auth.database import init_db
    init_db()
    yield db_file


# ── 1. 註冊寄出驗證信 ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_sends_verification_email(test_db):
    from web.auth.auth_router import api_register, RegisterBody
    with patch("web.auth.auth_router.send_verification_email", new_callable=AsyncMock, return_value=True) as mock_send:
        resp = await api_register(RegisterBody(email="test@example.com", username="testuser", password="password123"))
        assert resp["ok"] is True
        mock_send.assert_called_once()
        assert mock_send.call_args[0][0] == "test@example.com"
    # 確認 is_verified = 0
    from web.auth.database import get_conn
    with get_conn() as conn:
        user = conn.execute("SELECT is_verified FROM users WHERE email=?", ("test@example.com",)).fetchone()
    assert user["is_verified"] == 0


# ── 2. 有效 token 驗證成功 ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_valid_token(test_db):
    from web.auth.database import get_conn
    from web.auth.auth_router import api_register, RegisterBody
    with patch("web.auth.auth_router.send_verification_email", new_callable=AsyncMock, return_value=True):
        await api_register(RegisterBody(email="v@example.com", username="vuser", password="password123"))
    with get_conn() as conn:
        row = conn.execute("SELECT token FROM email_verification_tokens LIMIT 1").fetchone()
        token = row["token"]
    from web.auth.auth_router import api_verify_email
    resp = await api_verify_email(token=token)
    assert resp.headers["location"].endswith("/login?verified=1")
    with get_conn() as conn:
        user = conn.execute("SELECT is_verified FROM users WHERE email=?", ("v@example.com",)).fetchone()
    assert user["is_verified"] == 1


# ── 3. 過期 token ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_expired_token(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        conn.execute("INSERT INTO users (email, username, hashed_password, is_verified) VALUES (?, ?, ?, 0)",
                     ("exp@example.com", "expuser", "hash"))
        uid = conn.execute("SELECT id FROM users WHERE email=?", ("exp@example.com",)).fetchone()["id"]
        expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        conn.execute("INSERT INTO email_verification_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
                     (uid, "expiredtoken", expired))
    from web.auth.auth_router import api_verify_email
    resp = await api_verify_email(token="expiredtoken")
    assert "token_expired" in resp.headers["location"]


# ── 4. 已使用 token ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_used_token(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        conn.execute("INSERT INTO users (email, username, hashed_password, is_verified) VALUES (?, ?, ?, 0)",
                     ("used@example.com", "useduser", "hash"))
        uid = conn.execute("SELECT id FROM users WHERE email=?", ("used@example.com",)).fetchone()["id"]
        future = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        now    = datetime.now(timezone.utc).isoformat()
        conn.execute("INSERT INTO email_verification_tokens (user_id, token, expires_at, used_at) VALUES (?, ?, ?, ?)",
                     (uid, "usedtoken", future, now))
    from web.auth.auth_router import api_verify_email
    resp = await api_verify_email(token="usedtoken")
    assert "token_used" in resp.headers["location"]


# ── 5. 未驗證用戶不能登入 ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_unverified_user(test_db):
    from web.auth.database import get_conn
    from web.auth.security import hash_password
    from web.auth.auth_router import api_login, LoginBody
    from fastapi import HTTPException
    with get_conn() as conn:
        conn.execute("INSERT INTO users (email, username, hashed_password, is_verified) VALUES (?, ?, ?, 0)",
                     ("unverified@example.com", "unver", hash_password("password123")))
    with pytest.raises(HTTPException) as exc_info:
        await api_login(LoginBody(email="unverified@example.com", password="password123"))
    assert exc_info.value.status_code == 403


# ── 6. 重寄驗證信：舊 token 失效，新 token 產生 ───────────────────────────────

@pytest.mark.asyncio
async def test_resend_verification_invalidates_old(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        conn.execute("INSERT INTO users (email, username, hashed_password, is_verified) VALUES (?, ?, ?, 0)",
                     ("resend@example.com", "resenduser", "hash"))
        uid = conn.execute("SELECT id FROM users WHERE email=?", ("resend@example.com",)).fetchone()["id"]
        future = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        conn.execute("INSERT INTO email_verification_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
                     (uid, "oldtoken", future))
    from web.auth.auth_router import api_resend_verification, ResendVerificationBody
    with patch("web.auth.auth_router.send_verification_email", new_callable=AsyncMock, return_value=True):
        resp = await api_resend_verification(ResendVerificationBody(email="resend@example.com"))
    assert resp["ok"] is True
    with get_conn() as conn:
        old = conn.execute("SELECT used_at FROM email_verification_tokens WHERE token=?", ("oldtoken",)).fetchone()
        new_count = conn.execute("SELECT COUNT(*) as c FROM email_verification_tokens WHERE token != 'oldtoken'").fetchone()["c"]
    assert old["used_at"] is not None  # 舊 token 已失效
    assert new_count >= 1               # 新 token 存在


# ── 7. Google OAuth 新用戶 ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_google_oauth_new_user(test_db):
    from web.auth.oauth_router import google_callback
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "fake_access_token"}
    mock_info_resp = MagicMock()
    mock_info_resp.status_code = 200
    mock_info_resp.json.return_value = {
        "sub": "google_123", "email": "newgoogle@example.com",
        "name": "New User", "picture": "https://example.com/avatar.jpg"
    }
    with patch("web.auth.oauth_router.GOOGLE_CLIENT_ID", "fake_id"), \
         patch("web.auth.oauth_router.GOOGLE_CLIENT_SECRET", "fake_secret"), \
         patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_token_resp)
        mock_client.return_value.__aenter__.return_value.get  = AsyncMock(return_value=mock_info_resp)
        resp = await google_callback(code="fake_code", state="teststate", error=None, oauth_state="teststate")
    assert resp.headers["location"] == "/plan"
    from web.auth.database import get_conn
    with get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=?", ("newgoogle@example.com",)).fetchone()
    assert user is not None
    assert user["is_verified"] == 1
    assert user["google_id"] == "google_123"


# ── 8. Google OAuth 已存在 email → 綁定 google_id ────────────────────────────

@pytest.mark.asyncio
async def test_google_oauth_existing_email_links_google_id(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        conn.execute("INSERT INTO users (email, username, hashed_password, is_verified) VALUES (?, ?, ?, 1)",
                     ("existing@example.com", "existuser", "hash"))
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "fake_access_token"}
    mock_info_resp = MagicMock()
    mock_info_resp.status_code = 200
    mock_info_resp.json.return_value = {
        "sub": "google_456", "email": "existing@example.com",
        "name": "Exist User", "picture": ""
    }
    from web.auth.oauth_router import google_callback
    with patch("web.auth.oauth_router.GOOGLE_CLIENT_ID", "fake_id"), \
         patch("web.auth.oauth_router.GOOGLE_CLIENT_SECRET", "fake_secret"), \
         patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_token_resp)
        mock_client.return_value.__aenter__.return_value.get  = AsyncMock(return_value=mock_info_resp)
        await google_callback(code="fake_code", state="s", error=None, oauth_state="s")
    with get_conn() as conn:
        user = conn.execute("SELECT google_id FROM users WHERE email=?", ("existing@example.com",)).fetchone()
    assert user["google_id"] == "google_456"
