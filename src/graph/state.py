from typing_extensions import TypedDict


class State(TypedDict):
    """
    State for the tagger node.
    """

    content: str
    category: str
