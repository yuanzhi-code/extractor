"""
crawl package
"""

from .crawl import (
    WebContentExtractor,
    quick_scrape,
    scrape_multiple_websites,
    scrape_sync,
    scrape_website_to_markdown,
)

__all__ = [
    "WebContentExtractor",
    "scrape_multiple_websites",
    "scrape_sync",
    "scrape_website_to_markdown",
    "quick_scrape",
]
