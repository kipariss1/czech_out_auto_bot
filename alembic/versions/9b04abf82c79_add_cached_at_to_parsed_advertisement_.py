"""add cached_at to parsed advertisement cache

Revision ID: 9b04abf82c79
Revises: 60b4deb1bd84
Create Date: 2026-09-11 15:03:11.757549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b04abf82c79'
down_revision: Union[str, Sequence[str], None] = '60b4deb1bd84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _created_at_default():
    if op.get_context().dialect.name == "postgresql":
        return sa.text("now()")
    return sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "Parsed_Advertisements_Cache",
        sa.Column(
            "cached_at",
            sa.DateTime(timezone=True),
            server_default=_created_at_default(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("Parsed_Advertisements_Cache", "cached_at")
