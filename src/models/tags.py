from datetime import datetime
from .base import Base
from sqlalchemy import Index, Integer, SmallInteger, String, UniqueConstraint, orm


class tags(Base):
    __tablename__ = "tags"
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, autoincrement=True)
    name: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )
    category: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)


class feeds_tags(Base):
    __tablename__ = "content_tags"
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, autoincrement=True)
    feed_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    tag_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )
