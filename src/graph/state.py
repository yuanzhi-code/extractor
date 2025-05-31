from typing import List

from typing_extensions import TypedDict


class State(TypedDict):
    """
    State for the tagger node.
    """

    content: str
    category: str


class DeduplicateState(TypedDict):
    """
    State for the deduplicate node.
    """

    contents: List[str]
    deduplicated_contents: dict[int, str]
