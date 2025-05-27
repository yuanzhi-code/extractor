import logging
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.messages import HumanMessage

from .tagger import tagger_node

from .state import State

logger = logging.getLogger(__name__)

def get_graph() -> StateGraph:
    """
    Get the graph for the tagger node.
    """
    builder = StateGraph(State)
    builder.add_edge(START, "tagger")
    builder.add_node("tagger", tagger_node)
    builder.add_edge("tagger", END)
    return builder

async def run_graph(content: str):
    if not content:
        raise ValueError("Content is required")

    graph = get_graph().compile()
    
    init_state= {
        "messages": [{"role": "user", "content": content}]
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