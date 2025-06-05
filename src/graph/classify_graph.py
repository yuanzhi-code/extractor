import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

from src.graph.score import score_node
from src.graph.state import ClassifyState
from src.graph.tagger import tagger_node, tagger_review_node
from src.models import db
from src.models.rss_entry import RssEntry
from src.models.score import EntryScore
from src.models.tags import EntryCategory

logger = logging.getLogger(__name__)


def get_classification_graph() -> CompiledStateGraph:
    """
    Get the graph for the tagger node.
    """
    builder = StateGraph(ClassifyState)

    def check_tag_and_score_exist(state: ClassifyState) -> bool:
        with Session(db) as session:
            entry_category = (
                session.query(EntryCategory)
                .filter(EntryCategory.entry_id == state["entry"].id)
                .first()
            )
            entry_score = (
                session.query(EntryScore)
                .filter(EntryScore.entry_id == state["entry"].id)
                .first()
            )
            if entry_category and entry_score:
                return END
            elif entry_category:
                return "to_score"
            else:
                return "to_tagger"

    builder.add_node("tagger", tagger_node)
    builder.add_node("tagger_review", tagger_review_node)
    builder.add_node("score", score_node)

    # builder.add_edge(START, "tagger")
    builder.add_conditional_edges(
        START,
        check_tag_and_score_exist,
        {
            "to_score": "score",
            "to_tagger": "tagger",
            END: END,
        },
    )
    builder.add_edge("tagger", "score")
    # builder.add_edge("tagger_review", "score")
    builder.add_edge("score", END)
    return builder.compile()


async def run_classification_graph(entry: RssEntry):
    graph = get_classification_graph()

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
                    logger.info(f"message: {message}")
                else:
                    message.pretty_print()
        except Exception as e:
            logger.exception("Error:")
            break
