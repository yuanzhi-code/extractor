from langgraph.graph import StateGraph
from langgraph.graph import START, END

from .tagger import tagger_node

from .state import State


def get_graph() -> StateGraph:
    """
    Get the graph for the tagger node.
    """
    builder = StateGraph(State)
    builder.add_edge(START, "tagger")
    builder.add_node("tagger", tagger_node)
    builder.add_edge("tagger", END)
    return builder


graph = get_graph()
