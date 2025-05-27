from datetime import datetime
from sqlalchemy import orm
from .base import Base


class EntryScore(Base):
    __tablename__ = "entry_scores"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    entry_id: orm.Mapped[int] = orm.mapped_column(
        orm.Integer(), nullable=False
    )
    quality_score: orm.Mapped[int] = orm.mapped_column(
        orm.Integer(), nullable=False
    )
    relevance_score: orm.Mapped[int] = orm.mapped_column(
        orm.Integer(), nullable=False
    )
    final_score: orm.Mapped[int] = orm.mapped_column(
        orm.Integer(), nullable=False
    )
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        orm.DateTime(), nullable=False, default=datetime.now
    )
    __table_args__ = (
        orm.Index("idx_entry_scores_entry_id", "entry_id"),
        orm.Index("idx_entry_scores_final_score", "final_score"),
    )