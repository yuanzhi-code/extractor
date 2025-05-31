from datetime import datetime
from enum import IntEnum

from sqlalchemy import (
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    orm,
)

from .base import Base

class Categories(IntEnum):
    TECH = 1
    BUSINESS = 2
    EXPERIENCE = 3
    OTHER = 4

    @staticmethod
    def from_str(value: str) -> int:
        if value.casefold() == "tech":
            return Categories.TECH
        elif value.casefold() == "business":
            return Categories.BUSINESS
        elif value.casefold() == "experience":
            return Categories.EXPERIENCE
        else:
            raise ValueError(f"Invalid category: {value}")


class EntriesCategories(Base):
    __tablename__ = "entries_categories"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    entry_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    category: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )

    __table_args__ = (
        Index("idx_entries_categories_entry_id", "entry_id"),
        Index("idx_entries_categories_category", "category"),
    )

    @property
    def entry_category_(self) -> Categories:
        return Categories(self.category)
