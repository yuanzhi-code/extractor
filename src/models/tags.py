from datetime import datetime
from enum import IntEnum

from sqlalchemy import (
    Index,
    Integer,
    orm,
)

from .base import Base


class Category(IntEnum):
    TECH = 1
    BUSINESS = 2
    EXPERIENCE = 3
    AGGREGATION = 4
    OTHER = 4

    @staticmethod
    def from_str(value: str) -> int:
        if value.casefold() == "tech":
            return Category.TECH
        elif value.casefold() == "business":
            return Category.BUSINESS
        elif value.casefold() == "experience":
            return Category.EXPERIENCE
        else:
            raise ValueError(f"Invalid category: {value}")


class EntryCategory(Base):
    __tablename__ = "entry_category"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    entry_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    category: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )

    __table_args__ = (
        Index("idx_entry_category_entry_id", "entry_id"),
        Index("idx_entry_category_category", "category"),
    )

    @property
    def entry_category_(self) -> Category:
        return Category(self.category)
