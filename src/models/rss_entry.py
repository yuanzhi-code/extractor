from datetime import datetime
from enum import IntEnum

from sqlalchemy import (
    TEXT,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    orm,
)

from models.base import Base


class FeedStatus(IntEnum):
    NOT_HANDLE = 0
    SUCCESS = 1
    FAIL = 2


class RssEntry(Base):
    """
    RssFeeds 类表示 RSS 源的数据库模型。
    它存储从各种 RSS 源提取的文章信息，并跟踪每篇文章的状态。
    主要字段包括：
    - id: 文章的唯一标识符
    - feed_id: 源的唯一标识符
    - link: 文章的原始 URL
    - content: 文章内容
    - published: 文章的发布时间
    - title: 文章标题
    - author: 文章作者
    - status: 处理状态(0: 未处理, 1: 成功, 2: 失败)
    - summery: 总结
    - created_gmt: 记录创建时间
    - modified_gmt: 最后更新时间
    """

    __tablename__ = "rss_entry"
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    feed_id: orm.Mapped[int] = orm.mapped_column(Integer(), nullable=True)
    link: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    content: orm.Mapped[str] = orm.mapped_column(TEXT, nullable=False)
    title: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    author: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    status: orm.Mapped[int] = orm.mapped_column(
        SmallInteger(), nullable=False, default=0
    )
    summary: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    published_at: orm.Mapped[datetime] = orm.mapped_column(nullable=False)
    created_gmt: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )
    modified_gmt: orm.Mapped[datetime] = orm.mapped_column(
        nullable=False, default=datetime.now
    )
    __table_args__ = (
        UniqueConstraint("link", name="unique_rss_entry_link"),
        Index("idx_rss_entry_status", "status"),
        Index("idx_rss_entry_published_at", "published_at"),
    )

    def get_status(self) -> FeedStatus:
        return FeedStatus[self.status]  # type: ignore
