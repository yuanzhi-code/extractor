import asyncio
import datetime
import logging

from sqlalchemy.orm import Session

from src.config import config
from src.graph.classify_graph import run_classification_graph
from src.models import db
from src.models.rss_entry import RssEntry
from src.models.tags import EntryCategory
from src.rss.rss_reader import RssReader
from src.sources import Source, SourceConfig

logger = logging.getLogger(__name__)


# if __name__ == "__main__":
async def fetch_task(max_workers: int = 10):
    """
    entrypoint for fetch and parse source
    """
    try:
        rss_reader = RssReader(config.NETWORK_PROXY)

        source_config = SourceConfig(source_dir="./data")
        entries: list[dict] = []
        for source in source_config.sources:
            try:
                new_entries = await source.parse(rss_reader)
                logger.info(
                    f"Fetched {len(new_entries)} entries from {source.name}"
                )
                entries.extend(new_entries)
            except Exception as e:
                logger.exception(f"Error parsing source {source.name}:")
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
            # Add RssEntry objects directly (if this function is supposed to return RssEntry objects)
            # Or keep the existing logic if it should return dict entries from sources
            entries.extend(_e)
        if not entries or len(entries) == 0:
            logger.info(
                f"""No new entries for source {source.name} to process,
                check the entries in database which may need to be process"""
            )
        return entries
    except Exception as e:
        logger.exception("Error fetching task:")
        raise


async def run_crawl():
    """
    entrypoint for crawl and parse source
    """
    sources = SourceConfig(source_dir="./data")
    rss_reader = RssReader(config.NETWORK_PROXY)

    async def run_crawl_for_source(source: Source):
        try:
            await source.parse(rss_reader)
        except Exception as e:
            logger.exception(f"Error crawling source {source.name}:")

    tasks = [run_crawl_for_source(source) for source in sources.sources]
    await asyncio.gather(*tasks)


async def run_classify_graph(first: bool = True, entry_nums: int = 10):
    """
    run the graph for the entry with concurrent execution

    Args:
        first: if True, only process the first entry
        entry_nums: number of entries to process concurrently when first=False (default: 5)
    Returns:
        dict: processing results summary
    """
    with Session(db) as session:
        if first:
            entry = session.query(RssEntry).first()
            if entry:
                await run_classification_graph(entry)
                logger.info("Single entry processing completed")
                return {"processed": 1, "errors": 0}
            else:
                logger.info("No entries found to process")
                return {"processed": 0, "errors": 0}
        else:
            # Get limited number of entries
            entries = session.query(RssEntry).limit(entry_nums).all()
            if not entries:
                logger.info("No entries found to process")
                return {"processed": 0, "errors": 0}

            logger.info(
                f"Starting concurrent processing of {len(entries)} entries"
            )

            async def process_single_entry(entry):
                """Process a single entry and return result"""
                try:
                    await run_classification_graph(entry)
                    logger.info(f"Successfully processed entry {entry.id}")
                    return {"entry_id": entry.id, "status": "success"}
                except Exception as e:
                    logger.exception(f"Error processing entry {entry.id}:")
                    return {
                        "entry_id": entry.id,
                        "status": "error",
                        "error": str(e),
                    }

            # Create tasks for concurrent execution
            tasks = [process_single_entry(entry) for entry in entries]

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful and failed processes
            processed = 0
            errors = 0

            for result in results:
                if isinstance(result, dict):
                    if result.get("status") == "success":
                        processed += 1
                    else:
                        errors += 1
                else:
                    # Handle exceptions from gather
                    errors += 1
                    logger.error(
                        f"Unexpected error in concurrent processing: {result}"
                    )

            logger.info(
                f"Concurrent processing completed: {processed} successful, {errors} errors"
            )
            return {"processed": processed, "errors": errors}
