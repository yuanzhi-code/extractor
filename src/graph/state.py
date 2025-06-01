from typing import List

from typing_extensions import TypedDict

from src.models.rss_entry import RssEntry


class State(TypedDict):
    """
    State for the tagger node.
    """

    content: str
    entry: RssEntry
    category: str

    @property
    def entry_content(self) -> str:
        return self["entry"].content

    @property
    def entry_id(self) -> int:
        return self["entry"].id


class DeduplicateState(TypedDict):
    """
    State for the deduplicate node.
    """

    contents: List[str]
    deduplicated_contents: dict[int, str]
