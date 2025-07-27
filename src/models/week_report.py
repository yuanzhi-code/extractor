from datetime import datetime

from sqlalchemy import orm

from .base import Base


class WeekReport(Base):
    __tablename__ = "week_report"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    week_start: orm.Mapped[datetime] = orm.mapped_column(nullable=False)
    week_end: orm.Mapped[datetime] = orm.mapped_column(nullable=False)
    title: orm.Mapped[str] = orm.mapped_column(nullable=False)
    summary: orm.Mapped[str] = orm.mapped_column(nullable=False)
    content: orm.Mapped[str] = orm.mapped_column(nullable=False)
