"""
tests/test_auth.py — TASK-002 PG fixture 版本

執行: cd snowboarding_support && pytest web/auth/tests/ -v

TASK-002 變更（Major-1 pytest 相容性解決）:
- fixture 改用 testcontainers[postgres] 啟動 PG container
- 移除 sqlite3 / DB_PATH / init_db import
- SQL placeholder 全部 `?` → `%s`
- 整數比較 0/1 → BOOLEAN True/False
- 透過 web.auth.database.init_pool 設定 pool 連到測試 container
- 透過 Alembic upgrade head 建立 schema（保證測試環境與 production schema 一致）

NFR-002 / AC-045: 既有 8 個測試案例 100% 保留 — 僅換 DB driver。
"""
from __future__ import annotations

import os
import sys
import pytest
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


# ── 確保 import path 正確（pytest 可從 repo root 啟動）─────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ── PG container fixture（整個 session 共用一個 container）─────────────────

@pytest.fixture(scope="session")
def _pg_container():
    """啟動一次 PG container；session 結束時銷毀。"""
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip(
            "testcontainers[postgres] not installed — "
            "run: pip install 'testcontainers[postgres]==4.7.2'"
        )

    container = PostgresContainer("postgres:16-alpine")
    container.start()
    try:
        # 把連線資訊塞 env vars（讓 _build_dsn_from_env 取用）
        os.environ["POSTGRES_HOST"] = container.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(container.get_exposed_port(5432))
        os.environ["POSTGRES_USER"] = container.username
        os.environ["POSTGRES_PASSWORD"] = container.password
        os.environ["POSTGRES_DB"] = container.dbname
        os.environ["POSTGRES_SSL_MODE"] = "disable"
        os.environ["POSTGRES_POOL_MIN"] = "1"
        os.environ["POSTGRES_POOL_MAX"] = "5"
        os.environ["POSTGRES_POOL_TIMEOUT_MS"] = "5000"
        # 確保 lifespan 不會在 import main 時跑 bootstrap
        os.environ["RUN_DB_BOOTSTRAP"] = "0"

        # 跑 Alembic upgrade head 建立 schema
        from alembic.config import Config
        from alembic import command
        alembic_ini = _PROJECT_ROOT / "alembic.ini"
        cfg = Config(str(alembic_ini))
        # set_main_option 後 env.py 跳過 _build_dsn_from_env 改用此 url
        from web.auth.database import _build_dsn_from_env
        cfg.set_main_option("sqlalchemy.url", _build_dsn_from_env())
        command.upgrade(cfg, "head")

        yield container
    finally:
        container.stop()


@pytest.fixture
def test_db(_pg_container):
    """每個 test 開新 pool；test 結束清空三張表。"""
    from web.auth.database import init_pool, close_pool, get_conn

    init_pool()
    try:
        # 清空（test 之間隔離）— 順序按 FK 從葉到根
        with get_conn() as conn:
            conn.execute("TRUNCATE TABLE email_verification_tokens RESTART IDENTITY CASCADE")
            conn.execute("TRUNCATE TABLE favorites RESTART IDENTITY CASCADE")
            conn.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE")
        yield
    finally:
        close_pool()


# ── 1. 註冊寄出驗證信 ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_sends_verification_email(test_db):
    from web.auth.auth_router import api_register, RegisterBody
    with patch(
        "web.auth.auth_router.send_verification_email",
        new_callable=AsyncMock, return_value=True,
    ) as mock_send:
        resp = await api_register(
            RegisterBody(email="test@example.com", username="testuser", password="password123")
        )
        assert resp["ok"] is True
        mock_send.assert_called_once()
        assert mock_send.call_args[0][0] == "test@example.com"
    # 確認 is_verified = False（PG BOOLEAN）
    from web.auth.database import get_conn
    with get_conn() as conn:
        user = conn.execute(
            "SELECT is_verified FROM users WHERE email = %s",
            ("test@example.com",),
        ).fetchone()
    assert user["is_verified"] is False


