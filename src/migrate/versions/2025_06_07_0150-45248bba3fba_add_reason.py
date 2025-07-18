"""add_reason

Revision ID: 45248bba3fba
Revises: 6858dee2ac72
Create Date: 2025-06-07 01:50:16.823895

"""

# isort: skip_file
from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "45248bba3fba"
down_revision: Union[str, None] = "6858dee2ac72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("entry_category", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("reason", sa.String(length=255), nullable=False)
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("entry_category", schema=None) as batch_op:
        batch_op.drop_column("reason")

    # ### end Alembic commands ###
