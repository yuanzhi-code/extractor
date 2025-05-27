"""
crawl package
"""

from .crawl import (
    WebContentExtractor,
    scrape_multiple_websites,
    scrape_sync,
    scrape_website_to_markdown,
    quick_scrape,
)

__all__ = [
    "WebContentExtractor",
    "scrape_multiple_websites",
    "scrape_sync",
    "scrape_website_to_markdown",
    "quick_scrape",
]
