import asyncio
import datetime
import logging
import time

from sqlalchemy.orm import Session

from src.config import config
from src.graph import run_classification_graph
from src.models import db
from src.models.rss_entry import RssEntry
from src.models.tags import EntryCategory
from src.rss.rss_reader import RssReader
from src.sources import SourceConfig

logger = logging.getLogger(__name__)


async def consumer(task_queue: asyncio.Queue):
    try:
        while True:
            entry = await task_queue.get()
            if entry is None:
                break
            try:
                logger.info(f"Processing entry: {entry.get('title', '')}")
                await run_classification_graph(entry)
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
            finally:
                task_queue.task_done()
    except asyncio.CancelledError:
        logger.info("Consumer task cancelled")
        raise


def _convert_rss_entry_to_dict(rss_entry: RssEntry) -> dict:
    """
    Convert SQLAlchemy RssEntry object to dictionary format
    """
    return {
        "id": rss_entry.id,
        "feed_id": rss_entry.feed_id,
        "title": rss_entry.title,
        "link": rss_entry.link,
        "content": rss_entry.content,
        "author": rss_entry.author,
        "summary": rss_entry.summary,
        "published_at": rss_entry.published_at,
        "created_gmt": rss_entry.created_gmt,
        "modified_gmt": rss_entry.modified_gmt,
    }


# if __name__ == "__main__":
async def fetch_task(max_workers: int = 10):
    """
    entrypoint for fetch and parse source
    """
    try:
        rss_reader = RssReader(config.NETWORK_PROXY)

        source_config = SourceConfig(source_dir="./data")
        entries = []
        for source in source_config.sources:
            try:
                new_entries = await source.parse(rss_reader)
                logger.info(
                    f"Fetched {len(new_entries)} entries from {source.name}"
                )
                entries.extend(new_entries)
            except Exception as e:
                logger.error(f"Error parsing source {source.name}: {e}")
        with Session(db) as session:
            today = datetime.datetime.today()
            _e = (
                session.query(RssEntry)
                .filter(
                    RssEntry.published_at >= today - datetime.timedelta(days=7)
                )
                .join(EntryCategory, RssEntry.id == EntryCategory.entry_id)
                .all()
            )
            # Convert SQLAlchemy objects to dictionary format
            db_entries = [_convert_rss_entry_to_dict(entry) for entry in _e]
            entries.extend(db_entries)
        if not entries or len(entries) == 0:
            logger.info(
                f"No new entries for source {source.name} to process, check the entries in database which may need to be process"
            )
        return entries
    except Exception as e:
        logger.error(f"Error fetching task: {e}")
        raise