# ── 2. 有效 token 驗證成功 ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_valid_token(test_db):
    from web.auth.database import get_conn
    from web.auth.auth_router import api_register, RegisterBody
    with patch(
        "web.auth.auth_router.send_verification_email",
        new_callable=AsyncMock, return_value=True,
    ):
        await api_register(
            RegisterBody(email="v@example.com", username="vuser", password="password123")
        )
    with get_conn() as conn:
        row = conn.execute(
            "SELECT token FROM email_verification_tokens LIMIT 1"
        ).fetchone()
        token = row["token"]
    from web.auth.auth_router import api_verify_email
    resp = await api_verify_email(token=token)
    assert resp.headers["location"].endswith("/login?verified=1")
    with get_conn() as conn:
        user = conn.execute(
            "SELECT is_verified FROM users WHERE email = %s",
            ("v@example.com",),
        ).fetchone()
    assert user["is_verified"] is True


# ── 3. 過期 token ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_expired_token(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, username, hashed_password, is_verified) "
            "VALUES (%s, %s, %s, FALSE) RETURNING id",
            ("exp@example.com", "expuser", "hash"),
        )
        uid = cur.fetchone()["id"]
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        conn.execute(
            "INSERT INTO email_verification_tokens (user_id, token, expires_at) "
            "VALUES (%s, %s, %s)",
            (uid, "expiredtoken", expired),
        )
    from web.auth.auth_router import api_verify_email
    resp = await api_verify_email(token="expiredtoken")
    assert "token_expired" in resp.headers["location"]


# ── 4. 已使用 token ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_used_token(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, username, hashed_password, is_verified) "
            "VALUES (%s, %s, %s, FALSE) RETURNING id",
            ("used@example.com", "useduser", "hash"),
        )
        uid = cur.fetchone()["id"]
        future = datetime.now(timezone.utc) + timedelta(hours=24)
        now    = datetime.now(timezone.utc)
        conn.execute(
            "INSERT INTO email_verification_tokens "
            "(user_id, token, expires_at, used_at) VALUES (%s, %s, %s, %s)",
            (uid, "usedtoken", future, now),
        )
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
        conn.execute(
            "INSERT INTO users (email, username, hashed_password, is_verified) "
            "VALUES (%s, %s, %s, FALSE)",
            ("unverified@example.com", "unver", hash_password("password123")),
        )
    with pytest.raises(HTTPException) as exc_info:
        await api_login(
            LoginBody(email="unverified@example.com", password="password123")
        )
    assert exc_info.value.status_code == 403


# ── 6. 重寄驗證信：舊 token 失效，新 token 產生 ───────────────────────────────

@pytest.mark.asyncio
async def test_resend_verification_invalidates_old(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, username, hashed_password, is_verified) "
            "VALUES (%s, %s, %s, FALSE) RETURNING id",
            ("resend@example.com", "resenduser", "hash"),
        )
        uid = cur.fetchone()["id"]
        future = datetime.now(timezone.utc) + timedelta(hours=24)
        conn.execute(
            "INSERT INTO email_verification_tokens (user_id, token, expires_at) "
            "VALUES (%s, %s, %s)",
            (uid, "oldtoken", future),
        )
    from web.auth.auth_router import api_resend_verification, ResendVerificationBody
    with patch(
        "web.auth.auth_router.send_verification_email",
        new_callable=AsyncMock, return_value=True,
    ):
        resp = await api_resend_verification(
            ResendVerificationBody(email="resend@example.com")
        )
    assert resp["ok"] is True
    with get_conn() as conn:
        old = conn.execute(
            "SELECT used_at FROM email_verification_tokens WHERE token = %s",
            ("oldtoken",),
        ).fetchone()
        new_count_row = conn.execute(
            "SELECT COUNT(*) AS c FROM email_verification_tokens WHERE token != %s",
            ("oldtoken",),
        ).fetchone()
        new_count = new_count_row["c"]
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
        resp = await google_callback(
            code="fake_code", state="teststate", error=None, oauth_state="teststate"
        )
    assert resp.headers["location"] == "/plan"
    from web.auth.database import get_conn
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = %s",
            ("newgoogle@example.com",),
        ).fetchone()
    assert user is not None
    assert user["is_verified"] is True
    assert user["google_id"] == "google_123"


# ── 8. Google OAuth 已存在 email → 綁定 google_id ────────────────────────────

@pytest.mark.asyncio
async def test_google_oauth_existing_email_links_google_id(test_db):
    from web.auth.database import get_conn
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (email, username, hashed_password, is_verified) "
            "VALUES (%s, %s, %s, TRUE)",
            ("existing@example.com", "existuser", "hash"),
        )
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
        user = conn.execute(
            "SELECT google_id FROM users WHERE email = %s",
            ("existing@example.com",),
        ).fetchone()
    assert user["google_id"] == "google_456"
