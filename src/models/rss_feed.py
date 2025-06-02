from datetime import datetime

from sqlalchemy import (
    String,
    UniqueConstraint,
    orm,
)

from src.utils.time import parse_feed_datetime

from .base import Base


class RssFeed(Base):
    """
    RSS Feed 数据模型，用于存储和管理 RSS Feed 的基本信息。

    Attributes:
        id (int): 唯一标识符，RSS Feed 的主键。
        title (str): RSS Feed 的标题，最大长度为 255 个字符，不能为空。
        description (str): RSS Feed 的描述信息，最大长度为 500 个字符。
        link (str): RSS Feed 的链接地址，最大长度为 255 个字符，不能为空。
        language (str): RSS Feed 的语言代码，最大长度为 50 个字符。
        updated (datetime): RSS Feed 最后更新的时间，不能为空。存储为 naive datetime (UTC)
    """

    __tablename__ = "rss_feed"
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    title: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(String(500))
    link: orm.Mapped[str] = orm.mapped_column(String(255), nullable=False)
    language: orm.Mapped[str] = orm.mapped_column(String(50))
    updated: orm.Mapped[datetime] = orm.mapped_column()

    __table_args__ = (UniqueConstraint("link", name="uix_rss_feed_link"),)

    def datetime_from_str(self, updated: str) -> datetime:
        """Convert RSS datetime string to naive UTC datetime and set it to updated field"""
        self.updated = parse_feed_datetime(updated)
        return self.updated

    def is_up_to_date(self, updated: str) -> bool:
        """
        Check if the feed is up to date
        All datetime comparisons are done in naive UTC
        """
        parsed_updated = parse_feed_datetime(updated)
        return self.updated >= parsed_updated
