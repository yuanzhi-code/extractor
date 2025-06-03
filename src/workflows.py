import asyncio
import datetime
import logging
import time

from sqlalchemy.orm import Session

from src.config import config
from src.graph.graph import run_graph
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
                await run_graph(entry)
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
            finally:
                task_queue.task_done()
    except asyncio.CancelledError:
        logger.info("Consumer task cancelled")
        raise


# if __name__ == "__main__":
async def fetch_task(max_workers: int = 10):
    """
    entrypoint for fetch and parse source
    """
    try:
        rss_reader = RssReader(config.NETWORK_PROXY)

        source_config = SourceConfig("./data/rss_sources.json")
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
            entries.extend(_e)
        if not entries or len(entries) == 0:
            logger.info(
                f"No new entries for source {source.name} to process, check the entries in database which may need to be process"
            )
            return

        task_queue = asyncio.Queue()
        for entry in entries:
            await task_queue.put(entry)

        logger.info(f"Starting {max_workers} workers")
        workers = [
            asyncio.create_task(consumer(task_queue))
            for _ in range(max_workers)
        ]
        start_time = time.time()

        try:
            await task_queue.join()
        finally:
            # 取消所有worker
            for worker in workers:
                worker.cancel()
            # 等待所有worker完成
            await asyncio.gather(*workers, return_exceptions=True)

        end_time = time.time()
        logger.info(f"Total time: {end_time - start_time} seconds")
    except Exception as e:
        logger.error(f"Error in fetch_task: {e}")
        raise
