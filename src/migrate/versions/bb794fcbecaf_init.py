"""init

Revision ID: bb794fcbecaf
Revises: 
Create Date: 2025-05-24 02:18:53.832366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb794fcbecaf'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'tb_rss_links',
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("link", sa.String(255), nullable=False),
        sa.Column("published_at", sa.DateTime, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("published", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        )
    
    op.create_index('idx_tb_rss_links_link', 'tb_rss_links', ['link'], unique=True)
    op.create_index('idx_tb_rss_links_published_at', 'tb_rss_links', ['published_at'])


def downgrade() -> None:
    """Downgrade schema."""
    pass
