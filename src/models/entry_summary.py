from datetime import datetime

from sqlalchemy import Integer, String, UniqueConstraint, orm

from src.models.base import Base


class EntrySummary(Base):
    __tablename__ = "entry_summary"
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    entry_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    ai_summary: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    created_gmt: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )
    __table_args__ = (
        UniqueConstraint("entry_id", name="unique_entry_summary_entry_id"),
    )
