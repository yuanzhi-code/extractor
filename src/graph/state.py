from typing import List

from typing_extensions import TypedDict

from src.graph.types import TagResult
from src.models.rss_entry import RssEntry


class ClassifyState(TypedDict):
    """
    State for the tagger node.
    """

    content: str
    entry: RssEntry
    tag_result: TagResult


class DeduplicateState(TypedDict):
    """
    State for the deduplicate node.
    """

    contents: List[str]
    deduplicated_contents: dict[int, str]
