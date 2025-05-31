from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Index, Integer, String, orm

from .base import Base

class Score(StrEnum):
    NOISE = "noise"
    ACTIONABLE = "actionable"
    SYSTEMATIC = "systematic"

class EntryScore(Base):
    __tablename__ = "entry_scores"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    entry_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    score: orm.Mapped[str] = orm.mapped_column(String(25), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        DateTime(), nullable=False, default=datetime.now
    )
    __table_args__ = (
        Index("idx_entry_scores_entry_id", "entry_id"),
        Index("idx_entry_scores_score", "score"),
    )
