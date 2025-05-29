import logging

from langgraph.graph import END, START, StateGraph

from src.graph.nodes import score_node, tagger_node
from src.graph.state import State

logger = logging.getLogger(__name__)


def get_tag_score_graph() -> StateGraph:
    """
    Get the graph for the tagger node.
    """
    builder = StateGraph(State)
    builder.add_edge(START, "tagger")
    builder.add_node("tagger", tagger_node)
    builder.add_node("score", score_node)
    builder.add_edge("score", END)
    return builder


def get_graph() -> StateGraph:
    """
    get the graph with parallel sub graph for tagger and score node
    """
    builder = StateGraph(State)
    parallel = 10

    for i in range(parallel):
        builder.add_node(
            f"parallel_sub_graph_{i}", get_tag_score_graph().compile()
        )
        builder.add_edge(START, f"parallel_sub_graph_{i}")
        # TODO(woxqaq) point to deduplicate node
        builder.add_edge(f"parallel_sub_graph_{i}", END)
    return builder


async def run_graph(content: str):
    if not content:
        raise ValueError("Content is required")

    graph = get_graph().compile()

    try:
        logging.info(graph.get_graph().draw_mermaid())
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e

    # init_state = {"content": content, "category": "business"}
    # async for s in graph.astream(input=init_state, stream_mode="values"):
    #     try:
    #         if isinstance(s, dict) and "message" in s:
    #             message = s["message"]
    #             if isinstance(message, tuple):
    #                 print(message)
    #             else:
    #                 message.pretty_print()
    #     except Exception as e:
    #         logger.error(f"Error: {e}")
    #         break
