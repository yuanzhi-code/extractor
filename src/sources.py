import asyncio
import json
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from sqlite3 import IntegrityError
from typing import List, Optional

import backoff
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.crawl.crawl import scrape_website_to_markdown
from src.models import db
from src.models.rss_entry import RssEntry
from src.models.rss_feed import RssFeed
from src.rss import RssReader
from src.utils.time import parse_feed_datetime

logger = logging.getLogger(__name__)


class Source:
    """
    Source for the RSS reader.
    """

    def __init__(self, name: str, url: str, description: str):
        self.name = name
        self.url = url
        self.description = description

    def __str__(self):
        return f"{self.name} - {self.url}"

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            url=data["url"],
            description=data["description"],
        )

    @classmethod
    def from_xml_element(cls, element: ET.Element):
        return cls(
            name=element.get("text"),
            url=element.get("xmlUrl"),
            description=element.get("title"),
        )

    def _get_or_insert_feed(self, feed_info: dict):
        """
        使用原生 SQL 实现 feed 的获取或插入功能。
        使用 SQLite 的 UPSERT 语法（INSERT OR REPLACE）来处理并发情况。

        Args:
            feed_info: feed 信息字典

        Returns:
            tuple:
                - feed_id: int, feed 的 ID
                - need_full_sync: bool, 是否需要全量同步
        """
        with Session(db) as session:
            try:
                # 首先尝试查找已存在的 feed
                result = session.execute(
                    text(
                        """
                    SELECT id, updated 
                    FROM rss_feed 
                    WHERE link = :link
                    """
                    ),
                    {"link": feed_info["link"]},
                ).first()

                if result:
                    # 如果找到记录，检查是否需要更新
                    feed_id, current_updated = result
                    return feed_id, True
                else:
                    # 如果不存在，插入新记录，updated 设置为 Unix 时间戳起始时间（naive UTC）
                    result = session.execute(
                        text(
                            """
                        INSERT INTO rss_feed (title, description, link, language, updated)
                        VALUES (:title, :description, :link, :language, :updated)
                        RETURNING id
                        """
                        ),
                        {
                            "title": feed_info["title"],
                            "description": feed_info["description"],
                            "link": feed_info["link"],
                            "language": feed_info["language"],
                            "updated": datetime(1970, 1, 1).replace(
                                tzinfo=None
                            ),  # naive UTC
                        },
                    )
                    feed_id = result.scalar()
                    feed_info["id"] = feed_id
                    session.commit()
                    return feed_id, True

            except Exception as e:
                session.rollback()
                logger.error(f"处理 feed 时发生错误: {e}")
                raise

    async def _crawl_entry(self, entries: List[dict]):
        """
        crawl entry content
        Args:
            entries: list of entries to crawl content for
        Returns:
            List[dict]: entries with crawled content
        """
        tasks = [scrape_website_to_markdown(entry["link"]) for entry in entries]
        results = await asyncio.gather(*tasks)
        for entry, result in zip(entries, results):
            entry["content"] = result["content"]
        return entries

    async def _full_sync_feed(
        self,
        rss_reader: RssReader,
        feed_updated: datetime | str,
        fetch_week: int = 1,
    ):
        """
        full sync feed entries
        Args:
            feed_updated: 最新更新时间，可以是datetime对象或RSS格式的时间字符串
            fetch_week: 要获取的历史数据的周数
        """
        if isinstance(feed_updated, str):
            feed_updated = parse_feed_datetime(feed_updated)

        logger.info("a new feed is found, need to full sync")
        today = datetime.now(timezone.utc).replace(
            tzinfo=None
        )  # 转换为 naive UTC
        end_date = today - timedelta(weeks=fetch_week)

        entries = rss_reader.get_entries_by_date(
            start_date=end_date,
            end_date=feed_updated,
        )
        await self._crawl_entry(entries)
        return entries

    async def _partial_sync_feed(
        self,
        rss_reader: RssReader,
        last_fetched: datetime,
        newest_updated: datetime | str,
    ):
        """
        partial sync feed entries
        Args:
            last_fetched: 上次获取的时间
            newest_updated: 最新更新时间，可以是datetime对象或RSS格式的时间字符串
        """
        if isinstance(newest_updated, str):
            newest_updated = parse_feed_datetime(newest_updated)

        logger.info(
            f"fetch new entry between {last_fetched} to {newest_updated}"
        )

        entries = rss_reader.get_entries_by_date(
            start_date=last_fetched,
            end_date=newest_updated,
        )
        await self._crawl_entry(entries)
        return entries

    @backoff.on_exception(
        backoff.expo, requests.RequestException, max_time=30, max_tries=3
    )
    async def parse(self, rss_reader: RssReader) -> list[dict]:
        """
        parse feed and return entries
        if feed is up to date, return empty list
        if feed is not up to date, parse entries and return entries
        if error occurs, raise the error
        """
        if not rss_reader.parse_feed(self.url):
            return []
        feed_info = rss_reader.get_feed_info()
        # TODO 判断 数据库里 是否存在
        feed_id, need_full_sync = self._get_or_insert_feed(feed_info)

        with Session(db) as session:
            feed = session.query(RssFeed).get(feed_id)
            # TODO
            if feed.is_up_to_date(feed_info["updated"]):
                logger.info(f"Feed {feed_info['title']} is up to date")
                return []

            rss_reader.update_feed_info(feed_info=feed_info)
            logger.info(f"Feed标题: {feed_info['title']}")
            logger.info(f"Feed描述: {feed_info['description']}")
            logger.info(f"Feed链接: {feed_info['link']}")
            logger.info(f"Feed语言: {feed_info['language']}")
            logger.info(f"最后更新: {feed_info['updated']}")
            logger.info("-" * 50)

            if need_full_sync:
                entries = await self._full_sync_feed(
                    rss_reader=rss_reader, feed_updated=feed_info["updated"]
                )
            else:
                entries = await self._partial_sync_feed(
                    rss_reader=rss_reader,
                    last_fetched=feed.updated,
                    newest_updated=feed_info["updated"],
                )

            # 更新条目，刷新 feed 作为一个完整的事务
            feed.datetime_from_str(feed_info["updated"])
            session.add(feed)

            # 然后更新或插入条目
            for entry in entries:
                existing_entry = (
                    session.query(RssEntry)
                    .filter_by(link=entry["link"])
                    .first()
                )
                # 条目已存在，考虑 content 是否为空
                if existing_entry:
                    if existing_entry.content.strip() == "":
                        existing_entry.content = entry["content"]
                        existing_entry.published_at = entry["published_at"]
                        session.add(existing_entry)
                else:
                    new_entry = entry.copy()
                    new_entry.pop("published")
                    new_entry["published_at"] = parse_feed_datetime(
                        entry["published"]
                    )
                    session.add(RssEntry(**new_entry))

            session.commit()
            return entries


class SourceConfig:
    def __init__(
        self,
        source_path: Optional[str] = None,
        source_dir: Optional[str] = None,
    ):
        self.sources = []
        self._link_set: set[str] = set()
        if source_path is not None:
            self.from_json(source_path)
        elif source_dir is not None:
            for file in os.listdir(source_dir):
                if file.endswith(".json"):
                    self.from_json(os.path.join(source_dir, file))
                elif file.endswith(".opml"):
                    self.from_opml(os.path.join(source_dir, file))
        else:
            raise ValueError("no source path or source dir provided")

    def insert_source(self, source: Source):
        if source.url in self._link_set:
            return
        self._link_set.add(source.url)
        self.sources.append(source)

    def from_json(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "sources" not in data:
                raise ValueError("invalid json file")
            data = data["sources"]
            for source in data:
                self.insert_source(Source.from_dict(source))

    def from_opml(self, opml_path: str):
        tree = ET.parse(opml_path)
        root = tree.getroot()
        if not isinstance(root, ET.Element):
            raise ValueError("invalid opml file")
        for child in root.iter("outline"):
            if child.get("type") == "rss":
                self.insert_source(Source.from_xml_element(child))
        return self
