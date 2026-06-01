"""FastAPI dependencies for auth."""
from fastapi import Cookie, HTTPException, status
from .security import decode_token
from .database import get_conn


def get_current_user(access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登入")
    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 無效或已過期")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 無效")
    with get_conn() as conn:
        row = conn.execute("SELECT id, email, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="使用者不存在")
    return dict(row)


def get_optional_user(access_token: str | None = Cookie(default=None)):
    if not access_token:
        return None
    payload = decode_token(access_token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    with get_conn() as conn:
        row = conn.execute("SELECT id, email, username FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None
