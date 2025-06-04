import logging

from langgraph.graph import END, START, StateGraph

from src.graph.deduplicate import deduplicate_node
from src.graph.reporter import reporter_node
from src.graph.state import DeduplicateState

logger = logging.getLogger(__name__)


def get_reporter_graph() -> StateGraph:
    """
    Get the graph for the reporter node.
    """
    builder = StateGraph(DeduplicateState)
    builder.add_edge(START, "deduplicate")
    builder.add_node("deduplicate", deduplicate_node)
    builder.add_node("reporter", reporter_node)
    builder.add_edge("reporter", END)
    return builder


def run_reporter_graph(contents: list[str]):
    if not contents or len(contents) == 0:
        raise ValueError("Contents is required")

    graph = get_reporter_graph().compile()
    init_state = {"contents": contents}
    for s in graph.stream(input=init_state, stream_mode="values"):
        try:
            if isinstance(s, dict) and "message" in s:
                message = s["message"]
                if isinstance(message, tuple):
                    logger.info("message: {}", message)
                else:
                    message.pretty_print()
        except Exception as e:
            logger.exception("Error:")
            break
