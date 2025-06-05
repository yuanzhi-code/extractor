"""
crawl package
"""

from .crawl import (
    WebContentExtractor,
    WebExtractorConfig,
    scrape_multiple_websites,
)

__all__ = [
    "WebContentExtractor",
    "WebExtractorConfig",
    "scrape_multiple_websites",
]
