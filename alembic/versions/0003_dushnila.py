"""Add dushnila_events, dushnila_streaks, dushnila_week_resets tables.

Revision ID: 0003_dushnila
Revises: 0002_bigint_ids_composite_idx
Create Date: 2026-07-27
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_dushnila"
down_revision = "0002_bigint_ids_composite_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dushnila_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dushnila_events_id", "dushnila_events", ["id"])
    op.create_index("ix_dushnila_events_chat_id", "dushnila_events", ["chat_id"])
    op.create_index("ix_dushnila_events_user_id", "dushnila_events", ["user_id"])
    op.create_index("ix_dushnila_events_created_at", "dushnila_events", ["created_at"])
    op.create_index(
        "ix_dushnila_events_chat_user_created",
        "dushnila_events",
        ["chat_id", "user_id", "created_at"],
    )

    op.create_table(
        "dushnila_streaks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )
    op.create_index("ix_dushnila_streaks_id", "dushnila_streaks", ["id"])
    op.create_index("ix_dushnila_streaks_chat_id", "dushnila_streaks", ["chat_id"])

    op.create_table(
        "dushnila_week_resets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("reset_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )
    op.create_index("ix_dushnila_week_resets_id", "dushnila_week_resets", ["id"])
    op.create_index(
        "ix_dushnila_week_resets_chat_id", "dushnila_week_resets", ["chat_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_dushnila_week_resets_chat_id", table_name="dushnila_week_resets")
    op.drop_index("ix_dushnila_week_resets_id", table_name="dushnila_week_resets")
    op.drop_table("dushnila_week_resets")

    op.drop_index("ix_dushnila_streaks_chat_id", table_name="dushnila_streaks")
    op.drop_index("ix_dushnila_streaks_id", table_name="dushnila_streaks")
    op.drop_table("dushnila_streaks")

    op.drop_index(
        "ix_dushnila_events_chat_user_created", table_name="dushnila_events"
    )
    op.drop_index("ix_dushnila_events_created_at", table_name="dushnila_events")
    op.drop_index("ix_dushnila_events_user_id", table_name="dushnila_events")
    op.drop_index("ix_dushnila_events_chat_id", table_name="dushnila_events")
    op.drop_index("ix_dushnila_events_id", table_name="dushnila_events")
    op.drop_table("dushnila_events")
