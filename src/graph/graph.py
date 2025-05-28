import logging

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.graph.score import score_node
from src.graph.state import State
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


async def run_graph(content: str):
    if not content:
        raise ValueError("Content is required")

    graph = get_graph().compile()

    # try:
    #     print(graph.get_graph().draw_mermaid_png())
    # except Exception as e:
    #     logger.error(f"Error: {e}")

    init_state = {
                    "content": content,
                    "category": "business"
                 }
    async for s in graph.astream(input=init_state, stream_mode="values"):
        try:
            if isinstance(s, dict) and "message" in s:
                message = s["message"]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
        except Exception as e:
            logger.error(f"Error: {e}")
            break
