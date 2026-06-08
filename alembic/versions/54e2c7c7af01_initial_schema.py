"""initial schema

Revision ID: 54e2c7c7af01
Revises:
Create Date: 2026-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "54e2c7c7af01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    if op.get_context().dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def _created_at_default():
    if op.get_context().dialect.name == "postgresql":
        return sa.text("now()")
    return sa.text("CURRENT_TIMESTAMP")


def _table_exists(table_name: str) -> bool:
    try:
        return sa.inspect(op.get_bind()).has_table(table_name)
    except sa.exc.NoInspectionAvailable:
        return False


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("Users"):
        op.create_table(
            "Users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("telegram_id", sa.BIGINT(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=_created_at_default(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("telegram_id"),
        )
    if not _table_exists("Car_Models"):
        op.create_table(
            "Car_Models",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("manufacturer", sa.String(length=20), nullable=True),
            sa.Column("model", sa.String(length=40), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _table_exists("Car_Searches"):
        op.create_table(
            "Car_Searches",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("car_model_id", sa.Integer(), nullable=False),
            sa.Column("psc_code", sa.String(length=6), nullable=True),
            sa.Column("psc_km_range", sa.String(length=4), nullable=True),
            sa.Column("year_range_from", sa.Integer(), nullable=True),
            sa.Column("year_range_to", sa.Integer(), nullable=True),
            sa.Column("mileage_range_from", sa.Integer(), nullable=True),
            sa.Column("mileage_range_to", sa.Integer(), nullable=True),
            sa.Column("price_range_from", sa.Integer(), nullable=True),
            sa.Column("price_range_to", sa.Integer(), nullable=True),
            sa.Column("_last_checked_links", _json_type(), nullable=True),
            sa.Column("_last_checked_toped_links", _json_type(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=_created_at_default(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["car_model_id"], ["Car_Models.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["Users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _table_exists("Advertisements_Queue"):
        op.create_table(
            "Advertisements_Queue",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("car_search_id", sa.Integer(), nullable=False),
            sa.Column("queue", _json_type(), nullable=True),
            sa.ForeignKeyConstraint(
                ["car_search_id"],
                ["Car_Searches.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("car_search_id", name="uq_car_search_queue"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table_name in (
        "Advertisements_Queue",
        "Car_Searches",
        "Car_Models",
        "Users",
    ):
        if _table_exists(table_name):
            op.drop_table(table_name)
