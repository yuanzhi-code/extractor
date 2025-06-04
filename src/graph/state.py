from typing_extensions import TypedDict

from src.models.rss_entry import RssEntry


class State(TypedDict):
    """
    State for the tagger node.
    """

    content: str
    entry: RssEntry
    category: str


class DeduplicateState(TypedDict):
    """
    State for the deduplicate node.
    """

    contents: list[str]
    deduplicated_contents: dict[int, str]
