from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, orm

from .base import Base


class EntryScore(Base):
    __tablename__ = "entry_scores"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    entry_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    quality_score: orm.Mapped[int] = orm.mapped_column(
        Integer(), nullable=False
    )
    relevance_score: orm.Mapped[int] = orm.mapped_column(
        Integer(), nullable=False
    )
    final_score: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    __table_args__ = (
        Index("idx_entry_scores_entry_id", "entry_id"),
        Index("idx_entry_scores_final_score", "final_score"),
    )
