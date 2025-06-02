import asyncio
import json
import logging
from datetime import datetime, timedelta
from sqlite3 import IntegrityError
from typing import List

import backoff
import requests
from sqlalchemy.orm import Session

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

    def _get_or_insert_feed(self, feed_info: dict):
        """
        get feed info from database, if not found, insert it from input dict.

        returns:
            - feed_info_model: RssFeed model
            - need_full_sync: bool, it indicates that the feed parser need to sync all entries if `True`
        """
        with Session(db) as session:
            rss_feed = (
                session.query(RssFeed).filter_by(link=feed_info["link"]).first()
            )
            if rss_feed is not None:
                feed_info["id"] = rss_feed.id
                return rss_feed, False
            rss_feed = RssFeed(
                title=feed_info["title"],
                description=feed_info["description"],
                link=feed_info["link"],
                language=feed_info["language"],
            )
            rss_feed.datetime_from_str(feed_info["updated"])
            try:
                session.add(rss_feed)
                session.commit()
                session.refresh(rss_feed)
                feed_info["id"] = rss_feed.id
                return rss_feed, True
            except IntegrityError:
                session.rollback()
            except Exception as e:
                logger.error(f"Error inserting feed: {e}")
                raise e

    async def _crawl_entry(self, entries: List[dict]):
        """
        crawl entry content
        """
        tasks = [scrape_website_to_markdown(entry["link"]) for entry in entries]
        results = await asyncio.gather(*tasks)
        for entry, result in zip(entries, results):
            entry["content"] = result["content"]

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
        today = datetime.now(datetime.UTC)  # 使用UTC时间
        end_date = today - timedelta(weeks=fetch_week)

        entries = rss_reader.get_entries_by_date(
            start_date=end_date,
            end_date=feed_updated,
        )
        entries = await self._crawl_entry(entries)
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

        return rss_reader.get_entries_by_date(
            start_date=last_fetched,
            end_date=newest_updated,
        )

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
        feed_info_model, need_full_sync = self._get_or_insert_feed(feed_info)
        if feed_info_model.is_up_to_date(feed_info["updated"]):
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
                last_fetched=feed_info_model.updated,
                newest_updated=feed_info["updated"],
            )

        # update feed updated time after parsing all entries
        session = Session(db)
        try:
            for entry in entries:
                existing_entry = (
                    session.query(RssEntry)
                    .filter_by(link=entry["link"])
                    .first()
                )
                if existing_entry:
                    if existing_entry.content.strip() == "":
                        existing_entry.content = entry["content"]
                        existing_entry.published_at = entry["published_at"]
                        session.flush(existing_entry)
                else:
                    new_entry = entry.copy()
                    new_entry.pop("published")
                    new_entry["published_at"] = parse_feed_datetime(
                        entry["published"]
                    )
                    session.add(RssEntry(**new_entry))
            session.flush(feed_info_model)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        return entries


class SourceConfig:
    def __init__(self, source_path: str):
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.sources = [Source.from_dict(source) for source in data["sources"]]

    @classmethod
    def from_dict(cls, data: dict):
        return [Source.from_dict(source) for source in data["sources"]]
