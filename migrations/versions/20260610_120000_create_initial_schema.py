"""create initial schema

Revision ID: 20260610_120000
Revises:
Create Date: 2026-06-10 12:00:00

對應 SA FUNC-103 / SD db-schema.md §4.2。
建立三張 TBL [REUSE: TBL-001/002/003, from TASK-001] 的 PG schema：
- users (8 欄 + 3 UNIQUE 索引)
- favorites (6 欄 + 1 FK + 1 FK 索引)
- email_verification_tokens (5 欄 + 1 FK + 1 UNIQUE 索引 + 1 FK 索引)

[CROSS-TASK: TASK-001 / TBL-001/002/003 / 改 storage engine SQLite → PG / 觸發 FR-002]
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260610_120000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- TBL-001 users ----
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.BigInteger,
            sa.Identity(always=True, start=1),
            primary_key=True,
        ),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("username", sa.Text, nullable=False),
        sa.Column(
            "hashed_password", sa.Text, nullable=False, server_default=""
        ),
        sa.Column(
            "is_verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("google_id", sa.Text, nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("uniq_users_email", "users", ["email"], unique=True)
    op.create_index(
        "uniq_users_username", "users", ["username"], unique=True
    )
    # partial unique index — 允許多個 NULL google_id
    op.create_index(
        "uniq_users_google_id",
        "users",
        ["google_id"],
        unique=True,
        postgresql_where=sa.text("google_id IS NOT NULL"),
    )

    # ---- TBL-002 favorites ----
    op.create_table(
        "favorites",
        sa.Column(
            "id",
            sa.BigInteger,
            sa.Identity(always=True, start=1),
            primary_key=True,
        ),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("data", sa.Text, nullable=False),
        sa.Column("label", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_favorites_user_id_users",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    op.create_index(
        "fk_idx_favorites_user_id", "favorites", ["user_id"]
    )

    # ---- TBL-003 email_verification_tokens ----
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
            "expires_at", sa.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.Column("used_at", sa.TIMESTAMP(timezone=True), nullable=True),
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


def downgrade() -> None:
    # 順序：依 FK 從葉到根
    op.drop_index(
        "fk_idx_email_verification_tokens_user_id",
        table_name="email_verification_tokens",
    )
    op.drop_index(
        "uniq_email_verification_tokens_token",
        table_name="email_verification_tokens",
    )
    op.drop_table("email_verification_tokens")

    op.drop_index(
        "fk_idx_favorites_user_id", table_name="favorites"
    )
    op.drop_table("favorites")

    op.drop_index("uniq_users_google_id", table_name="users")
    op.drop_index("uniq_users_username", table_name="users")
    op.drop_index("uniq_users_email", table_name="users")
    op.drop_table("users")
