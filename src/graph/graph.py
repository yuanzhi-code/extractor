import logging
from typing import List

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.graph.deduplicate import deduplicate_node
from src.graph.reporter import reporter_node
from src.graph.score import score_node
from src.graph.state import DeduplicateState, State
from src.graph.tagger import tagger_node

logger = logging.getLogger(__name__)


def get_graph() -> StateGraph:
    """
    Get the graph for the tagger node.
    """
    builder = StateGraph(State)
    builder.add_edge(START, "tagger")
    builder.add_node("tagger", tagger_node)
    builder.add_node("score", score_node)
    builder.add_edge("score", END)
    return builder


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


def run_reporter_graph(contents: List[str]):
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
            logger.error(f"Error: {e}")
            break


async def run_graph(content: str):
    if not content:
        raise ValueError("Content is required")

    graph = get_graph().compile()

    # try:
    #     print(graph.get_graph().draw_mermaid_png())
    # except Exception as e:
    #     logger.error(f"Error: {e}")

    init_state = {"content": content, "category": "business"}
    async for s in graph.astream(input=init_state, stream_mode="values"):
        try:
            if isinstance(s, dict) and "message" in s:
                message = s["message"]
                if isinstance(message, tuple):
                    logger.info("message: {}", message)
                else:
                    message.pretty_print()
        except Exception as e:
            logger.error(f"Error: {e}")
            break
