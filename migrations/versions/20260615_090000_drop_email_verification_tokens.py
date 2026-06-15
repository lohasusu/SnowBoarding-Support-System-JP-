"""drop email_verification_tokens table

Revision ID: 20260615_090000
Revises: 20260615_080000
Create Date: 2026-06-15 09:00:00

User goal 2026-06-15: 把註冊寄出認證信整條路徑拔掉。
- /api/auth/verify-email + /api/auth/resend-verification 路由已從 auth_router 移除
- email_service.py 已刪除
- login.html 重寄按鈕 + URL 錯誤提示已移除
- 此 migration 把 email_verification_tokens 表 drop 掉（auth-only 表；非 ski/flight 範圍）

Downgrade 重建空表 + 索引；不嘗試還原任何資料（原本就 ephemeral）。
"""
from alembic import op
import sqlalchemy as sa


revision = "20260615_090000"
down_revision = "20260615_080000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # drop indexes first (alembic 的 drop_table 在 PG 會 cascade，但顯式較安全)
    op.drop_index(
        "fk_idx_email_verification_tokens_user_id",
        table_name="email_verification_tokens",
    )
    op.drop_index(
        "uniq_email_verification_tokens_token",
        table_name="email_verification_tokens",
    )
    op.drop_table("email_verification_tokens")


def downgrade() -> None:
    # 重建空表（schema 取自 20260610_120000 + 20260610_120100）
    op.create_table(
        "email_verification_tokens",
        sa.Column(
            "id",
            sa.BigInteger,
            sa.Identity(always=True, start=1),
            primary_key=True,
        ),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("token", sa.Text, nullable=False),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "deleted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_email_verification_tokens_user_id_users",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    op.create_index(
        "uniq_email_verification_tokens_token",
        "email_verification_tokens",
        ["token"],
        unique=True,
    )
    op.create_index(
        "fk_idx_email_verification_tokens_user_id",
        "email_verification_tokens",
        ["user_id"],
    )
