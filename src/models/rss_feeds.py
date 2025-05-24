from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Optional
from numpy import integer
from sqlalchemy import Index, Integer, SmallInteger, String, UniqueConstraint,  orm

from models.base import Base

class FeedStatus(IntEnum):
    NOT_HANDLE = 0
    SUCCESS = 1
    FAIL = 2

class RssFeeds(Base):
    __tablename__  = "rss_feeds"
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    source_type: orm.Mapped[str] = orm.mapped_column(String(10),nullable=False)
    source_url: orm.Mapped[str] = orm.mapped_column(String(255),nullable=False)
    content_file_path: orm.Mapped[str] = orm.mapped_column(String(255),nullable=False)
    published_at: orm.Mapped[datetime] = orm.mapped_column(nullable=False)
    title: orm.Mapped[str] = orm.mapped_column(String(255),nullable=False)
    author: orm.Mapped[str] = orm.mapped_column(String(255),nullable=False)
    status: orm.Mapped[int] = orm.mapped_column(SmallInteger(), nullable=False ,default=0)
    created_at: orm.Mapped[datetime] = orm.mapped_column(nullable=False, default=datetime.now)
    updated_at: orm.Mapped[datetime] = orm.mapped_column(nullable=False, default=datetime.now)
    __table_args__ = (
        UniqueConstraint('source_type', 'source_url', name='unique_source_type_source_url'),
        Index('idx_tb_rss_feeds_status', 'status'),
        Index("idx_tb_rss_feeds_published_at", "published_at")
    )

    def get_status(self)-> FeedStatus:
        return FeedStatus[self.status] # type: ignore