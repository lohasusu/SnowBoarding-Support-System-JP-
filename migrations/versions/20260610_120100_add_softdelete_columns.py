"""add softdelete columns

Revision ID: 20260610_120100
Revises: 20260610_120000
Create Date: 2026-06-10 12:01:00

對應 SA FUNC-104 / SD db-schema.md §4.3。
新增 7 個欄位（updated_at×3 + deleted_at×3 + email_verification_tokens.created_at×1）。

[CROSS-TASK: TASK-001 / TBL-001/002/003 / 補 updated_at + deleted_at / 觸發 FR-004]
[CROSS-TASK: TASK-001 / TBL-003 / 補 created_at — TASK-001 baseline gap]
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260610_120100"
down_revision = "20260610_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users: + updated_at + deleted_at
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # favorites: + updated_at + deleted_at
    op.add_column(
        "favorites",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "favorites",
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # email_verification_tokens: + created_at (補 baseline gap) + updated_at + deleted_at
    op.add_column(
        "email_verification_tokens",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "email_verification_tokens",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "email_verification_tokens",
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_verification_tokens", "deleted_at")
    op.drop_column("email_verification_tokens", "updated_at")
    op.drop_column("email_verification_tokens", "created_at")
    op.drop_column("favorites", "deleted_at")
    op.drop_column("favorites", "updated_at")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "updated_at")
