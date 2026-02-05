"""Initial schema.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-02-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "last_winner",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("chat_title", sa.String(), nullable=True),
        sa.Column("last_datetime", sa.DateTime(), nullable=False),
        sa.Column("winner_user_id", sa.String(), nullable=False),
        sa.Column("winner_full_name", sa.String(), nullable=False),
        sa.Column("winner_username", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )
    op.create_index("ix_last_winner_chat_id", "last_winner", ["chat_id"])
    op.create_index("ix_last_winner_id", "last_winner", ["id"])

    op.create_table(
        "winner_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("chat_title", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_winner_stats_chat_id", "winner_stats", ["chat_id"])
    op.create_index("ix_winner_stats_id", "winner_stats", ["id"])
    op.create_index("ix_winner_stats_user_id", "winner_stats", ["user_id"])

    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("chat_title", sa.String(), nullable=True),
        sa.Column("last_active", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_participants_chat_id", "participants", ["chat_id"])
    op.create_index("ix_participants_id", "participants", ["id"])
    op.create_index("ix_participants_last_active", "participants", ["last_active"])
    op.create_index("ix_participants_user_id", "participants", ["user_id"])

    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("added_by", sa.String(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=True),
        sa.Column("deleted_by", sa.String(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )
    op.create_index("ix_chats_chat_id", "chats", ["chat_id"])
    op.create_index("ix_chats_id", "chats", ["id"])

    op.create_table(
        "search_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_logs_id", "search_logs", ["id"])

    op.create_table(
        "morning_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("filename"),
    )
    op.create_index("ix_morning_images_id", "morning_images", ["id"])


def downgrade() -> None:
    op.drop_index("ix_morning_images_id", table_name="morning_images")
    op.drop_table("morning_images")

    op.drop_index("ix_search_logs_id", table_name="search_logs")
    op.drop_table("search_logs")

    op.drop_index("ix_chats_id", table_name="chats")
    op.drop_index("ix_chats_chat_id", table_name="chats")
    op.drop_table("chats")

    op.drop_index("ix_participants_user_id", table_name="participants")
    op.drop_index("ix_participants_last_active", table_name="participants")
    op.drop_index("ix_participants_id", table_name="participants")
    op.drop_index("ix_participants_chat_id", table_name="participants")
    op.drop_table("participants")

    op.drop_index("ix_winner_stats_user_id", table_name="winner_stats")
    op.drop_index("ix_winner_stats_id", table_name="winner_stats")
    op.drop_index("ix_winner_stats_chat_id", table_name="winner_stats")
    op.drop_table("winner_stats")

    op.drop_index("ix_last_winner_id", table_name="last_winner")
    op.drop_index("ix_last_winner_chat_id", table_name="last_winner")
    op.drop_table("last_winner")
