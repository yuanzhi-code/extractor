from typing_extensions import TypedDict

from src.graph.types import TagResult
from src.models.rss_entry import RssEntry


class ClassifyState(TypedDict):
    """
    State for the tagger node.
    """

    content: str
    entry: RssEntry
    category: str
    tagger_approved: bool
    tagger_refine_reason: str
    tag_result: TagResult


class DeduplicateState(TypedDict):
    """
    State for the deduplicate node.
    """

    contents: list[str]
    deduplicated_contents: dict[int, str]
