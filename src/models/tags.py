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


class Tags(Base):
    __tablename__ = "tags"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    name: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )
    category: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(
        String(255), nullable=False
    )
    parent_id: orm.Mapped[int | None] = orm.mapped_column(
        Integer(), nullable=True
    )
    level: orm.Mapped[int] = orm.mapped_column(
        SmallInteger(), nullable=False, default=1
    )

    __table_args__ = (
        Index("idx_tags_parent_id", "parent_id"),
        Index("idx_tags_level", "level"),
        UniqueConstraint("name", "parent_id", name="uq_tags_name_parent"),
    )


class EntriesTags(Base):
    __tablename__ = "entries_tags"
    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    entry_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    tag_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )

    __table_args__ = (
        Index("idx_entries_tags_entry_id", "entry_id"),
        Index("idx_entries_tags_tag_id", "tag_id"),
    )
