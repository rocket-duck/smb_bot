"""Migrate ID columns from String to BigInteger; add composite unique constraints.

Revision ID: 0002_bigint_ids_composite_idx
Revises: 0001_initial
Create Date: 2026-03-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_bigint_ids_composite_idx"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("last_winner") as batch_op:
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "winner_user_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    with op.batch_alter_table("winner_stats") as batch_op:
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "user_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.create_unique_constraint(
            "uq_winner_stats_chat_user", ["chat_id", "user_id"]
        )

    with op.batch_alter_table("participants") as batch_op:
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "user_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.create_unique_constraint(
            "uq_participants_chat_user", ["chat_id", "user_id"]
        )

    with op.batch_alter_table("chats") as batch_op:
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    with op.batch_alter_table("search_logs") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.String(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("search_logs") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )

    with op.batch_alter_table("chats") as batch_op:
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )

    with op.batch_alter_table("participants") as batch_op:
        batch_op.drop_constraint("uq_participants_chat_user", type_="unique")
        batch_op.alter_column(
            "user_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )

    with op.batch_alter_table("winner_stats") as batch_op:
        batch_op.drop_constraint("uq_winner_stats_chat_user", type_="unique")
        batch_op.alter_column(
            "user_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )

    with op.batch_alter_table("last_winner") as batch_op:
        batch_op.alter_column(
            "winner_user_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.BigInteger(),
            type_=sa.String(),
            existing_nullable=False,
        )
