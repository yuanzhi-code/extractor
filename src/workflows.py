
import asyncio
import logging
import time

from src.config import config
from src.graph.graph import run_graph
from src.rss.rss_reader import RssReader
from src.sources import SourceConfig


logger = logging.getLogger(__name__)

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
