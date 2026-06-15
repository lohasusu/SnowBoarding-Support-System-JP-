"""drop email verification gate

Revision ID: 20260615_080000
Revises: 20260610_120100
Create Date: 2026-06-15 08:00:00

User goal 2026-06-15: 完成 register→login 完整運作，去除「註冊後無法登入」之窘境。
- users.is_verified default FALSE → TRUE
- backfill 既有未驗證帳號為 TRUE（讓既有殘留註冊都可登入）

email_verification_tokens 表 + verify-email 路由仍保留作為日後 opt-in；register 不再寫入 token。
"""
from alembic import op
import sqlalchemy as sa


revision = "20260615_080000"
down_revision = "20260610_120100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) 改 default：日後新註冊 INSERT 不指定 is_verified 也會自動 TRUE
    op.alter_column(
        "users",
        "is_verified",
        server_default=sa.true(),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    # 2) 回填既有 FALSE 列 — 讓任何之前卡在「註冊未驗證」狀態的帳號可立即登入
    op.execute("UPDATE users SET is_verified = TRUE WHERE is_verified = FALSE")


def downgrade() -> None:
    op.alter_column(
        "users",
        "is_verified",
        server_default=sa.false(),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    # 不在 downgrade 重設已驗證 user — 避免影響營運帳號可登入性
