import logging

from langgraph.graph import END, START, StateGraph

from src.graph.score import score_node
from src.graph.state import State
from src.graph.tagger import tagger_node
from src.models.rss_entry import RssEntry

logger = logging.getLogger(__name__)


def get_classification_graph() -> StateGraph:
    """
    Get the graph for the tagger node.
    """
    builder = StateGraph(State)
    builder.add_edge(START, "tagger")
    builder.add_node("tagger", tagger_node)
    builder.add_node("score", score_node)
    builder.add_edge("tagger", "score")
    builder.add_edge("score", END)
    return builder


async def run_classification_graph(entry: RssEntry):
    graph = get_classification_graph().compile()

    # try:
    #     print(graph.get_graph().draw_mermaid_png())
    # except Exception as e:
    #     logger.error(f"Error: {e}")

    init_state = {"entry": entry}
    async for s in graph.astream(input=init_state, stream_mode="values"):
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
