import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from sqlite3 import IntegrityError

import backoff
import requests
from sqlalchemy.orm import Session

from src.config.app_config import AppConfig
from src.graph.graph import run_graph
from src.models import db
from src.models.rss_feed import RssFeed
from src.rss import RssReader

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

    def _full_sync_feed(
        self,
        rss_reader: RssReader,
        feed_updated: datetime | str,
        fetch_week: int = 1,
    ):
        """
        full sync feed entries
        """
        if isinstance(feed_updated, str):
            feed_updated = datetime.strptime(
                feed_updated, "%a, %d %b %Y %H:%M:%S %z"
            )
        logger.info(f"a new feed is found, need to full sync")
        # 虽然是全量拉取，但对于我们的业务场景而言，我们可能不需要拉取所有条目，因为订阅源有时效性问题
        today = datetime.today()
        end_date = today - timedelta(weeks=fetch_week)
        return rss_reader.get_entries_by_date(
            start_date=end_date,
            end_date=feed_updated,
        )

    def _partial_sync_feed(
        self,
        rss_reader: RssReader,
        last_fetched: datetime,
        newest_updated: datetime | str,
    ):
        """
        partial sync feed entries
        """
        if isinstance(newest_updated, str):
            newest_updated = datetime.strptime(
                newest_updated, "%a, %d %b %Y %H:%M:%S %z"
            )
        logger.info(
            "fetch new entry between {} to {}", last_fetched, newest_updated
        )
        return rss_reader.get_entries_by_date(
            start_date=newest_updated,
            end_date=last_fetched,
        )

    @backoff.on_exception(
        backoff.expo, requests.RequestException, max_time=30, max_retries=3
    )
    def parse(self, rss_reader: RssReader) -> list[dict]:
        """
        parse feed and return entries
        if feed is up to date, return empty list
        if feed is not up to date, parse entries and return entries
        if error occurs, raise the error
        """
        if rss_reader.parse_feed(self.url):
            feed_info = rss_reader.get_feed_info()
            feed_info_model, need_full_sync = self._get_or_insert_feed(
                feed_info
            )
            if feed_info_model.is_up_to_date(feed_info["updated"]):
                logger.info(f"Feed {feed_info['title']} is up to date")
                return []
            rss_reader.update_feed_info(feed_info)
            logger.info(f"Feed标题: {feed_info['title']}")
            logger.info(f"Feed描述: {feed_info['description']}")
            logger.info(f"Feed链接: {feed_info['link']}")
            logger.info(f"Feed语言: {feed_info['language']}")
            logger.info(f"最后更新: {feed_info['updated']}")
            logger.info("-" * 50)
            if need_full_sync:
                entries = self._full_sync_feed(
                    rss_reader=rss_reader, feed_updated=feed_info["updated"]
                )
            else:
                entries = self._partial_sync_feed(
                    rss_reader=rss_reader,
                    last_fetched=feed_info_model.updated,
                    newest_updated=feed_info["updated"],
                )
            # today = datetime.today()
            # start_date = datetime(today.year, today.month, 1)
            # end_date = datetime(today.year, today.month, 1) + timedelta(days=31)
            # end_date = end_date.replace(day=1) - timedelta(days=1)

            # logger.info(
            #     f"本月的RSS条目 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}):"
            # )
            # entries = rss_reader.get_entries_by_date(
            #     start_date=start_date,
            #     end_date=end_date,
            # )

            # update feed updated time after parsing all entries
            with Session(db) as session:
                session.flush(feed_info_model)

            return entries
        # 在请求之间添加延时，避免请求过于频繁
        return []


class SourceConfig:
    def __init__(self, source_path: str):
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.sources = [
            Source.from_dict(source) for source in data["sources"]
        ]

    @classmethod
    def from_dict(cls, data: dict):
        return [Source.from_dict(source) for source in data["sources"]]


async def consumer(task_queue: asyncio.Queue):
    while True:
        entry = await task_queue.get()
        if entry is None:
            break
        logger.info(f"Processing entry: {entry.id}")
        await run_graph(entry)
        task_queue.task_done()


# if __name__ == "__main__":
async def fetch_task(max_workers: int = 10):
    """
    entrypoint for fetch and parse source
    """

    config = AppConfig()
    rss_reader = RssReader(config.NETWORK_PROXY)

    source_config = SourceConfig("./data/rss_sources.json")
    entries = []
    for source in source_config.sources:
        entries.extend(source.parse(rss_reader))

    task_queue = asyncio.Queue()
    for entry in entries:
        await task_queue.put(entry)

    logger.info(f"Starting {max_workers} workers")
    workers = [
        asyncio.create_task(consumer(task_queue)) for _ in range(max_workers)
    ]
    start_time = time.time()

    await task_queue.join()

    for worker in workers:
        worker.cancel()

    await asyncio.gather(*workers)

    end_time = time.time()
    logger.info(f"Total time: {end_time - start_time} seconds")
