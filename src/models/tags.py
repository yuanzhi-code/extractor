from datetime import datetime

from sqlalchemy import (
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    orm,
)

from .base import Base


class Categories(Base):
    __tablename__ = "categories"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    name: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )
    description: orm.Mapped[str] = orm.mapped_column(
        String(255), nullable=False
    )

    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)


class EntriesCategories(Base):
    __tablename__ = "entries_categories"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    entry_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    category_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )

    __table_args__ = (
        Index("idx_entries_categories_entry_id", "entry_id"),
        Index("idx_entries_categories_category_id", "category_id"),
    )
