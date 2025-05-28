from langgraph.graph import MessagesState


class State(MessagesState):
    """
    State for the tagger node.
    """

    category: str
